"""Scenario reconstruction on synthetic flows; no OSAGO facts asserted."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from validate import validate, schema_errors
from scenario import build_scenario, flow_selectors
from test_business_rules import rule_fixture


def scenario_fixture():
    k, tree, definition, source_map, technical, rules = rule_fixture()
    template = copy.deepcopy(k['claims'][0])
    def claim(cid, subject, predicate, value, modality='implemented'):
        c = copy.deepcopy(template)
        c.update(id=cid, subject_id=subject, predicate=predicate, value=copy.deepcopy(value),
                 text=f'Synthetic: {predicate} {value}', modality=modality)
        k['claims'].append(c)
        return cid
    k['entities'].append({'id': 'decision:accuracy', 'type': 'Decision', 'label': 'Synthetic technical guard'})
    step_ids = ['scenario-step:guard', 'scenario-step:return-one', 'scenario-step:return-zero']
    steps = []
    for order, sid in enumerate(step_ids, 1):
        k['entities'].append({'id': sid, 'type': 'ScenarioStep', 'label': sid})
        guard = order == 1
        step = {'id': sid, 'order': order, 'kind': 'decision' if guard else 'system_reaction',
                'actor': None, 'action': 'Check accuracy' if guard else 'Return fixture result',
                'business_meaning': 'UNKNOWN',
                'system_behavior': 'Evaluate accuracy < 7' if guard else ('return 1' if order == 2 else 'return 0'),
                'evaluated_rules': ['BR-FIXTURE-001'] if guard else [], 'integrations': [],
                'state_before': None, 'state_after': None, 'user_result': 'UNKNOWN',
                'implementation': ['FixtureHandler.Handle'], 'technical_step_refs': ['technical-step:guard'],
                'decision_ref': 'decision:accuracy' if guard else None, 'decision_kind': 'technical' if guard else 'none',
                'source_ids': ['source:handler'], 'evidence': ['evidence:fixture'], 'attribute_claims': {},
                'unknown_fields': ['business_meaning', 'state_before', 'state_after', 'user_result'],
                'not_applicable_fields': ['actor', 'integrations'] + ([] if guard else ['evaluated_rules']),
                'gap_ids': [f'gap:{sid}'], 'conflict_ids': []}
        k['gaps'].append({'id': f'gap:{sid}', 'reason': 'unknown_reason', 'question': 'Business meaning, states and actor result?',
                         'affected_ids': [sid], 'next_action': 'Find documents and caller/result mapping.', 'status': 'open'})
        for field in ['kind', 'action', 'system_behavior'] + (['decision_ref', 'decision_kind'] if guard else []):
            step['attribute_claims'][field] = [claim(f'claim:{sid}:{field}', sid, field, step[field])]
        for field in ('evaluated_rules', 'implementation'):
            for i, value in enumerate(step[field]):
                step['attribute_claims'][f'{field}/{i}'] = [claim(f'claim:{sid}:{field}:{i}', sid, field, value)]
        for field in step['not_applicable_fields']:
            step['attribute_claims'][f'not_applicable/{field}'] = [claim(f'claim:{sid}:na:{field}', sid, 'not_applicable', field)]
        steps.append(step)
    transitions = []
    for index, (target, outcome, condition) in enumerate([(step_ids[1], 'false', 'accuracy >= 7'), (step_ids[2], 'true', 'accuracy < 7')]):
        cids = [claim(f'claim:edge:{index}', step_ids[0], 'rule_branch', target),
                claim(f'claim:edge:{index}:condition', step_ids[0], 'branch_condition',
                      {'rule_id': 'BR-FIXTURE-001', 'outcome': outcome, 'condition': condition})]
        transitions.append({'id': f'transition:{index}', 'from_step': step_ids[0], 'to_step': target,
                            'kind': 'rule_branch', 'decision_ref': 'decision:accuracy', 'rule_ref': 'BR-FIXTURE-001',
                            'rule_outcome': outcome, 'condition': condition, 'claim_ids': cids,
                            'source_ids': ['source:handler'], 'evidence': ['evidence:fixture'], 'gap_ids': [], 'conflict_ids': []})
    main_condition = 'accuracy >= 7'
    alt_condition = 'accuracy < 7'
    main_claim = claim('claim:flow:main', 'scenario:fixture', 'flow_condition', main_condition)
    alt_claim = claim('claim:flow:alternative', 'scenario:fixture', 'flow_condition', alt_condition)
    main_type = claim('claim:flow:main:type', 'scenario:fixture', 'flow_type',
                      {'flow_id': 'scenario-flow:main', 'type': 'main'}, 'source_statement')
    alt_type = claim('claim:flow:alternative:type', 'scenario:fixture', 'flow_type',
                     {'flow_id': 'scenario-flow:alternative', 'type': 'alternative'}, 'source_statement')
    flows = [
        {'id': 'scenario-flow:main', 'type': 'main', 'entry_step': step_ids[0], 'branch_from': None,
         'entry_condition': main_condition, 'condition_claim_ids': [main_claim],
         'type_claim_ids': [main_type],
         'step_refs': step_ids[:2], 'terminal_steps': [step_ids[1]], 'gap_ids': [], 'conflict_ids': []},
        {'id': 'scenario-flow:alternative', 'type': 'alternative', 'entry_step': step_ids[2], 'branch_from': step_ids[0],
         'entry_condition': alt_condition, 'condition_claim_ids': [alt_claim],
         'type_claim_ids': [alt_type],
         'step_refs': [step_ids[2]], 'terminal_steps': [step_ids[2]], 'gap_ids': [], 'conflict_ids': []}]
    coverage = [
        {'category': 'main', 'status': 'found', 'flow_ids': ['scenario-flow:main'], 'source_ids': ['source:handler'],
         'claim_ids': [main_claim], 'diagnostic': 'Inspected synthetic return-one path.'},
        {'category': 'alternative', 'status': 'found', 'flow_ids': ['scenario-flow:alternative'], 'source_ids': ['source:handler'],
         'claim_ids': [alt_claim], 'diagnostic': 'Inspected synthetic return-zero path.'},
        {'category': 'error', 'status': 'incomplete', 'flow_ids': [], 'source_ids': ['source:handler'],
         'claim_ids': [], 'diagnostic': 'Caller error mapping unavailable in fixture.'}]
    result = {'schema_version': '1.0', 'id': 'scenario-output:fixture', 'scenario_id': 'scenario:fixture',
              'scope_ref': 'scope:fixture', 'package_ref': {'id': 'kb:fixture', 'revision': 1},
              'scenario_definition_ref': definition['id'], 'technical_flow_ref': technical['id'],
              'business_rules_ref': rules['id'], 'source_map_ref': source_map['id'],
              'confluence_evidence_ids': [], 'test_evidence_ids': [], 'steps': steps, 'flows': flows,
              'transitions': transitions, 'flow_coverage': coverage,
              'gap_ids': [g['id'] for g in k['gaps']], 'conflict_ids': [],
              'coverage': {'status': 'partial', 'limitations': ['Synthetic technical backbone; business meaning unknown.'], 'frontier': []}}
    result=build_scenario({key:value for key,value in result.items() if key not in {'steps','flows','transitions'}},steps,flows,transitions)
    return k, tree, definition, source_map, technical, rules, result


class ScenarioTests(unittest.TestCase):
    def setUp(self):
        self.k, self.t, self.d, self.m, self.f, self.r, self.s = scenario_fixture()

    def errors(self):
        return validate('scenario', self.s, self.k, self.t, self.d, self.f, self.m, self.r)

    def test_main_and_alternative_preserve_unknown(self):
        self.assertEqual(self.errors(), [])

    def test_single_main_selector_and_variant_refs(self):
        self.assertEqual(self.s['main_flow'], 'scenario-flow:main')
        self.assertEqual(self.s['alternative_flows'], ['scenario-flow:alternative'])
        self.assertEqual(self.s['exception_flows'], [])
        self.assertEqual(self.errors(), [])
        self.s['main_flow'] = 'scenario-flow:alternative'
        self.assertTrue(any('sole main flow' in e for e in self.errors()))

    def test_second_main_is_rejected_even_with_classification_evidence(self):
        other = copy.deepcopy(self.s['flows'][0]); other['id'] = 'scenario-flow:second-main'
        c = copy.deepcopy(next(c for c in self.k['claims'] if c['id'] == 'claim:flow:main:type'))
        c.update(id='claim:second-main:type', value={'flow_id':other['id'], 'type':'main'})
        self.k['claims'].append(c); other['type_claim_ids'] = [c['id']]
        self.s['flows'].append(other); self.s['flow_coverage'][0]['flow_ids'].append(other['id'])
        self.assertTrue(schema_errors('scenario', self.s))
        self.assertTrue(self.errors())
        with self.assertRaisesRegex(ValueError, 'single main'):
            flow_selectors(self.s['flows'])

    def test_happy_path_uc_and_copied_flow_are_not_second_representations(self):
        for key in ('happy_path', 'use_case', 'uc_main_flow'):
            artifact = copy.deepcopy(self.s); artifact[key] = copy.deepcopy(self.s['flows'][0])
            self.assertTrue(schema_errors('scenario', artifact), key)
        self.s['main_flow'] = copy.deepcopy(self.s['flows'][0])
        self.assertTrue(schema_errors('scenario', self.s))

    def test_variant_selector_cannot_omit_or_misclassify_a_flow(self):
        self.s['alternative_flows'] = []
        self.assertTrue(any('alternative_flows' in e for e in self.errors()))
        self.s['alternative_flows'] = ['scenario-flow:alternative']
        self.s['exception_flows'] = ['scenario-flow:alternative']
        self.assertTrue(any('exception_flows' in e for e in self.errors()))

    def test_main_sequence_cannot_disagree_with_display_order(self):
        self.s['steps'][0]['order'], self.s['steps'][1]['order'] = 2, 1
        self.assertTrue(any('main_flow order' in e for e in self.errors()))

    def test_unknown_main_is_explicit_without_invented_success_path(self):
        self.s.update(main_flow=None, alternative_flows=[], exception_flows=[], steps=[], flows=[], transitions=[])
        for row in self.s['flow_coverage']:
            row.update(status='incomplete', flow_ids=[], claim_ids=[])
        self.k['gaps'].append(dict(id='gap:main-unresolved', reason='missing_link', status='open',
            affected_ids=[self.s['scenario_id']], question='What is the main process?', next_action='Verify process sources.'))
        self.s['gap_ids'].append('gap:main-unresolved')
        self.assertEqual(self.errors(), [])
        self.k['gaps'][-1]['status'] = 'resolved'
        self.assertTrue(any('unknown main_flow' in e for e in self.errors()))

    def test_scenario_id_cannot_be_technical_node_id(self):
        self.s['steps'][0]['id'] = 'technical-step:guard'
        self.assertTrue(schema_errors('scenario', self.s))

    def test_generator_preserves_model_refs_without_actor_inference(self):
        before = copy.deepcopy(self.s)
        metadata = {key:value for key,value in self.s.items() if key not in {'steps','flows','transitions'}}
        result = build_scenario(metadata, self.s['steps'], self.s['flows'], self.s['transitions'])
        self.assertEqual(result, before)
        result['steps'][0]['technical_step_refs'].append('technical-step:extra')
        self.assertEqual(self.s, before)
        with self.assertRaises(ValueError):
            build_scenario(dict(metadata, happy_path=[]), self.s['steps'], self.s['flows'], self.s['transitions'])
        with self.assertRaises(ValueError):
            build_scenario(dict(metadata, main_flow='scenario-flow:alternative'), self.s['steps'], self.s['flows'], self.s['transitions'])
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            build_scenario(metadata, self.s['steps'] + [copy.deepcopy(self.s['steps'][0])], self.s['flows'], self.s['transitions'])

    def test_link2_frozen_grouped_main_process(self):
        from validate import load
        folder = Path(__file__).parent / 'fixtures/scenario/link2'
        inputs = load(folder / 'inputs.json'); scenario = load(folder / '05-scenario.json')
        self.assertEqual(validate('scenario', scenario, inputs['knowledge'], inputs['domain-tree'],
            inputs['scenario-definition'], inputs['technical-flow'], inputs['source-map'], inputs['business-rules']), [])
        main = next(f for f in scenario['flows'] if f['id'] == scenario['main_flow'])
        self.assertEqual([s.rsplit(':',1)[1] for s in main['step_refs']],
                         ['calculate','import','payment','issuance','status-document'])
        self.assertEqual(len(scenario['steps']), 5)
        self.assertEqual(len(inputs['technical-flow']['nodes']), 12)
        technical = {n['id'] for n in inputs['technical-flow']['nodes']}
        claims = {c['id'] for c in inputs['knowledge']['claims']}
        rules = {r['id'] for r in inputs['business-rules']['rules']}
        for step in scenario['steps']:
            self.assertGreater(len(step['technical_step_refs']), 1)
            self.assertTrue(set(step['technical_step_refs']) <= technical)
            self.assertTrue(set(step['evaluated_rules']) <= rules)
            self.assertTrue(all(cid in claims for cs in step['attribute_claims'].values() for cid in cs))
            self.assertTrue(step['evidence'])
        issue = scenario['steps'][3]
        self.assertIsNone(issue['actor'])
        self.assertIn('actor', issue['not_applicable_fields'])
        self.assertNotIn('actor', issue['unknown_fields'])
        self.assertEqual(issue['knowledge_status'], 'CONFIRMED')
        self.assertEqual(len(issue['technical_step_refs']), 3)
        self.assertNotIn('happy_path', scenario)
        scenario['steps'][1]['technical_step_refs'].pop()
        self.assertTrue(validate('scenario', scenario, inputs['knowledge'], inputs['domain-tree'],
            inputs['scenario-definition'], inputs['technical-flow'], inputs['source-map'], inputs['business-rules']))

    def test_code_symbol_cannot_be_the_process_action(self):
        from validate import load
        folder = Path(__file__).parent / 'fixtures/scenario/link2'
        inputs = load(folder / 'inputs.json'); scenario = load(folder / '05-scenario.json')
        step = scenario['steps'][3]
        node = next(n for n in inputs['technical-flow']['nodes'] if n['id'] == step['technical_step_refs'][0])
        step['action'] = node['symbol']
        c = next(c for c in inputs['knowledge']['claims'] if c['id'] == step['attribute_claims']['action'][0])
        c['value'] = node['symbol']
        errors = validate('scenario', scenario, inputs['knowledge'], inputs['domain-tree'],
            inputs['scenario-definition'], inputs['technical-flow'], inputs['source-map'], inputs['business-rules'])
        self.assertTrue(any('code symbol is not a process action' in e for e in errors))
        step['nodes'] = [copy.deepcopy(node)]
        self.assertTrue(schema_errors('scenario', scenario))

    def test_cli_writer_validates_canonical_scenario_before_writing(self):
        from scenario import main
        from unittest.mock import patch
        from contextlib import redirect_stdout, redirect_stderr
        import io
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            artifacts = {'prepared':self.s, 'knowledge':self.k, 'domain-tree':self.t, 'scenario-definition':self.d,
                         'source-map':self.m, 'technical-flow':self.f, 'business-rules':self.r}
            args = ['scenario.py']
            for key, value in artifacts.items():
                path = root / (key + '.json'); path.write_text(json.dumps(value), encoding='utf8')
                args += ['--input' if key == 'prepared' else '--' + key, str(path)]
            args += ['--output', str(root / '05-scenario.json')]
            with patch.object(sys, 'argv', args), patch('socket.socket', side_effect=AssertionError('no sources')), redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(main(), 0)
                self.assertEqual(json.loads((root / '05-scenario.json').read_text(encoding='utf8')), self.s)
                self.assertEqual(main(), 1)
                bad = copy.deepcopy(self.s); bad['happy_path'] = self.s['flows'][0]
                (root / 'prepared.json').write_text(json.dumps(bad), encoding='utf8')
                args[-1] = str(root / 'rejected.json')
                self.assertEqual(main(), 1)
                self.assertFalse((root / 'rejected.json').exists())

    def test_decision_without_rule_link(self):
        self.s['steps'][0]['evaluated_rules'] = []
        self.assertTrue(self.errors())

    def test_technical_guard_cannot_be_business_decision(self):
        self.s['steps'][0]['decision_kind'] = 'business'
        self.assertTrue(self.errors())

    def test_missing_implementation(self):
        self.s['steps'][0]['implementation'] = ['OtherHandler']
        self.assertTrue(self.errors())

    def test_missing_transition(self):
        self.s['transitions'].pop(0)
        self.assertTrue(self.errors())

    def test_order_is_not_causality_evidence(self):
        self.s['transitions'][0]['claim_ids'] = []
        self.assertTrue(self.errors())

    def test_transition_claim_must_match_direction(self):
        self.s['transitions'][0]['to_step'] = 'scenario-step:guard'
        self.assertTrue(self.errors())

    def test_branch_must_match_evaluated_rule(self):
        self.s['transitions'][0]['rule_ref'] = 'BR-NOT-IN-INPUT'
        self.assertTrue(self.errors())

    def test_branch_condition_needs_claim(self):
        self.s['transitions'][0]['condition'] = 'accuracy >= 8'
        self.assertTrue(self.errors())

    def test_invented_user_result(self):
        self.s['steps'][1]['user_result'] = 'Partner can pay now'
        self.s['steps'][1]['unknown_fields'].remove('user_result')
        self.assertTrue(self.errors())

    def test_unknown_business_meaning_requires_gap(self):
        self.s['steps'][0]['gap_ids'] = []
        self.assertTrue(self.errors())

    def test_invented_integration(self):
        step = self.s['steps'][0]
        step['integrations'] = ['NSIS']
        step['not_applicable_fields'].remove('integrations')
        self.assertTrue(self.errors())

    def test_partial_cannot_be_complete(self):
        self.s['coverage'] = {'status': 'complete', 'limitations': [], 'frontier': []}
        self.assertTrue(self.errors())

    def test_error_flow_coverage_required(self):
        self.s['flow_coverage'].pop()
        self.assertTrue(self.errors())

    def test_unknown_transition_is_explicit_partial(self):
        e = self.s['transitions'][0]
        e.update(kind='unresolved', decision_ref=None, rule_ref=None, rule_outcome='UNKNOWN',
                 condition=None, claim_ids=[], evidence=[], source_ids=[], gap_ids=['gap:transition'])
        self.k['gaps'].append({'id': 'gap:transition', 'reason': 'missing_link', 'question': 'Is guard followed by return-one?',
                              'affected_ids': [e['from_step']], 'next_action': 'Verify control flow.', 'status': 'open'})
        self.s['gap_ids'].append('gap:transition')
        self.assertEqual(self.errors(), [])
        e['gap_ids'] = []
        self.assertTrue(self.errors())

    def test_unique_display_order(self):
        self.s['steps'][1]['order'] = 1
        self.assertTrue(self.errors())

    def test_unresolved_link_cannot_hide_condition(self):
        e = self.s['transitions'][0]
        e.update(kind='unresolved', decision_ref=None, rule_ref=None, rule_outcome='UNKNOWN',
                 condition='Invented eligibility condition', claim_ids=[], evidence=[], source_ids=[], gap_ids=['gap:transition'])
        self.k['gaps'].append({'id': 'gap:transition', 'reason': 'missing_link', 'question': 'What connects these steps?',
                              'affected_ids': [e['from_step']], 'next_action': 'Inspect source.', 'status': 'open'})
        self.assertTrue(any('cannot assert causal/branch facts' in error for error in self.errors()))

    def test_revision_mismatch(self):
        self.r['package_ref']['revision'] = 2
        self.assertTrue(self.errors())

    def test_orphan_step(self):
        self.s['flows'][0]['step_refs'] = ['scenario-step:guard']
        self.s['flows'][0]['terminal_steps'] = ['scenario-step:guard']
        self.assertTrue(self.errors())

    def test_wrong_test_evidence_type(self):
        self.s['test_evidence_ids'] = ['evidence:fixture']
        self.assertTrue(self.errors())

    def test_inferred_business_meaning_rejected(self):
        step = self.s['steps'][0]
        value = 'Prevent fixture underwriting risk.'
        e = copy.deepcopy(self.k['evidence'][0])
        e.update(id='evidence:meaning-inference', source_type='INFERENCE', snapshot_id=None, inference=True,
                 basis_claim_ids=['claim:scenario-step:guard:system_behavior'], rationale='Synthetic inference')
        self.k['evidence'].append(e)
        c = copy.deepcopy(self.k['claims'][0])
        c.update(id='claim:meaning-inference', subject_id=step['id'], predicate='business_meaning', value=value,
                 inference=True, modality='inferred', support=[{'evidence_id': e['id'], 'role': 'supports'}])
        self.k['claims'].append(c)
        step['business_meaning'] = value
        step['unknown_fields'].remove('business_meaning')
        step['attribute_claims']['business_meaning'] = [c['id']]
        step['evidence'].append(e['id'])
        self.assertTrue(any('inference cannot create business meaning' in error for error in self.errors()))

    def test_error_flow_is_source_classified(self):
        # Counterfactual synthetic author statement for this test only.
        text = '\n// Synthetic return-zero branch is classified as a technical error flow.'
        self.k['sources'][0]['excerpt'] += text
        import hashlib
        self.k['sources'][0]['content_hash'] = hashlib.sha256(self.k['sources'][0]['excerpt'].encode()).hexdigest()
        self.k['evidence'][0]['excerpt'] = self.k['sources'][0]['excerpt']
        alt = self.s['flows'][1]
        alt['type'] = 'error'
        self.s.update(flow_selectors(self.s['flows']))
        c = next(c for c in self.k['claims'] if c['id'] == 'claim:flow:alternative:type')
        c['value'] = {'flow_id': alt['id'], 'type': 'error'}
        self.s['flow_coverage'][1].update(status='not_found', flow_ids=[], diagnostic='No alternative path in this counterfactual.')
        self.s['flow_coverage'][2].update(status='found', flow_ids=[alt['id']], claim_ids=alt['type_claim_ids'], diagnostic='Explicit synthetic error classification.')
        self.assertEqual(self.errors(), [])
        alt['type_claim_ids'] = []
        self.assertTrue(self.errors())

    def test_state_mismatch_requires_explicit_handoff(self):
        self.k['sources'][0]['excerpt'] += '\n// Counterfactual state handoff: fixture finished -> next object pending.'
        import hashlib
        self.k['sources'][0]['content_hash'] = hashlib.sha256(self.k['sources'][0]['excerpt'].encode()).hexdigest()
        self.k['evidence'][0]['excerpt'] = self.k['sources'][0]['excerpt']
        for step, field, state in [(self.s['steps'][0], 'state_after', 'state:finished'),
                                   (self.s['steps'][1], 'state_before', 'state:other-pending')]:
            self.k['entities'].append({'id': state, 'type': 'State', 'label': state})
            c = copy.deepcopy(self.k['claims'][0])
            c.update(id=f'claim:{state}', subject_id=step['id'], predicate=field, value=state, modality='source_statement')
            self.k['claims'].append(c)
            step[field] = state
            step['unknown_fields'].remove(field)
            step['attribute_claims'][field] = [c['id']]
        self.assertTrue(any('state continuity mismatch' in error for error in self.errors()))
        edge = self.s['transitions'][0]
        c = copy.deepcopy(self.k['claims'][0])
        c.update(id='claim:state-handoff', subject_id=edge['from_step'], predicate='state_handoff',
                 value={'from_state': 'state:finished', 'to_state': 'state:other-pending'}, modality='source_statement')
        self.k['claims'].append(c)
        edge['claim_ids'].append(c['id'])
        self.assertEqual(self.errors(), [])

    def test_missing_inputs(self):
        self.assertTrue(validate('scenario', self.s, self.k))

    def test_cli_scenario(self):
        import yaml
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            files = {'knowledge.yaml': self.k, 'domain-tree.yaml': self.t, 'scenario-definition.yaml': self.d,
                     'source-map.json': self.m, 'technical-flow.json': self.f, 'business-rules.json': self.r, 'scenario.json': self.s}
            for name, data in files.items():
                (root / name).write_text(json.dumps(data) if name.endswith('.json') else yaml.safe_dump(data), encoding='utf-8')
            command = [sys.executable, str(Path(__file__).resolve().parents[1] / 'validate.py'), 'scenario', str(root / 'scenario.json')]
            for flag, name in [('knowledge', 'knowledge.yaml'), ('domain-tree', 'domain-tree.yaml'),
                               ('scenario-definition', 'scenario-definition.yaml'), ('technical-flow', 'technical-flow.json'),
                               ('source-map', 'source-map.json'), ('business-rules', 'business-rules.json')]:
                command += [f'--{flag}', str(root / name)]
            result = subprocess.run(command, capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
