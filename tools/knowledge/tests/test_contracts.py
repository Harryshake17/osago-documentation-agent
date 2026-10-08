"""Synthetic contract and provenance tests; no live connector access."""
import copy
import hashlib
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from validate import CATEGORIES, load, schema_errors, validate


def fixture():
    text = (Path(__file__).parent / 'fixtures/flow.cs').read_text(encoding='utf-8')
    confidence = {'score': 1.0, 'rationale': 'Direct synthetic fixture statement.'}
    snapshot = {'id': 'snapshot:fixture', 'adapter': 'repository', 'locator': 'fixtures/flow.cs',
                'repository': 'fixture', 'revision': 'fixture-v1', 'commit': None,
                'retrieved_at': '2026-10-01T09:00:00Z', 'content_hash': hashlib.sha256(text.encode()).hexdigest(),
                'hash_scope': 'full_content', 'working_tree_state': 'clean', 'availability': 'available', 'excerpt': text}
    evidence = {'id': 'evidence:fixture', 'source_type': 'CODE', 'source_location': 'fixtures/flow.cs:1',
                'repository': 'fixture', 'file': 'fixtures/flow.cs', 'class': 'FixtureHandler', 'method': 'Handle',
                'page': None, 'section': None, 'version': 'fixture-v1', 'commit': None,
                'snapshot_id': snapshot['id'], 'confidence': confidence, 'inference': False,
                'excerpt': text, 'basis_claim_ids': [], 'rationale': None}
    knowledge = {'schema_version': '1.0', 'package_id': 'kb:fixture', 'revision': 1,
                 'scope': {'id': 'scope:fixture', 'repositories': ['fixture'], 'revisions': {'fixture': 'fixture-v1'},
                           'components': ['fixture'], 'scenarios': ['scenario:fixture'], 'environments': ['test'],
                           'time_range': None, 'exclusions': ['production'], 'unresolved_constraints': []},
                 'sources': [snapshot], 'entities': [], 'claims': [], 'evidence': [evidence],
                 'relations': [], 'gaps': [], 'conflicts': []}
    for eid, typ in [('scenario:fixture', 'Scenario'), ('actor:fixture', 'Actor'),
                     ('FixtureCommand', 'CodeComponent'), ('FixtureHandler.Handle', 'CodeComponent')]:
        knowledge['entities'].append({'id': eid, 'type': typ, 'label': eid})
    def claim(cid, subject, predicate, value, modality='discovery'):
        knowledge['claims'].append({'id': cid, 'subject_id': subject, 'predicate': predicate, 'value': value,
                                    'text': f'Synthetic: {subject} {predicate} {value}', 'modality': modality,
                                    'context': {'repository': 'fixture', 'revision': 'fixture-v1', 'environment': 'test'},
                                    'support': [{'evidence_id': 'evidence:fixture', 'role': 'supports'}],
                                    'confidence': confidence, 'inference': False, 'validation_status': 'supported',
                                    'lifecycle_status': 'current'})
    values = {'business_goal': 'Process fixture request', 'trigger': 'FixtureCommand',
              'entry_state': 'fixture pending', 'exit_states': 'fixture done', 'actors': 'actor:fixture'}
    attrs = {}
    for key, value in values.items():
        cid = f'claim:{key}'
        claim(cid, 'scenario:fixture', key, value, 'source_statement')
        attrs[key + '/0' if key in ('exit_states', 'actors') else key] = [cid]
    claim('claim:anchor', 'scenario:fixture', 'entry_point', 'FixtureCommand')
    claim('claim:edge', 'FixtureCommand', 'registered_handler', 'FixtureHandler.Handle')
    base = {'schema_version': '1.0', 'scope_ref': 'scope:fixture', 'package_ref': {'id': 'kb:fixture', 'revision': 1}}
    criteria = {k: {'status': 'satisfied', 'claim_ids': [cid]} for k, cid in
                [('business_goal', 'claim:business_goal'), ('trigger', 'claim:trigger'),
                 ('lifecycle', 'claim:entry_state'), ('outcome', 'claim:exit_states')]}
    node = {'id': 'scenario:fixture', 'name': 'Fixture scenario', 'type': 'scenario', 'parent': None,
            'business_goal': values['business_goal'], 'trigger': values['trigger'], 'entry_state': values['entry_state'],
            'exit_states': [values['exit_states']], 'actors': ['actor:fixture'], 'recommended_document': True,
            'decomposition_reason': 'One synthetic goal/lifecycle.', 'discovered_sources': ['snapshot:fixture'],
            'attribute_claims': attrs, 'proposed_fields': ['name'], 'recommendation_basis_claim_ids': ['claim:business_goal'],
            'assessment': {'atomicity': 'atomic', 'lifecycle': {'start_claim_ids': ['claim:entry_state'],
                                                             'end_claim_ids': ['claim:exit_states']},
                           'criteria': criteria, 'unknown_fields': [], 'not_applicable_fields': []},
            'gap_ids': [], 'conflict_ids': []}
    tree = dict(base, id='tree:fixture', nodes=[node], relations=[],
                coverage={'status': 'complete', 'limitations': [], 'frontier': []})
    definition = dict(base, id='definition:fixture', scenario_id='scenario:fixture', name='Fixture scenario',
                      business_goal=values['business_goal'], trigger=values['trigger'], entry_state=values['entry_state'],
                      expected_outcomes=[values['exit_states']], actors=['actor:fixture'],
                      attribute_claims=copy.deepcopy(attrs), proposed_fields=['name'], unknown_fields=[],
                      entry_point_candidates=[{'id': 'FixtureCommand', 'snapshot_id': 'snapshot:fixture', 'claim_ids': ['claim:anchor']}],
                      known_source_refs=['snapshot:fixture'], aliases=['fixture'], exclusions=['production'], gap_ids=[])
    claim('claim:expected_outcomes', 'scenario:fixture', 'expected_outcomes', values['exit_states'], 'source_statement')
    definition['attribute_claims'].pop('exit_states/0')
    definition['attribute_claims']['expected_outcomes/0'] = ['claim:expected_outcomes']
    source = {'id': 'source:handler', 'source_type': 'CODE', 'artifact_kind': 'handler', 'category': 'commands_handlers',
              'repository': 'fixture', 'path': 'fixtures/flow.cs', 'symbol': 'FixtureHandler.Handle', 'page_id': None,
              'section': None, 'source_location': 'fixtures/flow.cs:5', 'version': 'fixture-v1', 'commit': None,
              'snapshot_ref': 'snapshot:fixture', 'relevance': 'Explicit synthetic command/handler registration.',
              'relevance_claim_ids': ['claim:edge'], 'relevance_path': [{'from_ref': 'FixtureCommand',
                  'relation_type': 'registered_handler', 'to_ref': 'FixtureHandler.Handle',
                  'evidence_ids': ['evidence:fixture'], 'claim_ids': ['claim:edge']}],
              'evidence_ids': ['evidence:fixture'], 'confidence': confidence}
    coverage, runs = [], []
    for category in CATEGORIES:
        rid = f'search:{category}'
        coverage.append({'category': category, 'status': 'found' if category == 'commands_handlers' else 'not_found',
                         'search_run_ids': [rid], 'basis_claim_ids': [], 'limitations': []})
        runs.append({'id': rid, 'category': category, 'adapter': 'confluence' if category == 'confluence_pages' else 'repository',
                     'query': 'synthetic fixture search', 'scope_ref': 'scope:fixture', 'revision': 'fixture-v1',
                     'cursor': None, 'status': 'complete', 'snapshot_ids': [], 'diagnostic': 'Synthetic search.'})
    source_map = dict(base, id='source-map:fixture', scenario='scenario:fixture', scenario_definition_ref=definition['id'], domain_tree_ref=tree['id'],
                      sources=[source], candidates=[], exclusions=[], category_coverage=coverage, search_runs=runs,
                      gap_ids=[], conflict_ids=[], coverage={'status': 'complete', 'limitations': [], 'frontier': []})
    return knowledge, tree, definition, source_map


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.k, self.t, self.d, self.m = fixture()

    def tree_errors(self):
        return validate('domain-tree', self.t, self.k)

    def map_errors(self):
        return validate('source-map', self.m, self.k, self.t, self.d)

    def test_valid_outputs(self):
        self.assertEqual(self.tree_errors(), [])
        self.assertEqual(validate('scenario-definition', self.d, self.k), [])
        self.assertEqual(self.map_errors(), [])

    def test_required_user_field(self):
        del self.t['nodes'][0]['trigger']
        self.assertTrue(self.tree_errors())

    def test_unknown_goal_with_gap_is_valid_partial(self):
        n = self.t['nodes'][0]
        n['business_goal'] = None
        n['assessment']['unknown_fields'] = ['business_goal']
        n['assessment']['atomicity'] = 'undetermined'
        n['assessment']['criteria']['business_goal'] = {'status': 'unknown', 'claim_ids': []}
        n['gap_ids'] = ['gap:goal']
        self.k['gaps'].append({'id': 'gap:goal', 'reason': 'unknown_field', 'question': 'What is the goal?',
                              'affected_ids': [n['id']], 'next_action': 'Read documented purpose.', 'status': 'open'})
        self.t['coverage']['status'] = 'partial'
        self.assertEqual(self.tree_errors(), [])
        n['gap_ids'] = []
        self.assertTrue(self.tree_errors())

    def test_atomic_without_lifecycle_rejected(self):
        self.t['nodes'][0]['assessment']['lifecycle'] = None
        self.assertTrue(self.tree_errors())

    def test_parent_cycle(self):
        self.t['nodes'][0]['parent'] = 'scenario:fixture'
        self.assertTrue(any('cycle' in e for e in self.tree_errors()))

    def test_unsupported_business_field(self):
        self.k['claims'][0]['support'] = []
        self.assertTrue(self.tree_errors())

    def test_stale_claim_rejected(self):
        self.k['claims'][0]['lifecycle_status'] = 'stale'
        self.assertTrue(self.tree_errors())

    def test_jira_only_not_primary(self):
        e = self.k['evidence'][0]
        e.update(source_type='JIRA', page='ISSUE-1')
        self.k['sources'][0]['adapter'] = 'jira'
        self.assertTrue(self.tree_errors())

    def test_inference_cycle(self):
        e = self.k['evidence'][0]
        e.update(source_type='INFERENCE', inference=True, basis_claim_ids=['claim:business_goal'], rationale='Cycle')
        for c in self.k['claims']:
            c['inference'] = True
        self.assertTrue(any('cycle' in e for e in self.tree_errors()))

    def test_supported_inference(self):
        e = copy.deepcopy(self.k['evidence'][0])
        e.update(id='evidence:inference', source_type='INFERENCE', inference=True,
                 basis_claim_ids=['claim:trigger'], rationale='Synthetic grounded deduction', snapshot_id=None)
        self.k['evidence'].append(e)
        self.k['claims'][0].update(inference=True, support=[{'evidence_id': e['id'], 'role': 'supports'}])
        self.assertEqual(self.tree_errors(), [])

    def test_conflict_not_silently_accepted(self):
        self.k['conflicts'].append({'id': 'conflict:goal', 'claim_ids': ['claim:business_goal', 'claim:trigger'],
                                   'disagreement': 'Synthetic disagreement', 'status': 'unresolved', 'resolution_claim_id': None})
        self.assertTrue(self.tree_errors())

    def test_word_match_without_path_not_accepted(self):
        self.m['sources'][0]['relevance_path'] = []
        self.assertTrue(self.map_errors())

    def test_broken_path(self):
        self.m['sources'][0]['relevance_path'][0]['from_ref'] = 'OtherCommand'
        self.assertTrue(self.map_errors())

    def test_unrelated_edge_claim(self):
        self.m['sources'][0]['relevance_path'][0]['claim_ids'] = ['claim:business_goal']
        self.assertTrue(self.map_errors())

    def test_missing_category(self):
        self.m['category_coverage'].pop()
        self.assertTrue(self.map_errors())

    def test_process_not_evidence_type(self):
        self.m['sources'][0]['source_type'] = 'PROCESS'
        self.assertTrue(self.map_errors())

    def test_not_found_requires_completed_search(self):
        self.m['search_runs'][0]['status'] = 'incomplete'
        self.assertTrue(self.map_errors())

    def test_source_version_mismatch(self):
        self.m['sources'][0]['version'] = 'other-version'
        self.assertTrue(self.map_errors())

    def test_found_with_unfinished_search_is_partial(self):
        run = next(r for r in self.m['search_runs'] if r['category'] == 'commands_handlers')
        run['status'] = 'incomplete'
        self.assertTrue(self.map_errors())
        self.m['coverage']['status'] = 'partial'
        self.assertEqual(self.map_errors(), [])

    def test_scope_leak(self):
        self.m['sources'][0]['repository'] = 'outside'
        self.assertTrue(self.map_errors())

    def test_input_revision_mismatch(self):
        self.d['package_ref']['revision'] = 2
        self.assertTrue(self.map_errors())

    def test_unknown_schema_version(self):
        self.t['schema_version'] = '99.0'
        self.assertTrue(self.tree_errors())

    def test_duplicate_json_yaml_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'duplicate.yaml'
            path.write_text('id: first\nid: second\n', encoding='utf-8')
            with self.assertRaises(ValueError):
                load(path)

    def test_contradiction_is_not_support(self):
        self.k['claims'][0]['support'][0]['role'] = 'contradicts'
        self.assertTrue(self.tree_errors())

    def test_candidates_can_be_saved_as_partial(self):
        self.m['candidates'].append({'id': 'candidate:word-match', 'source_location': 'Unrelated.cs',
                                     'category': 'controllers', 'snapshot_ref': None,
                                     'reason': 'Name match only; relation unconfirmed.', 'gap_ids': []})
        self.m['coverage']['status'] = 'partial'
        self.assertEqual(self.map_errors(), [])
        self.m['coverage']['status'] = 'complete'
        self.assertTrue(self.map_errors())

    def test_cli_yaml_and_json(self):
        import json
        import yaml
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, data in [('knowledge', self.k), ('domain-tree', self.t), ('scenario-definition', self.d)]:
                (root / f'{name}.yaml').write_text(yaml.safe_dump(data, allow_unicode=True), encoding='utf-8')
            map_path = root / 'source-map.json'
            map_path.write_text(json.dumps(self.m), encoding='utf-8')
            command = [sys.executable, str(Path(__file__).resolve().parents[1] / 'validate.py'),
                       'source-map', str(map_path), '--knowledge', str(root / 'knowledge.yaml'),
                       '--domain-tree', str(root / 'domain-tree.yaml'),
                       '--scenario-definition', str(root / 'scenario-definition.yaml')]
            result = subprocess.run(command, capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.m['sources'][0]['relevance_path'] = []
            map_path.write_text(json.dumps(self.m), encoding='utf-8')
            result = subprocess.run(command, capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
