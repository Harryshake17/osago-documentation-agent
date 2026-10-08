"""Read-only pipeline gates over accepted artifacts; no scoring, repairs or discovery."""
import hashlib
import re
from markdown_it import MarkdownIt
from audit import digest
from compose import SECTION_IDS, STANDARDS, template_sections
from publication import publication_errors
from validate import schema_errors, validate

MD = MarkdownIt('commonmark', {'html': False}).enable('table')
GATES = ('technical-model', 'scenario-model', 'publication-relevance', 'document-structure', 'final-invariants')
OWNERS = {'technical-model': 'osago-technical-flow-analyzer',
          'scenario-model': 'osago-scenario-reconstructor',
          'publication-relevance': 'osago-evidence-gap-validator',
          'document-structure': 'osago-documentation-composer',
          'final-invariants': 'osago-language-reviewer'}
INTERNAL = re.compile(r'\b(?:entity|claim|evidence|snapshot|source|scenario-step|scenario-flow|step:flow|technical-step|domain|scope|kb|rule|actor|integration|comparison|finding|gap|component):[\w:./-]+|\b(?:pageId\s*[=: ]\s*\d+|derived_from|source_fields)\b')
LOCAL = re.compile(r'(?<!\w)(?:\.\.[\\/]|[A-Za-z]:[\\/]|\\\\)[^\s<>]+|(?<![\w:/])(?:sources|runs|tools|\.codex|\.cursor|\.tmp)/[^\s<>]+|(?<![\w:/])/(?:home|tmp|mnt|Users|workspace)/[^\s<>]+|[^\s<>]*\.(?:cs|spec\.ts|mmd)\b')
DUPLICATE = re.compile(r'(?i)^(?:(?:UC\s*(?:[-\w]+\s*)?[:—-]?\s*)?(?:main[ _-]*flow|happy[ _-]*path)|use case(?:\s*[:—-].*)?|основной поток scenario)\b')


class PipelineGateError(ValueError):
    pass


def reject(gate, code, detail):
    raise PipelineGateError(f'[{gate}/{code}] {detail}; return output to {OWNERS[gate]}. Publication stopped; no artifact was repaired.')


def mandatory_gates(stage):
    driver, primary = stage['validator'], stage.get('primary')
    if driver == 'artifact' and primary == 'technical-flow': return ['technical-model']
    if driver == 'artifact' and primary == 'scenario': return ['scenario-model']
    return {'validation': ['scenario-model', 'publication-relevance'],
            'documentation': ['document-structure'], 'language_review': ['final-invariants']}.get(driver, [])


def effective_gates(stage):
    # Historical snapshots get the same safety floor without rewriting their DAG.
    return list(dict.fromkeys(mandatory_gates(stage) + stage.get('gates', [])))


def structured_errors(kind, artifact, inputs):
    names = {'domain-tree': 'domain_tree', 'scenario-definition': 'scenario_definition',
             'technical-flow': 'technical_flow', 'source-map': 'source_map', 'business-rules': 'business_rules'}
    return validate(kind, artifact, inputs['knowledge'], **{
        arg: inputs[name] for name, arg in names.items() if name != kind and name in inputs})


def technical_model(inputs):
    gate = 'technical-model'
    flow = inputs['technical-flow']
    if 'steps' in flow:
        reject(gate, 'COMPETING_COLLECTIONS', 'technical-flow has steps as well as canonical nodes')
    ids = [n['id'] for n in flow.get('nodes', [])]
    if len(ids) != len(set(ids)):
        reject(gate, 'DUPLICATE_ID', 'technical node IDs are not unique')
    if any(not ident.startswith('technical-step:') for ident in ids):
        reject(gate, 'WRONG_NAMESPACE', 'technical node IDs must belong to technical-step:, never Scenario steps')
    errors = structured_errors('technical-flow', flow, inputs)
    if errors: reject(gate, 'SCHEMA_OR_REFS', '\n'.join(errors))


def scenario_model(inputs):
    gate = 'scenario-model'
    scenario, flow = inputs['scenario'], inputs['technical-flow']
    mains = [f['id'] for f in scenario.get('flows', []) if f['type'] == 'main']
    if len(mains) != 1 or scenario.get('main_flow') != mains[0] or 'happy_path' in scenario:
        reject(gate, 'CANONICAL_MAIN_FLOW', 'exactly one classified main Flow and its main_flow selector are required')
    for collection in ('steps', 'flows', 'transitions'):
        ids = [row['id'] for row in scenario.get(collection, [])]
        if len(ids) != len(set(ids)):
            reject(gate, 'DUPLICATE_ID', 'duplicate canonical Scenario ' + collection + ' ID')
    technical_ids = {n['id'] for n in flow['nodes']}
    scenario_ids = {s['id'] for s in scenario['steps']}
    if technical_ids & scenario_ids or any(not s.startswith('scenario-step:') for s in scenario_ids):
        reject(gate, 'TECHNICAL_AS_SCENARIO', 'technical node cannot be a Scenario step; use technical_step_refs')
    errors = structured_errors('scenario', scenario, inputs)
    if errors: reject(gate, 'SCHEMA_OR_REFS', '\n'.join(errors))


