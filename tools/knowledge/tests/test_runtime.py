"""Synthetic, offline contracts for optional OpenSearch observations."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit import calculate_summary, check_report, draft
from compose import compose, cell
from test_composer import review_relevance
from glossary import empty_glossary, validation_errors
from model import increment_errors
from runtime import GAP_REASONS, assessment, case_reference, runtime_errors
from test_audit import mark_reviewed
from test_model import profile_fixture, sync_evidence
from validate import schema_errors, validate, SCHEMAS, schema_validator

PATH = ['calculate', 'scoring_request', 'import']
ALTERNATIVE = ['calculate', 'import', 'scoring_request']
START, END = '2026-09-25T10:00:00Z', '2026-09-25T11:00:00Z'


def runtime_fixture(paths=None, capability='available', static=None, ambiguity=True, minimum=3,
                    observation=False, outcomes=None):
    k,t,d,m,f,r,s = profile_fixture()
    inputs = dict(knowledge=k, **{'domain-tree':t,'scenario-definition':d,'source-map':m,
                                  'technical-flow':f,'business-rules':r,'scenario':s})
    k['scope']['environments'] = ['production', 'test']
    k['runtime_traces'], k['runtime_confirmations'] = [], []
    m['runtime_lookup'] = dict(capability=capability, lookup_keys=['fields.AccountNumber'],
                              representative_case_refs=[], diagnostic='Synthetic optional MCP capability.')
    for i,path in enumerate(paths or []):
        eid,sid,tid = f'evidence:runtime:{i}',f'snapshot:runtime:{i}',f'trace:runtime:{i}'
        timeline = [dict(order=j+1,timestamp=f'2026-09-25T10:0{i}:0{j}Z',event=event,
                         technical_step_ref='technical-step:guard',technical_refs=['FixtureHandler.Handle'],
                         evidence_ids=[eid]) for j,event in enumerate(path)]
        excerpt = json.dumps(timeline,sort_keys=True)
        snap = copy.deepcopy(k['sources'][0])
        snap.update(id=sid,adapter='opensearch',repository=None,locator='logs-apps-* / synthetic bounded query',
                    revision='runtime-v1',commit=None,working_tree_state='not_applicable',excerpt=excerpt,
                    content_hash=hashlib.sha256(excerpt.encode()).hexdigest())
        e = copy.deepcopy(k['evidence'][0])
        e.update(id=eid,source_type='OPENSEARCH',snapshot_id=sid,source_location=snap['locator'],
                 repository=None,file=None,version='runtime-v1',commit=None,page=None,section=None,
                 excerpt=excerpt, **{'class':None,'method':None})
        e['runtime'] = dict(environment='production',index='logs-apps-*',query_description='Synthetic bounded query.',
                            case_ref=case_reference('synthetic-'+str(i)), time_from=START,time_to=END,
                            application_version='runtime-v1',limitations=['Only this observed case.'])
        trace = dict(id=tid,scenario_id=s['scenario_id'],environment='production',application_version='runtime-v1',
                     time_from=timeline[0]['timestamp'],time_to=timeline[-1]['timestamp'],
                     identifiers=dict(case_ref=e['runtime']['case_ref']), outcome=(outcomes or ['SUCCESS']*len(paths))[i],
                     complete=True,ordering_basis='correlated_events',timeline=timeline,evidence_ids=[eid],
                     limitations=['Synthetic correlated markers; no production access.'])
        k['sources'].append(snap); k['evidence'].append(e); k['runtime_traces'].append(trace)
    check = dict(id='runtime:ordering',scenario_id=s['scenario_id'],question='Which possible ordering is observed?',
                 material_ambiguity=ambiguity,capability=capability,environment='production',application_version='runtime-v1',
                 time_from=START,time_to=END,cohort='SUCCESS',minimum_sample_size=minimum,
                 event_filter=PATH,static_claim_ids=[],static_sequences=[],
                 static_review_evidence_ids=['evidence:fixture'],selection_reason='Independent completed synthetic cases of one version.',
                 trace_refs=[t['id'] for t in k['runtime_traces']],claim_ids=[],gap_ids=[],status='NOT_CHECKED',
                 limitations=['Observed cases cannot establish a universal business rule.'])
    if static:
        c = copy.deepcopy(k['claims'][0])
        c.update(id='claim:static:ordering',subject_id=s['scenario_id'],predicate='possible_event_sequence',
                 value=static,text='Synthetic possible static sequence.')
        k['claims'].append(c)
        check['static_claim_ids'] = [c['id']]; check['static_sequences'] = [static]
    check['status'] = assessment(check,{t['id']:t for t in k['runtime_traces']})['result']
    reason = GAP_REASONS.get(check['status'])
    if reason:
        gap = dict(id='gap:runtime:ordering',reason=reason,question='Runtime ordering remains unresolved.',
                   affected_ids=[check['id']],next_action='verify_source',status='open')
        check['gap_ids'] = [gap['id']]; k['gaps'].append(gap)
    if observation:
        c = copy.deepcopy(k['claims'][0])
        c.update(id='claim:runtime:ordering',subject_id=s['scenario_id'],predicate='observed_runtime_sequence',
                 value=dict(confirmation_ref=check['id'],extent='observed_cases',statement='Observed synthetic ordering.',sequence=paths[0]),
                 text='Observed synthetic ordering.',modality='runtime_observation',
                 context=dict(c['context'],environment='production'),
                 support=[dict(evidence_id=t['evidence_ids'][0],role='supports') for t in k['runtime_traces']],
                 knowledge_status='CONFIRMED' if check['status']=='OBSERVED' else 'PARTIALLY_CONFIRMED')
        k['claims'].append(c); check['claim_ids'] = [c['id']]
        if reason:
            k['gaps'][-1]['affected_ids'].append(c['id'])
    k['runtime_confirmations'].append(check)
    f['runtime_confirmation_refs'] = [check['id']]; s['runtime_confirmation_refs'] = [check['id']]
    if k['runtime_traces']:
        r['rules'][0]['runtime_examples'] = [k['runtime_traces'][0]['id']]
    sync_evidence(k)
    return inputs


def reviewed(inputs):
    report,gaps = draft(inputs)
    for cid in report['claim_inventory']:
        c = next(c for c in inputs['knowledge']['claims'] if c['id']==cid)
        row = mark_reviewed(inputs,report,cid,c['knowledge_status'])
        if c['knowledge_status']=='PARTIALLY_CONFIRMED':
            row.update(supported_parts=['Observed selected case.'],unsupported_parts=['Current representative flow.'])
    for row in report.get('runtime_reviews',[]):
        row.update(reviewed=True,reason='Synthetic correlation, scope and representativeness reviewed.')
    review_relevance(report,gaps)
    return report,gaps


class RuntimeTests(unittest.TestCase):
    def errors(self, inputs):
        return validate('scenario',inputs['scenario'],inputs['knowledge'],inputs['domain-tree'],
                        inputs['scenario-definition'],inputs['technical-flow'],inputs['source-map'],inputs['business-rules'])

    def test_01_static_pipeline_without_runtime_unchanged(self):
        k,t,d,m,f,r,s = profile_fixture()
        self.assertEqual(validate('scenario',s,k,t,d,f,m,r),[])
        i = runtime_fixture(ambiguity=False,capability='unavailable')
        self.assertEqual(self.errors(i),[])
        self.assertEqual(i['knowledge']['runtime_confirmations'][0]['status'],'NOT_REQUIRED')

    def test_02_three_matching_traces_support_only_current_scoped_flow(self):
        i = runtime_fixture([PATH]*3,observation=True)
        self.assertEqual(self.errors(i),[])
        report,gaps = reviewed(i)
        self.assertEqual(check_report(report,gaps,i),[])
        self.assertEqual(validation_errors(i['knowledge'],report),[])
        self.assertEqual(report['runtime_reviews'][0]['sample_size'],3)
        doc,manifest = compose(i,report,gaps,empty_glossary())
        self.assertIn('кейсов=3',doc)
        self.assertIn(cell(START),doc)
        self.assertIn('Наблюдение ограничено этой выборкой.',doc)
        self.assertTrue(any('runtime:ordering' in b['derived_from'] for b in manifest['document']['blocks']))

    def test_03_different_traces_preserve_variability(self):
        i = runtime_fixture([PATH,ALTERNATIVE,PATH])
        self.assertEqual(self.errors(i),[])
        report,gaps = draft(i)
        self.assertEqual(report['runtime_reviews'][0]['result'],'VARIABLE')
        self.assertTrue(any(g['reason']=='RUNTIME_VARIABILITY' for g in gaps['gaps']))
        self.assertFalse(report['runtime_reviews'][0]['reviewed'])

    def test_04_static_runtime_conflict_preserves_static_model(self):
        i = runtime_fixture([PATH]*3,static=ALTERNATIVE)
        self.assertEqual(self.errors(i),[])
        self.assertEqual(i['knowledge']['runtime_confirmations'][0]['status'],'STATIC_RUNTIME_CONFLICT')
        self.assertEqual(i['knowledge']['claims'][-1]['value'],ALTERNATIVE)
        self.assertEqual(i['knowledge']['claims'][-1]['knowledge_status'],'CONFIRMED')

    def test_05_single_case_is_insufficient_but_limited_observation_allowed(self):
        i = runtime_fixture([PATH],observation=True)
        self.assertEqual(self.errors(i),[])
        report,gaps = reviewed(i)
        self.assertEqual(check_report(report,gaps,i),[])
        self.assertEqual(report['runtime_reviews'][0]['result'],'INSUFFICIENT_SAMPLE')
        row = next(r for r in report['claim_reviews'] if r['claim_id']=='claim:runtime:ordering')
        row.update(status='CONFIRMED',unsupported_parts=[])
        report['summary'] = calculate_summary(report,gaps)
        self.assertTrue(any('limited sample' in e for e in check_report(report,gaps,i)))

    def test_06_unavailable_mcp_creates_gap_without_static_failure(self):
        i = runtime_fixture(capability='unavailable')
        self.assertEqual(self.errors(i),[])
        report,gaps = draft(i)
        self.assertEqual(report['mechanical_errors'],[])
        self.assertEqual(report['runtime_reviews'][0]['result'],'NOT_CHECKED')
        self.assertTrue(any(g['reason']=='RUNTIME_UNVERIFIED' for g in gaps['gaps']))

    def test_07_runtime_cannot_supply_business_rationale(self):
        i = runtime_fixture([PATH]*3,observation=True)
        self.assertEqual(i['business-rules']['rules'][0]['business_rationale']['status'],'UNKNOWN')
        report,gaps=reviewed(i)
        self.assertEqual(check_report(report,gaps,i),[])
        doc,_=compose(i,report,gaps,empty_glossary())
        self.assertNotIn('Причина: [UNKNOWN',doc)
        self.assertNotIn('Business intent from logs.',doc)
        c = i['knowledge']['claims'][-1]
        c.update(predicate='business_rationale',modality='source_statement',value='Business intent from logs.')
        self.assertTrue(any('logs may support only' in e for e in self.errors(i)))

    def test_invariants_period_version_environment_cohort_and_completion(self):
        for field,value in [('environment','test'),('application_version','old-v0'),('complete',False),
                            ('outcome','ERROR'),('ordering_basis','timestamp_only'),('time_to','2026-09-26T10:00:00Z')]:
            with self.subTest(field=field):
                i = runtime_fixture([PATH]*3)
                i['knowledge']['runtime_traces'][0][field] = value
                check = i['knowledge']['runtime_confirmations'][0]
                self.assertEqual(assessment(check,{t['id']:t for t in i['knowledge']['runtime_traces']})['result'],'NOT_CHECKED')
                self.assertTrue(self.errors(i))

    def test_distinct_cases_and_five_case_target(self):
        i = runtime_fixture([PATH]*3)
        t = i['knowledge']['runtime_traces']; c = i['knowledge']['runtime_confirmations'][0]
        t[1]['identifiers'] = copy.deepcopy(t[0]['identifiers'])
        self.assertEqual(assessment(c,{t['id']:t for t in t})['result'],'INSUFFICIENT_SAMPLE')
        i = runtime_fixture([PATH]*3,minimum=5)
        self.assertEqual(self.errors(i),[])
        self.assertEqual(i['knowledge']['runtime_confirmations'][0]['status'],'INSUFFICIENT_SAMPLE')
        self.assertEqual(self.errors(runtime_fixture([PATH]*5,minimum=5,observation=True)),[])

    def test_no_runtime_without_ambiguity_or_static_review(self):
        i = runtime_fixture([PATH]*3,ambiguity=False)
        self.assertTrue(any('not justified' in e for e in self.errors(i)))
        i = runtime_fixture([PATH]*3)
        i['knowledge']['runtime_confirmations'][0]['static_review_evidence_ids']=['evidence:runtime:0']
        self.assertTrue(any('static review' in e for e in self.errors(i)))

    def test_normalized_refs_and_event_evidence_cannot_dangle(self):
        i = runtime_fixture([PATH]*3)
        i['knowledge']['runtime_traces'][0]['timeline'][0]['technical_step_ref']='step:missing'
        self.assertTrue(any('dangling technical' in e for e in self.errors(i)))
        i = runtime_fixture([PATH]*3)
        i['knowledge']['runtime_traces'][0]['timeline'][0]['evidence_ids']=[]
        self.assertTrue(any('every event' in e for e in self.errors(i)))

    def test_universal_extent_and_raw_identifiers_rejected_by_shared_schema(self):
        i = runtime_fixture([PATH]*3,observation=True)
        i['knowledge']['claims'][-1]['value']['extent']='always'
        self.assertTrue(schema_errors('knowledge-package',i['knowledge']))
        i = runtime_fixture([PATH]*3)
        i['knowledge']['runtime_traces'][0]['identifiers']['case_ref']='real-account-number'
        self.assertTrue(schema_errors('knowledge-package',i['knowledge']))
        self.assertNotIn('sensitive-original-id',case_reference('sensitive-original-id'))

    def test_runtime_history_is_immutable(self):
        i = runtime_fixture([PATH]*3)
        old=copy.deepcopy(i['knowledge']); new=copy.deepcopy(old); new['revision']+=1
        new['runtime_traces'][0]['outcome']='ERROR'
        self.assertTrue(any('immutable runtime_traces' in e for e in increment_errors(old,new)))
        new=copy.deepcopy(old); new['revision']+=1; new['runtime_confirmations'][0]['status']='VARIABLE'
        self.assertTrue(any('immutable runtime_confirmations' in e for e in increment_errors(old,new)))

    def test_semantic_review_not_automatically_granted(self):
        i = runtime_fixture([PATH]*3,observation=True); report,gaps=reviewed(i)
        report['runtime_reviews'][0]['reviewed']=False
        self.assertTrue(any('semantic runtime review' in e for e in check_report(report,gaps,i)))
        report['runtime_reviews'][0].update(reviewed=True,sample_size=20)
        self.assertTrue(any('incorrect runtime review' in e for e in check_report(report,gaps,i)))

    def test_composer_never_queries_sources_or_renders_raw_log_lines(self):
        i=runtime_fixture([PATH]*3,observation=True)
        sentinel='RAW_LOG_SECRET_SENTINEL'
        for e in i['knowledge']['evidence']:
            if e['source_type']=='OPENSEARCH':
                e['excerpt']+=sentinel
        report,gaps=reviewed(i)
        with patch('socket.socket',side_effect=AssertionError('network forbidden')):
            doc,_=compose(i,report,gaps,empty_glossary())
        self.assertNotIn(sentinel,doc)
        self.assertNotIn('Synthetic bounded query.',doc)
        self.assertNotIn(i['knowledge']['runtime_traces'][0]['identifiers']['case_ref'],doc)

    def test_schema_wrappers_reuse_single_shared_model(self):
        i=runtime_fixture([PATH]*3)
        self.assertEqual(schema_errors('runtime-trace',i['knowledge']['runtime_traces'][0]),[])
        self.assertEqual(schema_errors('runtime-confirmation',i['knowledge']['runtime_confirmations'][0]),[])
        for p in SCHEMAS.glob('*.schema.json'):
            schema_validator(p.name.removesuffix('.schema.json'))

    def test_runtime_gaps_cannot_be_omitted_or_closed_in_review(self):
        i=runtime_fixture(capability='unavailable'); report,gaps=reviewed(i)
        gap=next(g for g in gaps['gaps'] if g['reason']=='RUNTIME_UNVERIFIED')
        gap['status']='resolved'
        report['summary']=calculate_summary(report,gaps)
        self.assertTrue(any('cannot be hidden or closed' in e for e in check_report(report,gaps,i)))
        report,gaps=reviewed(i)
        report['gap_ids'].remove('gap:runtime:ordering')
        self.assertTrue(any('omitted' in e for e in check_report(report,gaps,i)))

    def test_normalized_event_must_occur_in_captured_evidence(self):
        i=runtime_fixture([PATH]*3)
        i['knowledge']['runtime_traces'][0]['timeline'][0]['event']='invented_marker'
        self.assertTrue(any('absent from captured' in e for e in self.errors(i)))

    def test_upstream_runtime_refs_and_rule_examples_checked(self):
        for artifact,field in [('technical-flow','runtime_confirmation_refs'),('scenario','runtime_confirmation_refs')]:
            i=runtime_fixture([PATH]*3); i[artifact][field]=['runtime:missing']
            self.assertTrue(any('dangling/cross-scenario' in e for e in self.errors(i)))
        i=runtime_fixture([PATH]*3); i['business-rules']['rules'][0]['runtime_examples']=['trace:missing']
        self.assertTrue(any('invalid runtime example' in e for e in self.errors(i)))

    def test_runtime_observation_cannot_ground_an_inferred_universal_rule(self):
        i=runtime_fixture([PATH]*3,observation=True)
        c=copy.deepcopy(i['knowledge']['claims'][-1])
        c.update(id='claim:inferred:universal',predicate='universal_rule',modality='inferred',inference=True,
                 value='Always execute scoring before import',knowledge_status='INFERRED',support=[],
                 basis_claim_ids=['claim:runtime:ordering'],inference_rationale='An invalid generalization from cases.')
        i['knowledge']['claims'].append(c)
        # Even a static context/support attached to an observation cannot launder it into a rule basis.
        i['knowledge']['claims'][-2]['support'].append(dict(evidence_id='evidence:fixture',role='supports'))
        sync_evidence(i['knowledge'])
        self.assertTrue(any('supported basis' in e for e in self.errors(i)))

    def test_assessment_cannot_hide_collected_cases_or_bind_static_claim_as_observation(self):
        i=runtime_fixture([PATH]*3)
        i['knowledge']['runtime_confirmations'][0]['trace_refs'].pop()
        self.assertTrue(any('retained in a runtime assessment' in e for e in self.errors(i)))
        i=runtime_fixture([PATH]*3)
        i['knowledge']['runtime_confirmations'][0]['claim_ids']=['claim:business_goal']
        self.assertTrue(any('qualified runtime observations' in e for e in self.errors(i)))

    def test_runtime_claim_environment_must_match_its_trace_scope(self):
        i=runtime_fixture([PATH]*3,observation=True)
        i['knowledge']['claims'][-1]['context']['environment']='test'
        self.assertTrue(any('Claim environment' in e for e in self.errors(i)))

    def test_legacy_static_backed_runtime_modality_keeps_its_original_value_shape(self):
        from test_composer import reviewed_fixture
        i,_,_=reviewed_fixture()
        i['knowledge']['claims'][0]['modality']='runtime_observation'
        report,gaps=draft(i)
        for cid in report['claim_inventory']:
            mark_reviewed(i,report,cid)
        review_relevance(report,gaps)
        self.assertEqual(check_report(report,gaps,i),[])
        compose(i,report,gaps,empty_glossary())

    def test_opensearch_cannot_use_unqualified_legacy_value(self):
        i=runtime_fixture([PATH]*3,observation=True)
        i['knowledge']['claims'][-1]['value']='Always execute scoring before import'
        self.assertTrue(any('normalized confirmation' in e for e in self.errors(i)))

    def test_new_immutable_runtime_increment_preserves_upstream_static_artifacts(self):
        i=runtime_fixture([PATH]*3,observation=True)
        static=copy.deepcopy(i['knowledge']); static.pop('runtime_traces'); static.pop('runtime_confirmations')
        static['claims']=[c for c in static['claims'] if c['modality']!='runtime_observation']
        static['evidence']=[e for e in static['evidence'] if e['source_type']!='OPENSEARCH']
        static['sources']=[s for s in static['sources'] if s['adapter']!='opensearch']
        sync_evidence(static)
        current=copy.deepcopy(i['knowledge']); current['revision']+=1
        self.assertEqual(increment_errors(static,current),[])
        from pipeline import projection
        for name in ('technical-flow','scenario'):
            artifact=copy.deepcopy(i[name]); artifact['package_ref']['revision']+=1
            self.assertEqual(projection(artifact),projection(i[name]))

    def test_runtime_failure_gap_and_all_variants_visible_in_composer(self):
        for paths,capability,status in [([PATH,ALTERNATIVE,PATH],'available','VARIABLE'),
                                         (None,'unavailable','NOT_CHECKED'),([PATH],'available','INSUFFICIENT_SAMPLE')]:
            with self.subTest(status=status):
                i=runtime_fixture(paths,capability=capability); report,gaps=reviewed(i)
                doc,_=compose(i,report,gaps,empty_glossary())
                self.assertIn('`' + status + '`',doc)
                self.assertTrue(gaps['publication_subset']['gap_ids'])
                for gid in gaps['publication_subset']['gap_ids']:
                    gap = next(g for g in gaps['gaps'] if g['id'] == gid)
                    self.assertIn(cell(gap['question']),doc)
                for t in i['knowledge']['runtime_traces']:
                    self.assertNotIn(cell(t['id']),doc)

    def test_five_stage_pipeline_adds_runtime_at_technical_stage(self):
        from pipeline import validate_run, KINDS
        i=runtime_fixture([PATH]*3,observation=True)
        manifest=json.loads((Path(__file__).parent/'fixtures/registration-address/pipeline-run.json').read_text(encoding='utf-8'))
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for number,row in enumerate(manifest['stages'],1):
                k=copy.deepcopy(i['knowledge']); k['revision']=number
                if number<3:
                    k.pop('runtime_traces'); k.pop('runtime_confirmations')
                    k['claims']=[c for c in k['claims'] if c['modality']!='runtime_observation']
                    k['evidence']=[e for e in k['evidence'] if e['source_type']!='OPENSEARCH']
                    k['sources']=[s for s in k['sources'] if s['adapter']!='opensearch']
                    sync_evidence(k)
                records={row['knowledge']:k,row['artifact']:copy.deepcopy(i[row['kind']])}
                records.update({row[key]:copy.deepcopy(i[kind]) for key,kind in KINDS.items() if key in row})
                for relative,data in records.items():
                    if data is not k:
                        data['package_ref']['revision']=number
                    path=root/relative; path.parent.mkdir(parents=True,exist_ok=True)
                    path.write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8')
            path=root/'pipeline-run.json'; path.write_text(json.dumps(manifest),encoding='utf-8')
            self.assertEqual(validate_run(path),[])


if __name__=='__main__':
    unittest.main()
