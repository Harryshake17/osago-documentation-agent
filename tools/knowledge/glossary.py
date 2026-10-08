"""Evidence-backed glossary projections, deterministic increments and offline merge."""
import argparse
import copy
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import yaml

from audit import STATUSES, digest, source_check_errors
from model import PROFILE, PRIMARY, increment_errors
from validate import load, schema_errors, validate
from runtime import runtime_review_errors, runtime_root

TYPE_MAP = {'Domain':'DOMAIN','Scenario':'SCENARIO','Integration':'INTEGRATION','Capability':'CAPABILITY',
            'Actor':'BUSINESS_ENTITY','State':'STATE','BusinessRule':'BUSINESS_RULE_TERM'}
FIELD_PREDICATES = {'preferred_name','definition','technical_aliases','same_concept_as'}


def empty_glossary(identifier='glossary:osago'):
    return dict(schema_version='1.0',model_profile=PROFILE,id=identifier,revision=1,
                terms=[],provenance=[],conflicts=[],unresolved=[])


def unknown():
    return dict(value=None,status='UNKNOWN',claim_ids=[],evidence_ids=[])


def require(errors):
    if errors:
        raise ValueError('\n'.join(dict.fromkeys(errors)))


def validation_errors(knowledge, report, supplied=None):
    """Reuse the 06 report, its claim hashes and shared source-check policy."""
    errors = schema_errors('knowledge-package',knowledge) + schema_errors('validation-report',report)
    if errors:
        return errors
    if knowledge.get('model_profile') != PROFILE:
        errors.append('glossary: scoped-knowledge-v1 knowledge required; migrate legacy input explicitly')
        return errors
    errors += validate('knowledge-package',knowledge,knowledge)
    package = dict(id=knowledge['package_id'],revision=knowledge['revision'])
    if report['package_ref'] != package or report['scope_ref'] != knowledge['scope']['id']:
        errors.append('validation: scope/package revision mismatch')
    entries = {r['kind']:r for r in report['inputs']}
    if len(entries) != len(report['inputs']):
        errors.append('validation: duplicate input kind')
    for kind,data in dict(supplied or {},knowledge=knowledge).items():
        entry = entries.get(kind,{})
        ident = data.get('package_id' if kind=='knowledge' else 'id')
        if entry.get('content_hash') != digest(data) or entry.get('id') != ident:
            errors.append(f'validation: stale input/hash {kind}')
    if report['mechanical_errors']:
        errors.append('validation: mechanical errors must be repaired before glossary curation')
    claims = {c['id']:c for c in knowledge['claims']}
    evidence = {e['id']:e for e in knowledge['evidence']}
    sources = {s['id']:s for s in knowledge['sources']}
    entities = {e['id']:e for e in knowledge['entities']}
    reviews = {r['claim_id']:r for r in report['claim_reviews']}
    if len(claims) != len(knowledge['claims']) or len(entities) != len(knowledge['entities']) or len(evidence) != len(knowledge['evidence']) or len(sources) != len(knowledge['sources']):
        errors.append('knowledge: duplicate registry IDs')
    if report['claim_inventory'] != sorted(claims) or set(reviews) != set(claims) or len(reviews) != len(report['claim_reviews']):
        errors.append('validation: every claim requires exactly one review')
    conflicts = {cid for row in knowledge['conflicts'] if row['status']=='unresolved' for cid in row['claim_ids']}
    def grounded(cid, trail=frozenset()):
        if cid in trail or cid not in claims:
            return False
        c,r = claims[cid],reviews.get(cid,{})
        if c['modality'] == 'runtime_observation':
            return False
        if not r.get('reviewed'):
            return False
        if r['status']=='INFERRED' and c['inference']:
            return bool(c.get('basis_claim_ids')) and all(grounded(b,trail|{cid}) for b in c['basis_claim_ids'])
        return r['status']=='CONFIRMED' and any(check['result']=='SUPPORTS' and
            check['verification'] in {'reopened','snapshot_only'} and evidence.get(check['evidence_id'],{}).get('source_type') in PRIMARY
            for check in r['source_checks'])
    for cid,c in claims.items():
        r = reviews.get(cid)
        if r is None:
            continue
        if r['claim_hash'] != digest(c):
            errors.append(cid+': changed claim hash')
        checks = {v['evidence_id']:v for v in r['source_checks']}
        if len(checks)!=len(r['source_checks']):
            errors.append(cid+': duplicate source checks')
        declared = {s['evidence_id'] for s in c['support'] if s['role'] in {'supports','contradicts'}}
        if not declared <= evidence.keys():
            errors.append(cid+': dangling Evidence ref')
        for eid,check in checks.items():
            e = evidence.get(eid)
            if not e or eid not in declared:
                errors.append(cid+': source check must refer to declared evidence')
                continue
            errors += source_check_errors(check,e,sources.get(e['snapshot_id'],{}),cid+'/'+eid)
        if not r['reviewed']:
            if r['status'] not in {'UNKNOWN','CONFLICT'} or r['status']=='CONFLICT' and cid not in conflicts:
                errors.append(cid+': unreviewed classification cannot confirm a term')
            continue
        if not declared <= checks.keys():
            errors.append(cid+': all declared sources must be checked')
        direct = [v for eid,v in checks.items() if eid in declared and
                  (evidence.get(eid,{}).get('source_type') in PRIMARY or runtime_root(c, evidence.get(eid,{})))
                  and v['verification'] in {'reopened','snapshot_only'} and v['result']=='SUPPORTS']
        if r['status']=='CONFIRMED' and (not direct or c['inference'] or r['unsupported_parts'] or
                any(v['result'] in {'PARTIAL_SUPPORT','CONTRADICTS','UNAVAILABLE','NOT_CHECKED'} for v in checks.values())):
            errors.append(cid+': CONFIRMED needs complete direct inspected support')
        if r['status']=='PARTIALLY_CONFIRMED' and (not r['supported_parts'] or not r['unsupported_parts'] or not any(
                v['result'] in {'SUPPORTS','PARTIAL_SUPPORT'} and
                (evidence.get(eid,{}).get('source_type') in PRIMARY or runtime_root(c, evidence.get(eid,{}))) for eid,v in checks.items())):
            errors.append(cid+': partial support must list supported/unsupported parts')
        if r['status']=='INFERRED' and (not c['inference'] or not grounded(cid)):
            errors.append(cid+': inference requires inspected, acyclic basis claims')
        if r['status']=='INFERRED' and c['predicate'] in {'business_rationale','business_meaning'}:
            errors.append(cid+': inference cannot supply business rationale/meaning')
        if not set(r['gap_ids'])<=set(report['gap_ids']):
            errors.append(cid+': dangling review Gap refs')
    counts = {status:sum(r['status']==status for r in report['claim_reviews']) for status in STATUSES}
    reviewed = sum(r['reviewed'] for r in report['claim_reviews'])
    summary = report['summary']
    if summary['counts']!=counts or summary['total_claims']!=len(claims) or summary['reviewed_claims']!=reviewed:
        errors.append('validation: inconsistent summary counts')
    if summary['review_status'] != ('complete' if reviewed==len(claims) else 'partial'):
        errors.append('validation: inconsistent review_status')
    return errors + runtime_review_errors(knowledge, report)


