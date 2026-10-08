"""Offline runtime observation invariants. Never queries OpenSearch or infers business rules."""
from datetime import datetime
import hashlib

GAP_REASONS = {'NOT_CHECKED':'RUNTIME_UNVERIFIED', 'VARIABLE':'RUNTIME_VARIABILITY',
               'STATIC_RUNTIME_CONFLICT':'STATIC_RUNTIME_CONFLICT', 'INSUFFICIENT_SAMPLE':'INSUFFICIENT_RUNTIME_SAMPLE'}


def case_reference(value, kind='case'):
    """Persist a one-way reference, not a production identifier or query credential."""
    if kind not in {'case','correlation','request','process'}:
        raise ValueError('unsupported reference kind')
    return kind + ':' + hashlib.sha256(value.encode('utf-8')).hexdigest()


def moment(value):
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError('runtime timestamps require timezone')
    return result


def sequence(trace, check):
    return [row['event'] for row in trace['timeline'] if row['event'] in check['event_filter']]


def assessment(check, traces):
    """Mechanical comparability/sample assessment; OBSERVED is not semantic approval."""
    result = dict(confirmation_ref=check['id'], result='NOT_CHECKED', sample_size=0,
                  trace_refs=list(check['trace_refs']))
    if not check['material_ambiguity']:
        return dict(result, result='NOT_REQUIRED', trace_refs=[])
    if check['capability'] != 'available' or not check['trace_refs']:
        return result
    selected = [traces.get(t) for t in check['trace_refs']]
    if any(t is None for t in selected):
        return result
    try:
        for t in selected:
            if (t['scenario_id'] != check['scenario_id'] or t['environment'] != check['environment'] or
                not t['application_version'] or t['application_version'] != check['application_version'] or
                not t['complete'] or t['outcome'] != check['cohort'] or t['ordering_basis'] != 'correlated_events' or
                not moment(check['time_from']) <= moment(t['time_from']) <= moment(t['time_to']) <= moment(check['time_to']) or
                len(sequence(t,check)) < 2):
                return result
    except (ValueError, TypeError):
        return result
    cases = {t['identifiers']['case_ref'] for t in selected}
    result['sample_size'] = len(cases)
    if len(cases) != len(selected):
        return dict(result, result='INSUFFICIENT_SAMPLE')  # duplicate queries are not new examples
    signatures = {tuple(sequence(t,check)) for t in selected}
    if len(signatures) > 1:
        return dict(result, result='VARIABLE')
    if check['static_sequences'] and next(iter(signatures)) not in {tuple(s) for s in check['static_sequences']}:
        return dict(result, result='STATIC_RUNTIME_CONFLICT')
    if len(cases) < check['minimum_sample_size']:
        return dict(result, result='INSUFFICIENT_SAMPLE')
    return dict(result, result='OBSERVED')


def runtime_root(claim, evidence):
    return (claim.get('modality') == 'runtime_observation' and isinstance(claim.get('value'),dict) and
            claim['value'].get('extent') == 'observed_cases' and evidence.get('source_type') == 'OPENSEARCH')


