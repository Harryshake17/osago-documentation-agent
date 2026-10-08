"""Publication pipeline protocol after an accepted Link2 language-review boundary.

Prior extraction nodes are fixture doubles. Real plan/render, shared schemas and
Run checkpoint/resume/finish/invalidation execute; no sources or publication API.
Historical upstream integration is covered by test_orchestrate.py.
"""
import copy
from pathlib import Path
import shutil
import socket
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from confluence_render import make_plan, approve, render, write_bundle, snapshot_assets, sha, digest
from language_review import _base_report
from orchestrate import Run, DEFAULT_PIPELINE, binding, compile_nodes, pipeline_errors, save_data
from validate import load, schema_errors

HERE=Path(__file__).parent/'fixtures/confluence-render'
DRIVERS={'confluence_plan','presentation_review','confluence_render'}

class BoundaryRun(Run):
    def _reconcile(self):
        # Boundary fixture represents outputs already accepted by prior skills.
        upstream=[n for n in self.state['nodes'].values() if n['active'] and self.spec(n)['validator'] not in DRIVERS]
        for n in upstream: n['active']=False
        try: super()._reconcile()
        finally:
            for n in upstream: n['active']=True

class ConfluenceOrchestrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.run=BoundaryRun.create(self.tmp.name,{'domain':'Synthetic Link2 boundary'},run_id='renderer-test')
        self.document=(HERE/'link2-reviewed.md').read_bytes().decode('utf8')
        self.manifest=load(HERE/'documentation-manifest.json')
        report=_base_report(dict(draft_hash=self.manifest['document_hash'],glossary_hash='0'*64,
            scenario_hash='0'*64,validation_hash='0'*64,manifest_hash=digest(self.manifest)),
            dict.fromkeys(['terminology','writing-style','documentation-template','evidence-policy','knowledge-model'],'0'*64),
            {'claim_inventory':self.manifest['claim_ids']})
        report.update(final_hash=sha(self.document),publication_gate=self.manifest['publication_gate'],
                      blocks=copy.deepcopy(self.manifest['document']['blocks']))
        report['review']['status']='COMPLETED'
        self.assertEqual(schema_errors('language-review',report),[])
        self.report=report
        folder=self.run.root/'inputs'
        (folder/'09-final-document.md').write_bytes(self.document.encode('utf8'))
        save_data(folder/'manifest.yaml',self.manifest);save_data(folder/'09-language-review.yaml',report)
        doc=binding(self.run.root,folder/'09-final-document.md',None)
        manifest=binding(self.run.root,folder/'manifest.yaml','documentation-manifest')
        review=binding(self.run.root,folder/'09-language-review.yaml','language-review')
        self.run.state['work_items']=[dict(id='link2',scenario_id='scenario:fixture:link2',domain_id='domain:fixture',
            artifacts=dict.fromkeys(['knowledge','domain-tree','scenario-definition'],doc))]
        compile_nodes(self.run.state)
        for key,node in self.run.state['nodes'].items():
            if self.run.spec(node)['validator'] not in DRIVERS:
                node.update(status='COMPLETED',bundle=dict.fromkeys(self.run.spec(node)['outputs'],doc))
        self.run.state['nodes']['documentation@link2']['bundle'].update(
            {'documentation-manifest':manifest,'documentation-meta':manifest})
        self.run.state['nodes']['language-review@link2']['bundle'].update(
            {'final-document':doc,'language-review':review})
        self.run.persist()

    def reload(self): self.run=BoundaryRun(self.run.root)

    def plan_result(self,*,expand=False,preapproved=False):
        task=self.run.start(self.run.plan()['node_id']);folder=Path(task['output_dir'])
        for name in ['link2-flow.mmd','link2-flow.png']: shutil.copyfile(HERE/name,folder/name)
        metadata=snapshot_assets(load(HERE/'presentation-metadata.yaml'),folder)
        plan=make_plan(self.document,self.manifest,self.report,technical_expand=expand)
        save_data(folder/'presentation-plan.yaml',approve(plan) if preapproved else plan)
        save_data(folder/'presentation-metadata.yaml',metadata)
        result={'artifacts':{'presentation-plan':'presentation-plan.yaml','presentation-metadata':'presentation-metadata.yaml'}}
        if task['corrections']: result['applied_review_ids']=[r['id'] for r in task['corrections']]
        return task,result

    def prepare(self,**kwargs):
        task,result=self.plan_result(**kwargs)
        self.assertEqual(self.run.finish(task['node_id'],result)['action'],'ACCEPTED')
        action=self.run.plan()
        self.assertEqual(action['action'],'WAITING_FOR_USER');self.assertEqual(action['node_id'],'presentation-review@link2')
        return action

    def agree(self): self.run.review('presentation-review@link2','APPROVE','Preserve the reviewed hierarchy and order.')

    def render_result(self):
        task=self.run.start(self.run.plan()['node_id']);paths=task['inputs']
        body,metadata,assets=render(Path(paths['document']).read_bytes().decode('utf8'),load(paths['manifest']),
            approve(load(paths['presentation-plan'])),review=load(paths['language-review']),
            metadata=load(paths['presentation-metadata']),asset_root=Path(paths['presentation-metadata']).parent)
        write_bundle(task['output_dir'],body,metadata,assets)
        return task,{'artifacts':{'confluence-body':'10-confluence-body.storage.xhtml',
                               'publisher-metadata':'10-publisher-metadata.yaml'}}

    def finish_render(self):
        task,result=self.render_result()
        self.assertEqual(self.run.finish(task['node_id'],result)['action'],'ACCEPTED')
        return task,result

    def test_declarative_default_and_bounded_inputs(self):
        config=load(DEFAULT_PIPELINE)
        self.assertEqual(pipeline_errors(config),[])
        self.assertEqual([s['id'] for s in config['stages'][-3:]],
                         ['confluence-plan','presentation-review','confluence-render'])
        task=self.run.plan()
        self.assertEqual(task['skill'],'osago-confluence-renderer');self.assertEqual(task['presentation_mode'],'plan')
        self.assertEqual(set(task['inputs']),{'document','manifest','language-review'})

    def test_real_handoff_checkpoint_and_completed_outputs_no_network(self):
        with patch.object(socket,'socket',side_effect=AssertionError('no network')):
            action=self.prepare();self.agree();task,_=self.finish_render()
            self.assertEqual(task['presentation_mode'],'render')
            self.assertEqual(task['hierarchy_approval']['response'],'Preserve the reviewed hierarchy and order.')
            final=self.run.plan()
        self.assertEqual(final['action'],'COMPLETED')
        self.assertEqual(len(action['review']['headings']),15)
        outputs=final['results']['link2']
        self.assertTrue(outputs['confluence-body']['path'].endswith('.storage.xhtml'))
        self.assertEqual(outputs['documentation'],outputs['final-document'])
        meta=load(self.run.root/outputs['publisher-metadata']['path'])
        self.assertFalse(meta['publisher']['eligible']);self.assertEqual(meta['publisher']['publication_gate'],'blocked')

    def test_checkpoint_blocks_start_and_persists_reload(self):
        first=self.prepare();self.reload()
        self.assertEqual(self.run.plan(),first)
        with self.assertRaises(ValueError): self.run.start('confluence-render@link2')
        self.assertEqual(len(self.run.state['reviews']),0)

    def test_preapproved_skill_plan_rejected(self):
        task,result=self.plan_result(preapproved=True)
        self.assertEqual(self.run.finish(task['node_id'],result)['action'],'FAILED')
        self.assertEqual(self.run.state['nodes']['language-review@link2']['status'],'COMPLETED')

    def test_forged_checkpoint_without_event_rejected(self):
        self.prepare();node=self.run.state['nodes']['presentation-review@link2']
        node.update(status='COMPLETED',approval_id='review:invented');self.run.persist()
        self.assertEqual(self.run.plan()['action'],'WAITING_FOR_USER')

    def test_approval_event_must_belong_to_current_checkpoint(self):
        self.prepare();self.agree()
        self.run.state['reviews'][-1]['node_id']='scope-review';self.run.persist()
        self.assertEqual(self.run.plan()['action'],'WAITING_FOR_USER')

    def test_running_render_resumes_same_mode_approval_and_directory(self):
        self.prepare();self.agree();task,_=self.render_result();self.reload()
        pending=self.run.plan()
        self.assertEqual(pending['action'],'RUNNING')
        for name in ['presentation_mode','hierarchy_approval','output_dir','attempt']:
            self.assertEqual(pending[name],task[name])

    def test_failed_renderer_retry_preserves_composer_and_language_review(self):
        self.prepare();self.agree();task,result=self.render_result()
        folder=Path(task['output_dir']);(folder/result['artifacts']['confluence-body']).write_text('# flat Markdown',encoding='utf8')
        self.assertEqual(self.run.finish(task['node_id'],result)['action'],'FAILED')
        for key in ['documentation@link2','language-review@link2']:
            self.assertEqual(self.run.state['nodes'][key]['status'],'COMPLETED')
        self.assertEqual(self.run.plan()['action'],'FAILED')
        self.reload();self.run.retry(task['node_id'])
        self.assertEqual(self.run.plan()['node_id'],task['node_id'])
        retried,_=self.finish_render();self.assertEqual(retried['attempt'],2)
        self.assertEqual(self.run.plan()['action'],'COMPLETED')

    def test_self_reported_metadata_cannot_promote_gate(self):
        self.prepare();self.agree();task,result=self.render_result()
        path=Path(task['output_dir'])/result['artifacts']['publisher-metadata'];meta=load(path)
        meta['publisher'].update(publication_gate='ready',eligible=True);save_data(path,meta)
        self.assertEqual(self.run.finish(task['node_id'],result)['action'],'FAILED')

    def test_accepted_attachment_tamper_invalidates_render_even_in_cache(self):
        self.prepare();self.agree();task,_=self.finish_render();self.run.plan()
        folder=Path(task['output_dir']);meta=load(folder/'10-publisher-metadata.yaml')
        (folder/meta['attachments'][0]['bundle_path']).write_bytes(b'tampered')
        self.assertEqual(self.run.plan()['node_id'],'confluence-render@link2')
        self.assertEqual(self.run.state['nodes']['presentation-review@link2']['status'],'COMPLETED')

    def test_selected_diagram_drift_invalidates_approval_and_render(self):
        self.prepare();self.agree();self.finish_render();self.run.plan()
        ref=self.run.state['nodes']['confluence-plan@link2']['bundle']['presentation-metadata']
        (self.run.root/ref['path']).parent.joinpath('link2-flow.mmd').write_text('graph TD; A-->Changed',encoding='utf8')
        self.assertEqual(self.run.plan()['node_id'],'confluence-plan@link2')
        for name in ['presentation-review','confluence-render']:
            self.assertEqual(self.run.state['nodes'][name+'@link2']['status'],'STALE')
        self.assertEqual(self.run.state['reviews'][-1]['status'],'STALE')

    def test_human_presentation_correction_delegates_to_plan(self):
        self.prepare()
        self.run.review('presentation-review@link2','CORRECT','Use technical expand.',target='confluence-plan@link2')
        self.assertEqual(self.run.plan()['node_id'],'confluence-plan@link2')
        action=self.prepare(expand=True)
        self.assertTrue(action['review']['technical_expand'])
        self.assertEqual(self.run.state['reviews'][-1]['status'],'APPLIED')
        self.agree();self.finish_render();self.assertEqual(self.run.plan()['action'],'COMPLETED')

    def test_rerun_language_review_invalidates_only_downstream_presentation(self):
        self.prepare();self.agree();self.finish_render();self.run.plan()
        self.run.rerun_from('language-review@link2')
        self.assertEqual(self.run.state['nodes']['documentation@link2']['status'],'COMPLETED')
        for name in ['confluence-plan','presentation-review','confluence-render']:
            self.assertEqual(self.run.state['nodes'][name+'@link2']['status'],'STALE')
        self.assertEqual(self.run.state['reviews'][-1]['status'],'STALE')

    def test_completed_resume_does_not_add_attempts(self):
        self.prepare();self.agree();self.finish_render();first=self.run.plan()
        attempts=copy.deepcopy({k:n['attempts'] for k,n in self.run.state['nodes'].items()})
        self.reload();self.assertEqual(self.run.plan(),first)
        self.assertEqual({k:n['attempts'] for k,n in self.run.state['nodes'].items()},attempts)

    def test_multiple_scenarios_have_independent_presentation_approvals(self):
        second=copy.deepcopy(self.run.state['work_items'][0]);second['id']='second'
        second['scenario_id']='scenario:fixture:second';self.run.state['work_items'].append(second)
        compile_nodes(self.run.state)
        for key,node in self.run.state['nodes'].items():
            if node['item_id']=='second' and self.run.spec(node)['validator'] not in DRIVERS:
                prior=self.run.state['nodes'][node['spec_id']+'@link2']
                node.update(status='COMPLETED',bundle=copy.deepcopy(prior['bundle']))
        self.run.persist()
        self.prepare();self.agree();self.finish_render()
        self.assertEqual(self.run.plan()['node_id'],'confluence-plan@second')
        task,result=self.plan_result()
        self.assertEqual(self.run.finish(task['node_id'],result)['action'],'ACCEPTED')
        self.assertEqual(self.run.plan()['node_id'],'presentation-review@second')
        self.run.review('presentation-review@second','APPROVE','Approve the second document hierarchy.')
        task,_=self.finish_render()
        self.assertEqual(task['hierarchy_approval']['node_id'],'presentation-review@second')
        final=self.run.plan();self.assertEqual(final['action'],'COMPLETED')
        self.assertEqual(set(final['results']),{'link2','second'})
        self.assertEqual(len(self.run.state['reviews']),2)

    def test_cli_plan_produces_shared_empty_metadata_sidecar(self):
        from confluence_render import main
        output=self.run.root/'cli-plan'
        args=['confluence_render.py','plan','--document',str(HERE/'link2-reviewed.md'),
              '--manifest',str(HERE/'documentation-manifest.json'),'--plan',str(output/'plan.yaml'),
              '--output-dir',str(output),'--asset-root',str(output)]
        with patch.object(sys,'argv',args): self.assertEqual(main(),0)
        metadata=load(output/'presentation-metadata.yaml')
        self.assertEqual(metadata,{'asset_hashes':{}})
        self.assertEqual(schema_errors('confluence-presentation-plan',load(output/'plan.yaml')),[])

    def test_lost_approval_event_cannot_be_hidden_by_cached_render_validation(self):
        self.prepare();self.agree();self.finish_render();self.run.plan()
        self.run.state['reviews'][-1]['input_fingerprints']['presentation-plan']='0'*64
        self.run.persist()
        self.assertEqual(self.run.plan()['node_id'],'presentation-review@link2')
        self.assertEqual(self.run.state['nodes']['confluence-render@link2']['status'],'STALE')

    def test_asset_escape_is_rejected_before_finish(self):
        task,_=self.plan_result();folder=Path(task['output_dir'])
        metadata=load(HERE/'presentation-metadata.yaml');metadata['diagrams']['link2-flow.mmd']['source_file']='../outside.mmd'
        with self.assertRaises(ValueError): snapshot_assets(metadata,folder)

    def test_renderer_without_checkpoint_or_with_research_input_rejected(self):
        config=load(DEFAULT_PIPELINE)
        config['stages'][-1]['depends_on'].remove('presentation-review')
        self.assertTrue(pipeline_errors(config))
        config=load(DEFAULT_PIPELINE);config['stages'][-1]['inputs']['source-map']='source-discovery.source-map'
        self.assertTrue(pipeline_errors(config))
        config=load(DEFAULT_PIPELINE);config['stages'][-1]['inputs'].pop('presentation-plan')
        self.assertTrue(pipeline_errors(config))

if __name__=='__main__': unittest.main()
