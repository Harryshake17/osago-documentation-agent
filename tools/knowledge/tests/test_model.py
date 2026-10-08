"""Shared model regression/negative invariants, independent of prose wording."""
import copy
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import json

from test_scenario import scenario_fixture
from test_technical_flow import execution_fixture
from model import PROFILE, increment_errors
from pipeline import validate_run
from validate import load, schema_errors, validate


def unknown():
    return dict(value=None, status='UNKNOWN', claim_ids=[], evidence_ids=[])


def sync_evidence(k):
    for e in k['evidence']:
        e['source_ref'] = e['snapshot_id']
        e['supports'] = [c['id'] for c in k['claims'] if
                         any(s['evidence_id'] == e['id'] and s['role'] == 'supports' for s in c['support'])]
        e['metadata'] = dict(repository=e['repository'], file=e['file'],
                             symbol='.'.join(x for x in (e['class'], e['method']) if x) or None,
                             revision=e['version'], page=e['page'])


def profile_fixture():
    k, tree, definition, source_map, flow, rules, scenario = scenario_fixture()
    technical_k, _, _, _, technical = execution_fixture()
    for group in ('claims', 'gaps'):
        existing = {r['id'] for r in k[group]}
        k[group] += [r for r in technical_k[group] if r['id'] not in existing]
    flow = technical
    for artifact in (k, tree, definition, source_map, flow, rules, scenario):
        artifact['model_profile'] = PROFILE
    for c in k['claims']:
        c.update(knowledge_status='CONFIRMED', basis_claim_ids=[], inference_rationale=None)
    for e in k['entities']:
        e.update(identity_key=e['id'], preferred_name=unknown(), technical_aliases=[e['id']],
                 search_aliases=[], terminology_candidates=[])
    for n in tree['nodes']:
        n.update(preferred_name=unknown(), technical_aliases=[n['id']], search_aliases=[],
                 terminology_candidates=[], evidence=['evidence:fixture'], scope_ref=k['scope']['id'])
    definition.update(preferred_name=unknown(), technical_aliases=[definition['scenario_id']], search_aliases=[],
                      terminology_candidates=[], evidence=['evidence:fixture'])
    source_map['terminology_candidates'] = []
    node = flow['nodes'][0]
    node.update(business_meaning=unknown(), integrations=[], technical_implementation=dict(
        implementation_refs=['FixtureHandler.Handle'], technical_step_refs=[node['id']], source_ids=['source:handler']))
    rule = rules['rules'][0]
    rule.update(business_statement=unknown(), business_rationale=unknown(),
                technical_condition=dict(value=rule['condition'], status='CONFIRMED',
                    claim_ids=rule['attribute_claims']['condition'], evidence_ids=rule['evidence']),
                technical_implementation=dict(implementation_refs=rule['implementation'],
                    technical_step_refs=['technical-step:guard'], source_ids=rule['source_ids']))
    for step in scenario['steps']:
        step.update(business_action=unknown(), business_result=unknown(), knowledge_status='UNKNOWN',
                    state_transition=dict(to=step['state_after'], **{'from':step['state_before']}),
                    technical_implementation=dict(implementation_refs=step['implementation'],
                        technical_step_refs=step['technical_step_refs'], source_ids=step['source_ids']))
    sync_evidence(k)
    return k, tree, definition, source_map, flow, rules, scenario


