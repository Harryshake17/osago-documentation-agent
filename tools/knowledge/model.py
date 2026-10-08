"""Shared structured knowledge invariants. No source access or prose parsing."""
import copy
from runtime import runtime_root

PROFILE = 'scoped-knowledge-v1'
PRIMARY = {'CODE', 'CONFIG', 'TEST', 'CONFLUENCE', 'GIT'}
BUSINESS_MODALITIES = {'source_statement', 'documented_requirement'}
TERM_FIELDS = ('preferred_name', 'technical_aliases', 'search_aliases', 'terminology_candidates')


def legacy_view(kind, artifact):
    """Reuse existing rule checks without mutating the canonical structured input."""
    if kind != 'business-rules' or artifact.get('model_profile') != PROFILE:
        return artifact
    result = copy.deepcopy(artifact)
    for rule in result['rules']:
        rule['business_rationale'] = rule['business_rationale']['value'] or 'UNKNOWN'
    return result


def model_errors(kind, artifact, knowledge, domain_tree=None, scenario_definition=None,
                 technical_flow=None, source_map=None, business_rules=None):
    if knowledge.get('model_profile') != PROFILE:
        return ['model: profiled output requires profiled knowledge'] if artifact.get('model_profile') else []
    errors = []
    def fail(message):
        errors.append('model: ' + message)
    inputs = [artifact, domain_tree, scenario_definition, technical_flow, source_map, business_rules]
    for data in inputs:
        if data is not None and data.get('model_profile') != PROFILE:
            fail('all inputs must explicitly use ' + PROFILE)
    if errors:
        return errors
    entities = {e['id']: e for e in knowledge['entities']}
    claims = {c['id']: c for c in knowledge['claims']}
    evidence = {e['id']: e for e in knowledge['evidence']}
    snapshots = {s['id']: s for s in knowledge['sources']}
    unresolved = {cid for c in knowledge['conflicts'] if c['status'] == 'unresolved' for cid in c['claim_ids']}

    def support(c):
        return {s['evidence_id'] for s in c['support'] if s['role'] == 'supports'}

    for e in evidence.values():
        if e['source_type'] == 'INFERENCE' or e['inference']:
            fail(e['id'] + ': inference is not evidence')
        if e['source_ref'] != e['snapshot_id']:
            fail(e['id'] + ': source_ref must identify its snapshot')
        expected = dict(repository=e['repository'], file=e['file'],
                        symbol='.'.join(x for x in (e['class'], e['method']) if x) or None,
                        revision=e['version'], page=e['page'])
        if e['metadata'] != expected:
            fail(e['id'] + ': metadata disagrees with source locator')
        expected_support = {c['id'] for c in claims.values() if e['id'] in support(c)}
        if set(e['supports']) != expected_support:
            fail(e['id'] + ': supports must match claim support references')

    def basis_ok(cid, seen=frozenset()):
        if cid in seen or cid not in claims:
            return False
        c = claims[cid]
        if c['modality'] == 'runtime_observation':
            return False  # bounded cases cannot ground an inferred universal statement
        if c['knowledge_status'] not in {'CONFIRMED', 'INFERRED'} or cid in unresolved:
            return False
        if c['inference']:
            return bool(c['basis_claim_ids']) and all(basis_ok(b, seen | {cid}) for b in c['basis_claim_ids'])
        return any(evidence.get(eid, {}).get('source_type') in PRIMARY for eid in support(c))

    for c in claims.values():
        status = c['knowledge_status']
        direct = [evidence[eid] for eid in support(c) if eid in evidence]
        if c['id'] in unresolved and status != 'CONFLICT':
            fail(c['id'] + ': unresolved conflict requires CONFLICT')
        if status == 'CONFLICT' and c['id'] not in unresolved:
            fail(c['id'] + ': CONFLICT requires unresolved conflict record')
        if status == 'CONFLICT' and not direct:
            fail(c['id'] + ': conflicting claim needs source evidence')
        if c['inference'] != (status == 'INFERRED'):
            fail(c['id'] + ': inference/status mismatch')
        if status in {'CONFIRMED', 'PARTIALLY_CONFIRMED'}:
            if not direct or not any(e['source_type'] in PRIMARY or runtime_root(c, e) for e in direct):
                fail(c['id'] + ': confirmed claim needs primary evidence')
            if c['validation_status'] != 'supported' or c['lifecycle_status'] != 'current':
                fail(c['id'] + ': confirmed claim must be supported/current')
        if c['inference']:
            if c['modality'] != 'inferred' or not c['inference_rationale'] or not c['basis_claim_ids'] or not basis_ok(c['id']):
                fail(c['id'] + ': inference requires an acyclic, supported basis and rationale')
        elif c['basis_claim_ids'] or c['inference_rationale'] is not None:
            fail(c['id'] + ': direct claim cannot carry inference bases/rationale')
        if status == 'UNKNOWN' and c['value'] is not None:
            fail(c['id'] + ': UNKNOWN value must be null')
        if status == 'UNKNOWN' and c['validation_status'] == 'supported':
            fail(c['id'] + ': UNKNOWN cannot be supported')
        # A contradictory primary source is retained as a conflict, never discarded.
        if any(s['role'] == 'contradicts' for s in c['support']) and status != 'CONFLICT':
            fail(c['id'] + ': contradictory evidence requires CONFLICT')

    # Only scalar predicates: several calls/states/rules are legitimate list members.
    scalar_predicates = {'preferred_name','business_goal','business_statement','business_rationale',
                         'business_action','business_result','condition','true_result','false_result'}
    scalar_groups = {}
    for c in claims.values():
        if c['predicate'] in scalar_predicates and c['lifecycle_status'] == 'current' and c['value'] is not None:
            key = (c['subject_id'], c['predicate'], c['context']['environment'])
            scalar_groups.setdefault(key, []).append(c)
    for rows in scalar_groups.values():
        for i, left in enumerate(rows):
            for right in rows[i+1:]:
                if left['value'] != right['value'] and not any(
                        conflict['status'] == 'unresolved' and {left['id'],right['id']} <= set(conflict['claim_ids'])
                        for conflict in knowledge['conflicts']):
                    fail(left['id'] + '/' + right['id'] + ': competing scalar claims require an explicit CONFLICT')

    def value_check(v, subject, predicate, business=False):
        label = subject + '/' + predicate
        cids, eids = set(v['claim_ids']), set(v['evidence_ids'])
        if not cids <= claims.keys() or not eids <= evidence.keys():
            fail(label + ': dangling claim/evidence reference')
        supporting = set().union(*(support(claims[c]) for c in cids if c in claims))
        if not supporting <= eids:
            fail(label + ': evidence omits claim support')
        for cid in cids & claims.keys():
            c = claims[cid]
            if c['subject_id'] != subject or c['predicate'] != predicate:
                fail(label + ': claim subject/predicate mismatch')
            if c['knowledge_status'] != v['status']:
                fail(label + ': claim knowledge status must be preserved')
            if v['status'] != 'CONFLICT' and c['value'] != v['value']:
                fail(label + ': claim value mismatch')
            if business and v['status'] in {'CONFIRMED', 'PARTIALLY_CONFIRMED'} and (
                    c['inference'] or c['modality'] not in BUSINESS_MODALITIES):
                fail(label + ': explicit source-stated business claim required')
        if v['status'] in {'CONFIRMED', 'PARTIALLY_CONFIRMED'} and (not cids or not eids):
            fail(label + ': confirmed value needs claims/evidence')
        if v['status'] == 'CONFLICT' and (not cids or not cids <= unresolved):
            fail(label + ': conflict value must reference unresolved claims')
        if business and v['status'] == 'INFERRED':
            fail(label + ': inferred business meaning must remain an unconfirmed candidate')

    def unresolved_value(v, subject, label):
        if v['status'] in {'UNKNOWN','PARTIALLY_CONFIRMED','CONFLICT'} and not any(
                g['status'] == 'open' and subject in g['affected_ids'] for g in knowledge['gaps']):
            fail(label + ': unresolved business value requires an affected open Gap')

    identities = {}
    for entity in entities.values():
        key = (entity['type'], entity['identity_key'])
        if key in identities:
            fail(entity['id'] + ': duplicate entity identity ' + identities[key])
        identities[key] = entity['id']
        value_check(entity['preferred_name'], entity['id'], 'preferred_name', business=True)

    def candidates(rows):
        for row in rows:
            if row['entity_ref'] not in entities or row['source_ref'] not in snapshots:
                fail('terminology candidate: dangling entity/source reference')
            for eid in row['evidence_ids']:
                e = evidence.get(eid, {})
                if e.get('source_ref') != row['source_ref'] or e.get('source_type') != row['source_type']:
                    fail('terminology candidate: evidence/source mismatch')
    for entity in entities.values():
        candidates(entity['terminology_candidates'])

    if kind in {'domain-tree', 'scenario-definition'}:
        rows = artifact['nodes'] if kind == 'domain-tree' else [artifact]
        for row in rows:
            eid = row.get('scenario_id', row['id'])
            entity = entities.get(eid, {})
            if any(row[field] != entity.get(field) for field in TERM_FIELDS):
                fail(eid + ': terminology must match shared entity registry')
            if kind == 'domain-tree' and row['scope_ref'] != knowledge['scope']['id']:
                fail(eid + ': node scope mismatch')
            if not set(row['evidence']) <= evidence.keys():
                fail(eid + ': dangling evidence reference')
            cids = [cid for refs in row['attribute_claims'].values() for cid in refs]
            required = set().union(*(support(claims[c]) for c in cids if c in claims))
            if not required <= set(row['evidence']):
                fail(eid + ': domain evidence omits field support')
            if row['preferred_name']['status'] == 'CONFIRMED' and row['name'] != row['preferred_name']['value']:
                fail(eid + ': name projection differs from preferred name')
            if row['preferred_name']['status'] != 'CONFIRMED' and 'name' not in row['proposed_fields']:
                fail(eid + ': unconfirmed name must remain a proposed navigation label')
            if row['business_goal'] is not None:
                for cid in row['attribute_claims'].get('business_goal', []):
                    c = claims.get(cid, {})
                    if c.get('inference') or c.get('modality') not in BUSINESS_MODALITIES:
                        fail(eid + ': business goal requires source-stated meaning')
    if kind == 'source-map':
        candidates(artifact['terminology_candidates'])
        for row in artifact['terminology_candidates']:
            registered = entities.get(row['entity_ref'], {}).get('terminology_candidates', [])
            if row not in registered:
                fail('source-map: terminology candidate missing from entity registry')

    flow = artifact if kind == 'technical-flow' else technical_flow
    accepted_map = artifact if kind == 'source-map' else source_map
    accepted = {s['id']: s for s in (accepted_map or {}).get('sources', [])}
    technical_steps = {s['id']: s for s in (flow or {}).get('nodes', [])}
    def technical_check(rep, implementations, refs, sources, label):
        if (set(rep['implementation_refs']) != set(implementations) or
                set(rep['technical_step_refs']) != set(refs) or set(rep['source_ids']) != set(sources)):
            fail(label + ': technical representation disagrees with traceability projection')
        if not set(rep['source_ids']) <= accepted.keys() or not set(rep['technical_step_refs']) <= technical_steps.keys():
            fail(label + ': dangling technical/source reference')
        for iid in rep['implementation_refs']:
            if entities.get(iid, {}).get('type') not in {'CodeComponent', 'ConfigRule', 'ApiOperation'}:
                fail(label + ': invalid implementation reference')
            if not any(s['component_id'] == iid for s in technical_steps.values()):
                fail(label + ': implementation absent from technical model')

    def accepted_value(v, label):
        allowed = {s['snapshot_ref'] for s in accepted.values()}
        if not all(evidence.get(e, {}).get('snapshot_id') in allowed for e in v['evidence_ids']):
            fail(label + ': structured claim evidence outside accepted sources')

    if kind == 'technical-flow':
        for node in artifact['nodes']:
            step = technical_steps.get(node['id'], {})
            technical_check(node['technical_implementation'], [step.get('component_id')], [node['id']], step.get('source_ids', []), node['id'])
            value_check(node['business_meaning'], node['id'], 'business_meaning', business=True)
            unresolved_value(node['business_meaning'], node['id'], node['id'])
            accepted_value(node['business_meaning'], node['id'])
            if not set(node['business_meaning']['evidence_ids']) <= set(node['evidence']):
                fail(node['id'] + ': business evidence omitted from node')
            for iid in node['integrations']:
                if entities.get(iid, {}).get('type') != 'Integration':
                    fail(node['id'] + ': invalid integration reference')
                matching = [c for c in claims.values() if c['subject_id'] == node['id'] and c['predicate'] == 'integrations'
                            and c['value'] == iid and c['knowledge_status'] == 'CONFIRMED']
                if not matching:
                    fail(node['id'] + ': integration requires a matching confirmed claim')
            if node['business_meaning']['status'] != 'CONFIRMED' and artifact['coverage']['status'] == 'complete':
                fail(node['id'] + ': unconfirmed meaning requires partial coverage')
    if kind == 'business-rules':
        for rule in artifact['rules']:
            refs = [s['id'] for s in technical_steps.values() if s['component_id'] in rule['implementation']]
            technical_check(rule['technical_implementation'], rule['implementation'], refs, rule['source_ids'], rule['id'])
            for field, predicate, business in [('business_statement', 'business_statement', True),
                    ('technical_condition', 'condition', False), ('business_rationale', 'business_rationale', True)]:
                value_check(rule[field], rule['id'], predicate, business)
                if business:
                    unresolved_value(rule[field], rule['id'], rule['id']+'/'+field)
                accepted_value(rule[field], rule['id'])
                if not set(rule[field]['evidence_ids']) <= set(rule['evidence']):
                    fail(rule['id'] + ': structured evidence omitted from rule')
            if rule['technical_condition']['value'] != (None if rule['condition'] == 'UNKNOWN' else rule['condition']):
                fail(rule['id'] + ': condition projection mismatch')
            if rule['rule_kind'] in {'business_rule','eligibility'} and rule['business_statement']['status'] != 'CONFIRMED':
                fail(rule['id'] + ': business classification requires confirmed business statement')
    if kind == 'scenario':
        rules = {r['id']: r for r in (business_rules or {}).get('rules', [])}
        for step in artifact['steps']:
            technical_check(step['technical_implementation'], step['implementation'], step['technical_step_refs'], step['source_ids'], step['id'])
            for field in ['business_action', 'business_result']:
                value_check(step[field], step['id'], field, business=True)
                unresolved_value(step[field], step['id'], step['id']+'/'+field)
                accepted_value(step[field], step['id'])
                if not set(step[field]['evidence_ids']) <= set(step['evidence']):
                    fail(step['id'] + ': structured evidence omitted from scenario step')
            if step['state_transition'] != {'from':step['state_before'], 'to':step['state_after']}:
                fail(step['id'] + ': state transition projection mismatch')
            statuses = {step[f]['status'] for f in ('business_action', 'business_result')}
            if step['unknown_fields']:
                statuses.add('UNKNOWN')
            if step['conflict_ids']:
                statuses.add('CONFLICT')
            expected = next((s for s in ('CONFLICT','UNKNOWN','INFERRED','PARTIALLY_CONFIRMED') if s in statuses), 'CONFIRMED')
            if step['knowledge_status'] != expected:
                fail(step['id'] + ': step status hides unresolved business knowledge')
            if expected != 'CONFIRMED' and artifact['coverage']['status'] == 'complete':
                fail(step['id'] + ': unconfirmed step requires partial coverage')
            for rid in step['evaluated_rules']:
                if rid in rules and not set(rules[rid]['implementation']) & set(step['implementation']):
                    fail(step['id'] + ': evaluated rule lacks linked technical implementation')
    return errors