def runtime_errors(knowledge, technical=None, artifact=None):
    """Caller validates shared schemas first. Keep static primary roots unchanged."""
    errors = []
    def fail(message):
        errors.append('runtime: ' + message)
    entities = {e['id']:e for e in knowledge['entities']}
    evidence = {e['id']:e for e in knowledge['evidence']}
    claims = {c['id']:c for c in knowledge['claims']}
    snapshots = {s['id']:s for s in knowledge['sources']}
    traces = {t['id']:t for t in knowledge.get('runtime_traces',[])}
    checks = {c['id']:c for c in knowledge.get('runtime_confirmations',[])}
    if (traces or checks or any(e['source_type'] == 'OPENSEARCH' for e in evidence.values())) and \
            knowledge.get('model_profile') != 'scoped-knowledge-v1':
        return ['runtime: observations require the existing scoped-knowledge-v1 profile']
    gaps = {g['id']:g for g in knowledge['gaps']}
    static_steps = {s['id'] for s in (technical or {}).get('nodes',[])}
    for name, index in (('runtime_traces',traces),('runtime_confirmations',checks)):
        if len(index) != len(knowledge.get(name,[])):
            fail('duplicate '+name+' IDs')
    for t in traces.values():
        if not any(t['id'] in c['trace_refs'] for c in checks.values()):
            fail(t['id']+': collected trace must be retained in a runtime assessment')
        if entities.get(t['scenario_id'],{}).get('type') != 'Scenario' or t['scenario_id'] not in knowledge['scope']['scenarios']:
            fail(t['id']+': scenario outside scope/registry')
        if t['environment'] not in knowledge['scope']['environments']:
            fail(t['id']+': environment outside explicit scope')
        try:
            start,end = moment(t['time_from']),moment(t['time_to'])
            if start > end:
                fail(t['id']+': reversed time range')
            times = [moment(r['timestamp']) for r in t['timeline']]
            if any(not start <= v <= end for v in times) or times != sorted(times):
                fail(t['id']+': timeline outside range or unordered')
        except (ValueError,TypeError):
            fail(t['id']+': invalid timezone/range')
        if [r['order'] for r in t['timeline']] != list(range(1,len(t['timeline'])+1)):
            fail(t['id']+': timeline order must be contiguous')
        used = set()
        for row in t['timeline']:
            if row['technical_step_ref'] not in entities or static_steps and row['technical_step_ref'] not in static_steps:
                fail(t['id']+': dangling technical step '+row['technical_step_ref'])
            if not set(row['technical_refs']) <= entities.keys():
                fail(t['id']+': dangling technical entity reference')
            if not row['evidence_ids']:
                fail(t['id']+': every event requires captured evidence')
            if row['evidence_ids'] and not any(row['event'] in (evidence.get(eid, {}).get('excerpt') or '') and
                    row['timestamp'] in (evidence.get(eid, {}).get('excerpt') or '') for eid in row['evidence_ids']):
                fail(t['id']+': event marker/timestamp absent from captured evidence')
            used.update(row['evidence_ids'])
        if used != set(t['evidence_ids']):
            fail(t['id']+': timeline/evidence projection mismatch')
        for eid in t['evidence_ids']:
            e = evidence.get(eid,{})
            r = e.get('runtime',{})
            if e.get('source_type') != 'OPENSEARCH' or not r:
                fail(t['id']+': event evidence must be OPENSEARCH')
                continue
            if (r['environment'] != t['environment'] or r['case_ref'] != t['identifiers']['case_ref'] or
                r['application_version'] != t['application_version']):
                fail(t['id']+': evidence case/environment/version mismatch')
            try:
                if not moment(r['time_from']) <= moment(t['time_from']) <= moment(t['time_to']) <= moment(r['time_to']):
                    fail(t['id']+': query period does not cover trace')
            except (ValueError,TypeError):
                fail(t['id']+': invalid query period')
    for e in evidence.values():
        if e['source_type'] != 'OPENSEARCH':
            continue
        snap = snapshots.get(e['snapshot_id'],{})
        if snap.get('adapter') != 'opensearch' or e['inference']:
            fail(e['id']+': invalid runtime snapshot/inference')
        if not any(e['id'] in t['evidence_ids'] for t in traces.values()):
            fail(e['id']+': runtime evidence needs a normalized trace')
    for c in checks.values():
        if entities.get(c['scenario_id'],{}).get('type') != 'Scenario' or c['scenario_id'] not in knowledge['scope']['scenarios']:
            fail(c['id']+': scenario outside scope')
        if not set(c['trace_refs']) <= traces.keys() or not set(c['claim_ids']+c['static_claim_ids']) <= claims.keys():
            fail(c['id']+': dangling Trace/Claim refs')
        if not set(c['gap_ids']) <= gaps.keys():
            fail(c['id']+': dangling Gap refs')
        for cid in c['claim_ids']:
            claim = claims.get(cid, {})
            if claim.get('modality') != 'runtime_observation' or not isinstance(claim.get('value'), dict) or \
                    claim['value'].get('confirmation_ref') != c['id'] or claim.get('subject_id') != c['scenario_id']:
                fail(c['id']+': claim_ids must reference its qualified runtime observations')
        if not c['material_ambiguity'] and (c['trace_refs'] or c['claim_ids']):
            fail(c['id']+': runtime lookup is not justified without material ambiguity')
        if any(evidence.get(eid, {}).get('source_type') not in {'CODE','CONFIG','TEST','CONFLUENCE','GIT'}
               for eid in c['static_review_evidence_ids']):
            fail(c['id']+': static review must precede runtime lookup')
        try:
            if moment(c['time_from']) > moment(c['time_to']):
                fail(c['id']+': reversed observation period')
        except (ValueError,TypeError):
            fail(c['id']+': invalid observation period')
        for path in c['static_sequences']:
            if not any(claims.get(cid,{}).get('value') == path and
                       claims[cid]['subject_id'] == c['scenario_id'] and
                       claims[cid]['lifecycle_status'] == 'current' and
                       any(evidence.get(s['evidence_id'],{}).get('source_type') in {'CODE','CONFIG','TEST','CONFLUENCE','GIT'}
                           and s['role'] == 'supports' for s in claims[cid]['support']) for cid in c['static_claim_ids'] if cid in claims):
                fail(c['id']+': static comparison path needs its own static Claim')
        result = assessment(c,traces)['result']
        if result != c['status']:
            fail(c['id']+': runtime assessment/status mismatch')
        reason = GAP_REASONS.get(result)
        if reason and not any(gaps.get(g,{}).get('reason') == reason and gaps[g]['status']=='open' and
                              c['id'] in gaps[g]['affected_ids'] for g in c['gap_ids']):
            fail(c['id']+': '+reason+' requires an open Gap')
    for claim in claims.values():
        support = [evidence.get(s['evidence_id'],{}) for s in claim['support'] if s['role']=='supports']
        has_runtime = any(e.get('source_type')=='OPENSEARCH' for e in support)
        if has_runtime and not all(runtime_root(claim,e) for e in support if e.get('source_type')=='OPENSEARCH'):
            fail(claim['id']+': logs may support only qualified runtime observations; use context for static/business claims')
        if claim['modality'] != 'runtime_observation':
            continue
        v = claim['value']
        if not isinstance(v, dict) or 'confirmation_ref' not in v:
            if has_runtime:
                fail(claim['id']+': OPENSEARCH observation requires a normalized confirmation value')
            continue  # retain legacy static-backed runtime_observation claims
        check = checks.get(v['confirmation_ref'])
        if not check or claim['id'] not in check['claim_ids'] or claim['subject_id'] != check['scenario_id']:
            fail(claim['id']+': observation must bind its Scenario/confirmation')
            continue
        if claim['context']['environment'] != check['environment']:
            fail(claim['id']+': runtime Claim environment differs from its confirmation')
        if claim['predicate'] != 'observed_runtime_sequence' or claim['text'] != v['statement']:
            fail(claim['id']+': runtime observation cannot supply another predicate/rationale or raw-log prose')
        selected = [traces[t] for t in check['trace_refs'] if t in traces]
        expected = {eid for t in selected for eid in t['evidence_ids']}
        if {e.get('id') for e in support if e.get('source_type')=='OPENSEARCH'} != expected or not expected:
            fail(claim['id']+': observation must preserve all compared trace evidence')
        if any(sequence(t,check) != v['sequence'] for t in selected):
            fail(claim['id']+': claimed sequence differs from observed cases')
        if claim.get('knowledge_status') == 'CONFIRMED' and check['status'] != 'OBSERVED':
            fail(claim['id']+': only a comparable sufficient sample can confirm current observed behaviour')
        if check['status'] not in {'OBSERVED','INSUFFICIENT_SAMPLE'}:
            fail(claim['id']+': variability/conflict must stay separate, not a selected sequence')
    if artifact:
        for cid in artifact.get('runtime_confirmation_refs',[]):
            if cid not in checks or checks[cid]['scenario_id'] != artifact.get('scenario_id'):
                fail('artifact: dangling/cross-scenario runtime confirmation')
        for rule in artifact.get('rules',[]):
            for tid in rule.get('runtime_examples',[]):
                if tid not in traces or traces[tid]['scenario_id'] != artifact.get('scenario_id'):
                    fail(rule['id']+': invalid runtime example')
    return list(dict.fromkeys(errors))


