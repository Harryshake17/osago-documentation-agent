"""Local contract/reference checks for OSAGO knowledge artifacts.

No connector access or semantic truth checking. Dependencies: requirements.txt.
"""
import argparse
from functools import lru_cache
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
from model import PROFILE, increment_errors, legacy_view, model_errors
from runtime import runtime_errors, runtime_root

from paths import contracts_root

SCHEMAS = contracts_root() / 'schemas'
CATEGORIES = {
    'api_endpoints': {'endpoint'}, 'controllers': {'controller'},
    'commands_handlers': {'command', 'handler'},
    'process_definitions': {'process_definition'}, 'subprocesses': {'subprocess'},
    'business_rule_implementations': {'rule_implementation'},
    'configuration_keys': {'configuration_key'}, 'integrations': {'integration'},
    'automated_tests': {'automated_test'}, 'confluence_pages': {'confluence_page'},
}
ROOT_TYPES = {'CODE', 'CONFIG', 'TEST', 'CONFLUENCE', 'GIT'}
RULE_CATEGORIES = {'guards', 'validators', 'rules_extensions', 'process_branches', 'thresholds',
                   'configuration_driven_behaviour', 'blocking_checks', 'eligibility_rules', 'result_calculations'}


class UniqueLoader(yaml.SafeLoader):
    pass


def unique_mapping(loader, node, deep=False):
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise ValueError(f'duplicate YAML/JSON key: {key}')
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def load(path):
    return yaml.load(Path(path).read_text(encoding='utf-8'), Loader=UniqueLoader)


@lru_cache(maxsize=None)
def schema_validator(kind):
    documents = [json.loads(p.read_text(encoding='utf-8')) for p in SCHEMAS.glob('*.json')]
    registry = Registry().with_resources((s['$id'], Resource.from_contents(s)) for s in documents)
    schema = json.loads((SCHEMAS / f'{kind}.schema.json').read_text(encoding='utf-8'))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, registry=registry, format_checker=FormatChecker())


def schema_errors(kind, data):
    validator = schema_validator(kind)
    return [f'{kind}/{"/".join(map(str, e.absolute_path))}: {e.message}'
            for e in validator.iter_errors(data)]


