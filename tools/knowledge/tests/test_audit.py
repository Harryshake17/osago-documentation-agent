"""Audit contracts: source-backed classifications and conservative draft behavior."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit import calculate_summary, check_report, draft
from test_scenario import scenario_fixture


def audit_inputs():
    k, t, d, m, f, r, s = scenario_fixture()
    return {'knowledge': k, 'domain-tree': t, 'scenario-definition': d,
            'source-map': m, 'technical-flow': f, 'business-rules': r, 'scenario': s}


def mark_reviewed(inputs, report, cid, status='CONFIRMED', result='SUPPORTS'):
    row = next(r for r in report['claim_reviews'] if r['claim_id'] == cid)
    claim = next(c for c in inputs['knowledge']['claims'] if c['id'] == cid)
    evidence = {e['id']: e for e in inputs['knowledge']['evidence']}
    snapshots = {s['id']: s for s in inputs['knowledge']['sources']}
    checks = []
    for support in claim['support']:
        e = evidence[support['evidence_id']]
        inferred = e['source_type'] == 'INFERENCE'
        snapshot = snapshots.get(e['snapshot_id'])
        checks.append({'evidence_id': e['id'], 'snapshot_id': e['snapshot_id'],
                       'source_location': e['source_location'], 'version': e['version'],
                       'content_hash': snapshot['content_hash'] if snapshot else None,
                       'verification': 'reasoning_checked' if inferred else 'snapshot_only',
                       'result': result, 'quote': e['rationale'] if inferred else e['excerpt'],
                       'reason': 'Synthetic check; semantic truth is not assessed by this test helper.'})
    row.update(reviewed=True, status=status, source_checks=checks,
               reason='Synthetic inspected evidence for fixed fixture version.', required_action='none')
    return row


def add_counterpart(inputs, source_type):
    k, m = inputs['knowledge'], inputs['source-map']
    text = 'FixtureCommand for fixture-v1: current implementation threshold is 8.' if source_type == 'CONFLUENCE' else 'FixtureCommand test expects threshold 8 for fixture-v1.'
    snapshot = copy.deepcopy(k['sources'][0])
    snapshot.update(id='snapshot:counterpart', adapter='confluence' if source_type == 'CONFLUENCE' else 'tests',
                    locator='fixture/page/42' if source_type == 'CONFLUENCE' else 'fixtures/threshold.spec',
                    repository=None if source_type == 'CONFLUENCE' else 'fixture', revision='page-v1' if source_type == 'CONFLUENCE' else 'fixture-v1',
                    content_hash=hashlib.sha256(text.encode()).hexdigest(), excerpt=text, working_tree_state='not_applicable')
    k['sources'].append(snapshot)
    e = copy.deepcopy(k['evidence'][0])
    e.update(id='evidence:counterpart', source_type=source_type, snapshot_id=snapshot['id'],
             source_location=snapshot['locator'], version=snapshot['revision'], excerpt=text,
             repository=snapshot['repository'], file='fixtures/threshold.spec' if source_type == 'TEST' else None,
             page='42' if source_type == 'CONFLUENCE' else None, section='threshold' if source_type == 'CONFLUENCE' else None,
             **{'class': None, 'method': None})
    k['evidence'].append(e)
    original = next(c for c in k['claims'] if c['id'] == 'claim:rule:parameters:0')
    c = copy.deepcopy(original)
    c.update(id='claim:counterpart', modality='source_statement' if source_type == 'CONFLUENCE' else 'test_expectation',
             support=[{'evidence_id': e['id'], 'role': 'supports'}])
    c['value']['value'] = 8
    k['claims'].append(c)
    # This snapshot is scoped by the explicit fixture identifier. Draft comparisons
    # remain UNRESOLVED until a reviewer compares modality and context.
    return original['id'], c['id']


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.i = audit_inputs()
        self.report, self.gaps = draft(self.i)

    def errors(self):
        self.report['summary'] = calculate_summary(self.report, self.gaps)
        return check_report(self.report, self.gaps, self.i)

    def test_draft_never_auto_confirms(self):
        self.assertTrue(all(r['status'] == 'UNKNOWN' and not r['reviewed'] for r in self.report['claim_reviews']))
        self.assertEqual(self.report['summary']['review_status'], 'partial')
        self.assertEqual(self.report['summary']['publication_gate'], 'blocked')
        self.assertEqual(self.errors(), [])

    def test_each_claim_has_inventory_entry(self):
        self.report['claim_reviews'].pop()
        self.assertTrue(self.errors())

    def test_old_supported_flag_not_confirmation(self):
        self.assertTrue(all(c['validation_status'] == 'supported' for c in self.i['knowledge']['claims']))
        self.assertEqual(self.report['summary']['counts']['CONFIRMED'], 0)

    def test_complete_audit_can_remain_blocked_by_gaps(self):
        for cid in self.report['claim_inventory']:
            mark_reviewed(self.i, self.report, cid)
        self.assertEqual(self.errors(), [])
        self.assertEqual(self.report['summary']['review_status'], 'complete')
        self.assertEqual(self.report['summary']['publication_gate'], 'blocked')

    def test_false_confirmed_without_inspection(self):
        row = self.report['claim_reviews'][0]
        row.update(status='CONFIRMED', reviewed=True)
        self.assertTrue(self.errors())

    def test_quote_must_match_snapshot(self):
        row = mark_reviewed(self.i, self.report, 'claim:business_goal')
        row['source_checks'][0]['quote'] = 'Invented business rationale.'
        self.assertTrue(self.errors())

    def test_hash_and_version_mismatch(self):
        row = mark_reviewed(self.i, self.report, 'claim:business_goal')
        row['source_checks'][0]['content_hash'] = '0' * 64
        row['source_checks'][0]['version'] = 'newer-version'
        self.assertTrue(self.errors())

    def test_modified_inputs_invalidate_report(self):
        self.i['knowledge']['claims'][0]['text'] += ' changed'
        self.assertTrue(any('stale' in e or 'changed' in e for e in self.errors()))

    def test_missing_evidence_is_diagnosed_not_dropped(self):
        c = self.i['knowledge']['claims'][0]
        c['support'] = []
        self.report, self.gaps = draft(self.i)
        self.assertTrue(any(f['kind'] == 'missing_evidence' and c['id'] in f['claim_ids'] for f in self.report['findings']))
        self.assertIn(c['id'], self.report['claim_inventory'])
        self.assertEqual(self.errors(), [])

    def test_malformed_support_is_diagnosed(self):
        self.i['knowledge']['claims'][0]['support'] = None
        self.report, self.gaps = draft(self.i)
        self.assertTrue(self.report['mechanical_errors'])
        self.assertEqual(self.errors(), [])

    def test_required_unknown_rationale_and_state_findings(self):
        kinds = {f['kind'] for f in self.report['findings']}
        self.assertIn('unknown_business_rationale', kinds)
        self.assertIn('unknown_state_transition', kinds)

    def test_unimplemented_scenario_is_gap_not_absence_claim(self):
        self.i['scenario']['steps'][0]['implementation'] = []
        self.report, self.gaps = draft(self.i)
        self.assertTrue(any(f['kind'] == 'scenario_without_implementation' for f in self.report['findings']))
        self.assertEqual(self.errors(), [])

    def test_config_documentation_gap(self):
        source = self.i['source-map']['sources'][0]
        source.update(artifact_kind='configuration_key', category='configuration_keys', symbol='Config:fixture-flag')
        self.report, self.gaps = draft(self.i)
        found = next(f for f in self.report['findings'] if f['kind'] == 'undocumented_config_behaviour')
        self.assertEqual(found['verification'], 'needs_source_verification')
        self.assertIn('supplied KB', found['reason'])
        self.assertEqual(self.errors(), [])

    def test_technical_branch_missing_from_scenario(self):
        k, f = self.i['knowledge'], self.i['technical-flow']
        k['entities'].append({'id': 'technical-step:unrepresented', 'type': 'SystemBehaviour', 'label': 'Synthetic branch target'})
        c = copy.deepcopy(k['claims'][0])
        c.update(id='claim:tech:unrepresented', subject_id='technical-step:unrepresented', predicate='implementation', value='FixtureHandler.Handle')
        k['claims'].append(c)
        c = copy.deepcopy(c)
        c.update(id='claim:tech:branch', subject_id='technical-step:guard', predicate='false_branch', value='technical-step:unrepresented')
        k['claims'].append(c)
        f['nodes'].append({'id': 'technical-step:unrepresented', 'component_id': 'FixtureHandler.Handle', 'source_ids': ['source:handler'],
                           'claim_ids': ['claim:tech:unrepresented']})
        f['relations'].append({'id': 'relation:branch', 'from_id': 'technical-step:guard', 'to_id': 'technical-step:unrepresented',
                              'relation_type': 'false_branch', 'claim_ids': ['claim:tech:branch']})
        self.report, self.gaps = draft(self.i)
        self.assertTrue(any(f['kind'] == 'unrepresented_technical_branch' for f in self.report['findings']))
        self.assertEqual(self.errors(), [])

    def test_code_confluence_difference_is_not_auto_conflict(self):
        add_counterpart(self.i, 'CONFLUENCE')
        self.report, self.gaps = draft(self.i)
        comp = next(c for c in self.report['comparisons'] if c['kind'] == 'code_confluence')
        self.assertEqual(comp['status'], 'UNRESOLVED')
        self.assertFalse(comp['reviewed'])
        self.assertEqual(self.errors(), [])

    def test_test_code_difference_is_not_auto_conflict(self):
        add_counterpart(self.i, 'TEST')
        self.report, self.gaps = draft(self.i)
        self.assertTrue(any(c['kind'] == 'test_code' and c['status'] == 'UNRESOLVED' for c in self.report['comparisons']))
        self.assertEqual(self.errors(), [])

    def test_conflict_needs_both_sources_and_context(self):
        a, b = add_counterpart(self.i, 'CONFLUENCE')
        self.report, self.gaps = draft(self.i)
        comp = self.report['comparisons'][0]
        comp.update(reviewed=True, status='CONFLICT', context_comparison='overlap')
        for cid in (a, b):
            row = mark_reviewed(self.i, self.report, cid, 'CONFLICT')
            row['comparison_ids'] = [comp['id']]
            row['required_action'] = 'analyst_review'
        self.assertEqual(self.errors(), [])
        comp['context_comparison'] = 'unknown'
        self.assertTrue(self.errors())

    def test_partial_claim_must_identify_unsupported_parts(self):
        row = mark_reviewed(self.i, self.report, 'claim:business_goal', 'PARTIALLY_CONFIRMED', 'PARTIAL_SUPPORT')
        self.assertTrue(self.errors())
        row.update(supported_parts=['Synthetic action'], unsupported_parts=['Unverified goal scope'],
                   gap_ids=[self.gaps['gaps'][0]['id']], required_action='split_claim')
        self.assertEqual(self.errors(), [])

    def test_unknown_review_can_be_complete_without_confirmation(self):
        row = mark_reviewed(self.i, self.report, 'claim:business_goal', 'UNKNOWN', 'IRRELEVANT')
        row.update(gap_ids=[self.gaps['gaps'][0]['id']], required_action='add_evidence')
        self.assertEqual(self.errors(), [])

    def test_summary_cannot_claim_success(self):
        self.report['summary']['publication_gate'] = 'passed'
        self.assertTrue(check_report(self.report, self.gaps, self.i))

    def test_finding_must_link_gap(self):
        self.gaps['finding_gap_links'] = []
        self.assertTrue(self.errors())

    def test_cli_outputs_and_preserves_existing_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            command = [sys.executable, str(Path(__file__).resolve().parents[1] / 'audit.py'), 'draft']
            for kind, data in self.i.items():
                path = root / f'{kind}.json'
                path.write_text(json.dumps(data), encoding='utf-8')
                command += ['--' + kind, str(path)]
            command += ['--output-dir', str(root / 'audit')]
            first = subprocess.run(command, capture_output=True, text=True, timeout=60)
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            self.assertTrue((root / 'audit/gaps.json').exists())
            second = subprocess.run(command, capture_output=True, text=True, timeout=60)
            self.assertEqual(second.returncode, 2)


class StructuredAuditTests(unittest.TestCase):
    def inputs(self):
        from test_model import profile_fixture
        k,t,d,m,f,r,s=profile_fixture()
        return dict(knowledge=k,**{'domain-tree':t,'scenario-definition':d,'source-map':m,
                                  'technical-flow':f,'business-rules':r,'scenario':s})

    def test_structured_unknown_rationale_produces_finding(self):
        inputs=self.inputs()
        report,gaps=draft(inputs)
        self.assertTrue(any(f['kind']=='unknown_business_rationale' for f in report['findings']))
        self.assertEqual(check_report(report,gaps,inputs),[])

    def test_structured_inference_uses_claim_basis_without_INFERENCE_evidence(self):
        inputs=self.inputs()
        k=inputs['knowledge']
        c=copy.deepcopy(k['claims'][0])
        c.update(id='claim:profile-inference',predicate='technical_hypothesis',value='Synthetic hypothesis',
                 inference=True,knowledge_status='INFERRED',modality='inferred',support=[],
                 basis_claim_ids=[k['claims'][0]['id']],inference_rationale='Synthetic deduction from inspected basis.')
        k['claims'].append(c)
        report,gaps=draft(inputs)
        self.assertFalse(any(f['kind']=='missing_evidence' and c['id'] in f['claim_ids'] for f in report['findings']))
        mark_reviewed(inputs,report,k['claims'][0]['id'])
        mark_reviewed(inputs,report,c['id'],status='INFERRED')
        report['summary']=calculate_summary(report,gaps)
        self.assertEqual(check_report(report,gaps,inputs),[])
        basis=next(r for r in report['claim_reviews'] if r['claim_id']==k['claims'][0]['id'])
        basis.update(status='UNKNOWN',reviewed=False,source_checks=[])
        report['summary']=calculate_summary(report,gaps)
        self.assertTrue(any('confirmed primary roots' in e for e in check_report(report,gaps,inputs)))


if __name__ == '__main__':
    unittest.main()