def status_of(claim, review):
    statuses = {claim['knowledge_status'],review['status'] if review['reviewed'] else 'UNKNOWN'}
    if claim['knowledge_status']=='CONFLICT' or review['status']=='CONFLICT':
        return 'CONFLICT'
    return next((s for s in ('UNKNOWN','INFERRED','PARTIALLY_CONFIRMED') if s in statuses),'CONFIRMED')


def index_context(provenance):
    k = provenance['knowledge']
    return dict(claims={c['id']:c for c in k['claims']},entities={e['id']:e for e in k['entities']},
                evidence={e['id']:e for e in k['evidence']},reviews={r['claim_id']:r for r in provenance['validation']['claim_reviews']})


def claim_evidence(cid, context, trail=frozenset()):
    if cid in trail or cid not in context['claims']:
        return set()
    c = context['claims'][cid]
    result = {s['evidence_id'] for s in c['support'] if s['role']=='supports'}
    for basis in c['basis_claim_ids']:
        result |= claim_evidence(basis,context,trail|{cid})
    return result


def field_value(entity_id, predicate, context):
    rows = [c for c in context['claims'].values() if c['subject_id']==entity_id and c['predicate']==predicate and
            c['lifecycle_status']=='current' and isinstance(c['value'],str) and c['value']]
    useful = []
    for c in rows:
        status = status_of(c,context['reviews'][c['id']])
        eids = claim_evidence(c['id'],context)
        # An inspected technical name still does not establish domain terminology.
        domain_source = any(context['evidence'].get(e,{}).get('source_type') in {'CONFLUENCE','TEST'} for e in eids)
        if status in {'CONFIRMED','PARTIALLY_CONFIRMED'} and (not domain_source or c['modality'] not in {'source_statement','documented_requirement'}):
            continue
        if status!='UNKNOWN':
            useful.append((c,status,eids))
    if not useful:
        return unknown()
    values = {c['value'] for c,_,_ in useful}
    if len(values)>1 or any(status=='CONFLICT' for _,status,_ in useful):
        return dict(value=None,status='CONFLICT',claim_ids=sorted(c['id'] for c,_,_ in useful),
                    evidence_ids=sorted(set().union(*(e for _,_,e in useful))))
    best = next(s for s in ('CONFIRMED','PARTIALLY_CONFIRMED','INFERRED') if any(status==s for _,status,_ in useful))
    chosen = [(c,e) for c,status,e in useful if status==best]
    return dict(value=chosen[0][0]['value'],status=best,claim_ids=sorted(c['id'] for c,_ in chosen),
                evidence_ids=sorted(set().union(*(e for _,e in chosen))))


