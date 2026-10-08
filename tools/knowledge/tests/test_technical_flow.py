"""Execution-path contracts on synthetic sources; no OSAGO facts."""
import copy
import unittest
import json
from pathlib import Path
import tempfile
import sys
from test_business_rules import rule_fixture
from validate import validate, schema_errors
from technical_flow import build_flow


def execution_fixture():
    k, tree, definition, source_map, flow, _ = rule_fixture()
    flow['analysis_profile'] = 'execution-path-v1'
    fields = ('inputs', 'outputs', 'conditions', 'calls', 'state_changes',
              'configuration_reads', 'checks', 'external_calls', 'async_events')
    node = dict(flow['nodes'][0], type='rule', symbol='FixtureHandler.Handle',
                purpose='Return a value after checking fixture accuracy.',
                evidence=['evidence:fixture'], attribute_claims={}, unknown_fields=[],
                not_applicable_fields=[], gap_ids=[])
    for field in fields:
        node[field] = []
    node.update(inputs=['command', 'accuracy'], outputs=['0 or 1'], conditions=['accuracy < 7'], checks=['accuracy < 7'])
    # Uninspected dimensions are unknown, never synthetic proof of absence.
    node['unknown_fields'] = [f for f in fields if not node[f]]
    node['gap_ids'] = ['gap:technical']
    k['gaps'].append(dict(id='gap:technical', reason='unknown_field', question='Which other technical effects exist?',
                          affected_ids=[node['id']], next_action='Inspect remaining technical dimensions.', status='open'))
    flow['gap_ids'] = node['gap_ids'][:]
    flow['coverage'] = dict(status='partial', limitations=['Uninspected technical dimensions.'], frontier=[])
    def add(field, value, key):
        c = copy.deepcopy(k['claims'][0])
        cid = 'claim:technical:' + key
        c.update(id=cid, subject_id=node['id'], predicate=field, value=value, text='Synthetic technical observation.')
        k['claims'].append(c)
        node['attribute_claims'][key] = [cid]
        node['claim_ids'].append(cid)
    for field in ('type', 'symbol', 'purpose'):
        add(field, node[field], field)
    for field in fields:
        for i, value in enumerate(node[field]):
            add(field, value, f'{field}/{i}')
    flow=build_flow({key:value for key,value in flow.items() if key not in {'nodes','relations'}},[node],flow['relations'])
    return k, tree, definition, source_map, flow


