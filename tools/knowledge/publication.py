"""Publication impact metadata over existing structured facts; no source discovery."""
from collections import defaultdict

PUBLIC = 'PUBLICATION_RELEVANT'
INTERNAL = 'INTERNAL_RESEARCH'
UNASSESSED = 'UNASSESSED'


def records(data, key):
    value = data.get(key, []) if isinstance(data, dict) else []
    return [row for row in value if isinstance(row, dict)] if isinstance(value, list) else []


def impact_index(inputs):
    """Minimum visible dependencies, excluding implementation/technical-node ancestry.

    A technical node being mapped to a business step does not make every detail material.
    This index detects declared process fields, not semantic truth or completeness.
    """
    index = defaultdict(set)
    pairs = defaultdict(set)
    knowledge = inputs['knowledge']
    scenario = inputs.get('scenario', {})
    steps = {s['id']: s for s in records(scenario, 'steps') if isinstance(s.get('id'), str)}
    flows = [f for f in records(scenario, 'flows') if isinstance(f.get('id'), str) and f.get('type') in {'main', 'alternative', 'error'}]
    roles = defaultdict(set)
    edge_roles = defaultdict(set)
    claims = {c['id']: c for c in records(knowledge, 'claims') if isinstance(c.get('id'), str)}

    def bind(cids, aspects, *, competing=True):
        for cid in cids:
            index[cid].update(aspects)
            claim = claims.get(cid, {})
            if competing and claim:
                pairs[(claim.get('subject_id'), claim.get('predicate'))].update(aspects)

    for flow in flows:
        aspect = 'MAIN_FLOW' if flow['type'] == 'main' else 'ALTERNATIVE_OR_EXCEPTION_FLOW'
        index[flow['id']].add(aspect)
        bind(flow.get('type_claim_ids', []) + flow.get('condition_claim_ids', []), {aspect}, competing=False)
        refs = flow.get('step_refs', [])
        for sid in refs:
            roles[sid].add(aspect)
        for pair in zip(refs, refs[1:]):
            edge_roles[pair].add(aspect)
        if flow.get('branch_from') and refs:
            edge_roles[(flow['branch_from'], refs[0])].add(aspect)

    for sid, step in steps.items():
        if not roles[sid]:
            continue
        field_roles = {'kind': roles[sid], 'actor': roles[sid], 'action': roles[sid],
                       'business_meaning': roles[sid], 'system_behavior': roles[sid],
                       'state_before': {'STATE_TRANSITION'}, 'state_after': {'STATE_TRANSITION'},
                       'user_result': {'BUSINESS_RESULT'}, 'business_action': roles[sid],
                       'business_result': {'BUSINESS_RESULT'}}
        for field, aspects in field_roles.items():
            bind(step.get('attribute_claims', {}).get(field, []), aspects)
            value = step.get(field)
            if isinstance(value, dict):
                bind(value.get('claim_ids', []), aspects)
                if value.get('status') != 'CONFIRMED':
                    index[sid].update(aspects)
            if field in step.get('unknown_fields', []):
                index[sid].update(aspects)
        for state in (step.get('state_before'), step.get('state_after')):
            if state:
                index[state].add('STATE_TRANSITION')

    for edge in records(scenario, 'transitions'):
        aspects = edge_roles[(edge.get('from_step'), edge.get('to_step'))]
        if edge.get('kind') == 'retry' and not aspects:
            aspects = roles[edge.get('from_step')] & roles[edge.get('to_step')]
        if isinstance(edge.get('id'), str):
            index[edge['id']].update(aspects)
        bind(edge.get('claim_ids', []), aspects)
        if edge.get('kind') == 'unresolved':
            for gid in edge.get('gap_ids', []):
                index[gid].update(aspects)

    used_rules = {rid for step in steps.values() if roles[step['id']] for rid in step.get('evaluated_rules', [])}
    for rule in records(inputs.get('business-rules', {}), 'rules'):
        if not isinstance(rule.get('id'), str):
            continue
        if rule['id'] not in used_rules and rule.get('rule_kind') not in {'business_rule', 'eligibility'}:
            continue
        for field, cids in rule.get('attribute_claims', {}).items():
            if field.split('/')[0] in {'condition', 'true_result', 'false_result', 'parameters', 'rule_statement'}:
                bind(cids, {'BUSINESS_RULE'})
        for field in ('business_statement', 'technical_condition'):
            value = rule.get(field, {})
            if isinstance(value, dict):
                bind(value.get('claim_ids', []), {'BUSINESS_RULE'})
        if set(rule.get('unknown_fields', [])) & {'condition', 'true_result', 'false_result'}:
            index[rule['id']].add('BUSINESS_RULE')

    definition = inputs.get('scenario-definition', {})
    for field, cids in definition.get('attribute_claims', {}).items():
        if field.split('/')[0] in {'business_goal', 'trigger', 'entry_state', 'expected_outcomes', 'actors'}:
            bind(cids, {'MAIN_FLOW'})
    if scenario.get('main_flow') is None or set(definition.get('unknown_fields', [])) & {'business_goal', 'trigger', 'entry_state', 'expected_outcomes'}:
        index[scenario.get('scenario_id')].add('MAIN_FLOW')

    entities = {e['id']: e for e in records(knowledge, 'entities') if isinstance(e.get('id'), str)}
    external = {'endpoint', 'route', 'http_method', 'request_contract', 'response_contract',
                'integration_role', 'integration_response', 'integration_error_behavior', 'api_error', 'api_status'}
    for claim in claims.values():
        if claim['id'] not in index:
            index[claim['id']].update(pairs[(claim.get('subject_id'), claim.get('predicate'))])
        if entities.get(claim.get('subject_id'), {}).get('type') in {'ApiOperation', 'Integration'} and claim.get('predicate') in external:
            index[claim['id']].add('EXTERNAL_CONTRACT')

    used_confirmations = set(scenario.get('runtime_confirmation_refs', []))
    for confirmation in records(knowledge, 'runtime_confirmations'):
        if confirmation.get('id') in used_confirmations:
            index[confirmation['id']].add('VERSION_ENVIRONMENT')
            bind(confirmation.get('claim_ids', []), {'VERSION_ENVIRONMENT'}, competing=False)
            for tid in confirmation.get('trace_refs', []):
                index[tid].add('VERSION_ENVIRONMENT')

    # Only evidence supporting an included process/contract assertion is material.
    evidence = {e['id']: e for e in records(knowledge, 'evidence') if isinstance(e.get('id'), str)}
    for cid, claim in claims.items():
        for support in records(claim, 'support'):
            if support.get('role') not in {'supports', 'contradicts'}:
                continue
            eid = support.get('evidence_id')
            index[eid].update(index[cid])
            snapshot = evidence.get(eid, {}).get('snapshot_id')
            if snapshot:
                index[snapshot].update(index[cid])
    return index