def semantic_status(term, context=None):
    statuses = {term['preferred_name']['status'],term['definition']['status']}
    if context:
        statuses |= {status_of(context['claims'][cid],context['reviews'][cid]) for cid in term['validation_claim_ids'] if cid in context['claims']
                     and status_of(context['claims'][cid],context['reviews'][cid])!='CONFIRMED'}
    if 'CONFLICT' in statuses:
        return 'CONFLICT'
    if 'INFERRED' in statuses:
        return 'INFERRED'
    if statuses=={'UNKNOWN'}:
        return 'UNKNOWN'
    if 'UNKNOWN' in statuses or 'PARTIALLY_CONFIRMED' in statuses:
        return 'PARTIALLY_CONFIRMED'
    return 'CONFIRMED'


def alias_witness(cid, alias, related_entities, context):
    c=context['claims'].get(cid,{})
    return (c.get('subject_id') in related_entities and c.get('predicate')=='technical_aliases' and
            c.get('value')==alias and status_of(c,context['reviews'][cid])=='CONFIRMED' and any(
                context['evidence'].get(e,{}).get('source_type') in {'CODE','CONFIG','GIT'} and
                alias in (context['evidence'][e].get('excerpt') or '') for e in claim_evidence(cid,context)))


def glossary_errors(glossary):
    errors = schema_errors('glossary',glossary)
    if errors:
        return errors
    provenance = {p['id']:p for p in glossary['provenance']}
    if len(provenance)!=len(glossary['provenance']):
        errors.append('glossary: duplicate provenance ID')
    contexts = {}
    identities,snapshots={},{}
    packages={}
    for pid,p in provenance.items():
        errors += validation_errors(p['knowledge'],p['validation'])
        k=p['knowledge']
        previous=packages.get(k['package_id'])
        if previous is not None and previous!=k:
            errors += increment_errors(previous,k)
        packages[k['package_id']]=k
        if pid != 'provenance:'+digest([p['knowledge'],p['validation']]):
            errors.append('glossary: provenance hash changed')
        contexts[pid]=index_context(p)
        for e in p['knowledge']['entities']:
            identity=(e['type'],e['identity_key'])
            if e['id'] in identities and identities[e['id']]!=identity:
                errors.append('glossary: Entity ID reused for another identity: '+e['id'])
            identities[e['id']]=identity
        for s in p['knowledge']['sources']:
            if s['id'] in snapshots and snapshots[s['id']]!=s:
                errors.append('glossary: immutable SourceSnapshot changed: '+s['id'])
            snapshots[s['id']]=s
    if errors:
        return list(dict.fromkeys(errors))
    term_ids,entity_ids = set(),set()
    for t in glossary['terms']:
        if t['id'] in term_ids or t['entity_ref'] in entity_ids:
            errors.append('glossary: duplicate stable term/entity ID')
        term_ids.add(t['id']);entity_ids.add(t['entity_ref'])
        linked = [contexts[p] for p in t['provenance_refs'] if p in contexts]
        if len(linked)!=len(t['provenance_refs']) or not linked:
            errors.append(t['id']+': dangling/empty provenance refs')
            continue
        entities = {eid:e for ctx in linked for eid,e in ctx['entities'].items()}
        claims = {cid:c for ctx in linked for cid,c in ctx['claims'].items()}
        evidence = {eid:e for ctx in linked for eid,e in ctx['evidence'].items()}
        if t['entity_ref'] not in entities or entities[t['entity_ref']]['identity_key']!=t['identity_key']:
            errors.append(t['id']+': existing Entity ID/identity required')
        if not set(t['related_entities']+t['domains'])<=entities.keys() or t['entity_ref'] not in t['related_entities']:
            errors.append(t['id']+': dangling entity/domain relation')
        if any(entities.get(d,{}).get('type')!='Domain' for d in t['domains']):
            errors.append(t['id']+': domains must reference Domain entities')
        if not set(t['evidence'])<=evidence.keys() or not set(t['validation_claim_ids'])<=claims.keys():
            errors.append(t['id']+': dangling Evidence/Claim refs')
        for field in ('preferred_name','definition'):
            v=t[field]
            for cid in v['claim_ids']:
                witnesses = [ctx for ctx in linked if cid in ctx['claims'] and ctx['claims'][cid]['subject_id']==t['entity_ref']
                             and ctx['claims'][cid]['predicate']==field and (v['status']=='CONFLICT' or ctx['claims'][cid]['value']==v['value'])
                             and status_of(ctx['claims'][cid],ctx['reviews'][cid])==v['status']]
                if not witnesses:
                    errors.append(t['id']+'/'+field+': matching validated claim required')
                elif not any(claim_evidence(cid,ctx)<=set(v['evidence_ids']) for ctx in witnesses):
                    errors.append(t['id']+'/'+field+': omitted field evidence')
                if v['status'] in {'CONFIRMED','PARTIALLY_CONFIRMED'} and not any(
                        ctx['claims'][cid]['modality'] in {'source_statement','documented_requirement'} and any(
                            ctx['evidence'].get(e,{}).get('source_type') in {'CONFLUENCE','TEST'} for e in claim_evidence(cid,ctx)) for ctx in witnesses):
                    errors.append(t['id']+'/'+field+': technical source cannot establish business terminology')
            if v['status']!='UNKNOWN' and (not v['claim_ids'] or not v['evidence_ids']):
                errors.append(t['id']+'/'+field+': known/hypothetical value requires evidence')
            if not set(v['evidence_ids'])<=set(t['evidence']):
                errors.append(t['id']+': term omits field evidence')
        for i,alias in enumerate(t['technical_aliases']):
            cids=t['attribute_claims'].get(f'technical_aliases/{i}',[])
            if not cids or not any(alias_witness(cid,alias,t['related_entities'],ctx) and
                    claim_evidence(cid,ctx)<=set(t['evidence']) for ctx in linked for cid in cids):
                errors.append(t['id']+': technical alias requires validated code/config mapping '+alias)
        for i,eid in enumerate(t['related_entities']):
            cids=t['attribute_claims'].get(f'related_entities/{i}',[])
            if not cids or not any(ctx['claims'].get(c,{}).get('subject_id')==eid and claim_evidence(c,ctx) and
                    claim_evidence(c,ctx)<=set(t['evidence']) for ctx in linked for c in cids):
                errors.append(t['id']+': related entity requires a claim about that entity')
        origins={r['value']:r for r in t['search_alias_origins']}
        if set(origins)!=set(t['search_aliases']) or len(origins)!=len(t['search_alias_origins']):
            errors.append(t['id']+': every search alias requires one origin')
        allowed = set(t['technical_aliases']) | {t['preferred_name']['value']} | {c['value'] for c in t['terminology_candidates']}
        for ctx in linked:
            e=ctx['entities'].get(t['entity_ref'],{})
            allowed.update(e.get('search_aliases',[]))
        normalized={v.casefold() for v in allowed if isinstance(v,str)}
        if any(a.casefold() not in normalized for a in t['search_aliases']):
            errors.append(t['id']+': artificial/unattributed search synonym')
        for candidate in t['terminology_candidates']:
            if not any(candidate in ctx['entities'].get(candidate['entity_ref'],{}).get('terminology_candidates',[])
                       for ctx in linked):
                errors.append(t['id']+': candidate must come from the shared Entity registry')
        for row in t['search_alias_origins']:
            origin_values=[]
            if row['entity_ref'] not in t['related_entities']:
                errors.append(t['id']+': search origin must reference a related entity')
            if row['origin']=='preferred_name':
                origin_values=[t['preferred_name']['value']]+[c['value'] for ctx in linked for c in ctx['claims'].values()
                    if c['subject_id']==row['entity_ref'] and c['predicate']=='preferred_name' and
                    status_of(c,ctx['reviews'][c['id']])!='UNKNOWN']
            elif row['origin']=='technical_alias':
                origin_values=t['technical_aliases']
            elif row['origin']=='candidate':
                origin_values=[c['value'] for c in t['terminology_candidates'] if c['entity_ref']==row['entity_ref']]
            elif row['origin']=='search_alias':
                origin_values=[v for ctx in linked for v in ctx['entities'].get(row['entity_ref'],{}).get('search_aliases',[])]
            if row['value'].casefold() not in {v.casefold() for v in origin_values if isinstance(v,str)}:
                errors.append(t['id']+': search alias origin mismatch')
        if not set(t['abbreviations'])<=set(t['technical_aliases']+t['search_aliases']):
            errors.append(t['id']+': abbreviation must preserve an existing spelling')
        expected='CONFLICT' if any(t['id'] in c['term_ids'] for c in glossary['conflicts']) else semantic_status(t,linked[-1])
        if t['status']!=expected:
            errors.append(t['id']+': aggregate status must preserve validation uncertainty')
    all_claims={cid for ctx in contexts.values() for cid in ctx['claims']}
    all_evidence={eid for ctx in contexts.values() for eid in ctx['evidence']}
    conflicts={c['id']:c for c in glossary['conflicts']}
    if len(conflicts)!=len(glossary['conflicts']):
        errors.append('glossary: duplicate conflict IDs')
    for c in conflicts.values():
        if c['record']['id']!=c['id'] or c['record']['status']!='unresolved' or c['record']['resolution_claim_id'] is not None:
            errors.append(c['id']+': terminology CONFLICT cannot be auto-resolved')
        if not set(c['term_ids'])<=term_ids or not set(c['record']['claim_ids'])<=all_claims or not set(c['evidence'])<=all_evidence:
            errors.append(c['id']+': dangling conflict refs')
        if set(c['entity_refs'])!={t['entity_ref'] for t in glossary['terms'] if t['id'] in c['term_ids']}:
            errors.append(c['id']+': conflict entity/term projection mismatch')
        if any(t['status']!='CONFLICT' for t in glossary['terms'] if t['id'] in c['term_ids']):
            errors.append(c['id']+': conflict must remain visible on affected terms')
    unresolved_ids=set()
    unresolved_terms=set()
    for row in glossary['unresolved']:
        if row['entity_ref'] in unresolved_ids:
            errors.append('glossary: duplicate unresolved entity')
        unresolved_ids.add(row['entity_ref'])
        if row['term_id'] is None:
            if row['entity_ref'] in entity_ids or row['status']!='UNKNOWN' or row['preferred_name']!=unknown() or not any(
                row['entity_ref'] in ctx['entities'] and set(row['technical_aliases'])<=set(ctx['entities'][row['entity_ref']]['technical_aliases'])
                for ctx in contexts.values()):
                errors.append('glossary: unmapped candidate requires a shared entity and UNKNOWN')
            if row['gap']['status']!='open' or row['entity_ref'] not in row['gap']['affected_ids']:
                errors.append('glossary: unmapped candidate requires an open Gap')
            continue
        unresolved_terms.add(row['entity_ref'])
        term=next((t for t in glossary['terms'] if t['id']==row['term_id']),None)
        if not term or row['entity_ref']!=term['entity_ref'] or row['preferred_name']!=term['preferred_name'] or row['status']!=term['status'] or row['technical_aliases']!=term['technical_aliases']:
            errors.append('glossary: unresolved projection mismatch')
        if row['gap']['status']!='open' or row['entity_ref'] not in row['gap']['affected_ids']:
            errors.append('glossary: unresolved requires an affected open shared Gap')
    if unresolved_terms!={t['entity_ref'] for t in glossary['terms'] if t['status']!='CONFIRMED'}:
        errors.append('glossary: every uncertain term must remain unresolved')
    return list(dict.fromkeys(errors))