class ModelTests(unittest.TestCase):
    def setUp(self):
        self.k, self.t, self.d, self.m, self.f, self.r, self.s = profile_fixture()

    def errors(self):
        return validate('scenario', self.s, self.k, self.t, self.d, self.f, self.m, self.r)

    def test_structured_pipeline_outputs(self):
        self.assertEqual(self.errors(), [])
        for kind, artifact in [('domain-tree', self.t), ('scenario-definition', self.d),
                ('source-map', self.m), ('technical-flow', self.f), ('business-rules', self.r), ('scenario', self.s)]:
            self.assertEqual(schema_errors(kind, artifact), [])

    def test_profile_requires_shared_fields(self):
        del self.s['steps'][0]['business_action']
        self.assertTrue(self.errors())

    def test_profile_does_not_accept_legacy_inputs(self):
        self.t.pop('model_profile')
        self.assertTrue(any('all inputs' in e for e in self.errors()))

    def test_A_code_confluence_conflict_retains_both_claims(self):
        code = copy.deepcopy(self.k['claims'][0])
        code.update(id='claim:code-version', predicate='preferred_name', value='Code term', knowledge_status='CONFLICT')
        doc = copy.deepcopy(code)
        doc.update(id='claim:document-version', value='Document term')
        snapshot = copy.deepcopy(self.k['sources'][0])
        snapshot.update(id='snapshot:document', adapter='confluence', repository=None, locator='page:1')
        e = copy.deepcopy(self.k['evidence'][0])
        e.update(id='evidence:document', source_type='CONFLUENCE', snapshot_id=snapshot['id'],
                 repository=None, file=None, page='page:1', section='Terms', **{'class':None, 'method':None})
        doc['support'] = [dict(evidence_id=e['id'], role='supports')]
        self.k['sources'].append(snapshot)
        self.k['evidence'].append(e)
        self.k['claims'] += [code, doc]
        self.k['conflicts'].append(dict(id='conflict:term', claim_ids=[code['id'], doc['id']],
             disagreement='Conflicting source terms', status='unresolved', resolution_claim_id=None))
        name = dict(value=None, status='CONFLICT', claim_ids=[code['id'], doc['id']],
                    evidence_ids=['evidence:fixture', e['id']])
        for row in (self.k['entities'][0], self.t['nodes'][0], self.d):
            row['preferred_name'] = copy.deepcopy(name)
        sync_evidence(self.k)
        self.assertEqual(validate('domain-tree', self.t, self.k), [])
        conflicts = self.k['conflicts']
        self.k['conflicts'] = []
        self.assertTrue(any('competing scalar claims' in e for e in validate('domain-tree', self.t, self.k)))
        self.k['conflicts'] = conflicts
        self.k['entities'][0]['preferred_name']['status'] = 'CONFIRMED'
        self.assertTrue(validate('domain-tree', self.t, self.k))

    def test_B_SAS_does_not_create_business_term(self):
        entity = dict(id='integration:sas', type='Integration', label='SAS', identity_key='fixture:SAS',
                      preferred_name=unknown(), technical_aliases=['SAS'], search_aliases=[], terminology_candidates=[])
        self.k['entities'].append(entity)
        self.assertEqual(self.errors(), [])
        entity['preferred_name'] = dict(value='скоринг', status='CONFIRMED', claim_ids=[], evidence_ids=[])
        self.assertTrue(self.errors())

    def test_C_process_name_cannot_confirm_meaning(self):
        self.f['nodes'][0]['business_meaning'] = dict(value='Registration', status='CONFIRMED',
             claim_ids=['claim:technical:symbol'], evidence_ids=['evidence:fixture'])
        self.assertTrue(self.errors())

    def test_D_confirmed_claim_without_evidence_rejected(self):
        self.k['claims'][0]['support'] = []
        sync_evidence(self.k)
        self.assertTrue(any('primary evidence' in e for e in self.errors()))

    def test_E_neighbor_source_word_match_rejected(self):
        self.m['sources'][0]['relevance_path'][0]['from_ref'] = 'NeighborScenario'
        self.assertTrue(self.errors())

    def test_inference_is_not_evidence(self):
        self.k['evidence'][0]['source_type'] = 'INFERENCE'
        self.assertTrue(self.errors())

    def test_inferred_claim_uses_basis_not_synthetic_evidence(self):
        c = copy.deepcopy(self.k['claims'][0])
        c.update(id='claim:grounded-inference', predicate='hypothesis', value='Unconfirmed hypothesis',
                 modality='inferred', inference=True, knowledge_status='INFERRED', support=[],
                 basis_claim_ids=['claim:trigger'], inference_rationale='A hypothesis based on the confirmed trigger.')
        self.k['claims'].append(c)
        self.assertEqual(self.errors(), [])
        c['basis_claim_ids'] = [c['id']]
        self.assertTrue(any('acyclic' in e for e in self.errors()))

    def test_business_meaning_UNKNOWN_requires_open_gap(self):
        self.f['nodes'][0]['gap_ids'] = []
        self.k['gaps'] = [g for g in self.k['gaps'] if 'technical-step:guard' not in g['affected_ids']]
        self.assertTrue(self.errors())

    def test_structured_claim_evidence_must_be_accepted_in_scope(self):
        source = copy.deepcopy(self.k['sources'][0])
        source['id'] = 'snapshot:neighbor'
        e = copy.deepcopy(self.k['evidence'][0])
        e.update(id='evidence:neighbor', snapshot_id=source['id'])
        self.k['sources'].append(source)
        self.k['evidence'].append(e)
        c = copy.deepcopy(self.k['claims'][0])
        c.update(id='claim:neighbor-action', subject_id=self.s['steps'][0]['id'], predicate='business_action', value='Action',
                 modality='source_statement', support=[dict(evidence_id=e['id'],role='supports')])
        self.k['claims'].append(c)
        self.s['steps'][0]['business_action'] = dict(value='Action',status='CONFIRMED',claim_ids=[c['id']],evidence_ids=[e['id']])
        self.s['steps'][0]['evidence'].append(e['id'])
        sync_evidence(self.k)
        self.assertTrue(any('outside accepted' in error for error in self.errors()))

    def test_confirmed_business_requires_explicit_source_statement(self):
        step = self.s['steps'][0]
        c = copy.deepcopy(self.k['claims'][0])
        c.update(id='claim:business-action', subject_id=step['id'], predicate='business_action', value='Action', modality='implemented')
        self.k['claims'].append(c)
        step['business_action'] = dict(value='Action', status='CONFIRMED', claim_ids=[c['id']], evidence_ids=step['evidence'])
        sync_evidence(self.k)
        self.assertTrue(any('source-stated' in e for e in self.errors()))

    def test_stable_scenario_rule_implementation_evidence_refs(self):
        for field, value in [('scenario_id', 'scenario:new')]:
            with self.subTest(field=field):
                original = self.s[field]
                self.s[field] = value
                self.assertTrue(self.errors())
                self.s[field] = original
        for field in ('evaluated_rules', 'implementation', 'evidence'):
            with self.subTest(field=field):
                original = self.s['steps'][0][field]
                self.s['steps'][0][field] = ['missing:ID']
                self.assertTrue(self.errors())
                self.s['steps'][0][field] = original

    def test_duplicate_alias_entity_identity_rejected(self):
        clone = copy.deepcopy(self.k['entities'][0])
        clone['id'] = 'scenario:translated-copy'
        self.k['entities'].append(clone)
        self.assertTrue(any('duplicate entity identity' in e for e in self.errors()))

    def test_business_rationale_does_not_copy_condition(self):
        rule = self.r['rules'][0]
        rule['business_rationale'] = copy.deepcopy(rule['technical_condition'])
        self.assertTrue(self.errors())

    def test_candidate_has_typed_source_and_registry_ref(self):
        row = dict(value='SAS', entity_ref=self.k['entities'][0]['id'], source_type='CODE',
                   source_ref='snapshot:fixture', evidence_ids=['evidence:fixture'])
        self.m['terminology_candidates'] = [row]
        self.k['entities'][0]['terminology_candidates'] = [row]
        self.t['nodes'][0]['terminology_candidates'] = [row]
        self.d['terminology_candidates'] = [row]
        self.assertEqual(self.errors(), [])
        row['source_type'] = 'CONFLUENCE'
        self.assertTrue(self.errors())

    def test_scenario_status_cannot_hide_unknown_business(self):
        self.s['steps'][0]['knowledge_status'] = 'CONFIRMED'
        self.assertTrue(self.errors())

    def test_unknown_term_promotion_requires_new_evidence(self):
        current = copy.deepcopy(self.k)
        current['revision'] += 1
        current['entities'][0]['preferred_name'] = dict(value='SAS', status='CONFIRMED', claim_ids=[], evidence_ids=[])
        self.assertTrue(any('promotion' in e for e in increment_errors(self.k, current)))

    def test_confirmed_term_reuses_registry_claim_in_projections(self):
        c = copy.deepcopy(self.k['claims'][0])
        c.update(id='claim:canonical-term',predicate='preferred_name',value='Fixture domain term',modality='source_statement')
        self.k['claims'].append(c)
        name = dict(value=c['value'],status='CONFIRMED',claim_ids=[c['id']],evidence_ids=['evidence:fixture'])
        for row in (self.k['entities'][0],self.t['nodes'][0],self.d):
            row['preferred_name'] = copy.deepcopy(name)
            if 'name' in row:
                row['name'] = c['value']
                row['proposed_fields'] = []
        sync_evidence(self.k)
        self.assertEqual(self.errors(), [])

    def test_status_and_scope_preserved_across_increments(self):
        for status in ('UNKNOWN', 'INFERRED', 'CONFLICT', 'PARTIALLY_CONFIRMED'):
            previous = copy.deepcopy(self.k)
            previous['claims'][0]['knowledge_status'] = status
            current = copy.deepcopy(previous)
            current['revision'] += 1
            self.assertEqual(increment_errors(previous, current), [])
            current['claims'][0]['knowledge_status'] = 'CONFIRMED'
            self.assertTrue(increment_errors(previous, current))
        current = copy.deepcopy(self.k)
        current['revision'] += 1
        current['scope']['components'].append('neighbor')
        self.assertTrue(any('scope changed' in e for e in increment_errors(self.k, current)))

    def test_evidence_and_aliases_cannot_be_lost_or_rewritten(self):
        for group in ('evidence', 'sources', 'entities', 'claims'):
            current = copy.deepcopy(self.k)
            current['revision'] += 1
            current[group].pop()
            self.assertTrue(increment_errors(self.k, current))
        current = copy.deepcopy(self.k)
        current['revision'] += 1
        current['entities'][0]['technical_aliases'] = []
        self.assertTrue(increment_errors(self.k, current))

    def test_new_increment_extends_existing_registry(self):
        current = copy.deepcopy(self.k)
        current['revision'] += 1
        current['entities'][0]['technical_aliases'].append('SAS')
        self.assertEqual(increment_errors(self.k, current), [])

    def test_conflict_records_cannot_be_auto_resolved(self):
        previous = copy.deepcopy(self.k)
        previous['conflicts'].append(dict(id='conflict:versions',claim_ids=['claim:trigger'],
                 disagreement='different versions',status='unresolved',resolution_claim_id=None))
        current = copy.deepcopy(previous)
        current['revision'] += 1
        current['conflicts'][0].update(status='resolved',resolution_claim_id='claim:trigger')
        self.assertTrue(any('cannot be resolved' in e for e in increment_errors(previous,current)))

    def test_same_revision_cannot_hide_changes(self):
        current = copy.deepcopy(self.k)
        current['entities'][0]['technical_aliases'].append('SAS')
        self.assertTrue(any('new revision' in e for e in increment_errors(self.k,current)))

    def test_all_schema_documents_are_valid(self):
        from validate import SCHEMAS
        from jsonschema import Draft202012Validator
        for path in SCHEMAS.glob('*.json'):
            with self.subTest(schema=path.name):
                Draft202012Validator.check_schema(load(path))

    def test_source_discovery_cannot_choose_canonical_name(self):
        previous = copy.deepcopy(self.k)
        self.k['revision'] += 1
        for artifact in (self.t, self.d, self.m):
            artifact['package_ref']['revision'] = self.k['revision']
        previous['entities'][0]['preferred_name'] = unknown()
        c = copy.deepcopy(self.k['claims'][0])
        c.update(id='claim:discovered-term', predicate='preferred_name', value='SAS', modality='source_statement')
        self.k['claims'].append(c)
        name = dict(value='SAS', status='CONFIRMED', claim_ids=[c['id']], evidence_ids=['evidence:fixture'])
        for row in (self.k['entities'][0], self.t['nodes'][0], self.d):
            row['preferred_name'] = copy.deepcopy(name)
            if 'name' in row:
                row['name'] = 'SAS'
        sync_evidence(self.k)
        errors = validate('source-map', self.m, self.k, self.t, self.d, previous_knowledge=previous)
        self.assertTrue(any('cannot choose' in e for e in errors))


