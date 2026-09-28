"""Golden regression against the main integrated on 2026-09-27.

No automatic fixture update, API calls, Streamlit sessions or production DB.
"""
from __future__ import annotations

import copy
import json
import unittest

from golden_model_support import CASES, DATA, FIXTURES, capture_case, differences, sha256


class ModelControlsGoldenTest(unittest.TestCase):
    @staticmethod
    def restorable_contract(snapshot):
        payload = copy.deepcopy(snapshot['report_contract'])
        # Os snapshots tipados armazenam datetime como marcador explícito.
        timestamp = payload['metadados_funcionais']['processado_em']
        payload['metadados_funcionais']['processado_em'] = timestamp['value']
        return payload

    @classmethod
    def setUpClass(cls):
        cls.expected = {name: json.loads((FIXTURES / f'{name}.json').read_text(encoding='utf8'))
                        for name in CASES}
        cls.actual = {name: capture_case(name) for name in CASES}

    def compare_case(self, name):
        # Delta autorizado da política v4; os snapshots históricos ficam intactos.
        # Todo o output do motor e os demais campos continuam comparados integralmente.
        expected = copy.deepcopy(self.expected[name])
        policy = expected['policy']
        labels = {'mobicloud': 'Risco reduzido', 'ssa_mro': 'Risco aceitável', 'jns': 'Risco relevante'}
        policy['segmento_politica'] = labels[name]
        policy['parametros_politica'].update(limite_aprovacao_qualificada=750.0,
                                            confiabilidade_minima_qualificada=0.90)
        if name == 'mobicloud':
            policy['rotulo'] = 'Aprovação qualificada'
            policy['fundamentacao'][0] = 'FinScore prudencial de 868,78 pontos, na faixa risco reduzido.'
            policy['fundamentacao'].append(
                'Aprovação qualificada: FinScore de pelo menos 750 pontos, qualidade dos dados de pelo menos 90%, '
                'sem bloqueios ou caps acionados e sem o sinal de estresse restritivo existente.')
        elif name == 'jns':
            policy['fundamentacao'][0] = 'FinScore prudencial de 372,22 pontos, na faixa risco relevante.'
        recommendation = expected['report_contract']['governanca']['recomendacao_finscore']
        recommendation.update(faixa=policy['segmento_politica'], rotulo=policy['rotulo'],
                              fundamentos=copy.deepcopy(policy['fundamentacao']),
                              parametros_politica=copy.deepcopy(policy['parametros_politica']),
                              versao_politica='three-decisions-finscore-only-v4-qualified-approval')
        finding = next(item for item in expected['report_contract']['achados'] if item['achado_id'] == 'ACH-RES-FINSCORE')
        finding['evidencias'][9:9] = [
            {'origem': 'governanca.recomendacao_finscore', 'campo': field, 'valor': value,
             'exercicio': None, 'unidade': None}
            for field, value in (('faixa', policy['segmento_politica']), ('rotulo', policy['rotulo']))
        ]
        changes = differences(expected, self.actual[name])
        self.assertFalse(changes, '\n'.join(changes))

    def test_mobicloud_full_golden(self):
        self.compare_case('mobicloud')

    def test_ssa_mro_full_golden(self):
        self.compare_case('ssa_mro')

    def test_jns_full_golden(self):
        self.compare_case('jns')

    def test_mobicloud_preserves_approval_without_blockers_and_visible_saturation(self):
        case = self.actual['mobicloud']
        observed = case['output']['finscore_observado']
        self.assertAlmostEqual(observed['finscore_prudencial'], 868.78, places=2)
        self.assertEqual(case['policy']['decisao'], 'aprovar')
        self.assertFalse(case['policy']['bloqueios'])
        self.assertEqual(case['output']['status_qualidade']['alertas_bloqueadores_decisao'], 0)
        alerts = case['report_contract']['qualidade']['alertas']
        self.assertTrue(any(item['categoria'] == 'SATURACAO_CURVA' for item in alerts))
        self.assertEqual(case['report_contract']['evidencias_suplementares']['serasa']['nivel_divergencia'], 'elevada')

    def test_ssa_cap_preserves_math_and_current_mitigator_policy(self):
        case = self.actual['ssa_mro']
        observed = case['output']['finscore_observado']
        self.assertAlmostEqual(observed['finscore_prudencial_pre_cap'], 516.06, places=2)
        self.assertEqual(observed['cap_prudencial_aplicavel'], 500.0)
        self.assertEqual(observed['finscore_prudencial'], 500.0)
        self.assertEqual(case['policy']['decisao'], 'aprovar')
        self.assertEqual(case['policy']['segmento_politica'], 'Risco aceitável')
        self.assertEqual(case['policy']['rotulo'], 'Aprovar')
        self.assertTrue(case['policy']['garantia']['recomendada'])
        self.assertNotIn('decision_state', case['policy'])

    def test_jns_preserves_provisional_calculation_and_decision_block(self):
        case = self.actual['jns']
        observed = case['output']['finscore_observado']
        status = case['output']['status_qualidade']
        self.assertAlmostEqual(observed['finscore_prudencial'], 372.22, places=2)
        self.assertTrue(status['apto_calculo'])
        self.assertFalse(status['apto_decisao'])
        self.assertEqual(status['alertas_bloqueadores_decisao'], 2)
        self.assertEqual(observed['utilizavel_decisao'], 'NAO')
        self.assertEqual(case['policy']['decisao'], 'dados_inconsistentes')
        self.assertTrue(case['policy']['bloqueios_detalhados'])

    def test_input_and_fixture_integrity(self):
        manifest = json.loads((FIXTURES / 'manifest.json').read_text(encoding='utf8'))
        for name, spec in CASES.items():
            with self.subTest(case=name):
                record = manifest['cases'][name]
                self.assertEqual(sha256(DATA / spec['file']), record['input']['sha256'])
                self.assertEqual(sha256(FIXTURES / record['snapshot']), record['sha256'])

    def test_historical_contracts_remain_readable_without_reclassification(self):
        from app_front.components.parecer_data_schema import ParecerData
        for name, snapshot in self.expected.items():
            with self.subTest(case=name):
                saved = self.restorable_contract(snapshot)
                restored = ParecerData.model_validate(saved)
                self.assertEqual(restored.governanca.recomendacao_finscore.faixa,
                                 saved['governanca']['recomendacao_finscore']['faixa'])
                self.assertEqual(restored.finscore.prudencial, saved['finscore']['prudencial'])

    def test_qualified_contract_rejects_cap_and_restrictive_stress_tampering(self):
        from app_front.components.parecer_data_schema import ParecerData
        payload = self.restorable_contract(self.actual['mobicloud'])
        payload['finscore']['caps'] = copy.deepcopy(self.actual['ssa_mro']['report_contract']['finscore']['caps'])
        with self.assertRaisesRegex(ValueError, 'cap prudencial acionado'):
            ParecerData.model_validate(payload)
        payload = self.restorable_contract(self.actual['mobicloud'])
        severe = next(row for row in payload['cenarios']['deterministicos'] if row['nome'] == 'SEVERO')
        severe['finscore_prudencial'] = 249.99
        with self.assertRaisesRegex(ValueError, 'cenário severo restritivo'):
            ParecerData.model_validate(payload)

    def test_comparator_detects_score_policy_weight_and_blocker_mutations(self):
        before = self.expected['ssa_mro']
        mutations = [
            ('score', lambda case: case['output']['finscore_observado'].__setitem__('finscore_prudencial', 500.01)),
            ('policy', lambda case: case['policy'].__setitem__('decisao', 'nao_aprovar')),
            ('weight', lambda case: case['report_contract']['finscore']['pesos_pca'][0].__setitem__('peso_adaptativo', 0.99)),
            ('blocker', lambda case: case['policy']['bloqueios'].append('new block')),
        ]
        for name, mutate in mutations:
            with self.subTest(mutation=name):
                changed = copy.deepcopy(before)
                mutate(changed)
                self.assertTrue(differences(before, changed))

    def test_comparator_preserves_missing_zero_types_and_subcent_changes(self):
        self.assertTrue(differences({'x': {'__kind__': 'float', 'value': 'nan'}}, {'x': 0.0}))
        self.assertTrue(differences({'x': None}, {'x': 0.0}))
        self.assertTrue(differences({'x': False}, {'x': 0}))
        self.assertTrue(differences({'x': 500.0}, {'x': 500.0001}))
        self.assertFalse(differences({'x': 500.0}, {'x': 500.0 + 1e-12}))


if __name__ == '__main__':
    unittest.main()
