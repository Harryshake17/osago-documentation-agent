"""Workflow integration on existing synthetic contracts; no IDE, sources or MCP calls."""
import copy
import hashlib
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from audit import calculate_summary, draft
from publication import annotate_draft
from compose import compose
from glossary import curate, empty_glossary
from model import PROFILE
from orchestrate import Run, DEFAULT_PIPELINE, StateChangedError, pipeline_errors, save_data
from test_audit import add_counterpart, mark_reviewed
from test_composer import review_relevance
from test_model import profile_fixture, sync_evidence, unknown
from validate import load, validate


def historical_pipeline():
    """Saved stage-09 runs retain their snapshot; stage-10 integration has its own suite."""
    config=load(DEFAULT_PIPELINE)
    config['stages']=[s for s in config['stages'] if s['validator'] not in
                      {'confluence_plan','presentation_review','confluence_render'}]
    return config


def complete_fixture():
    """Synthetic source-stated fields and explicit N/A proofs, never production knowledge."""
    k,t,d,m,f,r,s=profile_fixture()
    domain='domain:workflow-fixture'
    k['entities'].append(dict(id=domain,type='Domain',label='Synthetic workflow domain',identity_key=domain,
                             preferred_name=unknown(),technical_aliases=[],search_aliases=[],terminology_candidates=[]))
    template=copy.deepcopy(k['claims'][0])
    def claim(subject,predicate,value,modality='source_statement'):
        c=copy.deepcopy(template)
        c.update(id='claim:workflow:'+str(len(k['claims'])),subject_id=subject,predicate=predicate,value=value,
                 text='Synthetic '+predicate+': '+str(value),modality=modality)
        k['claims'].append(c)
        return c['id']
    def value(row,field):
        cid=claim(row['id'],field,'Synthetic '+field)
        row[field]=dict(value='Synthetic '+field,status='CONFIRMED',claim_ids=[cid],evidence_ids=['evidence:fixture'])
        return cid
    node=f['nodes'][0]
    value(node,'business_meaning')
    for field in node['unknown_fields']:
        node['not_applicable_fields'].append(field)
        cid=claim(node['id'],'not_applicable',field)
        node['attribute_claims']['not_applicable/'+field]=[cid]
        node['claim_ids'].append(cid)
    node['unknown_fields']=[];node['gap_ids']=[]
    rule=r['rules'][0]
    value(rule,'business_statement')
    cid=value(rule,'business_rationale');rule['attribute_claims']['business_rationale']=[cid]
    rule['attribute_claims']['not_applicable/affected_state']=[claim(rule['id'],'not_applicable','affected_state')]
    rule['not_applicable_fields'].append('affected_state')
    rule['externally_visible_result']='Synthetic result'
    rule['attribute_claims']['externally_visible_result']=[claim(rule['id'],'externally_visible_result',rule['externally_visible_result'])]
    rule['unknown_fields']=[]
    state='state:workflow-fixture'
    k['entities'].append(dict(id=state,type='State',label='Synthetic stable state',identity_key=state,
                             preferred_name=unknown(),technical_aliases=[],search_aliases=[],terminology_candidates=[]))
    for step in s['steps']:
        value(step,'business_action');value(step,'business_result')
        for field,v in [('business_meaning','Synthetic business meaning'),('state_before',state),
                        ('state_after',state),('user_result','Synthetic result')]:
            step[field]=v;step['attribute_claims'][field]=[claim(step['id'],field,v)]
        step.update(unknown_fields=[],gap_ids=[],knowledge_status='CONFIRMED',state_transition={'from':state,'to':state})
    for row in (node,rule,*s['steps']):
        row['evidence']=['evidence:fixture']
    k['gaps']=[]
    def clear_gap_refs(value):
        if isinstance(value,dict):
            for key,child in value.items():
                if key=='gap_ids': value[key]=[]
                else: clear_gap_refs(child)
        elif isinstance(value,list):
            for child in value: clear_gap_refs(child)
    for artifact in (t,d,m,f,r,s): clear_gap_refs(artifact)
    sync_evidence(k)
    return dict(knowledge=k,**{'domain-tree':t,'scenario-definition':d,'source-map':m,
                              'technical-flow':f,'business-rules':r,'scenario':s}),domain