def runtime_review_errors(knowledge, report, gap_output=None):
    """Recompute sample diagnostics and require separate human/agent semantic review."""
    checks = {c['id']: c for c in knowledge.get('runtime_confirmations', [])}
    traces = {t['id']: t for t in knowledge.get('runtime_traces', [])}
    reviews = {r['confirmation_ref']: r for r in report.get('runtime_reviews', [])}
    errors = []
    if set(reviews) != set(checks) or len(reviews) != len(report.get('runtime_reviews', [])):
        errors.append('runtime review: every confirmation requires exactly one assessment')
    for cid, check in checks.items():
        review = reviews.get(cid, {})
        expected = assessment(check, traces)
        if any(review.get(key) != value for key, value in expected.items()):
            errors.append(cid + ': stale or incorrect runtime review/sample')
        if not set(check['gap_ids']) <= set(report['gap_ids']):
            errors.append(cid + ': runtime Gap omitted from validation report')
        if gap_output is not None:
            gaps = {g['id']: g for g in gap_output['gaps']}
            reason = GAP_REASONS.get(expected['result'])
            if reason and not any(gaps.get(g, {}).get('reason') == reason and
                    gaps[g]['status'] == 'open' and cid in gaps[g]['affected_ids'] for g in check['gap_ids']):
                errors.append(cid + ': unresolved runtime Gap cannot be hidden or closed')
    claims = {c['id']: c for c in knowledge['claims']}
    for row in report['claim_reviews']:
        claim = claims.get(row['claim_id'], {})
        if claim.get('modality') != 'runtime_observation' or row['status'] not in {'CONFIRMED','PARTIALLY_CONFIRMED'}:
            continue
        if not isinstance(claim.get('value'), dict) or 'confirmation_ref' not in claim['value']:
            continue
        review = reviews.get(claim['value']['confirmation_ref'], {})
        if not review.get('reviewed') or review.get('result') not in {'OBSERVED','INSUFFICIENT_SAMPLE'}:
            errors.append(row['claim_id'] + ': runtime observation requires scoped semantic runtime review')
        if row['status'] == 'CONFIRMED' and review.get('result') != 'OBSERVED':
            errors.append(row['claim_id'] + ': limited sample cannot confirm current behaviour')
    return errors