def publication_relevance(report, gaps, inputs):
    gate = 'publication-relevance'
    errors = schema_errors('validation-report', report) + schema_errors('validation-gaps', gaps)
    if errors: reject(gate, 'SCHEMA', '\n'.join(errors))
    pending = [item['id'] for item in report['findings'] + gaps['gaps']
               if not item['publication_relevance']['reviewed'] or
                  item['publication_relevance']['classification'] == 'UNASSESSED']
    if pending: reject(gate, 'UNASSESSED', 'publication relevance review is incomplete: ' + ', '.join(pending))
    errors = publication_errors(report, gaps, inputs)
    if errors: reject(gate, 'SUBSET_OR_IMPACT', '\n'.join(errors))


def _plain(tokens):
    parts = []
    for token in tokens:
        if token.type in {'text', 'code_inline', 'code_block', 'fence', 'html_inline', 'html_block'}:
            parts.append(token.content)
        elif token.type in {'softbreak', 'hardbreak'}: parts.append(' ')
        if token.children: parts.append(_plain(token.children))
    return ''.join(parts)


def _words(text):
    return re.findall(r'>=|<=|==|!=|≥|≤|>|<|[\w]+', text.casefold())


def _surface(text):
    return _plain(MD.parse(text))


def _anchors(text, inputs):
    # Verify unchanged lexical anchors after known display substitutions. This is
    # not a paraphrase score or a claim of semantic equivalence of arbitrary text.
    terms = {t['entity_ref']: t for t in inputs['glossary']['terms']}
    displays = {}
    for entity in inputs['knowledge']['entities']:
        term = terms.get(entity['id'], entity)
        value = term['preferred_name']
        label = value['value'] if value['value'] and value['status'] in {'CONFIRMED', 'PARTIALLY_CONFIRMED'} else (
            'CONFLICT' if term.get('status', value['status']) == 'CONFLICT' else 'UNKNOWN')
        spellings = {entity['id'], *entity.get('technical_aliases', []), *term.get('technical_aliases', [])}
        if value['value']: spellings.add(value['value'])
        for spelling in spellings: displays.setdefault(spelling, set()).add(label)
    text = _surface(text)
    if displays:
        pattern = re.compile(r'(?<![\w.])(?:' + '|'.join(re.escape(s) for s in sorted(displays, key=lambda s: (-len(s), s))) + r')(?![\w]|\.[\w])')
        text = pattern.sub(lambda m: next(iter(displays[m.group()])) if len(displays[m.group()]) == 1 else 'UNKNOWN', text)
    return _words(LOCAL.sub(' ', INTERNAL.sub(' ', text)))


def _visible(source, body, inputs):
    anchors = _anchors(source, inputs)
    if not anchors: return False
    actual = iter(_words(_surface(body)))
    return all(any(word == expected for word in actual) for expected in anchors)


def _block_text(document, block):
    lines = document.splitlines()
    return '\n'.join(lines[block['start_line'] - 1:block['end_line']])