def lookup(glossary, spelling):
    key=spelling.casefold()
    return [copy.deepcopy(t) for t in glossary['terms'] if key in {v.casefold() for v in
            [t['preferred_name']['value']]+t['technical_aliases']+t['search_aliases'] if isinstance(v,str)}]


def conflict_record(terms, variants, claims, eids, message):
    cids=sorted(set(claims))
    if len(cids)<2:
        raise ValueError('Terminology ambiguity needs both mapping claims; retain candidates until evidence is available')
    ident='term-conflict:'+digest([sorted(t['id'] for t in terms),sorted(set(variants)),message])[:20]
    return dict(id=ident,record=dict(id=ident,claim_ids=cids,disagreement=message,status='unresolved',resolution_claim_id=None),
                entity_refs=sorted(set(t['entity_ref'] for t in terms)),term_ids=sorted(t['id'] for t in terms),
                variants=sorted(set(variants)),evidence=sorted(set(eids)),required_action='ANALYST_REVIEW',knowledge_status='CONFLICT')


def curate(current, inputs, domain_id, selection=None):
    require(glossary_errors(current))
    knowledge,scenario,report=inputs['knowledge'],inputs['scenario'],inputs['validation']
    require(schema_errors('scenario',scenario))
    supplied={kind:data for kind,data in inputs.items() if kind not in {'knowledge','validation'}}
    for kind,data in supplied.items():
        require(schema_errors(kind,data))
        if data.get('scope_ref')!=knowledge['scope']['id'] or data.get('package_ref')!={'id':knowledge['package_id'],'revision':knowledge['revision']}:
            raise ValueError(kind+': scope/package revision mismatch')
    require(validation_errors(knowledge,report,supplied))
    entities={e['id']:e for e in knowledge['entities']}
    if entities.get(domain_id,{}).get('type')!='Domain':
        raise ValueError('--domain-id must reference an existing Domain Entity ID')
    selected={}
    if selection is not None:
        require(schema_errors('glossary-selection',selection))
        for row in selection['selections']:
            if row['entity_ref'] not in entities or row['entity_ref'] in selected:
                raise ValueError('selection: dangling or duplicate Entity ID')
            selected[row['entity_ref']]=row['type']
    pid='provenance:'+digest([knowledge,report])
    p=dict(id=pid,knowledge=copy.deepcopy(knowledge),validation=copy.deepcopy(report))
    ctx=index_context(p)
    result=copy.deepcopy(current)
    if not any(v['id']==pid for v in result['provenance']):
        result['provenance'].append(p)
    base_terms={t['id']:t for t in current['terms']}
    pending={row['entity_ref']:copy.deepcopy(row) for row in current['unresolved'] if row['term_id'] is None}
    matched,candidate_count,ignored=0,0,0
    for eid,entity in sorted(entities.items()):
        typ=selected.get(eid,TYPE_MAP.get(entity['type']))
        candidates=entity['terminology_candidates']
        if typ is None and candidates:
            typ='TECHNICAL_CONCEPT'
        if typ is None:
            ignored+=1
            continue
        candidate_count+=len(set(entity['technical_aliases']+entity['search_aliases']+[c['value'] for c in candidates]+
                                 ([entity['preferred_name']['value']] if entity['preferred_name']['value'] else [])))
        # Text is useful for discovery, but is never sufficient for joining distinct entities.
        existing=[t for t in result['terms'] if eid in t['related_entities']]
        if len(existing)>1:
            raise ValueError('glossary: entity maps to multiple existing terms')
        if existing:
            term=existing[0];matched+=1
            if term['entity_ref']!=eid:
                # Preserve an already approved explicit association; never retarget its anchor.
                continue
            if term['identity_key']!=entity['identity_key']:
                raise ValueError('Entity ID reused for a different identity_key')
        else:
            term=dict(id='TERM-'+digest([current['id'],eid,entity['identity_key']])[:16].upper(),entity_ref=eid,
                identity_key=entity['identity_key'],preferred_name=unknown(),definition=unknown(),type=typ,
                technical_aliases=[],search_aliases=[],terminology_candidates=[],search_alias_origins=[],abbreviations=[],
                domains=[domain_id],related_entities=[eid],attribute_claims={},evidence=[],status='UNKNOWN',
                provenance_refs=[],validation_claim_ids=[])
            result['terms'].append(term)
        term['provenance_refs']=list(dict.fromkeys(term['provenance_refs']+[pid]))
        term['domains']=list(dict.fromkeys(term['domains']+[domain_id]))
        for c in candidates:
            if c not in term['terminology_candidates']:
                term['terminology_candidates'].append(copy.deepcopy(c))
        for field in ('preferred_name','definition'):
            proposed=field_value(eid,field,ctx)
            old=term[field]
            if old['status']=='CONFLICT':
                continue
            if proposed['status']=='CONFLICT' or old['value'] and proposed['value'] and old['value']!=proposed['value']:
                variants=[v for v in (old['value'],proposed['value']) if v]
                variants += [ctx['claims'][c]['value'] for c in proposed['claim_ids']]
                conflict=conflict_record([term],variants,old['claim_ids']+proposed['claim_ids'],old['evidence_ids']+proposed['evidence_ids'],
                                          'Competing terminology for one entity: '+field)
                if conflict not in result['conflicts']:
                    result['conflicts'].append(conflict)
                # Keep an approved historical field; the term as a whole is now CONFLICT.
                if old['status']!='CONFIRMED':
                    term[field]=dict(proposed,value=None,status='CONFLICT')
            elif old['status']!='CONFIRMED' and proposed['status']!='UNKNOWN':
                term[field]=proposed
        mapping=[c for c in ctx['claims'].values() if c['subject_id']==eid and c['lifecycle_status']=='current'
                 and c['predicate'] in FIELD_PREDICATES]
        for c in mapping:
            term['validation_claim_ids']=list(dict.fromkeys(term['validation_claim_ids']+[c['id']]))
            if (isinstance(c['value'],str) and c['value'] in entity['technical_aliases'] and
                    alias_witness(c['id'],c['value'],[eid],ctx)):
                if c['value'] not in term['technical_aliases']:
                    term['technical_aliases'].append(c['value'])
                i=term['technical_aliases'].index(c['value'])
                key=f'technical_aliases/{i}'
                term['attribute_claims'][key]=list(dict.fromkeys(term['attribute_claims'].get(key,[])+[c['id']]))
                term['evidence']=list(dict.fromkeys(term['evidence']+sorted(claim_evidence(c['id'],ctx))))
        binding=[c['id'] for c in mapping if claim_evidence(c['id'],ctx)]
        if not binding:
            # No evidence-backed mapping: keep a candidate unresolved, not a glossary business fact.
            if term['id'] not in base_terms:
                result['terms'].remove(term)
                if entity['technical_aliases'] or candidates or entity['preferred_name']['value']:
                    pending[eid]=dict(entity_ref=eid,term_id=None,technical_aliases=copy.deepcopy(entity['technical_aliases']),
                        preferred_name=unknown(),status='UNKNOWN',gap=dict(id='gap:glossary:'+digest([eid,'mapping'])[:20],
                            reason='missing_link',question='Как подтверждено соответствие имени и этой сущности?',
                            affected_ids=[eid],next_action='Add a scoped mapping Claim and validate it; aliases here are candidates.',status='open'))
            else:
                original=copy.deepcopy(base_terms[term['id']])
                term.clear();term.update(original)
            ignored+=1
            continue
        pending.pop(eid,None)
        term['attribute_claims']['related_entities/0']=list(dict.fromkeys(term['attribute_claims'].get('related_entities/0',[])+binding))
        term['evidence']=list(dict.fromkeys(term['evidence']+sorted(set().union(*(claim_evidence(cid,ctx) for cid in binding)))))
        for field in ('preferred_name','definition'):
            term['evidence']=list(dict.fromkeys(term['evidence']+term[field]['evidence_ids']))
        for value,origin in [(v,'technical_alias') for v in term['technical_aliases']]+[(v,'search_alias') for v in entity['search_aliases']]+[(c['value'],'candidate') for c in candidates]+(
                [(term['preferred_name']['value'],'preferred_name')] if term['preferred_name']['value'] else []):
            for spelling in dict.fromkeys([value,value.casefold()]):
                if spelling not in term['search_aliases']:
                    term['search_aliases'].append(spelling)
                    term['search_alias_origins'].append(dict(value=spelling,origin=origin,entity_ref=eid))
        term['abbreviations']=list(dict.fromkeys(term['abbreviations']+[a for a in term['technical_aliases'] if a.isupper() and 2<=len(a)<=10]))
        term['status']=semantic_status(term,ctx)
    for i,left in enumerate(result['terms']):
        for right in result['terms'][i+1:]:
            common_alias=set(left['technical_aliases']) & set(right['technical_aliases'])
            same_name=left['preferred_name']['value'] and left['preferred_name']['value']==right['preferred_name']['value']
            if common_alias or same_name:
                variants=sorted(common_alias) if common_alias else [left['preferred_name']['value']]
                cids=left['preferred_name']['claim_ids']+right['preferred_name']['claim_ids']
                if common_alias:
                    cids += [c for t in (left,right) for key,values in t['attribute_claims'].items() if key.startswith('technical_aliases/') for c in values]
                conflict=conflict_record([left,right],variants,cids,left['evidence']+right['evidence'],'Ambiguous terminology maps to distinct Entity IDs')
                if conflict not in result['conflicts']:
                    result['conflicts'].append(conflict)
    conflicted={tid for c in result['conflicts'] for tid in c['term_ids']}
    for term in result['terms']:
        if term['id'] in conflicted:
            term['status']='CONFLICT'
    result['unresolved']=[pending[eid] for eid in sorted(pending) if not any(eid in t['related_entities'] for t in result['terms'])]
    for term in result['terms']:
        if term['status']!='CONFIRMED':
            gid='gap:glossary:'+digest([term['id'],'terminology'])[:20]
            result['unresolved'].append(dict(entity_ref=term['entity_ref'],term_id=term['id'],technical_aliases=term['technical_aliases'],
                preferred_name=term['preferred_name'],status=term['status'],gap=dict(id=gid,reason='unknown_field',
                    question='Какой термин и определение этой сущности подтверждены в предметной области?',
                    affected_ids=[term['entity_ref']],next_action='Review terminology evidence; do not infer a translation.',status='open')))
    if result!=current:
        result['revision']=current['revision']+1
    require(glossary_errors(result))
    added=[dict(term=t) for t in result['terms'] if t['id'] not in base_terms]
    updated=[dict(term_id=t['id'],changes={key:copy.deepcopy(v) for key,v in t.items() if v!=base_terms[t['id']][key]})
             for t in result['terms'] if t['id'] in base_terms and t!=base_terms[t['id']]]
    updated_ids={r['term_id'] for r in updated}
    unchanged=[dict(term_id=t['id']) for t in current['terms'] if t['id'] not in updated_ids]
    increment=dict(schema_version='1.0',model_profile=PROFILE,id='glossary-increment:'+digest([current,inputs,domain_id,selection])[:24],
        glossary_ref=dict(id=current['id'],revision=current['revision']),base_hash=digest(current),result_hash=digest(result),
        domain_id=domain_id,package_ref=dict(id=knowledge['package_id'],revision=knowledge['revision']),scope_ref=knowledge['scope']['id'],
        input_hashes=dict({kind:digest(data) for kind,data in inputs.items()},glossary=digest(current)),added=added,updated=updated,unchanged=unchanged,
        provenance_added=[v for v in result['provenance'] if v not in current['provenance']],conflicts=result['conflicts'],unresolved=result['unresolved'],
        statistics=dict(candidates_total=candidate_count,matched_existing=matched,added=len(added),updated=len(updated),unchanged=len(unchanged),
                        conflicts=len(result['conflicts']),unresolved=len(result['unresolved']),ignored_entities=ignored))
    if selection is not None:
        increment['input_hashes']['selection']=digest(selection)
    require(schema_errors('glossary-increment',increment))
    return increment,result


