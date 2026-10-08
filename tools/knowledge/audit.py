"""Conservative audit drafts and report contract checks. No semantic auto-confirmation."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import yaml

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from validate import ROOT_TYPES, load, schema_errors, validate
from model import PROFILE
from publication import annotate_draft, publication_errors, refresh_publication_subset
from runtime import GAP_REASONS, assessment, runtime_errors, runtime_review_errors, runtime_root

STATUSES = ('CONFIRMED', 'PARTIALLY_CONFIRMED', 'INFERRED', 'CONFLICT', 'UNKNOWN')
REQUIRED_INPUTS = {'knowledge', 'source-map', 'scenario', 'business-rules', 'technical-flow'}


def digest(data):
    encoded = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(',', ':'), default=str)
    return hashlib.sha256(encoded.encode('utf-8')).hexdigest()


def rows(data, key):
    value = data.get(key, []) if isinstance(data, dict) else []
    return [r for r in value if isinstance(r, dict)] if isinstance(value, list) else []


def by_id(records):
    return {r['id']: r for r in records if isinstance(r.get('id'), str) and r['id']}


def lookup(table, key):
    return table.get(key, {}) if isinstance(key, str) else {}


def source_check_errors(check, evidence, snapshot, label):
    """Shared source-review verification for audit and glossary projections."""
    errors = []
    def fail(message):
        errors.append(f'{label}: {message}')
    if any(check[key] != evidence.get(ekey) for key, ekey in
           [('source_location','source_location'), ('version','version'), ('snapshot_id','snapshot_id')]):
        fail('checked locator/version/snapshot mismatch')
    inspected = check['verification'] in {'reopened','snapshot_only','reasoning_checked'}
    if check['result'] in {'SUPPORTS','PARTIAL_SUPPORT','CONTRADICTS','IRRELEVANT'} and not inspected:
        fail('semantic verdict requires source inspection')
    if inspected and not check['quote']:
        fail('inspected check requires actual quote')
    if evidence.get('source_type') == 'INFERENCE':
        if inspected and check['verification'] != 'reasoning_checked':
            fail('inference is not a primary source')
    else:
        if inspected and (snapshot.get('availability') != 'available' or check['content_hash'] != snapshot.get('content_hash')):
            fail('inspected source hash/availability mismatch')
        if check['verification'] == 'reasoning_checked':
            fail('primary source cannot be checked by reasoning only')
        stored = [evidence.get('excerpt'), snapshot.get('excerpt')]
        if inspected and any(isinstance(v,str) and v for v in stored) and not any(
                check['quote'] in v for v in stored if isinstance(v,str) and check['quote']):
            fail('quote does not occur in the captured evidence/snapshot')
    return errors


def inventory(inputs):
    return sorted(by_id(rows(inputs['knowledge'], 'claims')))


def manifest(inputs):
    result = []
    for kind, data in sorted(inputs.items()):
        ident = data.get('package_id' if kind == 'knowledge' else 'id') if isinstance(data, dict) else None
        result.append({'kind': kind, 'id': ident, 'content_hash': digest(data)})
    return result


def mechanical_errors(inputs):
    result = []
    for kind, data in inputs.items():
        result += schema_errors('knowledge-package' if kind == 'knowledge' else kind, data)
    k = inputs['knowledge']
    expected = {'id': k.get('package_id'), 'revision': k.get('revision')}
    scope = k.get('scope', {}).get('id')
    for kind, data in inputs.items():
        if kind != 'knowledge' and isinstance(data, dict) and (
                data.get('package_ref') != expected or data.get('scope_ref') != scope):
            result.append(f'{kind}: scope/package revision mismatch')
    for group in ('claims', 'entities', 'evidence', 'sources', 'gaps', 'conflicts'):
        items = rows(k, group)
        raw_items = k.get(group)
        if not isinstance(raw_items, list) or len(raw_items) != len(by_id(items)):
            result.append(f'knowledge/{group}: missing or duplicate IDs')
    if not result and {'domain-tree', 'scenario-definition', 'source-map'} <= set(inputs):
        result += validate('scenario', inputs['scenario'], k, inputs['domain-tree'],
                           inputs['scenario-definition'], inputs['technical-flow'],
                           inputs['source-map'], inputs['business-rules'])
    elif not result:
        result += runtime_errors(k, inputs.get('technical-flow'), inputs.get('scenario'))
    return list(dict.fromkeys(result))


def calculate_summary(report, gaps):
    counts = {status: 0 for status in STATUSES}
    for row in report['claim_reviews']:
        counts[row['status']] += 1
    reviewed = sum(row['reviewed'] for row in report['claim_reviews'])
    complete = (len(report['claim_reviews']) == len(report['claim_inventory']) == reviewed
                and not any('missing or duplicate IDs' in e for e in report['mechanical_errors']))
    blocked = (not complete or bool(report['mechanical_errors']) or bool(report['limitations']) or
               any(r['status'] != 'CONFIRMED' for r in report['claim_reviews']) or
               any(f['blocking'] and f['status'] == 'open' for f in report['findings']) or
               any(g['status'] == 'open' for g in gaps['gaps']) or
               any(c['status'] in {'CONFLICT', 'UNRESOLVED'} for c in report['comparisons']) or
               any(not r['reviewed'] and r['result'] != 'NOT_REQUIRED' for r in report.get('runtime_reviews', [])) or
               any(item['status'] == 'open' and not item.get('publication_relevance', {}).get('reviewed', False)
                   for item in report['findings'] + gaps['gaps']))
    return {'total_claims': len(report['claim_inventory']), 'reviewed_claims': reviewed,
            'counts': counts, 'review_status': 'complete' if complete else 'partial',
            'publication_gate': 'blocked' if blocked else 'passed'}


def draft(inputs):
    if not REQUIRED_INPUTS <= set(inputs):
        raise ValueError('knowledge, source-map, scenario, business-rules and technical-flow are required')
    k = inputs['knowledge']
    if not isinstance(k, dict) or not isinstance(k.get('package_id'), str) or not isinstance(k.get('revision'), int) or not isinstance(k.get('scope'), dict) or not isinstance(k['scope'].get('id'), str):
        raise ValueError('Cannot identify package/scope; fix input identity before creating an audit')
    claims, evidence, snapshots = (by_id(rows(k, name)) for name in ('claims', 'evidence', 'sources'))
    known = set().union(*(set(by_id(rows(k, name))) for name in
                        ('claims', 'evidence', 'sources', 'entities', 'relations', 'gaps', 'conflicts',
                         'runtime_traces', 'runtime_confirmations')))
    common = {'schema_version': '1.0', 'scope_ref': k['scope']['id'],
              'package_ref': {'id': k['package_id'], 'revision': k['revision']}}
    report = dict(common, id=f'validation:{k["scope"]["id"]}', inputs=manifest(inputs),
                  claim_inventory=inventory(inputs), claim_reviews=[], comparisons=[], findings=[],
                  mechanical_errors=mechanical_errors(inputs), summary={}, gap_ids=[], limitations=[])
    gap_output = dict(common, id=f'gaps:{k["scope"]["id"]}', report_ref=report['id'],
                      gaps=[dict(g) for g in rows(k, 'gaps')], finding_gap_links=[])
    conflict_index = by_id(rows(k, 'conflicts'))
    def finding(kind, target_refs, claim_ids, eids, reason, action, gap_reason='unverified', verification='observed_structure'):
        fid = 'finding:' + digest([kind, target_refs, claim_ids, reason])[:20]
        record = {'id': fid, 'kind': kind, 'target_refs': target_refs,
                  'claim_ids': [c for c in claim_ids if c in claims], 'evidence_ids': [e for e in eids if e in evidence],
                  'verification': verification, 'reason': reason, 'required_action': action,
                  'blocking': True, 'status': 'open', 'resolution_claim_ids': []}
        report['findings'].append(record)
        affected = [target for target in target_refs + claim_ids if target in known]
        linked = [g['id'] for g in gap_output['gaps'] if g.get('reason') == gap_reason
                  and set(g.get('affected_ids', [])) & set(affected)]
        if not linked:
            gid = 'gap:audit:' + fid.split(':', 1)[1]
            gap_output['gaps'].append({'id': gid, 'reason': gap_reason,
                                      'question': reason, 'affected_ids': sorted(set(affected)),
                                      'next_action': action, 'status': 'open'})
            linked = [gid]
        gap_output['finding_gap_links'].append({'finding_id': fid, 'gap_ids': linked})
        return linked
    for error in report['mechanical_errors']:
        finding('structural_error', [error.split(':', 1)[0]], [], [], error, 'fix_contract')
    for cid in report['claim_inventory']:
        c = claims[cid]
        support = [s for s in rows(c, 'support') if s.get('role') == 'supports']
        grounded_inference = k.get('model_profile') == PROFILE and c.get('inference') and c.get('basis_claim_ids')
        missing = (not support and not grounded_inference) or any(not isinstance(s.get('evidence_id'), str) or s['evidence_id'] not in evidence for s in support)
        c_gaps = [g['id'] for g in gap_output['gaps'] if cid in g.get('affected_ids', []) or c.get('subject_id') in g.get('affected_ids', [])]
        if missing:
            c_gaps += finding('missing_evidence', [cid], [cid], [],
                              f'Claim {cid} has missing/unresolved supporting evidence in the supplied package.',
                              'add_evidence', 'missing_source')
        conflicts = [ident for ident, conflict in conflict_index.items() if
                     conflict.get('status') == 'unresolved' and cid in conflict.get('claim_ids', [])]
        report['claim_reviews'].append({'claim_id': cid, 'claim_hash': digest(c),
            'status': 'CONFLICT' if conflicts else 'UNKNOWN', 'reviewed': False,
            'reason': 'Recorded unresolved KB conflict; sources not rechecked.' if conflicts else 'Primary sources and semantic support have not been reviewed.',
            'source_checks': [], 'supported_parts': [], 'unsupported_parts': [], 'comparison_ids': [],
            'conflict_ids': conflicts, 'gap_ids': sorted(set(c_gaps)),
            'required_action': 'analyst_review' if conflicts else 'verify_source'})
    for conflict in conflict_index.values():
        if conflict.get('status') == 'unresolved':
            finding('unverified_claim', conflict.get('claim_ids', []), conflict.get('claim_ids', []), [],
                    'Existing KB conflict requires source/context reinspection; no resolution is inferred.',
                    'analyst_review', 'unverified', 'needs_source_verification')
    for eid, e in evidence.items():
        snap = lookup(snapshots, e.get('snapshot_id'))
        if e.get('source_type') != 'INFERENCE' and (not snap or snap.get('availability') != 'available'):
            cids = [cid for cid, c in claims.items() if any(s.get('evidence_id') == eid for s in rows(c, 'support'))]
            finding('source_unavailable', [eid], cids, [eid],
                    f'Evidence {eid} has no available snapshot in the supplied package.', 'verify_source', 'missing_source')
    for rule in rows(inputs['business-rules'], 'rules'):
        rationale = rule.get('business_rationale')
        if rationale == 'UNKNOWN' or isinstance(rationale, dict) and rationale.get('status') == 'UNKNOWN':
            finding('unknown_business_rationale', [rule.get('id', 'business-rules/rule')], [], rule.get('evidence', []),
                    'Business rationale is explicitly UNKNOWN in the supplied rule; no motive is inferred.', 'analyst_review', 'unknown_reason')
    scenario_steps = rows(inputs['scenario'], 'steps')
    for step in scenario_steps:
        ident = step.get('id', 'scenario/step')
        unknown = set(step.get('unknown_fields', []))
        if unknown & {'state_before', 'state_after'}:
            finding('unknown_state_transition', [ident], [], step.get('evidence', []),
                    'State before/after is unknown in the supplied scenario step.', 'verify_source', 'missing_link')
        if not step.get('implementation') or not step.get('technical_step_refs'):
            finding('scenario_without_implementation', [ident], [], step.get('evidence', []),
                    'Scenario step has no implementation/technical mapping in the supplied artifact; this does not prove code is absent.',
                    'trace_implementation', 'missing_link')
    tech_to_scenario = {}
    for step in scenario_steps:
        for tid in step.get('technical_step_refs', []):
            tech_to_scenario.setdefault(tid, set()).add(step.get('id'))
    scenario_pairs = {(e.get('from_step'), e.get('to_step')) for e in rows(inputs['scenario'], 'transitions') if e.get('kind') != 'unresolved'}
    branch_types = {'rule_branch', 'branch', 'true_branch', 'false_branch', 'error_branch', 'switch_case'}
    for rel in rows(inputs['technical-flow'], 'relations'):
        if rel.get('relation_type') not in branch_types:
            continue
        left, right = tech_to_scenario.get(rel.get('from_id'), set()), tech_to_scenario.get(rel.get('to_id'), set())
        if not any((a, b) in scenario_pairs for a in left for b in right):
            finding('unrepresented_technical_branch', [rel.get('from_id', ''), rel.get('to_id', '')],
                    rel.get('claim_ids', []), [], 'Declared technical branch has no explicit mapped scenario transition; inspect business relevance and grouping.',
                    'analyst_review', 'missing_link', 'needs_source_verification')
    for source in rows(inputs['source-map'], 'sources'):
        if source.get('artifact_kind') != 'configuration_key':
            continue
        documented = any(c.get('predicate') == 'config_behaviour_documentation' and
                         c.get('value') in (source.get('id'), source.get('symbol')) and
                         any(lookup(evidence, s.get('evidence_id')).get('source_type') == 'CONFLUENCE' and s.get('role') == 'supports'
                             for s in rows(c, 'support')) for c in claims.values())
        if not documented:
            finding('undocumented_config_behaviour', [source.get('symbol') or source['id']], [], source.get('evidence_ids', []),
                    'No explicit Confluence documentation link for this config behaviour exists in supplied KB; search before claiming documentation is absent.',
                    'verify_source', 'missing_link', 'needs_source_verification')
    def supporting_types(c):
        return {evidence[s.get('evidence_id')]['source_type'] for s in rows(c, 'support') if
                s.get('role') == 'supports' and isinstance(s.get('evidence_id'), str) and s.get('evidence_id') in evidence}
    for a, b in itertools.combinations(claims.values(), 2):
        if a.get('subject_id') != b.get('subject_id') or a.get('predicate') != b.get('predicate') or a.get('value') == b.get('value'):
            continue
        ta, tb = supporting_types(a), supporting_types(b)
        for kind, other in [('code_confluence', 'CONFLUENCE'), ('test_code', 'TEST')]:
            if not ((ta & {'CODE', 'CONFIG'} and other in tb) or (tb & {'CODE', 'CONFIG'} and other in ta)):
                continue
            eids = sorted({s['evidence_id'] for c in (a, b) for s in rows(c, 'support') if
                           s.get('role') == 'supports' and isinstance(s.get('evidence_id'), str) and s.get('evidence_id') in evidence})
            comp_id = 'comparison:' + digest([kind, a['id'], b['id']])[:20]
            report['comparisons'].append({'id': comp_id, 'kind': kind, 'claim_ids': [a['id'], b['id']],
                'evidence_ids': eids, 'reviewed': False, 'status': 'UNRESOLVED', 'context_comparison': 'unknown',
                'reason': 'Different values for the same structured predicate; modality/conditions/version must be compared before declaring conflict.',
                'required_action': 'analyst_review'})
            finding(kind + '_conflict', [a['subject_id']], [a['id'], b['id']], eids,
                    'Potential cross-source discrepancy; this is not a verified business conflict.',
                    'analyst_review', 'unverified', 'needs_source_verification')
            for row in report['claim_reviews']:
                if row['claim_id'] in (a['id'], b['id']):
                    row['comparison_ids'].append(comp_id)
    if k.get('runtime_confirmations') and not schema_errors('knowledge-package', k):
        traces = by_id(k.get('runtime_traces', []))
        report['runtime_reviews'] = []
        for confirmation in k['runtime_confirmations']:
            assessment_row = assessment(confirmation, traces)
            report['runtime_reviews'].append(dict(assessment_row, reviewed=False,
                reason='Sample diagnostics only; event correlation, representativeness and static context need review.'))
            reason = GAP_REASONS.get(assessment_row['result'])
            if reason:
                finding(reason, [confirmation['id']], confirmation['claim_ids'], [],
                        reason + ': preserve the bounded observation and unresolved runtime question.',
                        'verify_source', reason)
    report['gap_ids'] = sorted(g['id'] for g in gap_output['gaps'])
    for row in report['claim_reviews']:
        row['gap_ids'] = sorted(set(row['gap_ids']) | {g['id'] for g in gap_output['gaps'] if row['claim_id'] in g.get('affected_ids', [])})
    annotate_draft(report, gap_output, inputs)
    report['summary'] = calculate_summary(report, gap_output)
    return report, gap_output


def check_report(report, gap_output, inputs, *, allow_omitted_inputs=frozenset()):
    errors = schema_errors('validation-report', report) + schema_errors('validation-gaps', gap_output)
    if errors:
        return errors
    k = inputs['knowledge']
    claims, evidence, snapshots = (by_id(rows(k, name)) for name in ('claims', 'evidence', 'sources'))
    reviews = {r['claim_id']: r for r in report['claim_reviews']}
    comparisons = by_id(report['comparisons'])
    findings = by_id(report['findings'])
    gaps = by_id(gap_output['gaps'])
    def fail(message):
        errors.append(message)
    def refs(values, target, label):
        for value in values:
            if value not in target:
                fail(f'{label}: dangling reference {value}')
    # A consumer may render a reviewed projection without the optional source map.
    # The report still records its original hash; every supplied input must match.
    expected_inputs = report['inputs']
    if not set(allow_omitted_inputs) <= {'source-map', 'scenario-definition'}:
        fail('only source-map and scenario-definition may be omitted by a reviewed consumer')
    expected_inputs = [entry for entry in expected_inputs
                       if entry['kind'] in inputs or entry['kind'] not in allow_omitted_inputs]
    if expected_inputs != manifest(inputs):
        fail('input manifest/hash mismatch: review is stale')
    if report['mechanical_errors'] != mechanical_errors(inputs):
        fail('mechanical diagnostics do not match inputs')
    for artifact in (report, gap_output):
        if artifact['scope_ref'] != k['scope']['id'] or artifact['package_ref'] != {'id': k['package_id'], 'revision': k['revision']}:
            fail('report/gaps scope or revision mismatch')
    if gap_output['report_ref'] != report['id']:
        fail('gaps report reference mismatch')
    if report['claim_inventory'] != inventory(inputs) or set(reviews) != set(report['claim_inventory']) or len(reviews) != len(report['claim_reviews']):
        fail('every identified claim must have exactly one review')
    if report['gap_ids'] != sorted(gaps) or len(gaps) != len(gap_output['gaps']):
        fail('gap IDs are duplicated or do not match report')
    conflict_ids = set(by_id(rows(k, 'conflicts')))
    known = set().union(*(set(by_id(rows(k, group))) for group in
                        ('claims', 'entities', 'evidence', 'sources', 'relations', 'gaps', 'conflicts',
                         'runtime_traces', 'runtime_confirmations')))
    checks_by_evidence = {}
    def grounded(cid, trail=frozenset()):
        if cid in trail:
            return False
        review = reviews.get(cid, {})
        if claims.get(cid, {}).get('modality') == 'runtime_observation':
            return False
        if not review.get('reviewed'):
            return False
        if review.get('status') == 'CONFIRMED':
            return any(evidence.get(c['evidence_id'], {}).get('source_type') in ROOT_TYPES and
                       c['result'] == 'SUPPORTS' and c['verification'] in {'reopened', 'snapshot_only'}
                       for c in review.get('source_checks', []))
        if review.get('status') != 'INFERRED':
            return False
        if k.get('model_profile') == PROFILE:
            bases = claims.get(cid, {}).get('basis_claim_ids', [])
            return bool(bases) and all(grounded(b, trail | {cid}) for b in bases)
        inferred_evidence = [lookup(evidence, s.get('evidence_id')) for s in rows(claims.get(cid, {}), 'support')
                             if s.get('role') == 'supports' and lookup(evidence, s.get('evidence_id')).get('source_type') == 'INFERENCE']
        return bool(inferred_evidence) and all(e.get('basis_claim_ids') and
                all(grounded(b, trail | {cid}) for b in e['basis_claim_ids']) for e in inferred_evidence)
    for cid, review in reviews.items():
        claim = claims.get(cid)
        if not claim:
            continue
        if review['claim_hash'] != digest(claim):
            fail(f'{cid}: claim changed since review')
        refs(review['gap_ids'], gaps, cid)
        refs(review['comparison_ids'], comparisons, cid)
        refs(review['conflict_ids'], conflict_ids, cid)
        checks = {c['evidence_id']: c for c in review['source_checks']}
        if len(checks) != len(review['source_checks']):
            fail(f'{cid}: duplicate source checks')
        for eid, source_check in checks.items():
            refs([eid], evidence, cid)
            checks_by_evidence.setdefault(eid, []).append(source_check)
            e = evidence.get(eid)
            if not e:
                continue
            errors += source_check_errors(source_check, e, snapshots.get(e.get('snapshot_id'), {}), f'{cid}/{eid}')
        if not review['reviewed']:
            recorded = any(c.get('status') == 'unresolved' and cid in c.get('claim_ids', []) for c in rows(k, 'conflicts'))
            if review['status'] not in {'UNKNOWN', 'CONFLICT'} or (review['status'] == 'CONFLICT' and not recorded):
                fail(f'{cid}: unreviewed claim cannot be confirmed/classified')
            continue
        declared = [s for s in rows(claim, 'support') if s.get('role') in {'supports', 'contradicts'}]
        known_eids = {s['evidence_id'] for s in declared if isinstance(s.get('evidence_id'), str) and s['evidence_id'] in evidence}
        if not known_eids <= set(checks):
            fail(f'{cid}: each declared supporting/contradicting evidence must be checked')
        direct = [checks[eid] for eid in known_eids if eid in checks and
                  (evidence[eid].get('source_type') in ROOT_TYPES or runtime_root(claim, evidence[eid])) and
                  checks[eid]['result'] == 'SUPPORTS' and checks[eid]['verification'] in {'reopened', 'snapshot_only'}]
        inferred = [eid for eid in known_eids if evidence[eid].get('source_type') == 'INFERENCE']
        contradiction = any(c['result'] == 'CONTRADICTS' for c in checks.values())
        status = review['status']
        if status == 'CONFIRMED':
            if not direct or claim.get('inference') or inferred or contradiction or review['unsupported_parts']:
                fail(f'{cid}: CONFIRMED requires complete direct support without inference/contradiction')
            if any(c['result'] in {'PARTIAL_SUPPORT', 'NOT_CHECKED', 'UNAVAILABLE'} for eid, c in checks.items() if eid in known_eids):
                fail(f'{cid}: partial/unavailable support cannot confirm entire claim')
        elif status == 'PARTIALLY_CONFIRMED':
            if not review['supported_parts'] or not review['unsupported_parts'] or not any(c['result'] in {'SUPPORTS', 'PARTIAL_SUPPORT'} and
                    (evidence.get(eid, {}).get('source_type') in ROOT_TYPES or runtime_root(claim, evidence.get(eid, {}))) and
                    c['verification'] in {'reopened', 'snapshot_only'} for eid, c in checks.items()):
                fail(f'{cid}: partial confirmation needs supported and unsupported parts')
        elif status == 'INFERRED':
            structured = k.get('model_profile') == PROFILE
            if not claim.get('inference') or (not inferred and not (structured and claim.get('basis_claim_ids'))):
                fail(f'{cid}: INFERRED requires declared inference')
            if claim.get('predicate') in {'business_rationale', 'business_meaning'}:
                fail(f'{cid}: inference cannot supply business rationale/meaning')
            for eid in inferred:
                if checks.get(eid, {}).get('verification') != 'reasoning_checked' or checks.get(eid, {}).get('result') != 'SUPPORTS':
                    fail(f'{cid}: inference deduction was not checked')
                bases = evidence[eid].get('basis_claim_ids', [])
                if not bases or any(reviews.get(b, {}).get('status') not in {'CONFIRMED', 'INFERRED'} or not reviews.get(b, {}).get('reviewed') for b in bases):
                    fail(f'{cid}: inference bases must be verified')
            if not grounded(cid):
                fail(f'{cid}: inference has a cycle or lacks confirmed primary roots')
        elif status == 'CONFLICT':
            if not any(comparisons.get(comp, {}).get('status') == 'CONFLICT' and comparisons[comp]['reviewed'] for comp in review['comparison_ids']):
                fail(f'{cid}: reviewed CONFLICT needs verified comparison')
        if status in {'UNKNOWN', 'PARTIALLY_CONFIRMED', 'CONFLICT'} and not any(gaps.get(g, {}).get('status') == 'open' for g in review['gap_ids']):
            fail(f'{cid}: unresolved claim classification requires open Gap')
    if len(comparisons) != len(report['comparisons']) or len(findings) != len(report['findings']):
        fail('duplicate comparison/finding IDs')
    for comp in comparisons.values():
        refs(comp['claim_ids'], claims, comp['id'])
        refs(comp['evidence_ids'], evidence, comp['id'])
        types = {evidence[e].get('source_type') for e in comp['evidence_ids'] if e in evidence}
        other = 'CONFLUENCE' if comp['kind'] == 'code_confluence' else 'TEST'
        if not types & {'CODE', 'CONFIG'} or other not in types:
            fail(f'{comp["id"]}: wrong source types for comparison')
        if not comp['reviewed'] and comp['status'] != 'UNRESOLVED':
            fail(f'{comp["id"]}: unreviewed comparison cannot resolve conflict')
        if comp['status'] == 'CONFLICT' and comp['context_comparison'] != 'overlap':
            fail(f'{comp["id"]}: conflict needs overlapping context')
        if comp['status'] == 'CONTEXT_DIFFERENCE' and comp['context_comparison'] != 'different':
            fail(f'{comp["id"]}: context difference must be explicit')
        if comp['reviewed']:
            for eid in comp['evidence_ids']:
                if not any(c['verification'] in {'reopened', 'snapshot_only'} and c['result'] not in {'UNAVAILABLE', 'NOT_CHECKED'} for c in checks_by_evidence.get(eid, [])):
                    fail(f'{comp["id"]}: both comparison sources must be inspected')
    linked_findings = set()
    for link in gap_output['finding_gap_links']:
        refs([link['finding_id']], findings, 'finding gap link')
        refs(link['gap_ids'], gaps, 'finding gap link')
        linked_findings.add(link['finding_id'])
    for finding in findings.values():
        refs(finding['claim_ids'], claims, finding['id'])
        refs(finding['evidence_ids'], evidence, finding['id'])
        refs(finding['resolution_claim_ids'], claims, finding['id'])
        if finding['status'] == 'open' and finding['id'] not in linked_findings:
            fail(f'{finding["id"]}: open finding must have Gap link')
        if finding['status'] == 'resolved' and (not finding['resolution_claim_ids'] or any(reviews.get(c, {}).get('status') != 'CONFIRMED' or not reviews.get(c, {}).get('reviewed') for c in finding['resolution_claim_ids'])):
            fail(f'{finding["id"]}: resolution needs confirmed evidence-backed claim')
    for gap in gaps.values():
        refs(gap['affected_ids'], known, gap['id'])
    errors += publication_errors(report, gap_output, inputs)
    if report['summary'] != calculate_summary(report, gap_output):
        fail('summary counts/review status/publication gate are inconsistent')
    if not schema_errors('knowledge-package', k):
        errors += runtime_review_errors(k, report, gap_output)
    return list(dict.fromkeys(errors))


def save(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['draft', 'summarize', 'check'])
    for kind in sorted(REQUIRED_INPUTS | {'domain-tree', 'scenario-definition'}):
        parser.add_argument('--' + kind, type=Path)
    parser.add_argument('--report', type=Path)
    parser.add_argument('--gaps', type=Path)
    parser.add_argument('--output-dir', type=Path)
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args()
    try:
        if args.mode == 'summarize':
            if not args.report or not args.gaps:
                raise ValueError('--report and --gaps are required')
            report, gap_output = load(args.report), load(args.gaps)
            schema_problems = schema_errors('validation-report', report) + schema_errors('validation-gaps', gap_output)
            if schema_problems:
                raise ValueError('\n'.join(schema_problems))
            refresh_publication_subset(report, gap_output)
            report['summary'] = calculate_summary(report, gap_output)
            report['gap_ids'] = sorted(g['id'] for g in gap_output['gaps'])
            save(args.gaps, gap_output)
            save(args.report, report)
            return
        inputs = {kind: load(path) for kind in REQUIRED_INPUTS | {'domain-tree', 'scenario-definition'}
                  if (path := getattr(args, kind.replace('-', '_'))) is not None}
        if not REQUIRED_INPUTS <= set(inputs):
            raise ValueError('all five required input files must be supplied')
        if args.mode == 'draft':
            if args.output_dir is None:
                raise ValueError('--output-dir is required')
            report, gap_output = draft(inputs)
            destinations = [args.output_dir / 'validation-report.json', args.output_dir / 'gaps.json']
            if not args.overwrite and any(p.exists() for p in destinations):
                raise ValueError('Existing outputs retained; select another output directory or explicit --overwrite')
            problems = check_report(report, gap_output, inputs)
            if problems:
                raise ValueError('\n'.join(problems))
            args.output_dir.mkdir(parents=True, exist_ok=True)
            save(destinations[0], report)
            save(destinations[1], gap_output)
            print('Conservative draft created: no claim was semantically confirmed.')
        else:
            if not args.report or not args.gaps:
                raise ValueError('--report and --gaps are required')
            report, gap_output = load(args.report), load(args.gaps)
            problems = check_report(report, gap_output, inputs)
            if problems:
                print('\n'.join(problems))
                raise SystemExit(1)
            print(f'Report contract valid. Review: {report["summary"]["review_status"]}; publication gate: {report["summary"]["publication_gate"]}. Semantic review is required.')
    except (OSError, ValueError, yaml.YAMLError) as exc:
        parser.exit(2, f'{exc}\n')


if __name__ == '__main__':
    main()