class GoldenTests(unittest.TestCase):
    path = Path(__file__).parent / 'fixtures/registration-address/pipeline-run.json'

    def test_full_real_domain_fixture(self):
        self.assertEqual(validate_run(self.path), [])

    def test_golden_frozen_source_hashes(self):
        import hashlib
        manifest = load(self.path)
        k = load(self.path.parent / manifest['stages'][-1]['knowledge'])
        for source in k['sources']:
            self.assertEqual(source['content_hash'], hashlib.sha256(source['excerpt'].encode('utf-8')).hexdigest())
        # Frozen source, not a live connector or an assertion of business truth.
        self.assertTrue(any('ShouldSkipRegistrationAddressValidationForImportProlongation' in s['excerpt'] for s in k['sources']))

    def test_pipeline_rejects_hidden_scope_expansion(self):
        with tempfile.TemporaryDirectory() as directory:
            import shutil
            target = Path(directory) / 'golden'
            shutil.copytree(self.path.parent, target)
            manifest = load(target / self.path.name)
            path = target / manifest['stages'][-1]['knowledge']
            k = load(path)
            k['scope']['components'].append('neighbor')
            path.write_text(json.dumps(k, ensure_ascii=False), encoding='utf-8')
            self.assertTrue(any('scope changed' in e for e in validate_run(target / self.path.name)))

    def test_cli_five_stages(self):
        result = subprocess.run([sys.executable, str(Path(__file__).parents[1] / 'pipeline.py'), str(self.path)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