def merge(current, increment):
    require(glossary_errors(current))
    require(schema_errors('glossary-increment',increment))
    for field in ('added','updated','unchanged','conflicts','unresolved'):
        if increment['statistics'][field]!=len(increment[field]):
            raise ValueError('merge: inconsistent statistics: '+field)
    if increment['input_hashes']['glossary']!=increment['base_hash']:
        raise ValueError('merge: inconsistent baseline hash')
    if digest(current)==increment['result_hash']:
        return copy.deepcopy(current)
    if increment['glossary_ref']!={'id':current['id'],'revision':current['revision']} or increment['base_hash']!=digest(current):
        raise ValueError('glossary merge: stale base revision/hash')
    result=copy.deepcopy(current)
    terms={t['id']:t for t in result['terms']}
    seen=set()
    for row in increment['added']:
        t=copy.deepcopy(row['term'])
        if t['id'] in terms or t['id'] in seen:
            raise ValueError('merge: duplicate added term ID')
        seen.add(t['id']);terms[t['id']]=t;result['terms'].append(t)
    for row in increment['updated']:
        tid=row['term_id']
        if tid not in terms or tid in seen:
            raise ValueError('merge: missing/duplicate updated term ID')
        seen.add(tid)
        old=terms[tid]
        new=dict(old,**copy.deepcopy(row['changes']))
        for field in ('technical_aliases','search_aliases','related_entities','domains','provenance_refs','validation_claim_ids'):
            if not set(old[field])<=set(new[field]):
                raise ValueError('merge: existing values cannot be lost: '+field)
        for field in ('evidence','abbreviations'):
            if not set(old[field])<=set(new[field]):
                raise ValueError('merge: existing values cannot be lost: '+field)
        if any(candidate not in new['terminology_candidates'] for candidate in old['terminology_candidates']):
            raise ValueError('merge: existing terminology candidates cannot be lost')
        for field in ('preferred_name','definition'):
            if old[field]['status']=='CONFIRMED' and new[field]!=old[field]:
                raise ValueError('merge: approved field must be retained; add a conflict for review')
        old.update(row['changes'])
    unchanged={row['term_id'] for row in increment['unchanged']}
    if len(unchanged)!=len(increment['unchanged']) or unchanged & seen or unchanged != {t['id'] for t in current['terms']} - seen:
        raise ValueError('merge: unchanged inventory must retain every other baseline term')
    for p in increment['provenance_added']:
        if not any(row['id']==p['id'] for row in result['provenance']):
            result['provenance'].append(copy.deepcopy(p))
    if not all(c in increment['conflicts'] for c in current['conflicts']):
        raise ValueError('merge: unresolved conflicts cannot be discarded')
    result['conflicts']=copy.deepcopy(increment['conflicts']);result['unresolved']=copy.deepcopy(increment['unresolved'])
    if result!=current:
        result['revision']+=1
    require(glossary_errors(result))
    if digest(result)!=increment['result_hash']:
        raise ValueError('merge: result hash mismatch')
    return result