def validate(kind, artifact, knowledge, domain_tree=None, scenario_definition=None,
             technical_flow=None, source_map=None, business_rules=None, previous_knowledge=None):
    errors = schema_errors('knowledge-package', knowledge) + schema_errors(kind, artifact)
    if domain_tree is not None:
        errors += schema_errors('domain-tree', domain_tree)
    if scenario_definition is not None:
        errors += schema_errors('scenario-definition', scenario_definition)
    if technical_flow is not None:
        errors += schema_errors('technical-flow', technical_flow)
    if source_map is not None:
        errors += schema_errors('source-map', source_map)
    if business_rules is not None:
        errors += schema_errors('business-rules', business_rules)
    if previous_knowledge is not None:
        errors += schema_errors('knowledge-package', previous_knowledge)
    if errors:
        return errors
    model_tree = artifact if kind == 'domain-tree' else domain_tree
    model_definition = artifact if kind == 'scenario-definition' else scenario_definition
    model_flow = artifact if kind == 'technical-flow' else technical_flow
    model_sources = artifact if kind == 'source-map' else source_map
    model_rules = artifact if kind == 'business-rules' else business_rules
    errors += runtime_errors(knowledge, model_flow, artifact)
    errors += model_errors(kind, artifact, knowledge, model_tree, model_definition,
                           model_flow, model_sources, model_rules)
    for input_kind, data in [('domain-tree', domain_tree), ('scenario-definition', scenario_definition),
                              ('technical-flow', technical_flow), ('source-map', source_map), ('business-rules', business_rules)]:
        if data is not None:
            errors += runtime_errors(knowledge, model_flow, data)
            errors += model_errors(input_kind, data, knowledge, model_tree, model_definition,
                                   model_flow, model_sources, model_rules)
    if previous_knowledge is not None:
        errors += increment_errors(previous_knowledge, knowledge)
        if kind == 'source-map' and knowledge.get('model_profile') == PROFILE:
            old_entities = {e['id']: e for e in previous_knowledge['entities']}
            old_claims = {c['id']: c for c in previous_knowledge['claims']}
            for claim in knowledge['claims']:
                if claim['id'] not in old_claims and claim['modality'] != 'discovery':
                    errors.append('source-map: Source Discovery can add only discovery claims')
                if claim['id'] in old_claims and claim != old_claims[claim['id']]:
                    errors.append('source-map: Source Discovery cannot rewrite upstream claims')
            for entity in knowledge['entities']:
                previous_name = old_entities.get(entity['id'], {}).get('preferred_name')
                if previous_name is not None and entity['preferred_name'] != previous_name:
                    errors.append('source-map: Source Discovery cannot choose preferred_name')
                if previous_name is None and entity['preferred_name']['status'] != 'UNKNOWN':
                    errors.append('source-map: new discovered entity must keep preferred_name UNKNOWN')
    if errors:
        return list(dict.fromkeys(errors))
    artifact = legacy_view(kind, artifact)
    def fail(message):
        errors.append(message)
    def index(records, label):
        result = {}
        for row in records:
            if row['id'] in result:
                fail(f'{label}: duplicate ID {row["id"]}')
            result[row['id']] = row
        return result
    def refs(values, target, label):
        for value in values:
            if value not in target:
                fail(f'{label}: dangling reference {value}')
    groups = {k: index(knowledge[k], k) for k in
              ('sources', 'entities', 'evidence', 'claims', 'relations', 'gaps', 'conflicts')}
    all_ids = [r['id'] for key in groups for r in knowledge[key]]
    all_ids += [r['id'] for key in ('runtime_traces', 'runtime_confirmations') for r in knowledge.get(key, [])]
    if len(set(all_ids)) != len(all_ids):
        fail('knowledge: IDs must be globally unique')
    sources, entities, evidence, claims = (groups[k] for k in ('sources', 'entities', 'evidence', 'claims'))
    gaps, conflicts = groups['gaps'], groups['conflicts']
    scope = knowledge['scope']
    for source in sources.values():
        if source['repository'] is not None and source['repository'] not in scope['repositories']:
            fail(f'{source["id"]}: repository outside scope')
        if source['revision'] is None and not any(
                g['reason'] == 'unknown_version' and source['id'] in g['affected_ids'] for g in gaps.values()):
            fail(f'{source["id"]}: unknown revision requires Gap')
    for e in evidence.values():
        inferred = e['source_type'] == 'INFERENCE'
        if inferred != e['inference']:
            fail(f'{e["id"]}: inference/source_type mismatch')
        refs(e['basis_claim_ids'], claims, e['id'])
        if inferred:
            if not e['basis_claim_ids'] or not e['rationale']:
                fail(f'{e["id"]}: inference needs bases and rationale')
        else:
            refs([e['snapshot_id']], sources, e['id'])
            if not e['excerpt'] or e['basis_claim_ids']:
                fail(f'{e["id"]}: primary evidence requires excerpt and no inference bases')
            snap = sources.get(e['snapshot_id'], {})
            if snap.get('availability') != 'available':
                fail(f'{e["id"]}: unavailable snapshot cannot be evidence')
            allowed = {'CODE': {'repository', 'git_history'}, 'CONFIG': {'repository', 'git_history'},
                       'TEST': {'repository', 'git_history', 'tests'}, 'CONFLUENCE': {'confluence'},
                       'JIRA': {'jira'}, 'GIT': {'git_history'}, 'OPENSEARCH': {'opensearch'}}
            if snap.get('adapter') not in allowed.get(e['source_type'], set()):
                fail(f'{e["id"]}: source type/adapter mismatch')
            if snap and (e['version'] != snap['revision'] or e['commit'] != snap['commit']):
                fail(f'{e["id"]}: evidence/snapshot version mismatch')
            if e['source_type'] in {'CODE', 'CONFIG', 'TEST'} and snap.get('repository') != e['repository']:
                fail(f'{e["id"]}: evidence/snapshot repository mismatch')
        if e['source_type'] in {'CODE', 'CONFIG', 'TEST'}:
            if not e['repository'] or not e['file'] or e['repository'] not in scope['repositories']:
                fail(f'{e["id"]}: missing or out-of-scope repository/file')
        if e['source_type'] in {'CONFLUENCE', 'JIRA'} and not e['page']:
            fail(f'{e["id"]}: page/issue locator required')
    unresolved = {cid for conflict in conflicts.values() if conflict['status'] == 'unresolved'
                  for cid in conflict['claim_ids']}
    memo = {}
    def supported(cid, trail=frozenset()):
        if cid in trail:
            fail(f'inference cycle at {cid}')
            return False
        if cid in memo:
            return memo[cid]
        c = claims.get(cid)
        if not c:
            return False
        usable = c['validation_status'] == 'supported' and c['lifecycle_status'] == 'current' and cid not in unresolved
        if knowledge.get('model_profile') == PROFILE and c['inference']:
            bases = c['basis_claim_ids']
            memo[cid] = usable and bool(bases) and all(supported(b, trail | {cid}) for b in bases)
            return memo[cid]
        good_roots = False
        for support in c['support']:
            if support['role'] != 'supports':
                continue
            e = evidence.get(support['evidence_id'])
            if not e:
                continue
            if e['source_type'] in ROOT_TYPES or runtime_root(c, e):
                good_roots = True
            elif e['source_type'] == 'INFERENCE':
                bases = e['basis_claim_ids']
                base_results = [supported(b, trail | {cid}) for b in bases]
                good_roots = (bool(bases) and all(base_results)) or good_roots
        memo[cid] = usable and good_roots
        return memo[cid]
    def supported_refs(cids, label):
        refs(cids, claims, label)
        for cid in cids:
            if not supported(cid):
                fail(f'{label}: claim {cid} lacks current, conflict-free primary support')
    for c in claims.values():
        refs([c['subject_id']], entities, c['id'])
        refs([s['evidence_id'] for s in c['support']], evidence, c['id'])
        direct = [evidence[s['evidence_id']] for s in c['support'] if s['role'] == 'supports' and s['evidence_id'] in evidence]
        inferred = (c['knowledge_status'] == 'INFERRED' if knowledge.get('model_profile') == PROFILE
                    else any(e['inference'] for e in direct))
        if inferred != c['inference'] or (c['modality'] == 'inferred' and not c['inference']):
            fail(f'{c["id"]}: claim inference mismatch')
        if c['validation_status'] == 'supported' and c['lifecycle_status'] == 'current' and c['id'] not in unresolved:
            supported_refs([c['id']], c['id'])
    for e in evidence.values():
        for cid in e['basis_claim_ids']:
            supported(cid)
    for conflict in conflicts.values():
        refs(conflict['claim_ids'], claims, conflict['id'])
        if conflict['status'] == 'resolved':
            supported_refs([conflict['resolution_claim_id']], conflict['id'])
        elif conflict['resolution_claim_id'] is not None:
            fail(f'{conflict["id"]}: unresolved conflict cannot have resolution')
    for gap in gaps.values():
        refs(gap['affected_ids'], set(all_ids), gap['id'])
    def binding(data):
        if data['scope_ref'] != scope['id'] or data['package_ref'] != {
                'id': knowledge['package_id'], 'revision': knowledge['revision']}:
            fail('artifact: scope/package revision mismatch')
    def field_claims(record, scalar, lists):
        for field in scalar:
            value = record[field]
            if value is None:
                continue
            if field == 'name' and knowledge.get('model_profile') == PROFILE:
                # The canonical name is supported once, through preferred_name in the registry.
                continue
            if field == 'name' and field in record['proposed_fields']:
                continue
            check_field(record, field, field, value)
        for field in lists:
            for i, value in enumerate(record[field]):
                check_field(record, f'{field}/{i}', field, value)
    def check_field(record, key, predicate, value):
        cids = record['attribute_claims'].get(key, [])
        if not cids:
            fail(f'{record["id"]}/{key}: missing attribute claims')
        supported_refs(cids, record['id'])
        subject = record.get('scenario_id', record['id'])
        if not any(claims.get(cid, {}).get('subject_id') == subject and
                   claims[cid]['predicate'] == predicate and claims[cid]['value'] == value for cid in cids if cid in claims):
            fail(f'{record["id"]}/{key}: claim must match subject/predicate/value')
    def unknowns(record, required_fields):
        assessment = record.get('assessment', record)
        unknown = set(assessment['unknown_fields'])
        na = set(assessment.get('not_applicable_fields', []))
        if unknown & na:
            fail(f'{record["id"]}: unknown and not_applicable overlap')
        for field in required_fields:
            if record[field] is None or record[field] == []:
                if field not in unknown | na:
                    fail(f'{record["id"]}/{field}: empty value needs unknown/not_applicable')
        refs(record['gap_ids'], gaps, record['id'])
        if unknown and not any(gaps.get(g, {}).get('status') == 'open' and
                               record.get('scenario_id', record['id']) in gaps[g]['affected_ids'] for g in record['gap_ids'] if g in gaps):
            fail(f'{record["id"]}: unknown fields require affected open Gap')
    def check_relation(r, endpoints):
        refs([r['from_id'], r['to_id']], endpoints, r['id'])
        supported_refs(r['claim_ids'], r['id'])
        if not any(claims.get(c, {}).get('subject_id') == r['from_id'] and
                   claims[c]['predicate'] == r['relation_type'] and claims[c]['value'] == r['to_id'] for c in r['claim_ids'] if c in claims):
            fail(f'{r["id"]}: relation claim mismatch')
    for r in groups['relations'].values():
        check_relation(r, set(entities) | set(evidence))
    def tree_check(tree):
        binding(tree)
        nodes = index(tree['nodes'], 'nodes')
        types = {'domain': 'Domain', 'scenario': 'Scenario', 'capability': 'Capability', 'business_rule': 'BusinessRule'}
        for node in nodes.values():
            refs([node['id']], entities, node['id'])
            if entities.get(node['id'], {}).get('type') != types[node['type']]:
                fail(f'{node["id"]}: entity type mismatch')
            if node['parent'] is not None:
                refs([node['parent']], nodes, node['id'])
            field_claims(node, ('name', 'business_goal', 'trigger', 'entry_state'), ('exit_states', 'actors'))
            unknowns(node, ('business_goal', 'trigger', 'entry_state', 'exit_states', 'actors'))
            for actor in node['actors']:
                if entities.get(actor, {}).get('type') != 'Actor':
                    fail(f'{node["id"]}: invalid Actor {actor}')
            refs(node['discovered_sources'], sources, node['id'])
            refs(node['conflict_ids'], conflicts, node['id'])
            supported_refs(node['recommendation_basis_claim_ids'], node['id'])
            a = node['assessment']
            criteria = a['criteria']
            for criterion in criteria.values():
                supported_refs(criterion['claim_ids'], node['id'])
                if criterion['status'] in {'satisfied', 'independent'} and not criterion['claim_ids']:
                    fail(f'{node["id"]}: satisfied criterion needs evidence')
            if node['type'] != 'scenario' and a['atomicity'] != 'not_applicable':
                fail(f'{node["id"]}: only scenario has atomicity')
            if node['type'] == 'scenario':
                if a['atomicity'] == 'not_applicable':
                    fail(f'{node["id"]}: scenario atomicity cannot be not_applicable')
                if a['atomicity'] == 'atomic' and (not a['lifecycle'] or any(c['status'] != 'satisfied' for c in criteria.values())):
                    fail(f'{node["id"]}: atomic requires four satisfied criteria and lifecycle')
                if a['atomicity'] == 'decompose' and not any(criteria[k]['status'] == 'independent' for k in ('business_goal', 'lifecycle')):
                    fail(f'{node["id"]}: decompose needs independent goal/lifecycle')
                if a['atomicity'] == 'undetermined' and (not node['gap_ids'] or not any(c['status'] == 'unknown' for c in criteria.values())):
                    fail(f'{node["id"]}: undetermined requires unknown criterion and Gap')
            if a['lifecycle']:
                supported_refs(a['lifecycle']['start_claim_ids'] + a['lifecycle']['end_claim_ids'], node['id'])
            trail, cur = set(), node['id']
            while cur in nodes:
                if cur in trail:
                    fail(f'domain-tree parent cycle at {cur}')
                    break
                trail.add(cur)
                cur = nodes[cur]['parent']
        index(tree['relations'], 'tree relations')
        for r in tree['relations']:
            check_relation(r, nodes)
            expected = {'uses_capability': 'capability', 'applies_rule': 'business_rule'}
            if r['relation_type'] not in expected or nodes.get(r['to_id'], {}).get('type') != expected.get(r['relation_type']):
                fail(f'{r["id"]}: invalid tree relation type/target')
        if tree['coverage']['status'] == 'complete' and (tree['coverage']['limitations'] or tree['coverage']['frontier'] or
                any(n['assessment']['unknown_fields'] or n['conflict_ids'] for n in nodes.values())):
            fail('domain-tree: unresolved limits require partial coverage')
    def definition_check(definition):
        binding(definition)
        if entities.get(definition['scenario_id'], {}).get('type') != 'Scenario':
            fail('ScenarioDefinition must reference Scenario')
        field_claims(definition, ('name', 'business_goal', 'trigger', 'entry_state'), ('expected_outcomes', 'actors'))
        unknowns(definition, ('business_goal', 'trigger', 'entry_state', 'expected_outcomes', 'actors'))
        refs(definition['known_source_refs'], sources, definition['id'])
        for anchor in definition['entry_point_candidates']:
            refs([anchor['id']], entities, 'anchor')
            refs([anchor['snapshot_id']], sources, 'anchor')
            supported_refs(anchor['claim_ids'], 'anchor')
            if not any(claims.get(c, {}).get('subject_id') == definition['scenario_id'] and claims[c]['value'] == anchor['id'] for c in anchor['claim_ids'] if c in claims):
                fail('anchor must have a claim linking it to scenario')
            if not any(any(evidence.get(s['evidence_id'], {}).get('snapshot_id') == anchor['snapshot_id']
                           and s['role'] == 'supports' for s in claims.get(c, {}).get('support', []))
                       for c in anchor['claim_ids']):
                fail('anchor must be supported by its own snapshot')
    if kind == 'knowledge-package':
        return list(dict.fromkeys(errors))
    binding(artifact)
    if kind == 'domain-tree':
        tree_check(artifact)
    elif kind == 'scenario-definition':
        definition_check(artifact)
    elif kind == 'source-map':
        if domain_tree is None or scenario_definition is None:
            fail('source-map requires domain-tree and scenario-definition')
            return errors
        tree_check(domain_tree)
        definition_check(scenario_definition)
        if artifact['domain_tree_ref'] != domain_tree['id'] or artifact['scenario_definition_ref'] != scenario_definition['id'] or artifact['scenario'] != scenario_definition['scenario_id']:
            fail('source-map: input artifact references mismatch')
        if not any(n['id'] == artifact['scenario'] and n['type'] == 'scenario' for n in domain_tree['nodes']):
            fail('source-map: scenario is absent from domain tree')
        accepted = index(artifact['sources'], 'accepted sources')
        candidates = index(artifact['candidates'], 'candidates')
        exclusions = index(artifact['exclusions'], 'exclusions')
        if set(accepted) & (set(candidates) | set(exclusions)) or set(candidates) & set(exclusions):
            fail('source-map: accepted/candidate/exclusion IDs overlap')
        anchors = {a['id'] for a in scenario_definition['entry_point_candidates']}
        for source in accepted.values():
            cat = source['category']
            if source['artifact_kind'] not in CATEGORIES[cat]:
                fail(f'{source["id"]}: category/artifact_kind mismatch')
            allowed_types = {'confluence_pages': {'CONFLUENCE'}, 'automated_tests': {'TEST'},
                             'process_definitions': {'CODE', 'CONFIG'}, 'subprocesses': {'CODE', 'CONFIG'},
                             'configuration_keys': {'CODE', 'CONFIG'}, 'api_endpoints': {'CODE', 'CONFIG'},
                             'integrations': {'CODE', 'CONFIG'}, 'business_rule_implementations': {'CODE', 'CONFIG'}}
            if source['source_type'] not in allowed_types.get(cat, {'CODE'}):
                fail(f'{source["id"]}: category/source_type mismatch')
            snap = sources.get(source['snapshot_ref'])
            refs([source['snapshot_ref']], sources, source['id'])
            if snap and (snap['availability'] != 'available' or snap['revision'] != source['version'] or snap['commit'] != source['commit']):
                fail(f'{source["id"]}: unavailable or mismatched snapshot')
            if snap and snap['repository'] != source['repository']:
                fail(f'{source["id"]}: source/snapshot repository mismatch')
            if source['source_type'] == 'CONFLUENCE':
                if not source['page_id'] or not source['section']:
                    fail(f'{source["id"]}: Confluence needs page/section')
            elif not source['repository'] or not source['path'] or not source['symbol'] or source['repository'] not in scope['repositories']:
                fail(f'{source["id"]}: file source needs scoped repository/path/symbol')
            refs(source['evidence_ids'], evidence, source['id'])
            if not any(evidence.get(e, {}).get('snapshot_id') == source['snapshot_ref'] and evidence[e]['source_type'] == source['source_type'] for e in source['evidence_ids'] if e in evidence):
                fail(f'{source["id"]}: source needs evidence for its own snapshot/type')
            supported_refs(source['relevance_claim_ids'], source['id'])
            path = source['relevance_path']
            if path[0]['from_ref'] not in anchors or path[-1]['to_ref'] not in {source['id'], source['symbol']}:
                fail(f'{source["id"]}: relevance path must connect anchor to source')
            for i, edge in enumerate(path):
                if i and path[i-1]['to_ref'] != edge['from_ref']:
                    fail(f'{source["id"]}: broken relevance path')
                refs(edge['evidence_ids'], evidence, source['id'])
                supported_refs(edge['claim_ids'], source['id'])
                if not any(claims.get(c, {}).get('subject_id') == edge['from_ref'] and claims[c]['predicate'] == edge['relation_type'] and claims[c]['value'] == edge['to_ref'] for c in edge['claim_ids'] if c in claims):
                    fail(f'{source["id"]}: relevance edge claim mismatch')
                for cid in edge['claim_ids'] + source['relevance_claim_ids']:
                    if claims.get(cid, {}).get('modality') != 'discovery':
                        fail(f'{source["id"]}: relevance requires discovery claims')
                for eid in edge['evidence_ids']:
                    if not any(any(s['evidence_id'] == eid and s['role'] == 'supports' for s in claims.get(c, {}).get('support', [])) for c in edge['claim_ids']):
                        fail(f'{source["id"]}: edge evidence is not supporting its claims')
        coverage = index([dict(c, id=c['category']) for c in artifact['category_coverage']], 'category coverage')
        if set(coverage) != set(CATEGORIES):
            fail('source-map: coverage must include exactly ten categories')
        runs = index(artifact['search_runs'], 'search runs')
        for run in runs.values():
            if run['category'] not in CATEGORIES or run['scope_ref'] != scope['id']:
                fail(f'{run["id"]}: invalid category or scope')
            refs(run['snapshot_ids'], sources, run['id'])
        for category, row in coverage.items():
            refs(row['search_run_ids'], runs, category)
            supported_refs(row['basis_claim_ids'], category)
            category_runs = [runs[r] for r in row['search_run_ids'] if r in runs]
            if any(r['category'] != category for r in category_runs):
                fail(f'{category}: search run category mismatch')
            if row['status'] == 'found' and not any(s['category'] == category for s in accepted.values()):
                fail(f'{category}: found requires accepted source')
            if row['status'] == 'not_found' and (not category_runs or any(r['status'] != 'complete' for r in category_runs) or any(s['category'] == category for s in accepted.values())):
                fail(f'{category}: not_found requires completed search and no accepted sources')
            if row['status'] == 'not_applicable' and not row['basis_claim_ids']:
                fail(f'{category}: not_applicable needs support')
            if row['status'] in {'found', 'unavailable'} and not category_runs:
                fail(f'{category}: search/availability diagnostic required')
        for candidate in candidates.values():
            refs(candidate['gap_ids'], gaps, candidate['id'])
            if candidate['snapshot_ref'] is not None:
                refs([candidate['snapshot_ref']], sources, candidate['id'])
        refs(artifact['gap_ids'], gaps, 'source-map')
        refs(artifact['conflict_ids'], conflicts, 'source-map')
        if artifact['coverage']['status'] == 'complete' and (candidates or artifact['gap_ids'] or artifact['conflict_ids'] or
                artifact['coverage']['limitations'] or artifact['coverage']['frontier'] or
                any(r['status'] != 'complete' for r in runs.values()) or
                any(c['status'] in {'unavailable', 'incomplete'} for c in coverage.values())):
            fail('source-map: unresolved limits require partial coverage')
    elif kind in {'technical-flow', 'business-rules', 'scenario'}:
        if source_map is None or domain_tree is None or scenario_definition is None:
            fail(f'{kind} requires source-map, domain-tree and scenario-definition')
            return errors
        source_errors = validate('source-map', source_map, knowledge, domain_tree, scenario_definition)
        if source_errors:
            return errors + source_errors
        accepted = index(source_map['sources'], 'accepted sources')
        def claim_snapshots(cid, seen=frozenset()):
            if cid in seen:
                return set()
            result = set()
            for support in claims.get(cid, {}).get('support', []):
                if support['role'] != 'supports':
                    continue
                e = evidence.get(support['evidence_id'], {})
                if e.get('source_type') in ROOT_TYPES:
                    result.add(e['snapshot_id'])
                elif e.get('source_type') == 'INFERENCE':
                    for basis in e['basis_claim_ids']:
                        result |= claim_snapshots(basis, seen | {cid})
            return result
        def claims_from_sources(cids, source_ids, label):
            allowed = {accepted[s]['snapshot_ref'] for s in source_ids if s in accepted}
            for cid in cids:
                snapshots = claim_snapshots(cid)
                if not snapshots or not snapshots <= allowed:
                    fail(f'{label}: claim {cid} is not supported by listed accepted sources')
        flow = artifact if kind == 'technical-flow' else technical_flow
        if flow is None:
            fail('business-rules requires technical-flow')
            return errors
        binding(flow)
        if flow['source_map_ref'] != source_map['id']:
            fail('technical-flow: source-map artifact ID mismatch')
        if flow['scenario_id'] != source_map['scenario']:
            fail('technical-flow: scenario mismatch')
        steps = index(flow['nodes'], 'technical nodes')
        component_ids = set()
        for step in steps.values():
            refs([step['id']], entities, step['id'])
            if entities.get(step['id'], {}).get('type') != 'SystemBehaviour':
                fail(f'{step["id"]}: technical node needs SystemBehaviour entity; ScenarioStep belongs to 05-scenario')
            if entities.get(step['component_id'], {}).get('type') not in {'CodeComponent', 'ConfigRule', 'ApiOperation'}:
                fail(f'{step["id"]}: invalid implementation component')
            component_ids.add(step['component_id'])
            refs(step['source_ids'], accepted, step['id'])
            supported_refs(step['claim_ids'], step['id'])
            claims_from_sources(step['claim_ids'], step['source_ids'], step['id'])
            if not any(claims.get(c, {}).get('subject_id') == step['id'] and claims[c]['predicate'] == 'implementation'
                       and claims[c]['value'] == step['component_id'] for c in step['claim_ids'] if c in claims):
                fail(f'{step["id"]}: missing implementation claim')
        for relation in flow['relations']:
            check_relation(relation, set(entities))
            if any(entities.get(relation[end], {}).get('type') == 'ScenarioStep' for end in ('from_id', 'to_id')):
                fail(f'{relation["id"]}: ScenarioStep relations belong to 05-scenario')
            claims_from_sources(relation['claim_ids'], list(accepted), relation['id'])
        if flow.get('analysis_profile') or any('symbol' in n for n in flow['nodes']):
            nodes = steps
            lists = ('inputs', 'outputs', 'conditions', 'calls', 'state_changes',
                     'configuration_reads', 'checks', 'external_calls', 'async_events')
            for node in nodes.values():
                nid = node['id']
                field_claims(node, ('type', 'symbol', 'purpose'), lists)
                unknowns(node, ('purpose',) + lists)
                if not set(node['gap_ids']) <= set(flow['gap_ids']):
                    fail(f'{nid}: node Gaps missing from flow projection')
                if not set(node['unknown_fields'] + node['not_applicable_fields']) <= set(('purpose',) + lists):
                    fail(f'{nid}: invalid technical unknown/not_applicable field')
                for field in node['not_applicable_fields']:
                    check_field(node, f'not_applicable/{field}', 'not_applicable', field)
                for field in node['unknown_fields']:
                    if node[field] not in (None, []):
                        fail(f'{nid}/{field}: unknown field must be empty')
                cids = {c for cs in node['attribute_claims'].values() for c in cs}
                if not cids <= set(steps.get(nid, {}).get('claim_ids', [])):
                    fail(f'{nid}: node field claims missing from canonical claim_ids')
                refs(node['evidence'], evidence, nid)
                supporting = {s['evidence_id'] for c in cids for s in claims.get(c, {}).get('support', []) if s['role'] == 'supports'}
                if not supporting <= set(node['evidence']):
                    fail(f'{nid}: node evidence omits field support')
                refs(node['calls'], nodes, nid)
                for target in node['calls']:
                    if not any(r['from_id'] == nid and r['to_id'] == target and r['relation_type'] == 'calls' for r in flow['relations']):
                        fail(f'{nid}: call needs directed evidence-backed relation')
                if node['unknown_fields'] and flow['coverage']['status'] == 'complete':
                    fail(f'{nid}: unknown technical fields require partial coverage')
        refs(flow['gap_ids'], gaps, flow['id'])
        refs(flow['conflict_ids'], conflicts, flow['id'])
        if flow['coverage']['status'] == 'complete' and (flow['gap_ids'] or flow['conflict_ids'] or
                flow['coverage']['limitations'] or flow['coverage']['frontier']):
            fail('technical-flow: unresolved limits require partial coverage')
        if kind == 'technical-flow':
            return list(dict.fromkeys(errors))
        if kind == 'scenario':
            if business_rules is None:
                fail('scenario requires business-rules')
                return errors
            rule_errors = validate('business-rules', business_rules, knowledge, domain_tree,
                                   scenario_definition, flow, source_map)
            if rule_errors:
                return errors + rule_errors
            if artifact['scenario_id'] != flow['scenario_id'] or artifact['scenario_definition_ref'] != scenario_definition['id'] or artifact['technical_flow_ref'] != flow['id'] or artifact['business_rules_ref'] != business_rules['id'] or artifact['source_map_ref'] != source_map['id']:
                fail('scenario: input scenario/artifact references mismatch')
            rules = index(business_rules['rules'], 'input business rules')
            scenario_steps = index(artifact['steps'], 'scenario steps')
            scalar_fields = ('actor', 'action', 'business_meaning', 'system_behavior', 'state_before', 'state_after', 'user_result')
            list_fields = ('evaluated_rules', 'integrations', 'implementation')
            def open_gaps(gids, target):
                return [gaps[g] for g in gids if g in gaps and gaps[g]['status'] == 'open' and target in gaps[g]['affected_ids']]
            def evidence_list(cids, eids, label):
                refs(eids, evidence, label)
                for cid in cids:
                    for support in claims.get(cid, {}).get('support', []):
                        if support['role'] == 'supports' and support['evidence_id'] not in eids:
                            fail(f'{label}: evidence list omits {support["evidence_id"]}')
            def matches(cids, subject, predicate, value):
                return any(claims.get(c, {}).get('subject_id') == subject and claims[c]['predicate'] == predicate and
                           claims[c]['value'] == value for c in cids if c in claims)
            def explicit_meaning(cids, label):
                if any(claims.get(c, {}).get('inference') for c in cids):
                    fail(f'{label}: inference cannot create business meaning')
                if not any(claims.get(c, {}).get('modality') in {'documented_requirement', 'source_statement'} for c in cids):
                    fail(f'{label}: explicit source-stated business meaning required')
            orders = sorted(s['order'] for s in scenario_steps.values())
            if orders != list(range(1, len(scenario_steps) + 1)):
                fail('scenario: display order must be unique and contiguous from 1')
            for step in scenario_steps.values():
                sid = step['id']
                if entities.get(sid, {}).get('type') != 'ScenarioStep':
                    fail(f'{sid}: expected ScenarioStep entity')
                refs(step['source_ids'], accepted, sid)
                refs(step['technical_step_refs'], steps, sid)
                refs(step['gap_ids'], gaps, sid)
                refs(step['conflict_ids'], conflicts, sid)
                impl = {steps[t]['component_id'] for t in step['technical_step_refs'] if t in steps}
                if set(step['implementation']) != impl:
                    fail(f'{sid}: implementation must match linked technical steps')
                narrative = [step['action'], step['system_behavior']]
                narrative += [step.get(field, {}).get('value') for field in ('business_action', 'business_result')]
                symbols = {steps[ref].get('symbol') for ref in step['technical_step_refs'] if ref in steps}
                if any(text and text in symbols for text in narrative):
                    fail(f'{sid}: a code symbol is not a process action/result; keep technical details in 03 refs')
                unknown, na = set(step['unknown_fields']), set(step['not_applicable_fields'])
                if unknown & na or not (unknown | na) <= set(scalar_fields + list_fields):
                    fail(f'{sid}: invalid unknown/not_applicable fields')
                if unknown and not open_gaps(step['gap_ids'], sid):
                    fail(f'{sid}: unknown fields require affected open Gap')
                if step['business_meaning'] == 'UNKNOWN' and ('business_meaning' not in unknown or
                        not any(g['reason'] == 'unknown_reason' for g in open_gaps(step['gap_ids'], sid))):
                    fail(f'{sid}: UNKNOWN business_meaning requires unknown_reason Gap')
                if step['system_behavior'] == 'UNKNOWN':
                    fail(f'{sid}: a reconstructed step needs known system_behavior')
                check_field(step, 'kind', 'kind', step['kind'])
                for field in scalar_fields:
                    missing = step[field] is None or step[field] == 'UNKNOWN'
                    if missing != (field in unknown | na):
                        fail(f'{sid}/{field}: unknown marker/status mismatch')
                    if not missing:
                        check_field(step, field, field, step[field])
                for field in list_fields:
                    if bool(step[field]) == (field in unknown | na):
                        fail(f'{sid}/{field}: list/status mismatch')
                    for i, value in enumerate(step[field]):
                        check_field(step, f'{field}/{i}', field, value)
                for field in na:
                    cids = step['attribute_claims'].get(f'not_applicable/{field}', [])
                    supported_refs(cids, sid)
                    if not cids or not matches(cids, sid, 'not_applicable', field):
                        fail(f'{sid}/{field}: not_applicable requires explicit claim')
                for field, typ in {'actor': 'Actor', 'state_before': 'State', 'state_after': 'State', 'decision_ref': 'Decision'}.items():
                    if step[field] is not None and entities.get(step[field], {}).get('type') != typ:
                        fail(f'{sid}/{field}: invalid {typ} reference')
                for integration in step['integrations']:
                    if entities.get(integration, {}).get('type') != 'Integration':
                        fail(f'{sid}: invalid Integration reference')
                refs(step['evaluated_rules'], rules, sid)
                for rid in step['evaluated_rules']:
                    if rid in rules and artifact['scenario_id'] not in rules[rid]['affected_scenario']:
                        fail(f'{sid}: rule belongs to another scenario')
                if step['kind'] == 'actor_action' and step['actor'] is None:
                    fail(f'{sid}: actor_action requires a known Actor')
                if step['kind'] == 'integration' and not step['integrations'] and 'integrations' not in unknown:
                    fail(f'{sid}: integration step must identify Integration or Gap')
                if step['kind'] == 'state_transition' and (step['state_before'] is None or step['state_after'] is None) and not {'state_before', 'state_after'} & unknown:
                    fail(f'{sid}: state transition needs states or explicit Gap')
                if step['kind'] == 'decision':
                    if step['decision_ref'] is None or step['decision_kind'] == 'none':
                        fail(f'{sid}: decision requires Decision reference and kind')
                    if not step['evaluated_rules'] and 'evaluated_rules' not in unknown:
                        fail(f'{sid}: decision must link a rule or explicit Gap')
                elif step['decision_ref'] is not None or step['decision_kind'] != 'none':
                    fail(f'{sid}: non-decision step cannot carry decision identity')
                if step['decision_ref'] is not None:
                    check_field(step, 'decision_ref', 'decision_ref', step['decision_ref'])
                    check_field(step, 'decision_kind', 'decision_kind', step['decision_kind'])
                if step['decision_kind'] == 'business' and not any(rules.get(r, {}).get('rule_kind') in {'business_rule', 'eligibility'} for r in step['evaluated_rules']):
                    fail(f'{sid}: technical constraints cannot become business decisions')
                if step['business_meaning'] != 'UNKNOWN':
                    explicit_meaning(step['attribute_claims'].get('business_meaning', []), sid)
                cids = [c for cs in step['attribute_claims'].values() for c in cs]
                supported_refs(cids, sid)
                claims_from_sources(cids, step['source_ids'], sid)
                evidence_list(cids, step['evidence'], sid)
            transitions = index(artifact['transitions'], 'scenario transitions')
            resolved_pairs = set()
            all_pairs = set()
            for edge in transitions.values():
                eid = edge['id']
                refs([edge['from_step'], edge['to_step']], scenario_steps, eid)
                refs(edge['source_ids'], accepted, eid)
                refs(edge['gap_ids'], gaps, eid)
                refs(edge['conflict_ids'], conflicts, eid)
                pair = (edge['from_step'], edge['to_step'])
                all_pairs.add(pair)
                if edge['kind'] == 'unresolved':
                    if not any(g['reason'] == 'missing_link' for g in open_gaps(edge['gap_ids'], edge['from_step'])):
                        fail(f'{eid}: unresolved transition requires affected open Gap')
                    if edge['claim_ids'] or edge['evidence'] or edge['rule_ref'] is not None or edge['decision_ref'] is not None or edge['rule_outcome'] != 'UNKNOWN' or edge['condition'] is not None:
                        fail(f'{eid}: unresolved transition cannot assert causal/branch facts')
                    continue
                if not edge['claim_ids'] or not edge['source_ids'] or not edge['evidence']:
                    fail(f'{eid}: transition needs claims, sources and evidence')
                supported_refs(edge['claim_ids'], eid)
                claims_from_sources(edge['claim_ids'], edge['source_ids'], eid)
                evidence_list(edge['claim_ids'], edge['evidence'], eid)
                if not matches(edge['claim_ids'], edge['from_step'], edge['kind'], edge['to_step']):
                    fail(f'{eid}: directed transition claim mismatch')
                resolved_pairs.add(pair)
                if edge['kind'] == 'rule_branch':
                    origin = scenario_steps.get(edge['from_step'], {})
                    if origin.get('kind') != 'decision' or edge['decision_ref'] != origin.get('decision_ref'):
                        fail(f'{eid}: branch must originate from its Decision step')
                    if edge['rule_ref'] not in rules or edge['rule_ref'] not in origin.get('evaluated_rules', []):
                        fail(f'{eid}: branch needs evaluated BusinessRule')
                    if edge['rule_outcome'] not in {'true', 'false', 'case'} or not edge['condition'] or edge['condition'] == 'UNKNOWN':
                        fail(f'{eid}: branch condition/outcome must be known')
                    value = {'rule_id': edge['rule_ref'], 'outcome': edge['rule_outcome'], 'condition': edge['condition']}
                    if not matches(edge['claim_ids'], edge['from_step'], 'branch_condition', value):
                        fail(f'{eid}: missing branch condition claim')
                elif edge['decision_ref'] is not None or edge['rule_ref'] is not None or edge['rule_outcome'] != 'none' or edge['condition'] is not None:
                    fail(f'{eid}: branch metadata belongs only to rule_branch')
                before = scenario_steps.get(edge['to_step'], {}).get('state_before')
                after = scenario_steps.get(edge['from_step'], {}).get('state_after')
                if before and after and before != after and not matches(edge['claim_ids'], edge['from_step'],
                        'state_handoff', {'from_state': after, 'to_state': before}):
                    fail(f'{eid}: state continuity mismatch requires explicit state handoff evidence')
                if edge['kind'] == 'retry' and not any(claims.get(c, {}).get('subject_id') == edge['from_step'] and
                        claims[c]['predicate'] == 'retry_bounds' for c in edge['claim_ids'] if c in claims):
                    if not open_gaps(edge['gap_ids'], edge['from_step']):
                        fail(f'{eid}: retry bounds require source claim or explicit Gap')
            flows = index(artifact['flows'], 'scenario flows')
            main_ids = [f['id'] for f in flows.values() if f['type'] == 'main']
            if len(main_ids) > 1 or artifact['main_flow'] != (main_ids[0] if len(main_ids) == 1 else None):
                fail('scenario: main_flow must reference the sole main flow; no second happy path')
            for selector, category in (('alternative_flows', 'alternative'), ('exception_flows', 'error')):
                if set(artifact[selector]) != {f['id'] for f in flows.values() if f['type'] == category}:
                    fail(f'scenario: {selector} must select exactly the {category} flows')
            main = flows.get(artifact['main_flow'], {})
            main_orders = [scenario_steps[s]['order'] for s in main.get('step_refs', []) if s in scenario_steps]
            if main_orders != sorted(main_orders):
                fail('scenario: main_flow order must agree with process display order')
            used_steps, used_pairs = set(), set()
            for path in flows.values():
                fid = path['id']
                refs(path['step_refs'], scenario_steps, fid)
                refs(path['terminal_steps'], scenario_steps, fid)
                refs(path['gap_ids'], gaps, fid)
                refs(path['conflict_ids'], conflicts, fid)
                supported_refs(path['type_claim_ids'], fid)
                claims_from_sources(path['type_claim_ids'], list(accepted), fid)
                if not matches(path['type_claim_ids'], artifact['scenario_id'], 'flow_type', {'flow_id': fid, 'type': path['type']}):
                    fail(f'{fid}: flow classification requires matching source-backed claim')
                if path['entry_step'] != path['step_refs'][0]:
                    fail(f'{fid}: entry must be first step')
                if not set(path['terminal_steps']) <= set(path['step_refs']):
                    fail(f'{fid}: terminal must belong to flow')
                if path['entry_condition'] == 'UNKNOWN':
                    if not open_gaps(path['gap_ids'], artifact['scenario_id']):
                        fail(f'{fid}: unknown entry condition requires Gap')
                    if path['condition_claim_ids']:
                        fail(f'{fid}: unknown entry condition cannot carry factual condition claims')
                else:
                    supported_refs(path['condition_claim_ids'], fid)
                    claims_from_sources(path['condition_claim_ids'], list(accepted), fid)
                    if not matches(path['condition_claim_ids'], artifact['scenario_id'], 'flow_condition', path['entry_condition']):
                        fail(f'{fid}: missing flow condition claim')
                if path['type'] == 'main' and path['branch_from'] is not None:
                    fail(f'{fid}: main flow cannot have branch origin')
                if path['branch_from'] is not None:
                    refs([path['branch_from']], scenario_steps, fid)
                    if not any(edge['from_step'] == path['branch_from'] and edge['to_step'] == path['entry_step'] for edge in transitions.values()):
                        fail(f'{fid}: branch origin must link to entry')
                    used_pairs.add((path['branch_from'], path['entry_step']))
                for pair in zip(path['step_refs'], path['step_refs'][1:]):
                    used_pairs.add(pair)
                    if pair not in all_pairs:
                        fail(f'{fid}: missing transition {pair}')
                used_steps |= set(path['step_refs'])
                if not path['terminal_steps'] and not open_gaps(path['gap_ids'], artifact['scenario_id']):
                    fail(f'{fid}: flow needs known terminal or Gap')
            if used_steps != set(scenario_steps):
                fail('scenario: orphan steps are not part of a flow')
            for edge in transitions.values():
                if edge['kind'] == 'retry' and any(edge['from_step'] in f['step_refs'] and edge['to_step'] in f['step_refs'] for f in flows.values()):
                    used_pairs.add((edge['from_step'], edge['to_step']))
            if not all_pairs <= used_pairs:
                fail('scenario: transition is absent from flows')
            coverage = index([dict(row, id=row['category']) for row in artifact['flow_coverage']], 'flow coverage')
            if set(coverage) != {'main', 'alternative', 'error'}:
                fail('scenario: coverage requires main, alternative and error')
            for category, row in coverage.items():
                refs(row['flow_ids'], flows, category)
                refs(row['source_ids'], accepted, category)
                supported_refs(row['claim_ids'], category)
                if row['status'] == 'found' and (not row['flow_ids'] or not row['source_ids']):
                    fail(f'{category}: found requires flows and sources')
                if row['status'] == 'not_found' and (row['flow_ids'] or not row['source_ids']):
                    fail(f'{category}: not_found requires surveyed sources and no flows')
                if row['status'] == 'not_applicable' and not row['claim_ids']:
                    fail(f'{category}: not_applicable requires support')
                for fid in row['flow_ids']:
                    if fid in flows and flows[fid]['type'] != category:
                        fail(f'{category}: flow type mismatch')
            if artifact['main_flow'] is None and (artifact['coverage']['status'] != 'partial' or
                    not open_gaps(artifact['gap_ids'], artifact['scenario_id'])):
                fail('scenario: unknown main_flow requires partial coverage and an affected open Gap')
            for path in flows.values():
                row = coverage.get(path['type'], {})
                if row.get('status') != 'found' or path['id'] not in row.get('flow_ids', []):
                    fail(f'{path["id"]}: flow must appear in found coverage')
            for key, typ in {'confluence_evidence_ids': 'CONFLUENCE', 'test_evidence_ids': 'TEST'}.items():
                refs(artifact[key], evidence, key)
                for eid in artifact[key]:
                    if evidence.get(eid, {}).get('source_type') != typ:
                        fail(f'{key}: wrong evidence type')
                    if evidence.get(eid, {}).get('snapshot_id') not in {s['snapshot_ref'] for s in accepted.values()}:
                        fail(f'{key}: evidence is outside accepted source map')
            for key in ('gap_ids', 'conflict_ids'):
                refs(artifact[key], gaps if key == 'gap_ids' else conflicts, 'scenario')
            if artifact['coverage']['status'] == 'complete' and (
                not any(f['type'] == 'main' for f in flows.values()) or artifact['gap_ids'] or artifact['conflict_ids'] or
                artifact['coverage']['limitations'] or artifact['coverage']['frontier'] or
                any(s['unknown_fields'] or s['gap_ids'] or s['conflict_ids'] for s in scenario_steps.values()) or
                any(e['kind'] == 'unresolved' or e['gap_ids'] or e['conflict_ids'] for e in transitions.values()) or
                any(f['gap_ids'] or f['conflict_ids'] for f in flows.values()) or
                any(row['status'] in {'incomplete', 'unavailable'} for row in coverage.values()) or
                any(x['coverage']['status'] == 'partial' for x in (flow, business_rules, source_map, domain_tree))):
                fail('scenario: unresolved knowledge or upstream limits require partial coverage')
            return list(dict.fromkeys(errors))
        if artifact['technical_flow_ref'] != flow['id'] or artifact['source_map_ref'] != source_map['id']:
            fail('business-rules: input artifact ID mismatch')
        if artifact['scenario_id'] != flow['scenario_id']:
            fail('business-rules: scenario mismatch')
        rules = index(artifact['rules'], 'business rules')
        scalar_fields = ('rule_statement', 'condition', 'true_result', 'false_result',
                         'externally_visible_result', 'business_rationale')
        list_fields = ('affected_actor', 'affected_scenario', 'affected_state', 'implementation', 'parameters')
        for rule in rules.values():
            rid = rule['id']
            if entities.get(rid, {}).get('type') != 'BusinessRule':
                fail(f'{rid}: rule needs BusinessRule entity')
            refs(rule['source_ids'], accepted, rid)
            refs(rule['evidence'], evidence, rid)
            refs(rule['gap_ids'], gaps, rid)
            refs(rule['conflict_ids'], conflicts, rid)
            if artifact['scenario_id'] not in rule['affected_scenario']:
                fail(f'{rid}: must affect input scenario')
            if scope['scenarios'] and not set(rule['affected_scenario']) <= set(scope['scenarios']):
                fail(f'{rid}: affected scenario outside scope')
            if rule['rule_statement'] == 'UNKNOWN':
                fail(f'{rid}: a rule must have a known statement')
            for field, allowed_types in {'affected_actor': {'Actor'}, 'affected_scenario': {'Scenario'},
                    'affected_state': {'State'}, 'implementation': {'CodeComponent', 'ConfigRule', 'ApiOperation'}}.items():
                for target in rule[field]:
                    if entities.get(target, {}).get('type') not in allowed_types:
                        fail(f'{rid}/{field}: invalid target {target}')
            if not set(rule['implementation']) <= component_ids:
                fail(f'{rid}: implementation is absent from technical-flow')
            unknown, na = set(rule['unknown_fields']), set(rule['not_applicable_fields'])
            if unknown & na or not (unknown | na) <= set(scalar_fields + list_fields):
                fail(f'{rid}: invalid unknown/not_applicable fields')
            open_gaps = [gaps[g] for g in rule['gap_ids'] if g in gaps and gaps[g]['status'] == 'open' and rid in gaps[g]['affected_ids']]
            if unknown and not open_gaps:
                fail(f'{rid}: unknown fields require affected open Gap')
            if rule['business_rationale'] == 'UNKNOWN':
                if 'business_rationale' not in unknown or not any(g['reason'] == 'unknown_reason' for g in open_gaps):
                    fail(f'{rid}: UNKNOWN rationale requires unknown_reason Gap')
            check_field(rule, 'rule_kind', 'rule_kind', rule['rule_kind'])
            for field in scalar_fields:
                empty = rule[field] == 'UNKNOWN'
                if empty != (field in unknown | na):
                    fail(f'{rid}/{field}: UNKNOWN marker/status mismatch')
                if not empty:
                    check_field(rule, field, field, rule[field])
            for field in list_fields:
                if not rule[field] and field not in unknown | na:
                    fail(f'{rid}/{field}: empty list requires unknown/not_applicable')
                if rule[field] and field in unknown | na:
                    fail(f'{rid}/{field}: known list cannot be unknown/not_applicable')
                for i, value in enumerate(rule[field]):
                    check_field(rule, f'{field}/{i}', field, value)
            for field in na:
                cids = rule['attribute_claims'].get(f'not_applicable/{field}', [])
                supported_refs(cids, rid)
                if not cids or not any(claims.get(c, {}).get('subject_id') == rid and
                    claims[c]['predicate'] == 'not_applicable' and claims[c]['value'] == field for c in cids if c in claims):
                    fail(f'{rid}/{field}: not_applicable requires explicit claim')
            field_cids = [cid for cids in rule['attribute_claims'].values() for cid in cids]
            supported_refs(field_cids, rid)
            claims_from_sources(field_cids, rule['source_ids'], rid)
            for cid in field_cids:
                for support in claims.get(cid, {}).get('support', []):
                    if support['role'] == 'supports' and support['evidence_id'] not in rule['evidence']:
                        fail(f'{rid}: evidence list omits field support {support["evidence_id"]}')
            for field in ('business_rationale', 'rule_kind'):
                if field == 'business_rationale' and rule[field] == 'UNKNOWN':
                    continue
                if field == 'rule_kind' and rule[field] not in {'business_rule', 'eligibility'}:
                    continue
                cids = rule['attribute_claims'].get(field, [])
                if any(claims.get(c, {}).get('inference') for c in cids):
                    fail(f'{rid}/{field}: inference cannot supply business meaning')
                if not any(claims.get(c, {}).get('modality') in {'documented_requirement', 'source_statement'} and
                           any(evidence.get(s['evidence_id'], {}).get('source_type') in ROOT_TYPES and s['role'] == 'supports'
                               for s in claims[c]['support']) for c in cids if c in claims):
                    fail(f'{rid}/{field}: explicit source-stated business meaning required')
        coverage = index([dict(c, id=c['category']) for c in artifact['category_coverage']], 'rule coverage')
        if set(coverage) != RULE_CATEGORIES:
            fail('business-rules: coverage must include all nine extraction categories')
        for rule in rules.values():
            for category in rule['extraction_categories']:
                row = coverage.get(category, {})
                if row.get('status') != 'found' or rule['id'] not in row.get('rule_ids', []):
                    fail(f'{rule["id"]}: extracted category {category} must appear in found coverage')
        for category, row in coverage.items():
            refs(row['source_ids'], accepted, category)
            refs(row['rule_ids'], rules, category)
            supported_refs(row['claim_ids'], category)
            if row['status'] == 'found' and (not row['source_ids'] or not row['rule_ids']):
                fail(f'{category}: found needs sources and rules')
            for rid in row['rule_ids']:
                if rid in rules and category not in rules[rid]['extraction_categories']:
                    fail(f'{category}: rule category mismatch')
            if row['status'] == 'not_found' and (not row['source_ids'] or row['rule_ids']):
                fail(f'{category}: not_found needs surveyed sources and no rules')
            if row['status'] == 'not_applicable' and not row['claim_ids']:
                fail(f'{category}: not_applicable needs support')
        refs(artifact['gap_ids'], gaps, artifact['id'])
        refs(artifact['conflict_ids'], conflicts, artifact['id'])
        if artifact['coverage']['status'] == 'complete' and (artifact['gap_ids'] or artifact['conflict_ids'] or
                artifact['coverage']['limitations'] or artifact['coverage']['frontier'] or
                any(r['unknown_fields'] or r['gap_ids'] or r['conflict_ids'] for r in rules.values()) or
                any(c['status'] in {'unavailable', 'incomplete'} for c in coverage.values())):
            fail('business-rules: unresolved knowledge requires partial coverage')
    return list(dict.fromkeys(errors))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('kind', choices=['knowledge-package', 'domain-tree', 'scenario-definition', 'source-map', 'technical-flow', 'business-rules', 'scenario'])
    parser.add_argument('artifact', type=Path)
    parser.add_argument('--knowledge', type=Path, required=True)
    parser.add_argument('--domain-tree', type=Path)
    parser.add_argument('--scenario-definition', type=Path)
    parser.add_argument('--technical-flow', type=Path)
    parser.add_argument('--source-map', type=Path)
    parser.add_argument('--business-rules', type=Path)
    parser.add_argument('--previous-knowledge', type=Path,
                        help='Compare with the previous stage package (structured profile).')
    args = parser.parse_args()
    try:
        errors = validate(args.kind, load(args.artifact), load(args.knowledge),
                          load(args.domain_tree) if args.domain_tree else None,
                          load(args.scenario_definition) if args.scenario_definition else None,
                          load(args.technical_flow) if args.technical_flow else None,
                          load(args.source_map) if args.source_map else None,
                          load(args.business_rules) if args.business_rules else None,
                          load(args.previous_knowledge) if args.previous_knowledge else None)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        parser.exit(2, f'{exc}\n')
    for error in errors:
        print(error)
    if errors:
        raise SystemExit(1)
    print('Mechanical validation passed. Semantic source review is required.')


if __name__ == '__main__':
    main()