def material_visibility(document, manifest, inputs, blocks, gate):
    gaps, report = inputs['gaps'], inputs['report']
    gap_ids, finding_ids = (set(gaps['publication_subset'][key]) for key in ('gap_ids', 'finding_ids'))
    linked = {link['finding_id'] for link in gaps['finding_gap_links'] if gap_ids & set(link['gap_ids'])}
    required = [('validation-gaps', g, 'question') for g in gaps['gaps'] if g['id'] in gap_ids]
    required += [('validation-report', f, 'reason') for f in report['findings'] if f['id'] in finding_ids - linked]
    for artifact, record, field in required:
        visible = [b for b in blocks if b['section'] == 'gaps' and
                   dict(artifact=artifact, record=record['id'], field=field) in b['source_fields']]
        if not any(_visible(record[field], _block_text(document, b), inputs) for b in visible):
            reject(gate, 'MATERIAL_GAP_HIDDEN', 'publication-relevant item not visible in a traced gaps block: ' + record['id'])
    material = {ref for g in gaps['gaps'] if g['id'] in gap_ids for ref in g['affected_ids']}
    material.update(cid for f in report['findings'] if f['id'] in finding_ids for cid in f['claim_ids'])
    conflicts = [c for c in report['comparisons'] if c['status'] in {'CONFLICT', 'UNRESOLVED'}]
    conflicts += [c for c in inputs['knowledge']['conflicts'] if c['status'] == 'unresolved']
    claims = {c['id']: c for c in inputs['knowledge']['claims']}
    for conflict in conflicts:
        cids = set(conflict['claim_ids'])
        if not cids & material: continue
        traced = [b for b in blocks if b['section'] == 'gaps' and cids & set(b['derived_from'])]
        if not any(cids <= set(b['derived_from']) and 'CONFLICT' in _block_text(document, b) for b in traced):
            reject(gate, 'MATERIAL_CONFLICT_HIDDEN', 'missing unresolved conflict disclosure: ' + conflict['id'])
        for cid in cids:
            value = claims[cid]['value']
            alternatives = [b for b in traced if cid in b['derived_from'] and
                            'CONFLICT' not in _block_text(document, b)]
            if not any(_surface(_block_text(document, b)).strip() and
                       (not isinstance(value, str) or _visible(value, _block_text(document, b), inputs)) for b in alternatives):
                reject(gate, 'CONFLICT_VERSION_HIDDEN', 'missing contested claim version: ' + cid)


def document_structure(document, manifest, inputs, *, blocks=None, gate='document-structure'):
    tokens = MD.parse(document)
    heads = [(t.tag, _plain(tokens[i + 1:i + 2]), t.map[0]) for i, t in enumerate(tokens) if t.type == 'heading_open']
    expected = [h.removeprefix('## ') for h in template_sections((STANDARDS / 'documentation-template.md').read_text(encoding='utf-8'))]
    h2 = [text for tag, text, line in heads if tag == 'h2']
    main_count = sum(text == expected[4] for tag, text, line in heads)
    if main_count != 1: reject(gate, 'MAIN_FLOW_COUNT', f'exactly one main process section required; found {main_count}')
    if h2 != expected or sum(tag == 'h1' for tag, text, line in heads) != 1:
        reject(gate, 'READER_FIRST_SECTIONS', 'mandatory sections must occur once in shared-template order, process before technical implementation')
    if any(DUPLICATE.search(text) for tag, text, line in heads) or any(
            DUPLICATE.search(_plain([t])) for t in tokens if t.type == 'inline'):
        reject(gate, 'APPENDED_PROCESS_COPY', 'appended UC/main flow/happy path representation is not allowed')
    starts = [line for tag, text, line in heads if tag == 'h2']
    section_at = lambda line: next((SECTION_IDS[i] for i in range(len(starts) - 1, -1, -1) if line >= starts[i]), 'title')
    tables = []
    for i, token in enumerate(tokens):
        if token.type != 'table_open': continue
        end = next(j for j in range(i + 1, len(tokens)) if tokens[j].type == 'table_close')
        rows = []
        for j in range(i + 1, end):
            if tokens[j].type == 'tr_open':
                close = next(k for k in range(j + 1, end) if tokens[k].type == 'tr_close')
                rows.append([_plain([t]) for t in tokens[j + 1:close] if t.type == 'inline'])
        if rows and rows[0] == ['Шаг', 'Кто', 'Что происходит', 'Правила', 'Интеграции', 'Результат']:
            tables.append((section_at(token.map[0]), rows))
    main = next(f for f in inputs['scenario']['flows'] if f['id'] == inputs['scenario']['main_flow'])
    if len(tables) != 1 or tables[0][0] != 'main-flow':
        reject(gate, 'COMPETING_FLOW_TABLES', 'exactly one canonical main process table is required')
    rows = tables[0][1][1:]
    if len(rows) != len(main['step_refs']) or [r[0] for r in rows] != [str(i) for i in range(1, len(rows) + 1)]:
        reject(gate, 'MAIN_FLOW_ROWS', 'main process row count/order must match canonical Scenario step_refs')
    blocks = manifest['document']['blocks'] if blocks is None else blocks
    lines = document.splitlines()
    end = 0
    for block in blocks:
        start, stop = block['start_line'], block['end_line']
        if not 1 <= start <= stop <= len(lines) or start <= end or any(
                section_at(line) != block['section'] for line in range(start - 1, stop)):
            reject(gate, 'PROVENANCE_SPANS', 'provenance blocks overlap or cross their declared document section')
        end = stop
    actual_steps = [f['record'] for b in blocks if b['section'] == 'main-flow'
                    for f in b['source_fields'] if f['artifact'] == 'scenario' and f['field'] == 'business_action']
    if actual_steps != main['step_refs']:
        reject(gate, 'SCENARIO_LINEAGE', 'main flow provenance must follow canonical Scenario step_refs exactly')
    for token in tokens:
        if token.map is None or section_at(token.map[0]) in {'technical', 'evidence'}: continue
        raw = '\n'.join(lines[token.map[0]:token.map[1]])
        # Remote link destinations are private locators behind human-readable
        # labels (Confluence pageId is common); local targets remain forbidden.
        raw = re.sub(r'(\[[^\]\n]*\])\(https?://[^)\n]*\)', r'\1', raw)
        text = _plain([token]) + '\n' + raw
        if INTERNAL.search(text) or re.search(r'\b(?:TERM-[A-Z0-9]+|[PEA]\d+|BR-[A-Z0-9-]+)\b', text):
            reject(gate, 'INTERNAL_ID_IN_NARRATIVE', f'internal metadata/ID in reader section at line {token.map[0] + 1}')
        if LOCAL.search(text):
            reject(gate, 'FILESYSTEM_PATH_IN_NARRATIVE', f'raw filesystem locator in reader section at line {token.map[0] + 1}')
    material_texts = {_surface(record[field]).strip() for artifact, record, field in
                      [('validation-gaps', g, 'question') for g in inputs['gaps']['gaps'] if g['id'] in inputs['gaps']['publication_subset']['gap_ids']]}
    internal = [('validation-gaps', g, 'question') for g in inputs['gaps']['gaps'] if g['publication_relevance']['classification'] == 'INTERNAL_RESEARCH']
    internal += [('validation-report', f, 'reason') for f in inputs['report']['findings'] if f['publication_relevance']['classification'] == 'INTERNAL_RESEARCH']
    surfaces = [_surface(_block_text(document, b)) for b in blocks]
    surfaces += [_plain([t]) for t in tokens if t.type == 'inline']
    for artifact, record, field in internal:
        reference = dict(artifact=artifact, record=record['id'], field=field)
        text = _surface(record[field]).strip()
        if any(reference in b['source_fields'] for b in blocks) or (
                text and text not in material_texts and any(text in body for body in surfaces)):
            reject(gate, 'INTERNAL_RESEARCH_GAP', 'internal research item rendered in Markdown: ' + record['id'])
    material_visibility(document, manifest, inputs, blocks, gate)


