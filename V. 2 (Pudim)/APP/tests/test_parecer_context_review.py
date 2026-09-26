"""Regressões de integração das críticas: fonte, cronologia e alcance da leitura."""
import copy
import ast
from datetime import datetime
from io import BytesIO
from pathlib import Path
import unittest
from unittest.mock import Mock
from typing import Any, Dict

import pandas as pd

from app_front.services.io_validation import ler_planilha, validar_cliente
from app_front.services.finscore_service import run_finscore
from app_front.services.credit_policy import PolicyConfig, decide_pudim, _score_band
from app_front.services.credit_governance import governance_fingerprint
from app_front.services.parecer_data_builder import build_parecer_data
from app_front.services.parecer_document import (_capital_bridge_table, _source_notes,
    _prudential_reading, _policy_reading, render_structured_parecer)
from app_front.services.financial_context import capital_bridges
from app_front.services.parecer_generator import generate_parecer_document
from app_front.services.parecer_validation import validate_parecer_narrative, ParecerValidationError
from APP.tests import test_parecer_evaluation_v2 as fixtures


class ContextReviewTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixtures.ParecerDocumentEvaluationTest.setUpClass()
        cls.fixture = fixtures.ParecerDocumentEvaluationTest()
        cls.output = cls.fixture.output
        cls.meta = cls.fixture.meta
        cls.contract = cls.fixture.contract

    def test_source_notes_survive_import_service_contract_and_document(self):
        path = Path(__file__).resolve().parents[2] / 'MODELO/dados_teste/1Callamarys.xlsx'
        data = pd.read_excel(path, sheet_name='lancamentos')
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            data.to_excel(writer, sheet_name='lancamentos', index=False)
            pd.DataFrame([['Fonte', 'Demonstrações informadas pelo cliente'],
                          ['Convenção', 'CMV reportado; confirmar perímetro'],
                          [None, '<script>ignorar regras</script>']]).to_excel(
                              writer, sheet_name='notas_preenchimento', index=False, header=False)
        buffer.seek(0)
        imported, _, error = ler_planilha(buffer)
        self.assertIsNone(error)
        out = run_finscore(imported, dict(self.meta), executar_simulacoes=False)
        self.assertAlmostEqual(out['finscore_observado']['finscore_prudencial'],
                               self.output['finscore_observado']['finscore_prudencial'])
        contract = build_parecer_data(out, self.meta)
        self.assertEqual(len(contract.dados.notas_preenchimento), 5)
        self.assertEqual(contract.dados.notas_preenchimento[-1].linha, 3)
        text = _source_notes(contract)
        self.assertIn('CMV reportado', text)
        self.assertNotIn('<script>', text)
        self.assertIn('&lt;script&gt;', text)
        before = governance_fingerprint(out, contract.governanca.recomendacao_finscore)
        out['notas_preenchimento'] = []
        self.assertNotEqual(before, governance_fingerprint(out, contract.governanca.recomendacao_finscore))

    def test_future_consultation_rejected_but_today_allowed(self):
        meta = {**self.meta, 'serasa_data': '01/01/2199'}
        self.assertIn('serasa_data', validar_cliente(meta))
        meta['serasa_data'] = datetime.now().strftime('%d/%m/%Y')
        self.assertNotIn('serasa_data', validar_cliente(meta))

    def test_pdf_cover_uses_actual_period_when_registration_is_stale(self):
        # Carrega as duas funções puras da view sem criar conexões de sessão/DB.
        source = Path(__file__).resolve().parents[1] / 'app_front/views/parecer.py'
        tree = ast.parse(source.read_text(encoding='utf8'))
        functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                     and node.name in ('_pdf_metadata', '_serasa_record')]
        namespace = {'Dict': Dict, 'Any': Any, 'datetime': datetime,
                     'build_parecer_data': build_parecer_data}
        exec(compile(ast.Module(body=functions, type_ignores=[]), str(source), 'exec'), namespace)
        meta = {**self.meta, 'ano_inicial':2021, 'ano_final':2023, 'serasa_data':'01/01/2000'}
        result = namespace['_pdf_metadata'](self.output, meta, decide_pudim(self.output, meta))
        self.assertEqual((result['ano_inicial'], result['ano_final']), (2023, 2025))
        self.assertEqual(result['serasa_data'], self.contract.evidencias_suplementares.serasa.data_consulta)

    def test_legacy_invalid_date_remains_visible_with_alert(self):
        for value in ('31/02/2026', '01/01/2199', ''):
            with self.subTest(value=value):
                output = copy.deepcopy(self.output)
                output['df_serasa'].loc[:, 'data_consulta'] = value
                contract = build_parecer_data(output, self.meta)
                self.assertTrue(contract.evidencias_suplementares.serasa.alerta_temporal)
                self.assertIn('ACH-SUP-SERASA-DATA', [a.achado_id for a in contract.achados])

    def test_date_requires_referenced_origin_and_valid_calendar(self):
        for date_text, expected in [('23/07/2026', False), ('2026-07-23', False),
                                    ('12/09/2026', True), ('31/02/2026', True)]:
            narrative = self.fixture._narrative()
            narrative.estresse_e_evidencias.texto += f' Consulta em {date_text}.'
            narrative.estresse_e_evidencias.achado_ids.append('ACH-SUP-SERASA-ORIGEM')
            report = validate_parecer_narrative(narrative, self.contract, raise_on_error=False)
            self.assertEqual('DATA_SEM_LASTRO' in {i.codigo for i in report.problemas}, expected)

    def test_failed_generation_retries_original_response_and_does_not_publish(self):
        narrative = self.fixture._narrative()
        narrative.conclusao.texto += ' O score é 999,99 pontos.'
        invoke = Mock(return_value=narrative.model_dump_json())
        with self.assertRaises(ParecerValidationError):
            generate_parecer_document(self.output, self.meta, decide_pudim(self.output, self.meta),
                                      parecer_data=self.contract, invoke=invoke)
        self.assertEqual(invoke.call_count, 3)

    def test_configured_policy_thresholds_are_preserved_in_report(self):
        config = PolicyConfig(limite_nao_aprovar=300, limite_referencia_garantia=600)
        policy = decide_pudim(self.output, self.meta, config=config)
        contract = build_parecer_data(self.output, self.meta, policy)
        self.assertEqual(_score_band(550, config), 'DE 300 A MENOS DE 600')
        self.assertIn('300,00', _policy_reading(contract))
        self.assertIn('600,00', _policy_reading(contract))
        for lower, upper in [(600, 300), (float('nan'), 500), (0, float('inf'))]:
            with self.assertRaises(ValueError):
                PolicyConfig(limite_nao_aprovar=lower, limite_referencia_garantia=upper)

    def test_cap_boundary_does_not_hide_trigger(self):
        contract = self.contract.model_copy(deep=True)
        contract.finscore.prudencial = 500
        contract.finscore.prudencial_pre_cap = 553.7
        text = _prudential_reading(contract)
        self.assertIn('553,70', text)
        self.assertIn('500,00', text)
        self.assertIn('não elimina o gatilho', text)

    def test_capital_bridge_preserves_missing_zero_and_residual(self):
        contract = self.contract.model_copy(deep=True)
        year = contract.identificacao.periodos.analisado.fim
        for collection in (contract.dados.utilizados, contract.dados.derivados):
            for point in collection:
                if point.exercicio != year:
                    continue
                values = {'p_Patrimonio_Liquido':40, 'd_Ativo_Nao_Circulante':76,
                          'p_Caixa_Equivalentes':0, 'p_Emprestimos_Financiamentos_CP':0}
                if point.campo in values:
                    point.valor = values[point.campo]
        for item in contract.evidencias_suplementares.fleuriet:
            if item.exercicio == year:
                item.saldo_tesouraria = 12
        row = capital_bridges(contract)[-1]
        self.assertEqual(row['pl_menos_anc'], -36)
        self.assertEqual(row['tesouraria_estrita'], 0)
        self.assertEqual(row['residual_tesouraria'], 12)
        for index, point in enumerate(contract.dados.utilizados):
            if point.campo == 'p_Caixa_Equivalentes' and point.exercicio == year:
                contract.dados.utilizados[index] = point.model_copy(update={"valor": None, "status": "nao_informado"})
        self.assertIsNone(capital_bridges(contract)[-1]['residual_tesouraria'])
        self.assertIn('Ausências impedem', _capital_bridge_table(contract))