def check_output(path,data,overwrite=False):
    path=Path(path)
    if path.exists():
        if load(path)==data:
            return False
        if not overwrite:
            raise ValueError('Existing output retained: '+str(path)+'; use --overwrite for an authorized update')
    return True


def write_output(path,data,overwrite=False):
    path=Path(path)
    if not check_output(path,data,overwrite):
        return
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.name+'.tmp')
    temporary.write_text(yaml.safe_dump(data,allow_unicode=True,sort_keys=False,width=110),encoding='utf-8')
    temporary.replace(path)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['init','curate','merge','check','lookup'])
    for flag in ('glossary','increment','knowledge','scenario','validation','domain-tree','source-map','technical-flow','business-rules','selection','output-dir','output'):
        parser.add_argument('--'+flag,type=Path)
    parser.add_argument('--id',default='glossary:osago');parser.add_argument('--domain-id');parser.add_argument('--term')
    parser.add_argument('--overwrite',action='store_true')
    args=parser.parse_args()
    try:
        if args.mode=='init':
            if not args.output:
                raise ValueError('init requires --output')
            write_output(args.output,empty_glossary(args.id),args.overwrite)
            return
        if not args.glossary:
            raise ValueError('--glossary is required')
        current=load(args.glossary)
        if args.mode=='curate':
            if not all((args.knowledge,args.scenario,args.validation,args.domain_id,args.output_dir)):
                raise ValueError('curate requires --knowledge --scenario --validation --domain-id --output-dir')
            inputs={key:load(getattr(args,key.replace('-','_'))) for key in
                    ('knowledge','scenario','validation','domain-tree','source-map','technical-flow','business-rules')
                    if getattr(args,key.replace('-','_')) is not None}
            increment,result=curate(current,inputs,args.domain_id,load(args.selection) if args.selection else None)
            if merge(current,increment)!=result:
                raise ValueError('increment does not reproduce curated result')
            outputs=[(args.output_dir/'07-glossary-increment.yaml',increment),(args.output_dir/'glossary.yaml',result)]
            protected={getattr(args,flag).resolve() for flag in ('knowledge','scenario','validation','domain_tree','source_map',
                       'technical_flow','business_rules','selection') if getattr(args,flag)}
            for path,data in outputs:
                if path.resolve() in protected:
                    raise ValueError('Output must not overwrite an upstream artifact')
                check_output(path,data,args.overwrite)
            for path,data in outputs:
                write_output(path,data,args.overwrite)
            print('Glossary increment and evidence-backed glossary created. Conflicts require analyst review.')
        elif args.mode=='merge':
            if not args.increment or not args.output:
                raise ValueError('merge requires --increment --output')
            if args.output.resolve()==args.increment.resolve():
                raise ValueError('Merge output must not overwrite the increment')
            write_output(args.output,merge(current,load(args.increment)),args.overwrite)
        elif args.mode=='check':
            require(glossary_errors(current))
            if args.increment:
                require(schema_errors('glossary-increment',load(args.increment)))
                if load(args.increment)['result_hash']!=digest(current):
                    raise ValueError('Glossary does not match increment result_hash')
            print('Glossary contracts passed. Semantic source verification remains required.')
        else:
            require(glossary_errors(current))
            if not args.term:
                raise ValueError('lookup requires --term')
            print(yaml.safe_dump(lookup(current,args.term),allow_unicode=True,sort_keys=False))
    except (OSError,ValueError,yaml.YAMLError) as exc:
        parser.exit(2,f'{exc}\n')


if __name__=='__main__':
    main()