def final_invariants(document, draft, manifest, review, inputs):
    gate = 'final-invariants'
    errors = schema_errors('language-review', review) + schema_errors('documentation-manifest', manifest)
    if errors: reject(gate, 'SCHEMA', '\n'.join(errors))
    sha = lambda value: hashlib.sha256(value.encode('utf-8')).hexdigest()
    if review['review']['status'] != 'COMPLETED' or review['final_hash'] != sha(document) or review['inputs']['draft_hash'] != sha(draft):
        reject(gate, 'REVIEW_BINDING', 'COMPLETED review must bind exact draft and final bytes')
    if (review['inputs'].get('manifest_hash') != digest(manifest) or
            review['inputs']['validation_hash'] != digest(inputs['report']) or
            review['inputs']['scenario_hash'] != digest(inputs['scenario']) or
            review['inputs']['glossary_hash'] != digest(inputs['glossary']) or
            review['claim_ids'] != manifest['claim_ids'] or manifest['claim_ids'] != inputs['report']['claim_inventory'] or
            review['blocks'] != manifest['document']['blocks'] or
            review['publication_gate'] != manifest['publication_gate'] or
            manifest['publication_gate'] != inputs['report']['summary']['publication_gate']):
        reject(gate, 'FACTUAL_LINEAGE_LOST', 'Claim inventory, manifest/blocks or publication gate changed')
    if any(review['review']['semantic_validation'].values()) or review['review']['protected_content_changes']['count']:
        reject(gate, 'DECLARED_INVARIANT_FAILURE', 'review report records changed knowledge or protected content')
    document_structure(document, manifest, inputs, blocks=review['blocks'], gate=gate)


def run_gate(name, data, inputs, *, document=None, draft=None, context=None):
    if name == 'technical-model': technical_model(dict(inputs, **data))
    elif name == 'scenario-model': scenario_model(dict(inputs, **data))
    elif name == 'publication-relevance': publication_relevance(data['validation-report'], data['gaps'], inputs)
    elif name == 'document-structure': document_structure(document, data['documentation-manifest'], inputs)
    elif name == 'final-invariants': final_invariants(document, draft, inputs['manifest'], data['language-review'], context)
    else: raise PipelineGateError('Unknown pipeline gate: ' + name)
