"""Golden regression against the main integrated on 2026-09-27.

No automatic fixture update, API calls, Streamlit sessions or production DB.
"""
from __future__ import annotations

import copy
import json
import unittest

from golden_model_support import CASES, DATA, FIXTURES, capture_case, differences, sha256


class ModelControlsGoldenTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.expected = {name: json.loads((FIXTURES / f'{name}.json').read_text(encoding='utf8'))
                        for name in CASES}
        cls.actual = {name: capture_case(name) for name in CASES}

    def compare_case(self, name):
        changes = differences(self.expected[name], self.actual[name])
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
        self.assertEqual(case['policy']['segmento_politica'], 'APROVAÇÃO SUJEITA A MITIGADORES')
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
