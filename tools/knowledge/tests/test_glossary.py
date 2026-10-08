"""Glossary contracts on synthetic sources; no OSAGO business assertions."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from audit import calculate_summary, check_report, draft, digest
from glossary import curate, empty_glossary, glossary_errors, lookup, merge, validation_errors
from test_audit import mark_reviewed
from test_model import profile_fixture, sync_evidence, unknown
from validate import load, schema_errors

DOMAIN='domain:glossary-fixture'
FIXTURES=Path(__file__).parent/'fixtures/glossary'


def glossary_fixture(case='confirmed'):
    k,t,d,m,f,r,s=profile_fixture()
    k['package_id']='kb:glossary:'+case
    for artifact in (t,d,m,f,r,s):
        artifact['package_ref']['id']=k['package_id']
    k['entities'].append(dict(id=DOMAIN,type='Domain',label='Synthetic glossary test domain',identity_key=DOMAIN,
                             preferred_name=unknown(),technical_aliases=[],search_aliases=[],terminology_candidates=[]))
    template=copy.deepcopy(k['claims'][0])
    def source(key,text,typ):
        snap=copy.deepcopy(k['sources'][0])
        snap.update(id='snapshot:glossary:'+key,adapter='confluence' if typ=='CONFLUENCE' else 'repository',
                    locator='fixture:'+key,repository=None if typ=='CONFLUENCE' else 'fixture',revision='fixture:'+key,
                    content_hash=hashlib.sha256(text.encode()).hexdigest(),excerpt=text)
        e=copy.deepcopy(k['evidence'][0])
        e.update(id='evidence:glossary:'+key,source_type=typ,snapshot_id=snap['id'],source_ref=snap['id'],
                 source_location=snap['locator'],repository=snap['repository'],file='fixtures/'+key+'.cs' if typ=='CODE' else None,
                 page=key if typ=='CONFLUENCE' else None,section='Glossary' if typ=='CONFLUENCE' else None,
                 version=snap['revision'],excerpt=text,**{'class':None,'method':None})
        k['sources'].append(snap);k['evidence'].append(e)
        return e['id']
    def claim(eid,subject,predicate,value):
        c=copy.deepcopy(template)
        cid='claim:glossary:'+case+':'+str(len(k['claims']))
        c.update(id=cid,subject_id=subject,predicate=predicate,value=value,text=f'Synthetic {predicate}: {value}',
                 modality='source_statement',support=[dict(evidence_id=eid,role='supports')])
        c['context']['revision']=next(e['version'] for e in k['evidence'] if e['id']==eid)
        k['claims'].append(c)
        return cid
    def concept(key,alias,name,definition,code_type='Integration'):
        eid='integration:glossary:'+key
        code=source(key+'-code',f'// Synthetic alias mapping: {alias} denotes {eid}.', 'CODE')
        ent=dict(id=eid,type=code_type,label=alias,identity_key='fixture:concept:'+key,preferred_name=unknown(),
                 technical_aliases=[alias],search_aliases=[],terminology_candidates=[])
        k['entities'].append(ent)
        claim(code,eid,'technical_aliases',alias)
        if code_type=='CodeComponent':
            ent['terminology_candidates']=[dict(value=alias,entity_ref=eid,source_type='CODE',source_ref='snapshot:glossary:'+key+'-code',evidence_ids=[code])]
        if name:
            doc=source(key+'-doc',f'Synthetic glossary: {alias} means {name}. Definition: {definition or "not supplied"}.','CONFLUENCE')
            claim(doc,eid,'preferred_name',name)
            if definition:
                claim(doc,eid,'definition',definition)
        return ent
    if case=='unknown':
        concept('eligibility','SomeEligibilityInvoker',None,None,'CodeComponent')
    elif case=='existing':
        concept('nsis','NSIS','НСИС','Синтетическое определение НСИС для теста.')
    elif case=='similar':
        concept('scoring','SAS','скоринг','Синтетическое понятие A.')
        concept('other','EligibilityCheck','скоринговая проверка','Синтетическое понятие B.')
    else:
        ent=concept('scoring','SAS','скоринг','Синтетическая проверка данных для теста.')
        if case=='conflict':
            doc2=source('scoring-second-doc','Synthetic competing terminology: SAS means проверка риска.','CONFLUENCE')
            b=claim(doc2,ent['id'],'preferred_name','проверка риска')
            a=next(c['id'] for c in k['claims'] if c['subject_id']==ent['id'] and c['predicate']=='preferred_name')
            for c in k['claims']:
                if c['id'] in (a,b):
                    c['knowledge_status']='CONFLICT'
            k['conflicts'].append(dict(id='conflict:glossary:scoring',claim_ids=[a,b],disagreement='Synthetic name conflict',status='unresolved',resolution_claim_id=None))
            k['gaps'].append(dict(id='gap:glossary:scoring',reason='unverified',question='Which business term is appropriate?',
                                 affected_ids=[ent['id']],next_action='Analyst review of both documents.',status='open'))
    sync_evidence(k)
    audit_inputs={'knowledge':k,'domain-tree':t,'scenario-definition':d,'source-map':m,'technical-flow':f,'business-rules':r,'scenario':s}
    report,gaps=draft(audit_inputs)
    for c in k['claims']:
        if c['knowledge_status']!='CONFLICT':
            mark_reviewed(audit_inputs,report,c['id'])
    report['summary']=calculate_summary(report,gaps)
    inputs={'knowledge':k,'scenario':s,'validation':report}
    current=empty_glossary()
    if case=='existing':
        _,current=curate(current,inputs,DOMAIN)
        next(t for t in current['terms'] if t['entity_ref']=='integration:glossary:nsis')['id']='TERM-NSIS'
    return current,inputs,audit_inputs,gaps


class GlossaryTests(unittest.TestCase):
    def fixture(self,case='confirmed'):
        current,inputs,_,_=glossary_fixture(case)
        return current,inputs

    def term(self,glossary):
        return next(t for t in glossary['terms'] if t['entity_ref'].startswith('integration:glossary:'))

    def test_01_confirmed_mapping(self):
        base,inputs=self.fixture()
        inc,result=curate(base,inputs,DOMAIN)
        term=self.term(result)
        self.assertEqual(term['preferred_name']['value'],'скоринг')
        self.assertEqual(term['preferred_name']['status'],'CONFIRMED')
        self.assertEqual(term['technical_aliases'],['SAS'])
        self.assertEqual(term['status'],'CONFIRMED')
        self.assertEqual(merge(base,inc),result)
        self.assertEqual(glossary_errors(result),[])

    def test_02_code_only_remains_UNKNOWN(self):
        base,inputs=self.fixture('unknown')
        _,result=curate(base,inputs,DOMAIN)
        term=self.term(result)
        self.assertIsNone(term['preferred_name']['value'])
        self.assertEqual(term['preferred_name']['status'],'UNKNOWN')
        self.assertEqual(term['status'],'UNKNOWN')
        self.assertEqual(term['technical_aliases'],['SomeEligibilityInvoker'])
        self.assertTrue(result['unresolved'])
        self.assertNotIn('Проверка права',json.dumps(result,ensure_ascii=False))

    def test_03_existing_term_keeps_ID(self):
        base,inputs=self.fixture('existing')
        inc,result=curate(base,inputs,DOMAIN)
        self.assertEqual(self.term(result)['id'],'TERM-NSIS')
        self.assertEqual(inc['added'],[])
        self.assertEqual(inc['unchanged'],[{'term_id':'TERM-NSIS'}])
        self.assertEqual(result,base)

    def test_04_conflict_requires_review(self):
        base,inputs=self.fixture('conflict')
        inc,result=curate(base,inputs,DOMAIN)
        self.assertEqual(self.term(result)['status'],'CONFLICT')
        self.assertEqual(result['conflicts'][0]['required_action'],'ANALYST_REVIEW')
        self.assertEqual(set(result['conflicts'][0]['variants']),{'скоринг','проверка риска'})
        self.assertEqual(merge(base,inc),result)

    def test_05_similar_entities_are_not_merged(self):
        base,inputs=self.fixture('similar')
        _,result=curate(base,inputs,DOMAIN)
        self.assertEqual(len(result['terms']),2)
        self.assertEqual(len({t['entity_ref'] for t in result['terms']}),2)
        self.assertEqual(result['conflicts'],[])

    def test_invariants_INPUTS_unchanged(self):
        base,inputs=self.fixture()
        before=copy.deepcopy((base,inputs))
        curate(base,inputs,DOMAIN)
        self.assertEqual((base,inputs),before)

    def test_repeated_curation_and_merge_are_idempotent(self):
        base,inputs=self.fixture()
        inc,result=curate(base,inputs,DOMAIN)
        again,repeated=curate(result,inputs,DOMAIN)
        self.assertEqual(repeated,result)
        self.assertEqual(again['added'],[])
        self.assertEqual(again['updated'],[])
        self.assertEqual(merge(result,inc),result)
        self.assertEqual(curate(base,inputs,DOMAIN),(inc,result))

    def test_lookup_in_both_directions(self):
        base,inputs=self.fixture()
        _,result=curate(base,inputs,DOMAIN)
        self.assertEqual(lookup(result,'SAS')[0]['id'],lookup(result,'скоринг')[0]['id'])

    def test_unselected_methods_are_not_catalogued(self):
        base,inputs=self.fixture()
        _,result=curate(base,inputs,DOMAIN)
        self.assertFalse(any(t['entity_ref'] in {'FixtureCommand','FixtureHandler.Handle'} for t in result['terms']))

    def test_existing_aliases_survive_merge(self):
        base,inputs=self.fixture('existing')
        k=inputs['knowledge']
        c=copy.deepcopy(next(c for c in k['claims'] if c['predicate']=='technical_aliases'))
        c.update(id='claim:glossary:extra-alias',value='RegisterPolicyContractNSIS')
        evidence=copy.deepcopy(next(e for e in k['evidence'] if e['id']==c['support'][0]['evidence_id']))
        snapshot=copy.deepcopy(next(s for s in k['sources'] if s['id']==evidence['snapshot_id']))
        text='// Synthetic additional alias: RegisterPolicyContractNSIS denotes integration:glossary:nsis.'
        snapshot.update(id='snapshot:extra-alias',locator='fixtures/extra-alias.cs',excerpt=text,
                        content_hash=hashlib.sha256(text.encode()).hexdigest())
        evidence.update(id='evidence:extra-alias',snapshot_id=snapshot['id'],source_ref=snapshot['id'],
                        source_location=snapshot['locator'],file='fixtures/extra-alias.cs',excerpt=text)
        k['sources'].append(snapshot);k['evidence'].append(evidence)
        c['support']=[dict(evidence_id=evidence['id'],role='supports')]
        eid=c['subject_id']
        next(e for e in k['entities'] if e['id']==eid)['technical_aliases'].append(c['value'])
        k['claims'].append(c)
        k['revision']+=1
        self.revalidate(inputs)
        inc,result=curate(base,inputs,DOMAIN)
        self.assertEqual(self.term(merge(base,inc))['technical_aliases'],['NSIS','RegisterPolicyContractNSIS'])
        self.assertEqual(self.term(result)['id'],'TERM-NSIS')

    def revalidate(self,inputs,alter=None):
        # New terminology snapshot is reviewed independently in synthetic fixtures.
        sync_evidence(inputs['knowledge'])
        _,_,upstream,gaps=glossary_fixture()
        upstream['knowledge']=inputs['knowledge'];upstream['scenario']=inputs['scenario']
        for kind,artifact in upstream.items():
            if kind!='knowledge':
                artifact['package_ref']=dict(id=inputs['knowledge']['package_id'],revision=inputs['knowledge']['revision'])
        report,gaps=draft(upstream)
        for c in inputs['knowledge']['claims']:
            if c['knowledge_status']!='CONFLICT':
                row=mark_reviewed(upstream,report,c['id'],status=c['knowledge_status'])
                if c['knowledge_status']=='PARTIALLY_CONFIRMED':
                    row.update(supported_parts=['Term spelling'],unsupported_parts=['Domain applicability'],required_action='add_evidence')
        if alter:
            alter(report,gaps)
        report['summary']=calculate_summary(report,gaps)
        inputs['validation']=report

    def test_stale_report_and_claim_hash_fail(self):
        base,inputs=self.fixture()
        inputs['knowledge']['entities'][-1]['label']='Changed'
        with self.assertRaisesRegex(ValueError,'stale'):
            curate(base,inputs,DOMAIN)

    def test_missing_definition_evidence_cannot_confirm(self):
        base,inputs=self.fixture()
        c=next(c for c in inputs['knowledge']['claims'] if c['predicate']=='definition')
        c['support']=[]
        self.revalidate(inputs)
        with self.assertRaisesRegex(ValueError,'direct inspected'):
            curate(base,inputs,DOMAIN)

    def test_fabricated_source_quote_is_rejected(self):
        base,inputs=self.fixture()
        review=next(r for r in inputs['validation']['claim_reviews'] if r['claim_id'].startswith('claim:glossary:'))
        review['source_checks'][0]['quote']='Invented quotation'
        with self.assertRaisesRegex(ValueError,'quote does not occur'):
            curate(base,inputs,DOMAIN)

    def test_draft_validation_does_not_promote_producer_status(self):
        base,inputs,audit_inputs,gaps=glossary_fixture()
        report,gaps=draft(audit_inputs)
        inputs['validation']=report
        # Keep only the alias verified; business claims remain unreviewed UNKNOWN.
        alias=next(c['id'] for c in inputs['knowledge']['claims'] if c['predicate']=='technical_aliases')
        mark_reviewed(audit_inputs,report,alias)
        report['summary']=calculate_summary(report,gaps)
        _,result=curate(base,inputs,DOMAIN)
        self.assertEqual(self.term(result)['preferred_name']['status'],'UNKNOWN')

    def test_code_name_is_not_domain_name_even_when_reviewed(self):
        base,inputs=self.fixture()
        k=inputs['knowledge']
        c=next(c for c in k['claims'] if c['predicate']=='preferred_name' and c['id'].startswith('claim:glossary:'))
        code=next(c for c in k['claims'] if c['predicate']=='technical_aliases')
        c['support']=copy.deepcopy(code['support'])
        self.revalidate(inputs)
        _,result=curate(base,inputs,DOMAIN)
        self.assertEqual(self.term(result)['preferred_name']['status'],'UNKNOWN')

    def test_glossary_needs_mapping_evidence(self):
        base,inputs=self.fixture()
        _,result=curate(base,inputs,DOMAIN)
        result['terms'][0]['attribute_claims']['technical_aliases/0']=[]
        self.assertTrue(glossary_errors(result))

    def test_fuzzy_name_never_retargets_stable_entity(self):
        base,inputs=self.fixture('similar')
        _,result=curate(base,inputs,DOMAIN)
        self.assertNotEqual(result['terms'][0]['id'],result['terms'][1]['id'])

    def test_merge_detects_stale_base(self):
        base,inputs=self.fixture()
        inc,_=curate(base,inputs,DOMAIN)
        base['revision']+=1
        with self.assertRaisesRegex(ValueError,'stale base'):
            merge(base,inc)

    def test_merge_preserves_unrelated_global_terms(self):
        base,first=self.fixture('confirmed')
        _,scoring=curate(base,first,DOMAIN)
        _,other=self.fixture('existing')
        # Scoped packages must retain immutable identities when extending the global glossary.
        inc,result=curate(scoring,other,DOMAIN)
        self.assertEqual(len(result['terms']),2)
        self.assertEqual(merge(scoring,inc),result)
        self.assertIn(self.term(scoring),result['terms'])

    def test_merge_rejects_confirmed_replacement(self):
        base,inputs=self.fixture('existing')
        inc,result=curate(base,inputs,DOMAIN)
        inc['updated']=[dict(term_id='TERM-NSIS',changes={'preferred_name':unknown()})]
        inc['unchanged']=[]
        inc['statistics'].update(updated=1,unchanged=0)
        inc['result_hash']='0'*64
        with self.assertRaisesRegex(ValueError,'approved field'):
            merge(base,inc)

    def test_merge_rejects_alias_loss(self):
        base,inputs=self.fixture('existing')
        inc,_=curate(base,inputs,DOMAIN)
        inc['updated']=[dict(term_id='TERM-NSIS',changes={'technical_aliases':[]})]
        inc['unchanged']=[];inc['result_hash']='0'*64
        inc['statistics'].update(updated=1,unchanged=0)
        with self.assertRaisesRegex(ValueError,'cannot be lost'):
            merge(base,inc)

    def test_artificial_search_alias_is_rejected(self):
        base,inputs=self.fixture()
        _,result=curate(base,inputs,DOMAIN)
        term=self.term(result)
        term['search_aliases'].append('проверка права на оформление')
        term['search_alias_origins'].append(dict(value='проверка права на оформление',origin='technical_alias',entity_ref=term['entity_ref']))
        self.assertTrue(any('artificial' in e for e in glossary_errors(result)))

    def test_fixture_files_satisfy_contracts_and_merge(self):
        self.assertEqual(len(list(FIXTURES.glob('*/inputs.json'))),5)
        for path in FIXTURES.glob('*/inputs.json'):
            with self.subTest(fixture=path.parent.name):
                data=load(path)
                inc,result=curate(data['current'],data['inputs'],DOMAIN)
                self.assertEqual(merge(data['current'],inc),result)
                self.assertEqual(inc,load(path.parent/'07-glossary-increment.yaml'))
                self.assertEqual(result,load(path.parent/'glossary.yaml'))

    def test_cli_curate_lookup_and_check(self):
        path=FIXTURES/'confirmed'
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)
            data=load(path/'inputs.json')
            args=[]
            for key,obj in dict(data['inputs'],glossary=data['current']).items():
                p=target/(key+'.json');p.write_text(json.dumps(obj,ensure_ascii=False),encoding='utf-8')
                args += ['--'+key,str(p)]
            command=[sys.executable,'-X','utf8',str(Path(__file__).parents[1]/'glossary.py')]
            before={p.name:p.read_bytes() for p in target.glob('*.json')}
            result=subprocess.run(command+['curate']+args+['--domain-id',DOMAIN,'--output-dir',str(target)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertEqual(before,{p.name:p.read_bytes() for p in target.glob('*.json')})
            for mode,extra in [('check',['--increment',str(target/'07-glossary-increment.yaml')]),('lookup',['--term','SAS'])]:
                result=subprocess.run(command+[mode,'--glossary',str(target/'glossary.yaml')]+extra,capture_output=True,text=True)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            result=subprocess.run(command+['merge','--glossary',str(target/'glossary.json'),
                '--increment',str(target/'07-glossary-increment.yaml'),'--output',str(target/'merged.yaml')],
                capture_output=True,text=True,timeout=60)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertEqual(load(target/'merged.yaml'),load(target/'glossary.yaml'))

    def test_glossary_schema_reuses_status_and_value_contracts(self):
        from validate import SCHEMAS
        term=load(SCHEMAS/'glossary-term.schema.json')
        self.assertEqual(term['properties']['preferred_name']['$ref'],'urn:osago:kb:1.0#/$defs/preferred_name')
        self.assertEqual(term['properties']['status']['$ref'],'urn:osago:kb:1.0#/$defs/knowledge_status')

    def test_INFERRED_name_stays_a_visible_hypothesis(self):
        base,inputs=self.fixture()
        k=inputs['knowledge']
        c=next(c for c in k['claims'] if c['predicate']=='preferred_name' and c['id'].startswith('claim:glossary:'))
        basis=next(c['id'] for c in k['claims'] if c['predicate']=='technical_aliases')
        c.update(inference=True,knowledge_status='INFERRED',modality='inferred',support=[],basis_claim_ids=[basis],
                 inference_rationale='Synthetic hypothesis for contract testing.')
        self.revalidate(inputs)
        _,result=curate(base,inputs,DOMAIN)
        term=self.term(result)
        self.assertEqual(term['preferred_name']['status'],'INFERRED')
        self.assertEqual(term['status'],'INFERRED')
        self.assertTrue(any(r['term_id']==term['id'] for r in result['unresolved']))
        self.assertEqual(next(e for e in k['entities'] if e['id']==term['entity_ref'])['preferred_name'],unknown())

    def test_PARTIAL_name_cannot_be_promoted(self):
        base,inputs=self.fixture()
        c=next(c for c in inputs['knowledge']['claims'] if c['predicate']=='preferred_name' and c['id'].startswith('claim:glossary:'))
        c['knowledge_status']='PARTIALLY_CONFIRMED'
        self.revalidate(inputs)
        _,result=curate(base,inputs,DOMAIN)
        self.assertEqual(self.term(result)['preferred_name']['status'],'PARTIALLY_CONFIRMED')
        self.assertEqual(self.term(result)['status'],'PARTIALLY_CONFIRMED')

    def test_status_tampering_and_hidden_unresolved_fail(self):
        base,inputs=self.fixture('unknown')
        _,result=curate(base,inputs,DOMAIN)
        result['unresolved']=[]
        self.term(result)['status']='CONFIRMED'
        errors=glossary_errors(result)
        self.assertTrue(any('aggregate status' in e for e in errors))

    def test_raw_alias_without_mapping_remains_unresolved(self):
        base,inputs=self.fixture('unknown')
        k=inputs['knowledge']
        k['claims']=[c for c in k['claims'] if c['predicate']!='technical_aliases']
        self.revalidate(inputs)
        _,result=curate(base,inputs,DOMAIN)
        self.assertFalse(result['terms'])
        pending=next(r for r in result['unresolved'] if r['entity_ref']=='integration:glossary:eligibility')
        self.assertIsNone(pending['term_id'])
        self.assertEqual(pending['technical_aliases'],['SomeEligibilityInvoker'])
        self.assertEqual(curate(result,inputs,DOMAIN)[1],result)

    def test_old_confirmed_name_is_retained_with_new_uncertainty(self):
        base,inputs=self.fixture('existing')
        _,_,upstream,_=glossary_fixture('existing')
        report,gaps=draft(upstream)
        alias=next(c['id'] for c in inputs['knowledge']['claims'] if c['predicate']=='technical_aliases')
        mark_reviewed(upstream,report,alias)
        report['summary']=calculate_summary(report,gaps)
        inputs['validation']=report
        inc,result=curate(base,inputs,DOMAIN)
        self.assertEqual(self.term(result)['preferred_name'],self.term(base)['preferred_name'])
        self.assertEqual(self.term(result)['status'],'PARTIALLY_CONFIRMED')
        self.assertEqual(merge(base,inc),result)

    def test_same_preferred_term_for_distinct_entities_is_conflict(self):
        base,inputs=self.fixture('similar')
        k=inputs['knowledge']
        c=next(c for c in k['claims'] if c['subject_id']=='integration:glossary:other' and c['predicate']=='preferred_name')
        c['value']='скоринг'
        self.revalidate(inputs)
        _,result=curate(base,inputs,DOMAIN)
        self.assertEqual(len(result['terms']),2)
        self.assertTrue(all(t['status']=='CONFLICT' for t in result['terms']))
        self.assertEqual(len(lookup(result,'скоринг')),2)

    def test_identity_and_snapshot_cannot_be_reused(self):
        base,inputs=self.fixture('existing')
        next(e for e in inputs['knowledge']['entities'] if e['id']=='integration:glossary:nsis')['identity_key']='another-concept'
        self.revalidate(inputs)
        with self.assertRaisesRegex(ValueError,'identity_key'):
            curate(base,inputs,DOMAIN)

    def test_alias_evidence_cannot_be_hidden(self):
        base,inputs=self.fixture('unknown')
        _,result=curate(base,inputs,DOMAIN)
        self.term(result)['evidence']=[]
        self.assertTrue(any('technical alias requires' in e for e in glossary_errors(result)))

    def test_editorial_selection_uses_existing_entity_id(self):
        base,inputs=self.fixture()
        selection=dict(schema_version='1.0',selections=[dict(entity_ref='integration:glossary:scoring',type='SYSTEM',
                                                            reason='Synthetic editorial grouping.')])
        inc,result=curate(base,inputs,DOMAIN,selection)
        term=self.term(result)
        self.assertEqual(term['type'],'SYSTEM')
        self.assertEqual(term['entity_ref'],'integration:glossary:scoring')
        self.assertEqual(inc['input_hashes']['selection'],digest(selection))
        self.assertEqual(merge(base,inc),result)

    def test_merge_statistics_must_match_patch(self):
        base,inputs=self.fixture()
        inc,_=curate(base,inputs,DOMAIN)
        inc['statistics']['added']+=1
        with self.assertRaisesRegex(ValueError,'statistics'):
            merge(base,inc)


if __name__=='__main__':
    unittest.main()
