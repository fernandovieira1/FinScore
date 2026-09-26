from __future__ import annotations
import copy
from datetime import date, timedelta
from io import BytesIO
from pathlib import Path
import unittest
import numpy as np
import pandas as pd
from app_front.finscore_v2 import core, executar_finscore
from app_front.finscore_v2.assessment import is_springate_applicable, validate_serasa_date
from app_front.services.credit_policy import decide_pudim, PolicyConfig
from app_front.services.finscore_service import run_finscore
from app_front.services.io_validation import ler_planilha, validar_cliente
from app_front.services.parecer_data_builder import build_parecer_data
from app_front.services.parecer_document import render_structured_parecer, select_report_content, _simulation_table
from app_front.services.parecer_validation import _validate_semantics
from APP.tests.test_parecer_pudim_v2 import _narrative

class ParecerAuditV3Test(unittest.TestCase):
    def simulation_contract(self, valid):
        from app_front.components.parecer_data_schema import SimulationSummary, SimulationDiagnostic
        contract=self.contract.model_copy(deep=True)
        contract.cenarios.resumos_simulacao=[SimulationSummary(abordagem='independente',metodo='prudencial',numero_trajetorias=100,media=600,frequencias=[{'corte':500,'frequencia':.2},{'corte':250,'frequencia':.1},{'corte':125,'frequencia':.03}])]
        contract.cenarios.diagnosticos=[SimulationDiagnostic(abordagem='independente',valida_para_interpretacao=valid)]
        return contract

    def test_frequency_table_valid_simulation(self):
        text=_simulation_table(self.simulation_contract(True))
        self.assertIn('FinScore < 500',text);self.assertIn('20,00%',text)
        self.assertIn('não são probabilidades de inadimplência',text)

    def test_frequency_table_invalid_simulation(self):
        text=_simulation_table(self.simulation_contract(False))
        self.assertNotIn('FinScore < 500',text);self.assertIn('indisponível para interpretação',text)

    def test_single_sentence_is_not_duplicated(self):
        from app_front.services.parecer_document import _split_paragraph
        self.assertEqual(_split_paragraph('Texto único.'),('Texto único.',''))

    @classmethod
    def setUpClass(cls):
        cls.data=pd.read_excel(Path(__file__).parents[2]/'MODELO/dados_teste/5umarket - Mobicloud Tecnologia.xlsx',sheet_name='lancamentos')
        cls.meta=dict(empresa='Teste',cnpj='00.000.000/0000-00',ano_inicial=2023,ano_final=2025,serasa=500,serasa_data='22/09/2026',tipo_empresa='Indústria')
        cls.output=run_finscore(cls.data,dict(cls.meta),executar_simulacoes=False)
        cls.contract=build_parecer_data(cls.output,cls.meta)

    def policy(self, score, caps=()):
        output=copy.deepcopy(self.output)
        output['finscore_observado']['finscore_prudencial']=score
        output['df_caps_prudenciais']=pd.DataFrame([{'cap':cap,'justificativa':'Cap de teste'} for cap in caps],columns=['cap','justificativa'])
        return decide_pudim(output,self.meta)

    def test_natural_500(self):
        self.assertEqual(self.policy(500)['segmento_politica'],'500 OU MAIS')
    def test_natural_above_500(self):
        self.assertEqual(self.policy(800)['segmento_politica'],'500 OU MAIS')
    def test_binding_500_cap(self):
        p=self.policy(500,[500]);self.assertEqual(p['segmento_politica'],'APROVAÇÃO SUJEITA A MITIGADORES');self.assertTrue(p['garantia']['recomendada'])
    def test_multiple_caps(self):
        self.assertTrue(self.policy(500,[650,500])['cap_acionado_ate_500'])
    def test_below_500_other_rule(self):
        self.assertEqual(self.policy(350)['segmento_politica'],'250 A 499,99')
    def test_low_cap_does_not_override_decline(self):
        self.assertEqual(self.policy(200,[500])['decisao'],'nao_aprovar')

    def test_industry_applicable(self):self.assertTrue(is_springate_applicable({'tipo_empresa':'Indústria'}))
    def test_trade_applicable(self):self.assertTrue(is_springate_applicable({'tipo_empresa':'Comércio'}))
    def test_services_applicable(self):self.assertTrue(is_springate_applicable({'tipo_empresa':'Serviços não financeiros'}))
    def test_insurer_not_applicable(self):
        frame=core.calcular_springate(self.output['df_contas_derivadas'],{'tipo_empresa':'Seguradora'})
        self.assertTrue(frame.springate_S.isna().all());self.assertEqual(set(frame.classificacao),{'NÃO APLICÁVEL'})
    def test_financial_types_not_applicable(self):
        for kind in ('Banco','Instituição financeira','Cooperativa de crédito'):
            with self.subTest(kind=kind):self.assertFalse(is_springate_applicable({'tipo_empresa':kind}))
    def test_unknown_not_inferred_from_name(self):self.assertFalse(is_springate_applicable({'empresa':'Indústria Exemplo'}))
    def test_financial_cnae_overrides_sector(self):self.assertFalse(is_springate_applicable({'tipo_empresa':'Serviços','cnae':'6422-1/00'}))

    def test_serasa_same_date(self):self.assertEqual(validate_serasa_date('26/09/2026',date(2026,9,26)),date(2026,9,26))
    def test_serasa_prior_date(self):self.assertEqual(validate_serasa_date('25/09/2026',date(2026,9,26)),date(2026,9,25))
    def test_serasa_future_date(self):
        with self.assertRaisesRegex(ValueError,'posterior'):validate_serasa_date('27/09/2026',date(2026,9,26))
    def test_serasa_future_rejected_by_engine(self):
        with self.assertRaisesRegex(ValueError,'posterior'):executar_finscore(self.data,serasa_data=(date.today()+timedelta(days=1)).isoformat(),executar_simulacoes=False)
    def test_serasa_future_rejected_by_form(self):
        meta={**self.meta,'serasa_data':'27/09/2026','data_analise':date(2026,9,26)}
        self.assertIn('serasa_data',validar_cliente(meta))

    def test_fleuriet_residual_and_unchanged_original(self):
        frame=self.output['df_fleuriet_complementar'];accounts=self.output['df_contas_derivadas']
        np.testing.assert_allclose(frame.ST_s,frame.CDG-frame.NCG_s)
        np.testing.assert_allclose(frame.T_estrito,accounts.p_Caixa_Equivalentes-accounts.p_Emprestimos_Financiamentos_CP)
        np.testing.assert_allclose(frame.residuo_fleuriet,frame.ST_s-frame.T_estrito)
    def test_fleuriet_missing_cash_does_not_become_zero(self):
        accounts=self.output['df_contas_derivadas'].copy();accounts['p_Caixa_Equivalentes']=np.nan
        self.assertTrue(core.calcular_fleuriet_simplificado(accounts).T_estrito.isna().all())
    def test_variations_zero_and_negative_bases(self):
        data=self.output['df_contas_analise'].copy()
        for values, label in [([0,1,1],'base nula ou próxima de zero'),([-100,100,100],'mudança de sinal'),([100,0,0],'variação percentual')]:
            data['p_Caixa_Equivalentes']=values
            rows=[r for r in core.detect_abrupt_variations(data) if r['conta']=='p_Caixa_Equivalentes']
            self.assertTrue(rows)
            if values[0]<=0:self.assertIsNone(rows[0]['variacao_percentual'])
    def test_variations_preserve_legacy_penalty_count(self):
        data=self.output['df_contas_analise'].copy();count=0
        for account in core.MONITORED_VARIATION_ACCOUNTS:
            for previous,current in zip(data[account],data[account].iloc[1:]):
                if pd.notna(previous) and pd.notna(current) and abs(previous)>1e-12 and abs(current/previous-1)>=.5:count+=1
        self.assertEqual(sum(r['alerta_legado'] for r in core.detect_abrupt_variations(data)),count)

    def workbook(self, notes=None):
        stream=BytesIO()
        with pd.ExcelWriter(stream,engine='openpyxl') as writer:
            self.data.to_excel(writer,sheet_name='lancamentos',index=False)
            if notes is not None:pd.DataFrame(notes).to_excel(writer,sheet_name='notas_preenchimento',index=False,header=False)
        stream.seek(0);return stream
    def test_notes_single_column_and_key_value(self):
        data,_,error=ler_planilha(self.workbook([['Fonte','DF assinada'],[None,None],['Convenção: caixa inclui aplicações',None]]))
        self.assertIsNone(error);notes=data.attrs['finscore_notas_preenchimento']
        self.assertEqual(notes[0]['celulas'],['Fonte','DF assinada']);self.assertEqual(notes[1]['linha'],3)
    def test_absent_notes(self):
        data,_,error=ler_planilha(self.workbook());self.assertIsNone(error);self.assertEqual(data.attrs['finscore_notas_preenchimento'],[])
    def test_notes_survive_contract_and_escape_html(self):
        output=copy.deepcopy(self.output);output['notas_preenchimento']=[{'linha':1,'celulas':['Fonte: <script>bad()</script>']}]
        contract=build_parecer_data(output,self.meta);text=render_structured_parecer(_narrative(),contract)
        self.assertNotIn('<script>',text);self.assertIn('&lt;script&gt;',text)
        self.assertEqual(contract.model_dump()['notas_preenchimento'],output['notas_preenchimento'])
    def test_pdf_levels_keep_traceability(self):
        full=render_structured_parecer(_narrative(),self.contract)
        main=select_report_content(full,'Parecer principal');annex=select_report_content(full,'Anexo técnico')
        self.assertNotIn('## Anexo 1',main);self.assertIn('## Anexo 2',main);self.assertIn('## Anexo 1',annex)
        self.assertEqual(select_report_content(full,'Parecer com anexo técnico'),full)
    def test_report_discloses_debt_and_avoids_quality_merit(self):
        text=render_structured_parecer(_narrative(),self.contract)
        self.assertIn('Perímetro da dívida FinScore',text);self.assertIn('Tesouraria estrita',text)
        final=text.split('## 8. Considerações finais')[1].split('## Anexo 1')[0]
        self.assertNotIn('da qualidade dos dados',final);self.assertNotIn('Springate de',final)
        self.assertNotIn('antes de uso em produção',text)
        self.assertIn('ausência de cap prudencial acionado de 500 ou menos',text)
    def test_semantic_guard_quality_merit(self):
        n=_narrative();n.conclusao.texto='A recomendação Aprovar decorre da qualidade dos dados.'
        self.assertIn('QUALIDADE_COMO_MERITO',[issue.codigo for issue in _validate_semantics(n,self.contract)])
    def test_blocked_conclusion_is_not_based_on_economic_merit(self):
        from app_front.services.parecer_document import _final_considerations
        data=pd.read_excel(Path(__file__).parents[2]/'MODELO/dados_teste/12Grupo JNP - JNS Seguradora.xlsx',sheet_name='lancamentos')
        meta={**self.meta,'tipo_empresa':'Seguradora'}
        output=run_finscore(data,meta,executar_simulacoes=False)
        contract=build_parecer_data(output,meta)
        self.assertEqual(contract.governanca.recomendacao_finscore.codigo.value,'dados_inconsistentes')
        final=_final_considerations(contract)
        self.assertNotIn('fundamentada na leitura econômico-financeira',final)
        self.assertIn('decorrente dos bloqueios informacionais',final)
    def test_semantic_guard_internal_message(self):
        n=_narrative();n.conclusao.texto='As âncoras devem ser revistas antes do uso em produção.'
        self.assertIn('DIAGNOSTICO_INTERNO',[issue.codigo for issue in _validate_semantics(n,self.contract)])
    def test_contractor_policy_preserves_numeric_score(self):
        cfg=PolicyConfig(rotulos_faixas={'500 OU MAIS':'Faixa institucional alta'},texto_recomendacao='Sujeita à política interna.')
        p=decide_pudim(self.output,self.meta,cfg)
        self.assertEqual(p['finscore_prudencial'],self.output['finscore_observado']['finscore_prudencial'])
        contract=build_parecer_data(self.output,self.meta,p)
        self.assertEqual(contract.governanca.recomendacao_finscore.faixa,'Faixa institucional alta')
