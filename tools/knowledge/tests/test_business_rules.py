"""Business-rule extraction contracts on synthetic code and provenance."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from validate import RULE_CATEGORIES, validate
from test_contracts import fixture


def rule_fixture():
    k, tree, definition, source_map = fixture()
    k['entities'] += [{'id': 'technical-step:guard', 'type': 'SystemBehaviour', 'label': 'Synthetic guard'},
                     {'id': 'BR-FIXTURE-001', 'type': 'BusinessRule', 'label': 'Synthetic constraint'}]
    template = copy.deepcopy(k['claims'][0])
    def claim(cid, subject, predicate, value, modality='implemented'):
        c = copy.deepcopy(template)
        c.update(id=cid, subject_id=subject, predicate=predicate, value=copy.deepcopy(value),
                 text=f'Synthetic: {predicate} {value}', modality=modality)
        k['claims'].append(c)
        return cid
    flow_claim = claim('claim:flow-implementation', 'technical-step:guard', 'implementation', 'FixtureHandler.Handle')
    base = {'schema_version': '1.0', 'scope_ref': 'scope:fixture', 'package_ref': {'id': 'kb:fixture', 'revision': 1}}
    flow = dict(base, id='flow:fixture', scenario_id='scenario:fixture', source_map_ref=source_map['id'],
                nodes=[{'id': 'technical-step:guard', 'component_id': 'FixtureHandler.Handle',
                        'source_ids': ['source:handler'], 'claim_ids': [flow_claim]}], relations=[],
                gap_ids=[], conflict_ids=[], coverage={'status': 'complete', 'limitations': [], 'frontier': []})
    rule = {'id': 'BR-FIXTURE-001', 'rule_kind': 'technical_constraint',
            'extraction_categories': ['guards', 'thresholds'],
            'rule_statement': 'Return 0 when fixture accuracy is below 7.', 'condition': 'accuracy < 7',
            'true_result': 'return 0', 'false_result': 'return 1',
            'affected_actor': ['actor:fixture'], 'affected_scenario': ['scenario:fixture'], 'affected_state': [],
            'externally_visible_result': 'UNKNOWN', 'business_rationale': 'UNKNOWN',
            'parameters': [{'name': 'accuracy threshold', 'value': 7, 'unit': None, 'origin': 'literal'}],
            'implementation': ['FixtureHandler.Handle'], 'source_ids': ['source:handler'],
            'evidence': ['evidence:fixture'], 'attribute_claims': {},
            'unknown_fields': ['affected_state', 'externally_visible_result', 'business_rationale'],
            'not_applicable_fields': [], 'gap_ids': ['gap:rationale', 'gap:external'], 'conflict_ids': []}
    for field in ('rule_kind', 'rule_statement', 'condition', 'true_result', 'false_result'):
        rule['attribute_claims'][field] = [claim(f'claim:rule:{field}', rule['id'], field, rule[field])]
    for field in ('affected_actor', 'affected_scenario', 'parameters', 'implementation'):
        for i, value in enumerate(rule[field]):
            rule['attribute_claims'][f'{field}/{i}'] = [claim(f'claim:rule:{field}:{i}', rule['id'], field, value)]
    k['gaps'] += [
        {'id': 'gap:rationale', 'reason': 'unknown_reason', 'question': 'Why this threshold?',
         'affected_ids': [rule['id']], 'next_action': 'Find explicit documented rationale.', 'status': 'open'},
        {'id': 'gap:external', 'reason': 'unknown_field', 'question': 'What is the external result/state?',
         'affected_ids': [rule['id']], 'next_action': 'Trace caller and result mapping.', 'status': 'open'}]
    categories = [{'category': c, 'status': 'found' if c in rule['extraction_categories'] else 'not_found',
                   'source_ids': ['source:handler'], 'rule_ids': [rule['id']] if c in rule['extraction_categories'] else [],
                   'claim_ids': [], 'diagnostic': 'Inspected the synthetic fixture body.'} for c in sorted(RULE_CATEGORIES)]
    result = dict(base, id='rules:fixture', scenario_id='scenario:fixture', technical_flow_ref=flow['id'],
                  source_map_ref=source_map['id'], rules=[rule], category_coverage=categories,
                  gap_ids=['gap:rationale', 'gap:external'], conflict_ids=[],
                  coverage={'status': 'partial', 'limitations': ['Business rationale and external mapping unknown.'], 'frontier': []})
    return k, tree, definition, source_map, flow, result


class BusinessRuleTests(unittest.TestCase):
    def setUp(self):
        self.k, self.t, self.d, self.m, self.f, self.r = rule_fixture()
        self.rule = self.r['rules'][0]

    def errors(self):
        return validate('business-rules', self.r, self.k, self.t, self.d, self.f, self.m)

    def test_unknown_rationale_valid_partial(self):
        self.assertEqual(self.errors(), [])
        self.assertEqual(validate('technical-flow', self.f, self.k, self.t, self.d, source_map=self.m), [])

    def test_unknown_rationale_needs_gap(self):
        self.rule['gap_ids'] = ['gap:external']
        self.assertTrue(self.errors())

    def test_invented_rationale_rejected(self):
        self.rule['business_rationale'] = 'Prevent underwriting risk.'
        self.rule['unknown_fields'].remove('business_rationale')
        self.assertTrue(self.errors())

    def test_inferred_rationale_cannot_be_business_fact(self):
        value = 'Synthetic inferred risk explanation.'
        self.rule['business_rationale'] = value
        self.rule['unknown_fields'].remove('business_rationale')
        e = copy.deepcopy(self.k['evidence'][0])
        e.update(id='evidence:rationale-inference', source_type='INFERENCE', snapshot_id=None,
                 inference=True, basis_claim_ids=['claim:rule:condition'], rationale='Hypothetical deduction')
        self.k['evidence'].append(e)
        c = copy.deepcopy(self.k['claims'][0])
        c.update(id='claim:rationale', subject_id=self.rule['id'], predicate='business_rationale', value=value,
                 inference=True, modality='inferred', support=[{'evidence_id': e['id'], 'role': 'supports'}])
        self.k['claims'].append(c)
        self.rule['attribute_claims']['business_rationale'] = [c['id']]
        self.rule['evidence'].append(e['id'])
        self.assertTrue(any('business meaning' in error for error in self.errors()))

    def test_explicit_source_stated_rationale(self):
        # Synthetic explicit author statement, not an actual OSAGO explanation.
        value = 'Synthetic documented fixture purpose.'
        self.k['sources'][0]['excerpt'] += '\n// Author rationale: ' + value
        import hashlib
        self.k['sources'][0]['content_hash'] = hashlib.sha256(self.k['sources'][0]['excerpt'].encode()).hexdigest()
        self.k['evidence'][0]['excerpt'] = self.k['sources'][0]['excerpt']
        self.rule['business_rationale'] = value
        self.rule['unknown_fields'].remove('business_rationale')
        c = copy.deepcopy(self.k['claims'][0])
        c.update(id='claim:rationale', subject_id=self.rule['id'], predicate='business_rationale',
                 value=value, modality='source_statement')
        self.k['claims'].append(c)
        self.rule['attribute_claims']['business_rationale'] = [c['id']]
        self.assertEqual(self.errors(), [])

    def test_missing_false_branch_can_stay_unknown(self):
        self.rule['false_result'] = 'UNKNOWN'
        self.rule['unknown_fields'].append('false_result')
        self.rule['attribute_claims'].pop('false_result')
        self.assertEqual(self.errors(), [])

    def test_external_error_without_support_rejected(self):
        self.rule['externally_visible_result'] = 'UI validation error'
        self.rule['unknown_fields'].remove('externally_visible_result')
        self.assertTrue(self.errors())

    def test_business_classification_needs_explicit_meaning(self):
        self.rule['rule_kind'] = 'business_rule'
        c = next(c for c in self.k['claims'] if c['id'] == 'claim:rule:rule_kind')
        c['value'] = 'business_rule'
        self.assertTrue(self.errors())
        c['modality'] = 'documented_requirement'
        self.k['sources'][0]['excerpt'] += '\n// Synthetic documented requirement: this threshold is a fixture business rule.'
        import hashlib
        self.k['sources'][0]['content_hash'] = hashlib.sha256(self.k['sources'][0]['excerpt'].encode()).hexdigest()
        self.k['evidence'][0]['excerpt'] = self.k['sources'][0]['excerpt']
        self.assertEqual(self.errors(), [])

    def test_candidate_source_not_accepted(self):
        self.rule['source_ids'] = ['candidate:unrelated']
        self.assertTrue(self.errors())

    def test_implementation_must_be_in_flow(self):
        self.f['nodes'] = []
        self.assertTrue(self.errors())

    def test_evidence_list_must_include_field_support(self):
        self.rule['evidence'] = ['missing-evidence']
        self.assertTrue(self.errors())

    def test_threshold_value_requires_matching_claim(self):
        self.rule['parameters'][0]['value'] = 8
        self.assertTrue(self.errors())

    def test_input_flow_revision_mismatch(self):
        self.f['package_ref']['revision'] = 2
        self.assertTrue(self.errors())

    def test_missing_input(self):
        self.assertTrue(validate('business-rules', self.r, self.k))

    def test_complete_cannot_hide_unknown(self):
        self.r['coverage'] = {'status': 'complete', 'limitations': [], 'frontier': []}
        self.assertTrue(self.errors())

    def test_all_categories_required(self):
        self.r['category_coverage'].pop()
        self.assertTrue(self.errors())

    def test_cli_business_rules(self):
        import yaml
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            files = {'knowledge.yaml': self.k, 'domain-tree.yaml': self.t, 'scenario-definition.yaml': self.d,
                     'source-map.json': self.m, 'technical-flow.json': self.f, 'business-rules.json': self.r}
            for name, data in files.items():
                (root / name).write_text(json.dumps(data) if name.endswith('.json') else yaml.safe_dump(data), encoding='utf-8')
            command = [sys.executable, str(Path(__file__).resolve().parents[1] / 'validate.py'),
                       'business-rules', str(root / 'business-rules.json')]
            for flag, name in [('knowledge', 'knowledge.yaml'), ('domain-tree', 'domain-tree.yaml'),
                               ('scenario-definition', 'scenario-definition.yaml'), ('technical-flow', 'technical-flow.json'),
                               ('source-map', 'source-map.json')]:
                command += [f'--{flag}', str(root / name)]
            result = subprocess.run(command, capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