def minimum_impacts(item, inputs, index):
    result = defaultdict(set)
    refs = item.get('affected_ids', []) + item.get('target_refs', []) + item.get('claim_ids', [])
    for ref in [item['id']] + refs:
        for aspect in index.get(ref, set()):
            result[aspect].add(ref)
    if item.get('reason') == 'unknown_version' and result:
        result['VERSION_ENVIRONMENT'].update(refs)
    if item.get('kind') == 'scope_mismatch':
        result['VERSION_ENVIRONMENT'].add(inputs['knowledge']['scope']['id'])
    if item.get('kind') == 'unknown_state_transition':
        step_ids = {s['id'] for s in records(inputs.get('scenario', {}), 'steps') if isinstance(s.get('id'), str)}
        result['STATE_TRANSITION'].update(set(refs) & step_ids)
    return [{'aspect': aspect, 'target_refs': sorted(targets)} for aspect, targets in sorted(result.items()) if targets]


def candidate(impacts):
    return dict(classification=PUBLIC if impacts else UNASSESSED, reviewed=False, impacts=impacts,
                reason='Declared structured references can affect the process/contract; semantic relevance review is pending.'
                if impacts else 'Reader impact is not established; review before declaring an internal research gap.')


def publication_subset(report, gaps):
    return {'gap_ids': sorted(g['id'] for g in gaps['gaps'] if g['status'] == 'open' and g.get('publication_relevance', {}).get('classification') == PUBLIC),
            'finding_ids': sorted(f['id'] for f in report['findings'] if f['status'] == 'open' and f.get('publication_relevance', {}).get('classification') == PUBLIC)}