class Producer:
    """Test double writes artifacts as a skill would; engine never fabricates them."""
    def __init__(self):
        self.inputs,self.domain=complete_fixture()
        self.scenario=self.inputs['scenario']['scenario_id']
        self.called=[]
        self.units={'fixture':self.inputs}

    def add_second_scenario(self):
        clone=copy.deepcopy(self.inputs);identifiers=set()
        def collect(value):
            if isinstance(value,dict):
                if isinstance(value.get('id'),str): identifiers.add(value['id'])
                for child in value.values(): collect(child)
            elif isinstance(value,list):
                for child in value: collect(child)
        collect(clone);identifiers.add(clone['knowledge']['package_id'])
        identifiers.discard(self.domain)
        mapping={v:v+':second' for v in identifiers}
        def rewrite(value):
            if isinstance(value,dict): return {k:rewrite(v) for k,v in value.items()}
            if isinstance(value,list): return [rewrite(v) for v in value]
            return mapping.get(value,value) if isinstance(value,str) else value
        self.units['second']=rewrite(clone)
        sync_evidence(self.units['second']['knowledge'])

    def write(self,directory,data):
        paths={}
        for key,value in data.items():
            name={'final-document':'09-final-document.md','language-review':'09-language-review.yaml'}.get(
                key,key+'.md' if isinstance(value,str) else key+'.yaml')
            path=directory/name
            if isinstance(value,str): path.write_bytes(value.encode('utf-8'))
            else: save_data(path,value)
            paths[key]=name
        return paths

    def domain_result(self,task):
        directory=Path(task['output_dir'])
        master={k:copy.deepcopy(self.inputs[k]) for k in ('knowledge','domain-tree')}
        master['knowledge']['package_id']='kb:workflow-master'
        master['domain-tree']['package_ref']['id']='kb:workflow-master'
        for item_id,data in self.units.items():
            if item_id=='fixture': continue
            for group in ('entities','sources','evidence','claims','relations','gaps','conflicts'):
                present={row['id'] for row in master['knowledge'][group]}
                master['knowledge'][group].extend(copy.deepcopy(row) for row in data['knowledge'][group] if row['id'] not in present)
            master['knowledge']['scope']['scenarios'].extend(data['knowledge']['scope']['scenarios'])
            nodes=copy.deepcopy(data['domain-tree']['nodes'])
            for node in nodes: node['scope_ref']=master['knowledge']['scope']['id']
            master['domain-tree']['nodes'].extend(nodes)
        artifacts=self.write(directory,master)
        items=[]
        for item_id,data in self.units.items():
            item_directory=directory/item_id;item_directory.mkdir()
            item_artifacts=self.write(item_directory,{k:copy.deepcopy(data[k]) for k in ('knowledge','domain-tree','scenario-definition')})
            items.append(dict(id=item_id,scenario_id=data['scenario']['scenario_id'],domain_id=self.domain,
                artifacts={k:item_id+'/'+p for k,p in item_artifacts.items()}))
        return dict(artifacts=artifacts,work_items=items)

    def produce(self,run, *, mutate=None, review_gap=False, review_conflict=False):
        plan=run.plan();key=plan['node_id'];task=run.start(key);self.called.append(key)
        stage=run.spec(run.state['nodes'][key]);directory=Path(task['output_dir'])
        inputs={k:Path(p).read_bytes().decode('utf-8') if k=='draft' else load(p) for k,p in task['inputs'].items()}
        seed=self.units.get(run.state['nodes'][key]['item_id'],self.inputs)
        if stage['validator']=='domain':
            result=self.domain_result(task)
        elif stage['validator']=='artifact':
            data={k:copy.deepcopy(inputs.get(k,seed.get(k))) for k in stage['outputs']}
            previous=load(task['previous_outputs']['knowledge']) if 'knowledge' in task['previous_outputs'] else None
            revision=max(inputs['knowledge']['revision'],previous['revision'] if previous else 0)+1
            data['knowledge']['revision']=revision
            for k,v in data.items():
                if k!='knowledge': v['package_ref']={'id':data['knowledge']['package_id'],'revision':revision}
            result={'artifacts':self.write(directory,data)}
        elif stage['validator']=='validation':
            report,gaps=draft(inputs)
            for cid in report['claim_inventory']: mark_reviewed(inputs,report,cid)
            if review_gap:
                row=report['claim_reviews'][0]
                row.update(status='UNKNOWN',gap_ids=['gap:workflow:review'],reason='Synthetic unresolved meaning.',required_action='analyst_review')
                gaps['gaps'].append(dict(id='gap:workflow:review',reason='unverified',question='Synthetic unresolved meaning?',
                                        affected_ids=[row['claim_id']],next_action='Review fixture.',status='open'))
                report['gap_ids']=sorted(g['id'] for g in gaps['gaps'])
            if review_conflict:
                comparison=report['comparisons'][0]
                comparison.update(reviewed=True,status='CONFLICT',context_comparison='overlap')
                for cid in comparison['claim_ids']:
                    row=mark_reviewed(inputs,report,cid,'CONFLICT')
                    row.update(comparison_ids=[comparison['id']],required_action='analyst_review')
            annotate_draft(report,gaps,inputs)
            review_relevance(report,gaps)
            result={'artifacts':self.write(directory,{'validation-report':report,'gaps':gaps})}
        elif stage['validator']=='glossary':
            base=inputs.pop('glossary')
            inc,current=curate(base,inputs,self.domain)
            result={'artifacts':self.write(directory,{'glossary-increment':inc,'glossary':current})}
        elif stage['validator']=='documentation':
            report,gaps,glossary=inputs.pop('report'),inputs.pop('gaps'),inputs.pop('glossary')
            doc,manifest=compose(inputs,report,gaps,glossary)
            result={'artifacts':self.write(directory,{'documentation':doc,'documentation-manifest':manifest,'documentation-meta':manifest})}
        elif stage['validator']=='language_review':
            from language_review import review
            final,report=review(inputs['draft'],inputs['glossary'],inputs['scenario'],inputs['validation'],
                                technical_flow=inputs.get('technical-flow'),business_rules=inputs.get('business-rules'),
                                glossary_increment=inputs.get('glossary-increment'),manifest=inputs.get('manifest'))
            result={'artifacts':self.write(directory,{'final-document':final,'language-review':report})}
        else:
            manifest=load(task['inputs']['manifest'])
            result={'artifacts':self.write(directory,{'reviewed-manifest':manifest})}
        if mutate: mutate(task,result)
        accepted=run.finish(key,result)
        return accepted,task,result


class OrchestratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seed=complete_fixture()

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.cleanup_directory)
        self.producer=Producer()
        self.run=Run.create(self.tmp.name,{'domain':'Synthetic OSAGO workflow domain'},run_id='workflow-test',pipeline=historical_pipeline())

    def cleanup_directory(self):
        # Windows can briefly report pending deletions as a nonempty directory.
        # Retry only that transient condition; never suppress a persistent failure.
        for attempt in range(4):
            try:
                self.tmp.cleanup();return
            except OSError as exc:
                if getattr(exc,'winerror',None)!=145 or attempt==3: raise
                time.sleep(.1*(attempt+1))

    def produce(self,**kwargs):
        result=self.producer.produce(self.run,**kwargs)
        self.assertEqual(result[0]['action'],'ACCEPTED',result[0])
        return result

    def scope(self):
        self.produce()
        self.assertEqual(self.run.plan()['action'],'WAITING_FOR_USER')
        self.run.review('scope-review','APPROVE','Approve this synthetic scope.')

    def through_validation(self,gap=False):
        self.scope()
        for _ in range(4): self.produce()
        self.produce(review_gap=gap)

    def complete(self):
        self.through_validation()
        self.assertEqual(self.run.plan()['skill'],'osago-glossary-curator')
        self.produce();self.produce();self.produce()
        self.assertEqual(self.run.plan()['action'],'COMPLETED')

    def test_01_happy_path_order_and_conditional_review(self):
        with patch.object(socket,'socket',side_effect=AssertionError('no network')):
            self.complete()
        self.assertEqual([k.split('@')[0] for k in self.producer.called],
            ['domain-decomposition','source-discovery','technical-flow','business-rules','scenario-reconstruction',
             'evidence-validation','glossary','documentation','language-review'])
        self.assertEqual(self.run.state['nodes']['evidence-review@fixture']['status'],'SKIPPED')
        self.assertIn('final-document',self.run.state['results']['fixture'])
        self.assertTrue(self.run.state['results']['fixture']['final-document']['path'].endswith('09-final-document.md'))
        self.assertIn('language-review',self.run.state['results']['fixture'])
        self.assertEqual(self.run.state['results']['fixture']['documentation'],self.run.state['results']['fixture']['final-document'])
        self.assertEqual(self.run.state['results']['fixture']['draft-document'],self.run.state['nodes']['documentation@fixture']['bundle']['documentation'])

    def test_02_scope_correction_persists_and_delegates_structured_update(self):
        self.produce();self.run.plan()
        self.run.review('scope-review','CORRECT','Exclude underwriting.',target='domain-decomposition')
        self.assertEqual(self.run.state['nodes']['source-discovery@fixture']['status'],'STALE')
        def correction(task,result):
            directory=Path(task['output_dir'])
            for p in [directory/result['artifacts']['knowledge'],directory/result['work_items'][0]['artifacts']['knowledge']]:
                k=load(p);k['scope']['exclusions'].append('underwriting');save_data(p,k)
            result['applied_review_ids']=[r['id'] for r in task['corrections']]
        _,task,_=self.produce(mutate=correction)
        self.assertEqual(task['corrections'][0]['response'],'Exclude underwriting.')
        event=self.run.state['reviews'][-1]
        self.assertEqual(event['status'],'APPLIED')
        self.assertTrue(event['applied_artifacts'])
        self.assertEqual(self.run.plan()['action'],'WAITING_FOR_USER')
        self.run.review('scope-review','APPROVE','Approve corrected scope.')
        self.assertEqual(self.run.plan()['skill'],'osago-source-discovery')

    def test_03_evidence_review_blocks_downstream_and_persists_reply(self):
        self.through_validation(gap=True)
        plan=self.run.plan()
        self.assertEqual(plan['action'],'WAITING_FOR_USER')
        self.assertTrue(plan['review']['items'])
        self.assertTrue(all(i['kind']!='CONFIRMED' for i in plan['review']['items']))
        self.assertEqual(self.run.state['nodes']['glossary@fixture']['status'],'PENDING')
        self.run.review(plan['node_id'],'APPROVE','Accept unresolved limits for this draft.')
        self.produce();self.produce();self.produce()
        self.assertEqual(self.run.plan()['action'],'COMPLETED')
        doc=self.run.state['results']['fixture']['final-document']
        self.assertNotIn('Publication gate:',(self.run.root/doc['path']).read_text(encoding='utf-8'))
        self.assertEqual(load(self.run.root / self.run.state['results']['fixture']['documentation-manifest']['path'])['publication_gate'], 'blocked')
        self.assertEqual(Run(self.run.root).state['reviews'][-1]['response'],'Accept unresolved limits for this draft.')

    def test_approved_domain_scope_revision_rebases_existing_source_attempt(self):
        self.scope();self.produce()
        self.run.rerun_from('domain-decomposition')
        self.producer.inputs['knowledge']['scope']['environments'].append('production')
        self.produce()
        self.assertEqual(self.run.plan()['action'],'WAITING_FOR_USER')
        self.run.review('scope-review','APPROVE','Approve production runtime scope.')
        self.produce()
        self.assertEqual(self.run.plan()['skill'],'osago-technical-flow-analyzer')

    def test_source_cannot_change_approved_domain_scope(self):
        self.scope();self.produce()
        self.run.rerun_from('source-discovery@fixture')
        def change_scope(task,result):
            path=Path(task['output_dir'])/result['artifacts']['knowledge']
            k=load(path);k['scope']['environments'].append('unauthorized')
            save_data(path,k)
        accepted,_,_=self.producer.produce(self.run,mutate=change_scope)
        self.assertEqual(accepted['action'],'FAILED')
        self.assertIn('scope changed',accepted['error'])

    def test_04_failure_preserves_upstream_and_05_retry_only_failed_stage(self):
        self.scope();self.produce()
        old=copy.deepcopy(self.run.state['nodes']['source-discovery@fixture']['bundle'])
        task=self.run.start('technical-flow@fixture')
        partial=Path(task['output_dir'])/'partial.txt';partial.write_text('Preserved partial attempt.')
        self.run.fail(task['node_id'],'SkillFailure','Synthetic technical failure.')
        self.assertEqual(self.run.plan()['action'],'FAILED')
        self.assertTrue(partial.exists())
        self.assertEqual(old,self.run.state['nodes']['source-discovery@fixture']['bundle'])
        self.assertEqual(self.run.state['nodes']['business-rules@fixture']['status'],'PENDING')
        self.run.retry('technical-flow@fixture');self.produce()
        self.assertEqual(self.run.plan()['skill'],'osago-business-rule-extractor')
        self.assertEqual(len(self.run.state['nodes']['technical-flow@fixture']['attempts']),2)

    def test_conflict_correction_updates_knowledge_and_reruns_validation(self):
        add_counterpart(self.producer.inputs,'CONFLUENCE');sync_evidence(self.producer.inputs['knowledge'])
        self.through_validation()
        # Replace the still-unapproved Validator report with a reviewed conflict.
        self.run.rerun_from('evidence-validation@fixture');self.produce(review_conflict=True)
        plan=self.run.plan()
        self.assertEqual(plan['action'],'WAITING_FOR_USER')
        self.assertTrue(any(i['kind']=='CONFLICT' for i in plan['review']['items']))
        self.assertEqual(self.run.state['nodes']['glossary@fixture']['status'],'STALE')
        response='Keep both versions; record this question for the analyst.'
        self.run.review(plan['node_id'],'CORRECT',response,target='business-rules@fixture')
        def correction(task,result):
            path=Path(task['output_dir'])/result['artifacts']['knowledge'];k=load(path)
            k['gaps'].append(dict(id='gap:workflow:human',reason='unverified',question=response,
                affected_ids=['claim:rule:parameters:0','claim:counterpart'],next_action='Analyst reviews the retained contradiction.',status='open'))
            save_data(path,k);result['applied_review_ids']=[r['id'] for r in task['corrections']]
        self.produce(mutate=correction)
        event=self.run.state['reviews'][-1]
        self.assertEqual(event['status'],'APPLIED')
        k=load(self.run.root/event['applied_artifacts']['knowledge']['path'])
        self.assertEqual(k['gaps'][-1]['question'],response)
        self.produce();self.produce(review_conflict=True)
        plan=self.run.plan();self.assertEqual(plan['action'],'WAITING_FOR_USER')
        self.run.review(plan['node_id'],'APPROVE','Proceed with these unresolved draft limitations.')
        self.produce();self.produce();self.produce();self.assertEqual(self.run.plan()['action'],'COMPLETED')

    def test_multiple_scenarios_share_one_run_and_chain_glossary_snapshots(self):
        self.producer.add_second_scenario()
        self.scope()
        while self.run.plan()['action']=='EXECUTE_SKILL': self.produce()
        self.assertEqual(self.run.plan()['action'],'COMPLETED')
        self.assertEqual(set(self.run.state['results']),{'fixture','second'})
        second=self.run.state['nodes']['glossary@second']
        self.assertIn('glossary@fixture',second['dependencies'])
        base=self.run.state['nodes']['glossary@fixture']['bundle']['glossary']
        self.assertEqual(second['input_fingerprints']['glossary'],base['content_hash'])
        self.run.rerun_from('glossary@fixture')
        self.assertEqual(self.run.state['nodes']['glossary@second']['status'],'STALE')
        self.assertEqual(self.run.state['nodes']['technical-flow@second']['status'],'COMPLETED')

    def test_06_new_session_resumes_same_review(self):
        self.through_validation(gap=True)
        first=self.run.plan();self.run=Run(self.run.root)
        self.assertEqual(first,self.run.plan())
        self.assertEqual(self.run.state['status'],'WAITING_FOR_USER')

    def test_07_completed_is_idempotent(self):
        self.complete()
        count={k:len(n['attempts']) for k,n in self.run.state['nodes'].items()}
        self.run=Run(self.run.root)
        self.assertEqual(self.run.plan()['action'],'COMPLETED')
        self.assertEqual(count,{k:len(n['attempts']) for k,n in self.run.state['nodes'].items()})

    def test_08_broken_rule_reference_blocks_validator(self):
        self.scope()
        for _ in range(3): self.produce()
        def broken(task,result):
            p=Path(task['output_dir'])/result['artifacts']['scenario'];s=load(p)
            s['steps'][0]['evaluated_rules']=['BR-NOT-REGISTERED'];save_data(p,s)
        accepted,_,_=self.producer.produce(self.run,mutate=broken)
        self.assertEqual(accepted['action'],'FAILED')
        self.assertEqual(self.run.state['nodes']['evidence-validation@fixture']['status'],'PENDING')

    def test_composer_broken_provenance_reference_is_rejected(self):
        self.through_validation();self.produce()
        def broken(task,result):
            for name in ('documentation-manifest','documentation-meta'):
                path=Path(task['output_dir'])/result['artifacts'][name];data=load(path)
                data['document']['blocks'][0]['derived_from'].append('claim:not-registered')
                save_data(path,data)
        accepted,_,_=self.producer.produce(self.run,mutate=broken)
        self.assertEqual(accepted['action'],'FAILED')
        self.assertIn('dangling provenance',accepted['error'])

    def test_composer_full_provenance_must_match_accepted_inputs(self):
        self.through_validation();self.produce()
        def broken(task,result):
            for name in ('documentation-manifest','documentation-meta'):
                path=Path(task['output_dir'])/result['artifacts'][name];data=load(path)
                data['document']['provenance']['knowledge']['claims'][0]['value']='Altered source fact'
                save_data(path,data)
        accepted,_,_=self.producer.produce(self.run,mutate=broken)
        self.assertEqual(accepted['action'],'FAILED')
        self.assertIn('structured provenance',accepted['error'])

    def test_09_declarative_future_stage_requires_no_core_change(self):
        config=historical_pipeline()
        config['stages'].append(dict(id='future-review',scope='item',type='skill',skill='osago-documentation-composer',
            depends_on=['scope-review','documentation','language-review'],inputs={'manifest':'documentation.documentation-manifest'},
            outputs={'reviewed-manifest':'documentation-manifest'},primary='reviewed-manifest',validator='schema'))
        self.run=Run.create(self.tmp.name,{'domain':'Future synthetic domain'},run_id='future-test',pipeline=config)
        self.through_validation();self.produce();self.produce();self.produce()
        self.assertEqual(self.run.plan()['node_id'],'future-review@fixture')
        self.produce();self.assertEqual(self.run.plan()['action'],'COMPLETED')

    def through_composer(self):
        self.through_validation();self.produce();self.produce()
        self.assertEqual(self.run.plan()['node_id'],'language-review@fixture')

    def test_language_failure_keeps_composer_complete_and_retries_only_reviewer(self):
        self.through_composer()
        upstream=copy.deepcopy(self.run.state['nodes']['documentation@fixture'])
        task=self.run.start('language-review@fixture')
        (Path(task['output_dir'])/'partial.md').write_text('Review preserved for retry.',encoding='utf-8')
        self.run.fail(task['node_id'],'LanguageReviewNeeded','Synthetic unresolved sentence requires review.')
        self.run=Run(self.run.root)
        self.assertEqual(self.run.plan()['action'],'FAILED')
        self.assertEqual(self.run.state['nodes']['documentation@fixture'],upstream)
        self.assertEqual(self.run.state['results'],{})
        self.run.retry('language-review@fixture');self.produce()
        self.assertEqual(self.run.plan()['action'],'COMPLETED')
        self.assertEqual(len(self.run.state['nodes']['documentation@fixture']['attempts']),1)
        self.assertEqual(len(self.run.state['nodes']['language-review@fixture']['attempts']),2)
        self.assertTrue((Path(task['output_dir'])/'partial.md').exists())

    def test_language_report_cannot_self_declare_success_after_identifier_change(self):
        self.through_composer()
        def broken(task,result):
            directory=Path(task['output_dir'])
            path=directory/result['artifacts']['final-document']
            document=path.read_text(encoding='utf-8')
            self.assertIn('FixtureHandler.Handle',document)
            document=document.replace('FixtureHandler.Handle','FixtureHandler.Changed')
            path.write_bytes(document.encode('utf-8'))
            report_path=directory/result['artifacts']['language-review'];report=load(report_path)
            report['review']['status']='COMPLETED'
            report['final_hash']=hashlib.sha256(document.encode('utf-8')).hexdigest()
            save_data(report_path,report)
        accepted,_,_=self.producer.produce(self.run,mutate=broken)
        self.assertEqual(accepted['action'],'FAILED')
        self.assertEqual(self.run.plan()['action'],'FAILED')
        self.assertEqual(self.run.state['nodes']['documentation@fixture']['status'],'COMPLETED')

    def test_language_review_preserves_original_crlf_input_hash(self):
        self.through_validation();self.produce()
        def crlf(task,result):
            directory=Path(task['output_dir']);path=directory/result['artifacts']['documentation']
            document=path.read_bytes().replace(b'\n',b'\r\n');path.write_bytes(document)
            for name in ('documentation-manifest','documentation-meta'):
                manifest_path=directory/result['artifacts'][name];manifest=load(manifest_path)
                manifest['document_hash']=hashlib.sha256(document).hexdigest();save_data(manifest_path,manifest)
        self.produce(mutate=crlf);self.produce()
        self.assertEqual(self.run.plan()['action'],'COMPLETED')

    def test_language_waiting_report_does_not_complete_run(self):
        self.through_composer()
        def waiting(task,result):
            path=Path(task['output_dir'])/result['artifacts']['language-review'];report=load(path)
            report['review']['status']='WAITING_FOR_REVIEW';save_data(path,report)
        accepted,_,_=self.producer.produce(self.run,mutate=waiting)
        self.assertEqual(accepted['action'],'FAILED')
        self.assertEqual(self.run.plan()['action'],'FAILED')
        self.assertEqual(self.run.state['nodes']['documentation@fixture']['status'],'COMPLETED')
        self.assertEqual(self.run.state['results'],{})

    def test_composer_rerun_invalidates_reviewer_and_resume_dispatches_it(self):
        self.complete();old=copy.deepcopy(self.run.state['nodes']['language-review@fixture']['bundle'])
        self.run.rerun_from('documentation@fixture')
        self.assertEqual(self.run.state['nodes']['language-review@fixture']['status'],'STALE')
        self.assertEqual(self.run.state['results'],{})
        self.produce();self.run=Run(self.run.root)
        plan=self.run.plan();self.assertEqual(plan['skill'],'osago-language-reviewer')
        self.assertEqual(plan['previous_outputs']['final-document'],str(self.run.root/old['final-document']['path']))
        self.produce();self.assertEqual(self.run.plan()['action'],'COMPLETED')
        self.assertEqual(len(self.run.state['nodes']['evidence-validation@fixture']['attempts']),1)

    def test_final_document_drift_invalidates_only_language_stage(self):
        self.complete()
        ref=self.run.state['nodes']['language-review@fixture']['bundle']['final-document']
        path=self.run.root/ref['path'];path.write_text('Unexpected external final edit.',encoding='utf-8')
        self.run=Run(self.run.root)
        self.assertEqual(self.run.plan()['node_id'],'language-review@fixture')
        self.assertEqual(self.run.state['nodes']['documentation@fixture']['status'],'COMPLETED')
        self.assertEqual(path.read_text(encoding='utf-8'),'Unexpected external final edit.')

    def test_language_review_has_only_declared_run_artifacts(self):
        self.through_composer();task=self.run.plan()
        self.assertEqual(set(task['inputs']),{'draft','manifest','glossary','scenario','validation',
                                             'technical-flow','business-rules','glossary-increment'})
        config=historical_pipeline();config['stages'][-1]['inputs'].pop('glossary')
        self.assertTrue(pipeline_errors(config))
        config=historical_pipeline();config['stages'][-1]['inputs']['source-map']='scenario-reconstruction.source-map'
        self.assertTrue(pipeline_errors(config))

    def test_scope_approval_cannot_be_bypassed(self):
        self.produce()
        with self.assertRaises(ValueError): self.run.start('source-discovery@fixture')
        self.assertEqual(self.run.state['status'],'WAITING_FOR_USER')

    def test_limited_inputs_and_run_identity(self):
        self.through_validation()
        task=self.run.plan()
        self.assertNotIn('source-map',task['inputs'])
        self.assertNotIn('documentation-request',task['inputs'])
        self.assertIn('knowledge',task['inputs'])
        self.assertEqual(task['run_id'],'workflow-test')
        for node in self.run.state['nodes'].values():
            for ref in node['bundle'].values():
                self.assertTrue((self.run.root/ref['path']).is_relative_to(self.run.root))

    def test_rerun_rules_invalidates_only_dependents(self):
        self.complete()
        self.run.rerun_from('business-rules@fixture')
        for key in ['domain-decomposition','scope-review','source-discovery@fixture','technical-flow@fixture']:
            self.assertEqual(self.run.state['nodes'][key]['status'],'COMPLETED')
        self.assertEqual(self.run.state['nodes']['business-rules@fixture']['status'],'PENDING')
        self.assertEqual(self.run.state['nodes']['scenario-reconstruction@fixture']['status'],'STALE')
        self.assertEqual(self.run.plan()['node_id'],'business-rules@fixture')

    def test_output_drift_propagates_without_rewriting_artifact(self):
        self.scope();self.produce()
        node=self.run.state['nodes']['source-discovery@fixture'];path=self.run.root/node['bundle']['source-map']['path']
        path.write_text('broken: schema',encoding='utf-8')
        self.assertEqual(self.run.plan()['node_id'],'source-discovery@fixture')
        self.assertEqual(path.read_text(encoding='utf-8'),'broken: schema')
        self.assertEqual(self.run.state['nodes']['technical-flow@fixture']['status'],'STALE')

    def test_interrupted_running_attempt_never_runs_twice(self):
        task=self.run.start('domain-decomposition')
        other=Run(self.run.root)
        self.assertEqual(other.plan()['action'],'RUNNING')
        with self.assertRaises(ValueError): other.start('domain-decomposition')
        self.assertEqual(len(other.state['nodes']['domain-decomposition']['attempts']),1)

    def test_correction_must_change_structured_artifact(self):
        self.produce();self.run.plan()
        self.run.review('scope-review','CORRECT','Change the domain.',target='domain-decomposition')
        def acknowledge_only(task,result): result['applied_review_ids']=[r['id'] for r in task['corrections']]
        accepted,_,_=self.producer.produce(self.run,mutate=acknowledge_only)
        self.assertEqual(accepted['action'],'FAILED')
        self.assertEqual(self.run.state['reviews'][-1]['status'],'PENDING')

    def test_output_path_escape_and_unknown_bundle_are_rejected(self):
        def escape(task,result): result['artifacts']['knowledge']='../../../../outside.yaml'
        accepted,_,_=self.producer.produce(self.run,mutate=escape)
        self.assertEqual(accepted['action'],'FAILED')
        self.assertIn('escapes',accepted['error'])

    def test_malformed_yaml_records_failure_and_preserves_attempt(self):
        def malformed(task,result):
            path=Path(task['output_dir'])/result['artifacts']['knowledge']
            path.write_text('knowledge: [broken',encoding='utf-8')
        accepted,task,_=self.producer.produce(self.run,mutate=malformed)
        self.assertEqual(accepted['action'],'FAILED')
        self.assertEqual(Run(self.run.root).plan()['action'],'FAILED')
        self.assertTrue((Path(task['output_dir'])/'knowledge.yaml').exists())

    def test_domain_base_artifact_drift_invalidates_domain_and_scope_approval(self):
        self.scope()
        ref=self.run.state['work_items'][0]['artifacts']['knowledge']
        path=self.run.root/ref['path'];k=load(path)
        k['scope']['exclusions'].append('External unaccepted change.');save_data(path,k)
        self.assertEqual(self.run.plan()['node_id'],'domain-decomposition')
        self.assertEqual(self.run.state['nodes']['scope-review']['status'],'STALE')

    def test_missing_skill_records_durable_failed_attempt(self):
        config=historical_pipeline();config['stages'][0]['skill']='not-installed-producer'
        self.run=Run.create(self.tmp.name,{'domain':'Missing producer'},run_id='unavailable',pipeline=config)
        with self.assertRaises(ValueError): self.run.start('domain-decomposition')
        plan=Run(self.run.root).plan()
        self.assertEqual(plan['action'],'FAILED')
        self.assertEqual(plan['error']['type'],'SkillUnavailable')

    def test_cycles_and_undeclared_inputs_rejected(self):
        config=historical_pipeline();config['stages'][2]['inputs']['everything']='documentation.documentation'
        self.assertTrue(pipeline_errors(config))
        config=historical_pipeline();config['stages'][0]['depends_on']=['documentation']
        self.assertTrue(pipeline_errors(config))
        config=historical_pipeline();config['stages'][1].update(type='skill',skill='osago-domain-decomposer',
            outputs={'domain-tree':'domain-tree'},primary='domain-tree')
        self.assertTrue(pipeline_errors(config))
        config=historical_pipeline()
        config['stages'][8]['depends_on'].remove('evidence-review')
        self.assertTrue(pipeline_errors(config))

    def test_revision_only_does_not_apply_human_correction(self):
        self.produce();self.run.plan()
        self.run.review('scope-review','CORRECT','Change the domain.',target='domain-decomposition')
        def bump(task,result):
            directory=Path(task['output_dir'])
            for name,path in result['artifacts'].items():
                data=load(directory/path)
                if name=='knowledge': data['revision']+=1
                else: data['package_ref']['revision']+=1
                save_data(directory/path,data)
            result['applied_review_ids']=[r['id'] for r in task['corrections']]
        accepted,_,_=self.producer.produce(self.run,mutate=bump)
        self.assertEqual(accepted['action'],'FAILED')

    def test_concurrent_session_cannot_overwrite_state(self):
        other=Run(self.run.root);self.run.plan()
        with self.assertRaises(StateChangedError): other.plan()

    def test_cli_domain_only_initialization(self):
        result=subprocess.run([sys.executable,str(Path(__file__).parents[1]/'orchestrate.py'),'init',
            '--domain','Synthetic minimal request','--runs-dir',self.tmp.name,'--run-id','cli-test'],capture_output=True,text=True,encoding='utf-8')
        self.assertEqual(result.returncode,0,result.stderr)
        task=json.loads(result.stdout)
        self.assertEqual(task['skill'],'osago-domain-decomposer')
        self.assertEqual(list(task['inputs']),['documentation-request'])


if __name__=='__main__': unittest.main()
