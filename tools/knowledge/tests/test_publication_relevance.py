"""Publication relevance tests over synthetic structured knowledge only."""
import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit import draft, calculate_summary, check_report
from publication import (PUBLIC, INTERNAL, UNASSESSED, impact_index, minimum_impacts,
                         refresh_publication_subset, publication_errors, annotate_draft)
from test_audit import mark_reviewed, add_counterpart, audit_inputs
from test_orchestrate import complete_fixture
from validate import schema_errors, load

FIXTURE = Path(__file__).parent / 'fixtures/publication-relevance'


def reviewed_fixture():
    inputs, _ = complete_fixture()
    scenario = inputs['scenario']
    main = next(f for f in scenario['flows'] if f['id'] == scenario['main_flow'])
    edge = next(e for e in scenario['transitions'] if e['from_step'] == main['step_refs'][0] and e['to_step'] == main['step_refs'][1])
    step = next(s for s in scenario['steps'] if s['id'] == main['step_refs'][-1])
    technical = inputs['technical-flow']['nodes'][0]['id']
    questions = ['Exact internal method?', 'Actor for an internal call?', 'Helper/extension wiring?',
                 'Full generated graph?', 'Secondary implementation detail?', 'Specific test/file locator?']
    for i in range(20):
        inputs['knowledge']['gaps'].append(dict(id=f'gap:internal:{i:02}', reason='unknown_field',
            question=questions[i % len(questions)], affected_ids=[technical],
            next_action='Continue internal implementation research.', status='open'))
    for gid, cid, question in [('gap:process:ordering', edge['claim_ids'][0], 'Does the main process use this order?'),
                               ('gap:process:result', step['business_result']['claim_ids'][0], 'Is this the business result?')]:
        inputs['knowledge']['gaps'].append(dict(id=gid, reason='unverified', question=question,
            affected_ids=[cid], next_action='Review the affected process assertion.', status='open'))
    report, gaps = draft(inputs)
    for cid in report['claim_inventory']:
        mark_reviewed(inputs, report, cid)
    for item in gaps['gaps'] + report['findings']:
        metadata = item['publication_relevance']
        metadata['reviewed'] = True
        if metadata['classification'] == UNASSESSED:
            metadata.update(classification=INTERNAL, reason='Synthetic review: only internal wiring is unresolved; process actions, rules and results have independent support.')
        else:
            metadata['reason'] = 'Synthetic review: this uncertainty can change the referenced process assertion.'
    refresh_publication_subset(report, gaps)
    report['summary'] = calculate_summary(report, gaps)
    return inputs, report, gaps