def refresh_publication_subset(report, gaps):
    """Derive IDs only. Never drop inventory, alter knowledge statuses or relax gate."""
    gaps['publication_subset'] = publication_subset(report, gaps)


def annotate_draft(report, gaps, inputs):
    index = impact_index(inputs)
    finding_impacts = {}
    for finding in report['findings']:
        finding_impacts[finding['id']] = minimum_impacts(finding, inputs, index)
        finding['publication_relevance'] = candidate(finding_impacts[finding['id']])
    linked = defaultdict(list)
    for link in gaps['finding_gap_links']:
        for gid in link['gap_ids']:
            linked[gid] += finding_impacts.get(link['finding_id'], [])
    for gap in gaps['gaps']:
        impacts = minimum_impacts(gap, inputs, index)
        merged = defaultdict(set)
        for impact in impacts + linked[gap['id']]:
            merged[impact['aspect']].update(impact['target_refs'])
        gap['publication_relevance'] = candidate([dict(aspect=a, target_refs=sorted(refs)) for a, refs in sorted(merged.items())])
    refresh_publication_subset(report, gaps)


def publication_errors(report, gaps, inputs):
    errors = []
    index = impact_index(inputs)
    known = {inputs['knowledge']['scope']['id']}
    for data in inputs.values():
        if not isinstance(data, dict):
            continue
        known.update(x for x in (data.get('id'), data.get('package_id')) if x)
        for values in data.values():
            if isinstance(values, list):
                known.update(row['id'] for row in values if isinstance(row, dict) and 'id' in row)
    finding_by_id = {f['id']: f for f in report['findings']}
    gap_by_id = {g['id']: g for g in gaps['gaps']}
    linked = defaultdict(set)
    for link in gaps['finding_gap_links']:
        linked[link['finding_id']].update(link['gap_ids'])
    expected = publication_subset(report, gaps)
    if gaps['publication_subset'] != expected:
        errors.append('publication: subset must exactly match open PUBLICATION_RELEVANT items')
    for original in records(inputs['knowledge'], 'gaps'):
        gap = gap_by_id.get(original['id'])
        if gap is None or not set(original['affected_ids']) <= set(gap['affected_ids']):
            errors.append('publication: input Gap/provenance was removed: ' + original['id'])
    for item in report['findings'] + gaps['gaps']:
        metadata = item['publication_relevance']
        minimum = minimum_impacts(item, inputs, index)
        actual_refs = {ref for impact in metadata['impacts'] for ref in impact['target_refs']}
        if not actual_refs <= known:
            errors.append('publication: unknown impact target refs: ' + item['id'])
        if minimum and (metadata['classification'] != PUBLIC or not any(
                impact['aspect'] == requirement['aspect'] and set(impact['target_refs']) & set(requirement['target_refs'])
                for impact in metadata['impacts'] for requirement in minimum)):
            errors.append('publication: material process/contract uncertainty cannot be hidden: ' + item['id'])
        if item['id'] in finding_by_id and item['status'] == 'open' and metadata['classification'] == PUBLIC:
            if not any(gap_by_id.get(gid, {}).get('publication_relevance', {}).get('classification') == PUBLIC for gid in linked[item['id']]):
                errors.append('publication: material finding needs a publication-relevant Gap link: ' + item['id'])
    conflicts = [c for c in report['comparisons'] if c['status'] in {'CONFLICT', 'UNRESOLVED'}]
    conflicts += [c for c in records(inputs['knowledge'], 'conflicts') if c['status'] == 'unresolved']
    for conflict in conflicts:
        cids = set(conflict['claim_ids'])
        if not any(index.get(cid) for cid in cids):
            continue
        visible = any(f['id'] in expected['finding_ids'] and cids & set(f['claim_ids']) for f in report['findings'])
        visible |= any(g['id'] in expected['gap_ids'] and cids & set(g['affected_ids']) for g in gaps['gaps'])
        if not visible:
            errors.append('publication: conflict affecting the process must remain visible: ' + conflict['id'])
    return errors