class TechnicalFlowTests(unittest.TestCase):
    def setUp(self):
        self.k, self.t, self.d, self.m, self.f = execution_fixture()
        self.n = self.f['nodes'][0]

    def errors(self):
        return validate('technical-flow', self.f, self.k, self.t, self.d, source_map=self.m)

    def test_partial_execution_valid(self):
        self.assertEqual(self.errors(), [])

    def test_profile_requires_nodes(self):
        del self.f['nodes']
        self.assertTrue(self.errors())

    def test_duplicate_steps_projection_is_rejected(self):
        self.f['steps']=[copy.deepcopy(self.n)]
        self.assertTrue(schema_errors('technical-flow',self.f))
        self.assertTrue(self.errors())

    def test_unknown_requires_gap(self):
        self.n['gap_ids'] = []
        self.assertTrue(self.errors())

    def test_unknown_disallows_complete(self):
        self.f['coverage']['status'] = 'complete'
        self.assertTrue(self.errors())

    def test_name_does_not_prove_purpose(self):
        self.n['purpose'] = 'Reduce insurance risk.'
        self.assertTrue(self.errors())

    def test_known_field_needs_matching_claim(self):
        self.n['conditions'] = ['accuracy < 9']
        self.assertTrue(self.errors())

    def test_call_without_directional_relation(self):
        self.n['calls'] = ['technical-step:guard']
        self.n['unknown_fields'].remove('calls')
        c = copy.deepcopy(self.k['claims'][0])
        c.update(id='claim:technical:call', subject_id=self.n['id'], predicate='calls', value=self.n['id'])
        self.k['claims'].append(c)
        self.n['attribute_claims']['calls/0'] = [c['id']]
        self.n['claim_ids'].append(c['id'])
        self.assertTrue(any('directed' in e for e in self.errors()))

    def test_evidence_omission(self):
        self.n['evidence'] = ['evidence:missing']
        self.assertTrue(self.errors())

    def test_not_applicable_requires_claim(self):
        self.n['unknown_fields'].remove('calls')
        self.n['not_applicable_fields'] = ['calls']
        self.assertTrue(self.errors())

    def test_namespace_rejects_scenario_style_technical_id(self):
        for identifier in ('step:flow:guard','scenario-step:guard'):
            with self.subTest(identifier=identifier):
                self.n['id']=identifier
                self.assertTrue(schema_errors('technical-flow',self.f))

    def test_scenario_step_entity_cannot_be_a_technical_node(self):
        entity=next(e for e in self.k['entities'] if e['id']==self.n['id'])
        entity['type']='ScenarioStep'
        self.assertTrue(any('SystemBehaviour' in error for error in self.errors()))

    def test_technical_relations_cannot_reference_scenario_steps(self):
        sid='scenario-step:fixture'
        self.k['entities'].append(dict(id=sid,type='ScenarioStep',label='Synthetic business step'))
        claim=copy.deepcopy(self.k['claims'][0])
        claim.update(id='claim:scenario-edge',subject_id=self.n['id'],predicate='calls',value=sid)
        self.k['claims'].append(claim)
        self.f['relations']=[dict(id='relation:scenario-edge',from_id=self.n['id'],to_id=sid,
                                 relation_type='calls',claim_ids=[claim['id']])]
        self.assertTrue(any('ScenarioStep relations' in error for error in self.errors()))

    def test_technical_node_requires_no_actor(self):
        self.assertNotIn('actor',self.n)
        self.assertNotIn('actor',self.n['unknown_fields'])
        self.assertEqual(self.errors(),[])
        self.n['actor']='actor:fixture'
        self.assertTrue(schema_errors('technical-flow',self.f))

    def test_generator_preserves_claim_evidence_and_source_provenance(self):
        before=copy.deepcopy(self.f)
        metadata={k:v for k,v in self.f.items() if k not in {'nodes','relations'}}
        result=build_flow(metadata,self.f['nodes'],self.f['relations'])
        self.assertEqual(result,before)
        self.assertNotIn('steps',result)
        self.assertEqual(result['nodes'][0]['claim_ids'],before['nodes'][0]['claim_ids'])
        self.assertEqual(self.f,before)
        result['nodes'][0]['source_ids'].append('source:new')
        self.assertEqual(self.f,before)

    def test_generator_rejects_second_projection_and_duplicate_node_ids(self):
        metadata={k:v for k,v in self.f.items() if k not in {'nodes','relations'}}
        with self.assertRaises(ValueError):
            build_flow(dict(metadata,steps=[copy.deepcopy(self.n)]),self.f['nodes'],self.f['relations'])
        duplicate=copy.deepcopy(self.n);duplicate['purpose']='Another technical operation'
        with self.assertRaisesRegex(ValueError,'duplicate'):
            build_flow(metadata,[self.n,duplicate],self.f['relations'])

    def test_node_claim_inventory_cannot_omit_field_claim(self):
        self.n['claim_ids'].remove(self.n['attribute_claims']['purpose'][0])
        self.assertTrue(any('canonical claim_ids' in error for error in self.errors()))

    def test_canonical_relations_retain_directional_claims(self):
        target=copy.deepcopy(self.n);target_id='technical-step:target'
        target['id']=target_id
        self.k['entities'].append(dict(id=target_id,type='SystemBehaviour',label='Synthetic target'))
        replacements={}
        for claim in list(self.k['claims']):
            if claim['subject_id']!=self.n['id']: continue
            copied=copy.deepcopy(claim);copied['id']=claim['id']+':target';copied['subject_id']=target_id
            self.k['claims'].append(copied);replacements[claim['id']]=copied['id']
        target['claim_ids']=[replacements[c] for c in target['claim_ids']]
        target['attribute_claims']={key:[replacements[c] for c in cs] for key,cs in target['attribute_claims'].items()}
        next(g for g in self.k['gaps'] if g['id']=='gap:technical')['affected_ids'].append(target_id)
        self.f['nodes'].append(target)
        self.n['calls']=[target_id];self.n['unknown_fields'].remove('calls')
        claim=copy.deepcopy(self.k['claims'][0]);claim.update(id='claim:directed-call',subject_id=self.n['id'],predicate='calls',value=target_id)
        self.k['claims'].append(claim);self.n['claim_ids'].append(claim['id'])
        self.n['attribute_claims']['calls/0']=[claim['id']]
        self.f['relations']=[dict(id='relation:directed-call',from_id=self.n['id'],to_id=target_id,
                                 relation_type='calls',claim_ids=[claim['id']])]
        self.assertEqual(self.errors(),[])
        self.f['relations'][0]['from_id'],self.f['relations'][0]['to_id']=target_id,self.n['id']
        self.assertTrue(self.errors())

    def test_cli_writer_validates_before_creating_output(self):
        from technical_flow import main
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            data={'prepared.json':self.f,'knowledge.json':self.k,'tree.json':self.t,
                  'definition.json':self.d,'source-map.json':self.m}
            for filename,artifact in data.items(): (root/filename).write_text(json.dumps(artifact),encoding='utf8')
            args=['technical_flow.py','--input',str(root/'prepared.json'),'--knowledge',str(root/'knowledge.json'),
                  '--domain-tree',str(root/'tree.json'),'--scenario-definition',str(root/'definition.json'),
                  '--source-map',str(root/'source-map.json'),'--output',str(root/'03-technical-flow.json')]
            with patch.object(sys,'argv',args),patch('socket.socket',side_effect=AssertionError('no sources')):
                self.assertEqual(main(),0)
                self.assertEqual(json.loads((root/'03-technical-flow.json').read_text()),self.f)
                self.assertEqual(main(),1) # immutable output requires explicit overwrite
                args[-1]=str(root/'rejected.json')
                data['prepared.json']['steps']=[copy.deepcopy(self.n)]
                (root/'prepared.json').write_text(json.dumps(data['prepared.json']),encoding='utf8')
                self.assertEqual(main(),1)
                self.assertFalse((root/'rejected.json').exists())

    def test_compact_nodes_input_still_valid(self):
        k, t, d, m, f, _ = rule_fixture()
        self.assertEqual(validate('technical-flow', f, k, t, d, source_map=m), [])


if __name__ == '__main__':
    unittest.main()