class PublicationRelevanceTests(unittest.TestCase):
    def setUp(self):
        self.inputs, self.report, self.gaps = reviewed_fixture()

    def errors(self):
        return check_report(self.report, self.gaps, self.inputs)

    def test_twenty_internal_plus_two_material_all_retained(self):
        before = copy.deepcopy(self.inputs)
        self.assertEqual(self.errors(), [])
        self.assertEqual(len(self.gaps['gaps']), 22)
        self.assertEqual(self.gaps['publication_subset'], dict(
            gap_ids=['gap:process:ordering', 'gap:process:result'], finding_ids=[]))
        self.assertEqual({g['id'] for g in self.gaps['gaps']}, {g['id'] for g in self.inputs['knowledge']['gaps']})
        self.assertEqual(self.inputs, before)
        self.assertEqual(self.report['summary']['publication_gate'], 'blocked')
        self.assertEqual(self.report['summary']['review_status'], 'complete')

    def test_frozen_regression_fixture(self):
        inputs = load(FIXTURE / 'inputs.json')
        report = load(FIXTURE / 'validation-report.json')
        gaps = load(FIXTURE / 'gaps.json')
        self.assertEqual(check_report(report, gaps, inputs), [])
        self.assertEqual((inputs, report, gaps), reviewed_fixture())

    def test_internal_is_never_assumed_from_node_mapping_or_high_confidence(self):
        report, gaps = draft(self.inputs)
        internal = next(g for g in gaps['gaps'] if g['id'] == 'gap:internal:00')
        self.assertEqual(internal['publication_relevance']['classification'], UNASSESSED)
        self.assertFalse(internal['publication_relevance']['reviewed'])
        self.assertEqual(len(gaps['publication_subset']['gap_ids']), 2)
        internal['publication_relevance'].update(classification=INTERNAL, reviewed=False)
        self.assertTrue(schema_errors('validation-gaps', gaps))

    def test_severity_blocking_and_confidence_do_not_select_reader_items(self):
        finding = dict(id='finding:internal-helper', kind='unrepresented_technical_branch',
            target_refs=[self.inputs['technical-flow']['nodes'][0]['id']],
            claim_ids=[], evidence_ids=[], verification='source_verified', reason='Synthetic internal wiring issue.',
            required_action='trace_implementation', blocking=True, status='open', resolution_claim_ids=[],
            publication_relevance=dict(classification=INTERNAL, reviewed=True, impacts=[],
                                       reason='Synthetic review: confirmed process outcome is unchanged.'))
        self.report['findings'].append(finding)
        self.gaps['finding_gap_links'].append(dict(finding_id=finding['id'], gap_ids=['gap:internal:00']))
        refresh_publication_subset(self.report, self.gaps)
        self.report['summary'] = calculate_summary(self.report, self.gaps)
        self.assertEqual(self.errors(), [])
        self.assertNotIn(finding['id'], self.gaps['publication_subset']['finding_ids'])
        altered = copy.deepcopy(self.inputs)
        for evidence in altered['knowledge']['evidence']:
            evidence['confidence']['score'] = 0
        report, gaps = draft(altered)
        self.assertEqual(gaps['publication_subset'], self.gaps['publication_subset'])

    def test_significant_variants_states_rules_external_contract_and_version(self):
        index = impact_index(self.inputs)
        scenario = self.inputs['scenario']
        alternative = next(f for f in scenario['flows'] if f['type'] == 'alternative')
        self.assertIn('ALTERNATIVE_OR_EXCEPTION_FLOW', index[alternative['type_claim_ids'][0]])
        rule = self.inputs['business-rules']['rules'][0]
        self.assertIn('BUSINESS_RULE', index[rule['attribute_claims']['condition'][0]])
        state_finding = dict(id='finding:state', kind='unknown_state_transition', target_refs=[scenario['steps'][0]['id']])
        self.assertIn('STATE_TRANSITION', {i['aspect'] for i in minimum_impacts(state_finding, self.inputs, index)})
        version_gap = dict(id='gap:version', reason='unknown_version', affected_ids=[self.inputs['knowledge']['sources'][0]['id']])
        self.assertIn('VERSION_ENVIRONMENT', {i['aspect'] for i in minimum_impacts(version_gap, self.inputs, index)})
        external = copy.deepcopy(self.inputs)
        external['knowledge']['entities'].append(dict(id='api:fixture', type='ApiOperation', label='Fixture API'))
        c = copy.deepcopy(external['knowledge']['claims'][0])
        c.update(id='claim:api:response', subject_id='api:fixture', predicate='response_contract', value='Synthetic response contract')
        external['knowledge']['claims'].append(c)
        self.assertIn('EXTERNAL_CONTRACT', impact_index(external)[c['id']])

    def test_secondary_discovery_source_is_not_automatically_a_process_gap(self):
        index = impact_index(self.inputs)
        cid = next(c['id'] for c in self.inputs['knowledge']['claims'] if c['predicate'] == 'registered_handler')
        gap = dict(id='gap:secondary-test', reason='missing_source', affected_ids=[cid])
        self.assertEqual(minimum_impacts(gap, self.inputs, index), [])

    def test_cli_summarize_updates_only_derived_subset_and_summary(self):
        from audit import main
        import tempfile, io
        from contextlib import redirect_stdout
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report_path, gap_path = root / 'report.json', root / 'gaps.json'
            self.gaps['publication_subset'] = dict(gap_ids=[], finding_ids=[])
            before = copy.deepcopy((self.report['claim_reviews'], self.report['findings'], self.gaps['gaps']))
            report_path.write_text(json.dumps(self.report), encoding='utf8')
            gap_path.write_text(json.dumps(self.gaps), encoding='utf8')
            args = ['audit.py', 'summarize', '--report', str(report_path), '--gaps', str(gap_path)]
            with patch.object(sys, 'argv', args), redirect_stdout(io.StringIO()):
                self.assertIsNone(main())
            report, gaps = load(report_path), load(gap_path)
            self.assertEqual(gaps['publication_subset']['gap_ids'], ['gap:process:ordering','gap:process:result'])
            self.assertEqual((report['claim_reviews'], report['findings'], gaps['gaps']), before)
            self.assertEqual(check_report(report, gaps, self.inputs), [])

    def test_material_gap_cannot_be_hidden_by_internal_label(self):
        gap = next(g for g in self.gaps['gaps'] if g['id'] == 'gap:process:ordering')
        gap['publication_relevance'] = dict(classification=INTERNAL, reviewed=True, impacts=[], reason='Cosmetic classification.')
        refresh_publication_subset(self.report, self.gaps)
        self.assertTrue(any('cannot be hidden' in error for error in self.errors()))

    def test_subset_must_be_exact_and_traceable(self):
        self.gaps['publication_subset']['gap_ids'] = ['gap:internal:00']
        self.assertTrue(any('subset must exactly match' in error for error in self.errors()))
        refresh_publication_subset(self.report, self.gaps)
        gap = next(g for g in self.gaps['gaps'] if g['id'] == 'gap:process:result')
        gap['publication_relevance']['impacts'][0]['target_refs'] = ['missing:claim']
        self.assertTrue(any('unknown impact target refs' in error for error in self.errors()))

    def test_input_research_gaps_cannot_be_deleted(self):
        self.gaps['gaps'] = [g for g in self.gaps['gaps'] if g['id'] != 'gap:internal:00']
        self.report['gap_ids'] = sorted(g['id'] for g in self.gaps['gaps'])
        refresh_publication_subset(self.report, self.gaps)
        self.report['summary'] = calculate_summary(self.report, self.gaps)
        self.assertTrue(any('input Gap/provenance was removed' in error for error in self.errors()))

    def test_closed_gap_is_kept_without_becoming_publication_warning(self):
        closed = copy.deepcopy(self.inputs['knowledge']['gaps'][0]); closed.update(id='gap:internal:closed', status='resolved')
        self.inputs['knowledge']['gaps'].append(closed)
        report, gaps = draft(self.inputs)
        self.assertIn(closed['id'], {g['id'] for g in gaps['gaps']})
        self.assertNotIn(closed['id'], gaps['publication_subset']['gap_ids'])
        self.assertEqual(check_report(report, gaps, self.inputs), [])

    def test_main_process_conflict_remains_visible(self):
        inputs = audit_inputs()
        _, counterpart = add_counterpart(inputs, 'CONFLUENCE')
        original = next(c for c in inputs['knowledge']['claims'] if c['id'] == 'claim:edge:0')
        competing = copy.deepcopy(next(c for c in inputs['knowledge']['claims'] if c['id'] == counterpart))
        competing.update(id='claim:conflicting-main-order', subject_id=original['subject_id'],
                         predicate=original['predicate'], value='scenario-step:return-zero', text='Synthetic competing main ordering.')
        inputs['knowledge']['claims'].append(competing)
        report, gaps = draft(inputs)
        comparison = next(c for c in report['comparisons'] if set(c['claim_ids']) == {original['id'], competing['id']})
        comparison.update(status='CONFLICT', reviewed=True, context_comparison='overlap')
        for cid in comparison['claim_ids']:
            review = mark_reviewed(inputs, report, cid, 'CONFLICT')
            review.update(comparison_ids=[comparison['id']], required_action='analyst_review')
        report['summary'] = calculate_summary(report, gaps)
        self.assertEqual(check_report(report, gaps, inputs), [])
        finding = next(f for f in report['findings'] if set(f['claim_ids']) == set(comparison['claim_ids']))
        self.assertIn(finding['id'], gaps['publication_subset']['finding_ids'])
        linked = next(link['gap_ids'] for link in gaps['finding_gap_links'] if link['finding_id'] == finding['id'])
        for item in [finding] + [g for g in gaps['gaps'] if g['id'] in linked]:
            item['publication_relevance'] = dict(classification=INTERNAL, reviewed=True, impacts=[], reason='Hide implementation noise.')
        refresh_publication_subset(report, gaps)
        self.assertTrue(any('conflict affecting the process must remain visible' in error
                            for error in publication_errors(report, gaps, inputs)))

    def test_schema_reuses_shared_gap_and_requires_reader_impact(self):
        from paths import contracts_root
        shared = load(contracts_root() / 'schemas/common.schema.json')
        self.assertIn('publication_relevance', shared['$defs']['gap']['properties'])
        gap = self.gaps['gaps'][0]
        gap['publication_relevance'] = dict(classification=PUBLIC, reviewed=True, impacts=[], reason='High severity.')
        self.assertTrue(schema_errors('validation-gaps', self.gaps))

    def test_no_source_access_determinism_and_input_immutability(self):
        before = copy.deepcopy(self.inputs)
        with patch('socket.socket', side_effect=AssertionError('No source lookup')):
            first = draft(self.inputs)
            self.assertEqual(first, draft(self.inputs))
        self.assertEqual(self.inputs, before)
        # Refreshing the projection never changes assessments, claims or inventory.
        metadata = copy.deepcopy((self.report['findings'], self.gaps['gaps']))
        refresh_publication_subset(self.report, self.gaps)
        self.assertEqual((self.report['findings'], self.gaps['gaps']), metadata)


if __name__ == '__main__':
    unittest.main()