def increment_errors(previous, current):
    """Compare actual upstream packages; never infer continuity from a display name."""
    errors = []
    if previous.get('model_profile') != PROFILE or current.get('model_profile') != PROFILE:
        return ['increment: both packages must use ' + PROFILE]
    if previous['package_id'] != current['package_id'] or current['revision'] < previous['revision']:
        errors.append('increment: package identity/revision changed')
    if previous['scope'] != current['scope']:
        errors.append('increment: scope changed; explicit Domain Decomposer revision is required')
    if previous['revision'] == current['revision'] and previous != current:
        errors.append('increment: changed knowledge requires a new revision')
    for group in ('entities','evidence','sources','claims','relations','gaps','conflicts',
                  'runtime_traces','runtime_confirmations'):
        old = {r['id']:r for r in previous.get(group, [])}
        new = {r['id']:r for r in current.get(group, [])}
        for rid, row in old.items():
            if rid not in new:
                errors.append(f'increment: {group} lost ID {rid}')
                continue
            now = new[rid]
            if group in {'sources','relations','runtime_traces','runtime_confirmations'} and row != now:
                errors.append(f'increment: immutable {group} changed {rid}')
            if group == 'evidence' and (any(row[f] != now[f] for f in row if f != 'supports') or
                                       not set(row['supports']) <= set(now['supports'])):
                errors.append(f'increment: immutable evidence changed or support lost {rid}')
            if group == 'claims':
                if any(row[f] != now[f] for f in ('subject_id','predicate','value','context','inference','basis_claim_ids')):
                    errors.append(f'increment: claim identity/value changed {rid}; retain it and add a new claim')
                if not all(s in now['support'] for s in row['support']):
                    errors.append(f'increment: claim support lost {rid}')
                if row['knowledge_status'] != now['knowledge_status']:
                    if row['knowledge_status'] == 'CONFLICT':
                        errors.append(f'increment: CONFLICT cannot be resolved automatically {rid}')
                    elif now['knowledge_status'] in {'CONFIRMED','PARTIALLY_CONFIRMED'}:
                        old_support = {s['evidence_id'] for s in row['support'] if s['role']=='supports'}
                        fresh = {s['evidence_id'] for s in now['support'] if s['role']=='supports'} - old_support
                        sources = {e['id']:e for e in current['evidence']}
                        if not any(sources.get(e, {}).get('source_type') in PRIMARY for e in fresh):
                            errors.append(f'increment: status upgrade needs new primary support {rid}')
            if group == 'entities':
                if row['type'] != now['type'] or row['identity_key'] != now['identity_key']:
                    errors.append(f'increment: entity identity changed {rid}')
                for field in ('technical_aliases','search_aliases','terminology_candidates'):
                    if not all(v in now[field] for v in row[field]):
                        errors.append(f'increment: {field} lost for {rid}')
                before, after = row['preferred_name'], now['preferred_name']
                if before != after and after['status'] in {'CONFIRMED','PARTIALLY_CONFIRMED'}:
                    if not set(after['evidence_ids']) - set(before['evidence_ids']):
                        errors.append(f'increment: preferred term promotion requires new evidence {rid}')
                if before['status'] == 'CONFLICT' and after['status'] != 'CONFLICT':
                    errors.append(f'increment: terminology conflict cannot be resolved automatically {rid}')
            if group == 'conflicts' and row['status'] == 'unresolved' and now['status'] != 'unresolved':
                errors.append(f'increment: conflict cannot be resolved automatically {rid}')
    return errors
