"""Render reviewed knowledge artifacts. No discovery, code analysis or new claims."""
import argparse
import copy
import html
import hashlib
import json
import re
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import yaml
from audit import REQUIRED_INPUTS, check_report, digest
from validate import load, schema_errors, validate
from glossary import glossary_errors, status_of
from model import BUSINESS_MODALITIES


def cell(value):
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, sort_keys=True)
    text = html.escape(text, quote=False)
    for char in ('\\', '`', '*', '_', '[', ']', '#'):
        text = text.replace(char, '\\' + char)
    return text.replace('|', '&#124;').replace('\r', '').replace('\n', '<br>')


def badge(review):
    return f'[{review["status"]}; reviewed={str(review["reviewed"]).lower()}]'


from paths import contracts_root

STANDARDS = contracts_root() / 'standards'
SECTION_IDS = ('purpose', 'scope', 'participants', 'preconditions', 'main-flow', 'business-rules',
               'states', 'alternatives', 'integrations', 'technical', 'evidence', 'gaps')
UNKNOWN = '[UNKNOWN — предметные данные не предоставлены]'


def template_sections(template):
    headings = re.findall(r'^## (\d+)\. (.+)$', template, re.MULTILINE)
    if [int(n) for n, _ in headings] != list(range(1, 13)):
        raise ValueError('documentation template must contain the twelve ordered sections')
    return [f'## {n}. {title}' for n, title in headings]


def anchor(kind, identifier):
    return kind + '-' + hashlib.sha256(identifier.encode('utf-8')).hexdigest()[:16]


def compose(inputs, report, gaps, glossary=None, *, template=None):
    required = {'knowledge', 'domain-tree', 'technical-flow', 'business-rules', 'scenario'}
    missing = required - inputs.keys()
    if missing or glossary is None:
        raise ValueError('Missing required Composer inputs: ' + ', '.join(sorted(missing | (
            {'glossary'} if glossary is None else set()))))
    problems = []
    for kind, artifact in inputs.items():
        if kind not in required | {'source-map', 'scenario-definition'}:
            problems.append('Unsupported Composer input: ' + kind)
        else:
            problems += schema_errors('knowledge-package' if kind == 'knowledge' else kind, artifact)
    if problems:
        raise ValueError('\n'.join(problems))
    problems = check_report(report, gaps, inputs, allow_omitted_inputs={'source-map', 'scenario-definition'})
    problems += glossary_errors(glossary)
    if problems:
        raise ValueError('\n'.join(problems))
    if report['summary']['review_status'] != 'complete' or report['mechanical_errors']:
        raise ValueError('Composer requires completed claim review and structurally valid inputs; return to Skill 6.')
    k, scenario, rules, technical = (inputs[x] for x in ('knowledge', 'scenario', 'business-rules', 'technical-flow'))
    # Optional source-map remains in the original review manifest; no source is reopened.
    problems = validate('knowledge-package', k, k) + validate('domain-tree', inputs['domain-tree'], k)
    if inputs.get('scenario-definition') is not None:
        problems += validate('scenario-definition', inputs['scenario-definition'], k)
    if problems:
        raise ValueError('\n'.join(problems))
    entities = {e['id']: e for e in k['entities']}
    claims = {c['id']: c for c in k['claims']}
    reviews = {r['claim_id']: r for r in report['claim_reviews']}
    runtime_checks = {c['id']: c for c in k.get('runtime_confirmations', [])}
    runtime_reviews = {r['confirmation_ref']: r for r in report.get('runtime_reviews', [])}
    runtime_traces = {t['id']: t for t in k.get('runtime_traces', [])}
    if any(item['status'] == 'open' and not item['publication_relevance']['reviewed']
           for item in report['findings'] + gaps['gaps']):
        raise ValueError('Composer requires completed publication relevance review; return to Skill 6.')
    nodes = {n['id']: n for n in inputs['domain-tree']['nodes']}
    if scenario['scenario_id'] not in nodes:
        raise ValueError('Scenario must resolve to its Domain Model node')
    definition = nodes[scenario['scenario_id']]
    terms = {}
    for term in glossary['terms']:
        eid = term['entity_ref']
        if eid not in entities:
            continue
        if term['identity_key'] != entities[eid].get('identity_key'):
            raise ValueError('glossary/current Entity identity mismatch: ' + eid)
        terms[eid] = term
    # A global glossary may have a newer terminology revision. Existing immutable
    # Claim/Evidence/Snapshot IDs must still mean exactly the same thing.
    for provenance in glossary['provenance']:
        for group in ('claims', 'evidence', 'sources'):
            current = {r['id']: r for r in k[group]}
            for row in provenance['knowledge'][group]:
                immutable = {key: value for key, value in row.items() if group != 'evidence' or key != 'supports'}
                baseline = {key: value for key, value in current.get(row['id'], {}).items()
                            if group != 'evidence' or key != 'supports'}
                if group == 'claims':
                    keys = ('subject_id', 'predicate', 'value', 'context', 'inference', 'basis_claim_ids')
                    immutable = {key: row.get(key) for key in keys}
                    baseline = {key: current.get(row['id'], {}).get(key) for key in keys}
                if row['id'] in current and immutable != baseline:
                    raise ValueError('glossary/current immutable record mismatch: ' + row['id'])

    template = template if template is not None else (STANDARDS / 'documentation-template.md').read_text(encoding='utf-8')
    style = (STANDARDS / 'writing-style.md').read_text(encoding='utf-8')
    headings = template_sections(template)
    lines, blocks, pending, fields = [], [], set(), []
    section = 'title'

    def use(record, key, artifact):
        pending.add(record['id'])
        ref = dict(artifact=artifact, record=record['id'], field=key)
        if ref not in fields:
            fields.append(ref)

    def emit(text, ids=()):
        pending.update(ids)
        start = len(lines) + 1
        lines.extend(text.split('\n'))
        if pending or fields:
            blocks.append(dict(section=section, start_line=start, end_line=len(lines),
                               derived_from=sorted(pending), source_fields=list(fields)))
        pending.clear()
        fields.clear()

    def sentence(text):
        return text if text.endswith(('.', '!', '?')) else text + '.'

    def heading(index):
        nonlocal section
        section = SECTION_IDS[index]
        emit('\n' + headings[index] + '\n')

    def effective(cid):
        c, r = claims[cid], reviews[cid]
        return status_of(dict(c, knowledge_status=c.get('knowledge_status', r['status'])), r)

    def refs(ids):
        # Full evidence chains stay in provenance; visible prose has no registry links.
        pending.update(ids)
        for cid in ids:
            claim = claims[cid]
            pending.update(claim.get('basis_claim_ids', []))
            for support in claim['support']:
                pending.add(support['evidence_id'])
                evidence = next(e for e in k['evidence'] if e['id'] == support['evidence_id'])
                pending.add(evidence['snapshot_id'])
        return ''

    def code(value):
        text = str(value).replace('|', '&#124;').replace('\n', ' ')
        fence = '`' * (max([len(x) for x in re.findall(r'`+', text)] + [0]) + 1)
        return fence + text + fence

    def clean(text):
        # Redact locators, never print them as factual prose or diagram content.
        text = re.sub(r'(?<!\w)(?:\.\./|\.\.\\|[A-Za-z]:[\\/]|\\\\)[^\s<>]+', 'служебная ссылка', text)
        text = re.sub(r'[^\s<>]*\.(?:mmd|cs|spec\.ts)(?=\s|$|[),;])', 'служебная ссылка', text)
        text = re.sub(r'\b(?:pageId[=: ]+\d+|(?:claim|evidence|snapshot|source|gap|finding|scope|technical-step|scenario-step|scenario-flow|component):[\w:./-]+)\b', 'служебная ссылка', text)
        return text

    def name(eid, *, purpose=False):
        if eid is None:
            return UNKNOWN
        if eid not in entities:
            return cell(clean(str(eid)))
        pending.add(eid)
        if eid in numbers:
            return 'Шаг ' + numbers[eid]
        t = terms.get(eid)
        if t:
            use(t, 'preferred_name', 'glossary')
            v = t['preferred_name']
            pending.update(v['claim_ids'] + v['evidence_ids'])
            statuses = {v['status']}
            statuses.update(effective(cid) for cid in v['claim_ids'] if cid in claims)
            if t['status'] == 'CONFLICT':
                statuses.add('CONFLICT')
            if v['value'] and not statuses & {'UNKNOWN', 'INFERRED', 'CONFLICT'}:
                return cell(clean(v['value'])) + (' [PARTIALLY_CONFIRMED — название требует уточнения]'
                                                if 'PARTIALLY_CONFIRMED' in statuses else '')
        if purpose:
            return UNKNOWN
        status = 'CONFLICT' if t and t['status'] == 'CONFLICT' else 'UNKNOWN'
        # Labels and code aliases cannot supply missing business terminology.
        label = {'Actor': 'Участник сценария', 'Integration': 'Внешняя система',
                 'State': 'Состояние', 'Scenario': 'Сценарий', 'BusinessRule': 'Правило'}.get(
                     entities[eid]['type'], 'Предметное название')
        aliases = (t or entities[eid]).get('technical_aliases', [])
        if entities[eid]['type'] == 'State' and aliases and not re.match(r'\w[\w-]*:', aliases[0]):
            return 'Техническое состояние ' + code(aliases[0]) + f' [{status} — предметное название требует уточнения]'
        if entities[eid]['type'] == 'State' and eid in state_numbers:
            label += ' ' + state_numbers[eid]
        return label + f' [{status} — предметное название требует уточнения]'

    spellings = {}
    for eid, entity in entities.items():
        for spelling in [eid] + entity.get('technical_aliases', []):
            spellings.setdefault(spelling, set()).add(eid)
    token_pattern = re.compile(r'(?<![\w.])(' + '|'.join(re.escape(s) for s in
        sorted(spellings, key=lambda s: (-len(s), s))) + r')(?![\w]|\.[\w])') if spellings else None

    def business_text(value, *, purpose=False):
        if isinstance(value, str):
            if token_pattern:
                def replace(match):
                    ids = spellings[match.group()]
                    if len(ids) != 1:
                        pending.update(ids)
                        return '[UNKNOWN — неоднозначная терминология]'
                    return name(next(iter(ids)), purpose=purpose)
                # Escape each source fragment before inserting already escaped names.
                chunks, end = [], 0
                for match in token_pattern.finditer(value):
                    chunks += [cell(clean(value[end:match.start()])), replace(match)]
                    end = match.end()
                return ''.join(chunks) + cell(clean(value[end:]))
            return cell(clean(value))
        if isinstance(value, (int, float, bool)):
            return cell(value)
        return UNKNOWN

    def fact(value, ids, *, business=True, declared=None, purpose=False, domain_only=False, code_value=True):
        if not ids:
            return UNKNOWN
        if any(cid not in claims for cid in ids):
            raise ValueError('Dangling factual claim reference')
        statuses = {effective(cid) for cid in ids}
        if declared:
            statuses.add(declared)
        refs(ids)
        if 'CONFLICT' in statuses:
            return '[CONFLICT — источники расходятся; см. спорные места]'
        if 'UNKNOWN' in statuses or value is None or value == 'UNKNOWN':
            return '[UNKNOWN — значение не установлено]'
        if business and domain_only and any(claims[cid]['modality'] not in BUSINESS_MODALITIES for cid in ids):
            return UNKNOWN
        text = business_text(value, purpose=purpose) if business else (code(value) if code_value else cell(clean(str(value))))
        if 'INFERRED' in statuses:
            text = '[INFERRED — гипотеза] ' + text
        elif 'PARTIALLY_CONFIRMED' in statuses:
            text = '[PARTIALLY_CONFIRMED — подтверждено частично] ' + text
        return text

    def field(record, key, artifact, *, business=True, purpose=False, domain_only=False, code_value=True):
        if key in record:
            use(record, key, artifact)
        value = record.get(key)
        attrs = record.get('attribute_claims', {})
        if isinstance(value, dict) and {'value', 'status', 'claim_ids', 'evidence_ids'} <= value.keys():
            pending.update(value['evidence_ids'])
            return fact(value['value'], value['claim_ids'], declared=value['status'], business=business,
                        purpose=purpose, domain_only=domain_only, code_value=code_value)
        if isinstance(value, list) and value:
            return '; '.join(fact(v, attrs.get(f'{key}/{i}', []), business=business, purpose=purpose,
                                  domain_only=domain_only, code_value=code_value) for i, v in enumerate(value))
        ids = attrs.get(key, [])
        if ids:
            return fact(value, ids, business=business, purpose=purpose, domain_only=domain_only, code_value=code_value)
        na = attrs.get(f'not_applicable/{key}', [])
        return fact('Не применимо', na, business=business) if na else UNKNOWN

    # Section-centric selection. Artifact registries are lookup tables, not sections.
    by_step = {s['id']: s for s in scenario['steps']}
    by_flow = {f['id']: f for f in scenario['flows']}
    main = by_flow.get(scenario['main_flow'])
    main_steps = [by_step[sid] for sid in main['step_refs']] if main else []
    variants = [by_flow[fid] for fid in scenario['alternative_flows'] + scenario['exception_flows']]
    selected_ids = list(dict.fromkeys([s['id'] for s in main_steps] +
                                     [sid for f in variants for sid in f['step_refs']]))
    selected_steps = [by_step[sid] for sid in selected_ids]
    numbers = {s['id']: str(i) for i, s in enumerate(main_steps, 1)}
    used_rule_ids = {rid for step in selected_steps for rid in step['evaluated_rules']}
    selected_rules = [r for r in rules['rules'] if r['id'] in used_rule_ids]
    rule_numbers = {r['id']: str(i) for i, r in enumerate(selected_rules, 1)}
    technical_nodes = {n['id']: n for n in technical['nodes']}
    selected_integration_ids = list(dict.fromkeys(eid for s in selected_steps for eid in s['integrations']))
    state_ids = list(dict.fromkeys(s[key] for s in selected_steps for key in ('state_before', 'state_after') if s[key]))
    state_numbers = {eid: str(i) for i, eid in enumerate(state_ids, 1)}

    def available(record, key):
        value = record.get(key)
        return value not in (None, [], '', 'UNKNOWN') or bool(record.get('attribute_claims', {}).get(key))

    def optional(record, key, artifact, **kwargs):
        if available(record, key) and key not in record.get('not_applicable_fields', []):
            return field(record, key, artifact, **kwargs)
        return None

    def step_label(step):
        return field(step, 'business_action', 'scenario')

    def rule_label(rid):
        pending.add(rid)
        rule = next(r for r in selected_rules if r['id'] == rid)
        return ('Техническая проверка ' if rule['rule_kind'] == 'technical_constraint' else 'Правило ') + rule_numbers[rid]

    def step_refs(step, key):
        use(step, key, 'scenario')
        for cid in step.get('attribute_claims', {}).get(key, []):
            refs([cid])
        parts = []
        for i, eid in enumerate(step[key]):
            cids = step.get('attribute_claims', {}).get(f'{key}/{i}', [])
            refs(cids)
            if cids and all(effective(cid) == 'CONFIRMED' for cid in cids):
                parts.append(rule_label(eid) if key == 'evaluated_rules' else name(eid))
            else:
                parts.append(fact(eid, cids))
        if parts:
            return '; '.join(parts)
        na = step.get('attribute_claims', {}).get('not_applicable/' + key, [])
        refs(na)
        return '—' if na and all(effective(cid) == 'CONFIRMED' for cid in na) else UNKNOWN

    # A confirmed goal is an acceptable descriptive title, never a preferred term.
    title = name(scenario['scenario_id'], purpose=True)
    if title == UNKNOWN:
        goal = definition.get('business_goal')
        goal_ids = definition.get('attribute_claims', {}).get('business_goal', [])
        if goal and goal_ids and all(effective(cid) == 'CONFIRMED' and
                                    claims[cid]['modality'] in BUSINESS_MODALITIES for cid in goal_ids):
            title = field(definition, 'business_goal', 'domain-tree', purpose=True, domain_only=True)
        else:
            title = 'Описание сценария ОСАГО'
    emit('# ' + title, [scenario['scenario_id']])
    heading(0)
    goal = field(definition, 'business_goal', 'domain-tree', purpose=True, domain_only=True)
    emit(goal)
    result = optional(definition, 'exit_states', 'domain-tree', domain_only=True)
    if result:
        emit('Результат сценария: ' + result + '.')
    heading(1)
    exclusions = k['scope']['exclusions']
    if exclusions:
        emit('Границы описания: ' + '; '.join(business_text(v) for v in exclusions) + '.', [k['scope']['id']])
    for relation in inputs['domain-tree']['relations']:
        if relation.get('from_id') == scenario['scenario_id'] and relation['claim_ids']:
            emit(sentence('Связь в области действия: ' + fact(relation['to_id'], relation['claim_ids'])), [relation['id']])
    heading(2)
    actors = list(dict.fromkeys([s['actor'] for s in selected_steps if s['actor']] + definition.get('actors', [])))
    for eid in actors:
        emit('- ' + name(eid) + '.', [eid])
    for eid in selected_integration_ids:
        emit('- ' + name(eid) + '.', [eid])
    heading(3)
    trigger = optional(definition, 'trigger', 'domain-tree', purpose=True, domain_only=True)
    if trigger:
        emit('Сценарий начинается: ' + trigger + '.')
    initial = optional(definition, 'entry_state', 'domain-tree', domain_only=True)
    if initial:
        emit('Исходное состояние: ' + initial + '.')
    for claim in claims.values():
        if claim['subject_id'] == scenario['scenario_id'] and claim['predicate'] in {
                'precondition', 'required_input', 'required_state', 'requires'}:
            emit(fact(claim['value'], [claim['id']], domain_only=True) + '.')
    heading(4)
    if main:
        use(main, 'step_refs', 'scenario')
        refs(main['type_claim_ids'])
        if any(effective(cid) != 'CONFIRMED' for cid in main['type_claim_ids']):
            emit(fact('Основной путь', main['type_claim_ids']))
        if main.get('entry_condition'):
            emit(sentence('Условие входа: ' + fact(main['entry_condition'], main['condition_claim_ids'])), [main['id']])
        emit('| Шаг | Кто | Что происходит | Правила | Интеграции | Результат |\n'
             '| --- | --- | --- | --- | --- | --- |')
        for step in main_steps:
            na_actor = step.get('attribute_claims', {}).get('not_applicable/actor', [])
            actor = field(step, 'actor', 'scenario')
            if step['actor'] is None and na_actor and all(effective(cid) == 'CONFIRMED' for cid in na_actor):
                actor = '—'
            values = [numbers[step['id']], actor, step_label(step), step_refs(step, 'evaluated_rules'),
                      step_refs(step, 'integrations'), field(step, 'business_result', 'scenario')]
            emit('| ' + ' | '.join(values) + ' |', [step['id'], main['id']])
        # Display order does not silently confirm uncertain transitions.
        for before, after in zip(main_steps, main_steps[1:]):
            transitions = [t for t in scenario['transitions'] if t['from_step'] == before['id'] and t['to_step'] == after['id']]
            for transition in transitions:
                if not transition['claim_ids'] or any(effective(cid) != 'CONFIRMED' for cid in transition['claim_ids']):
                    emit('Переход от шага ' + numbers[before['id']] + ' к шагу ' + numbers[after['id']] + ': ' +
                         fact('указанная последовательность', transition['claim_ids']) + '.', [transition['id']])
    else:
        emit('Основной путь пока не подтверждён [UNKNOWN].', [scenario['id']])
    heading(5)
    for rule in selected_rules:
        emit('### ' + rule_label(rule['id']))
        statement = rule.get('business_statement', {})
        if isinstance(statement, dict) and statement.get('value'):
            emit(field(rule, 'business_statement', 'business-rules', domain_only=True) + '.')
        else:
            emit('Предметное описание проверки пока не подтверждено [UNKNOWN].', [rule['id']])
        technical_rule = rule['rule_kind'] == 'technical_constraint'
        for key, label in [('condition', 'Условие'), ('true_result', 'При выполнении'), ('false_result', 'При невыполнении')]:
            emit(label + ': ' + field(rule, key, 'business-rules', business=not technical_rule) + '.')
        rationale = rule.get('business_rationale', {})
        if isinstance(rationale, dict) and rationale.get('value'):
            emit(field(rule, 'business_rationale', 'business-rules', domain_only=True) + '.')
        affected = [numbers[s['id']] for s in main_steps if rule['id'] in s['evaluated_rules']]
        if affected:
            emit('Применяется в шагах: ' + ', '.join(affected) + '.', [rule['id']])
    heading(6)
    seen_states = set()
    for step in selected_steps:
        if not step.get('state_before') and not step.get('state_after'):
            continue
        key = (step.get('state_before'), step.get('state_after'))
        if key in seen_states:
            continue
        seen_states.add(key)
        before = field(step, 'state_before', 'scenario')
        after = field(step, 'state_after', 'scenario')
        emit('- ' + step_label(step) + ': ' + before + ' → ' + after + '.', [step['id']])
    heading(7)
    for i, flow in enumerate(variants, 1):
        emit('### ' + ('Альтернативный вариант ' if flow['id'] in scenario['alternative_flows'] else 'Исключение ') + str(i))
        refs(flow['type_claim_ids'])
        if any(effective(cid) != 'CONFIRMED' for cid in flow['type_claim_ids']):
            emit(fact('Классификация ветки', flow['type_claim_ids']))
        if flow.get('branch_from') in by_step:
            emit(sentence('Отклонение от основного пути: ' + step_label(by_step[flow['branch_from']])), [flow['id']])
        emit('Условие: ' + fact(flow['entry_condition'], flow['condition_claim_ids']) + '.', [flow['id']])
        use(flow, 'step_refs', 'scenario')
        for number, sid in enumerate(flow['step_refs'], 1):
            step = by_step[sid]
            emit(str(number) + '. ' + step_label(step) + '. Результат: ' +
                 field(step, 'business_result', 'scenario') + '.', [sid, flow['id']])
    heading(8)
    for eid in selected_integration_ids:
        emit('### ' + name(eid))
        involved = [s for s in selected_steps if eid in s['integrations']]
        single_scope = k['scope']['scenarios'] == [scenario['scenario_id']]
        bound_steps = {s['id'] for s in involved if s['integrations'] == [eid]}
        for predicate, label in [('integration_role', 'Роль'), ('integration_response', 'Получаемые данные'),
                                 ('integration_error_behavior', 'Поведение при ошибке')]:
            explicit = [c for c in claims.values() if c['predicate'] == predicate and
                        ((single_scope and c['subject_id'] == eid) or c['subject_id'] in bound_steps)]
            for claim in explicit:
                emit(label + ': ' + fact(claim['value'], [claim['id']]) + '.')
        emit(sentence('Используется в процессе: ' + '; '.join(step_label(s) for s in involved)), [eid])
    heading(9)
    # One principal mapped component per meaningful step, plus mapped API/integration
    # boundaries. This is a navigation overview, never a traversal of all technical nodes.
    rank = {'api': 0, 'controller': 1, 'command': 2, 'process': 3, 'subprocess': 4,
            'integration': 5, 'callback': 6, 'state_modification': 7, 'rule': 8, 'event': 9, 'pipeline': 10, 'other': 11}
    for step in selected_steps:
        use(step, 'technical_implementation', 'scenario')
        mapping = step.get('technical_implementation', {})
        mapped = [technical_nodes[nid] for nid in mapping.get('technical_step_refs', step['technical_step_refs'])
                  if nid in technical_nodes and 'symbol' in technical_nodes[nid]]
        mapped.sort(key=lambda n: rank[n['type']])  # stable source-ref order breaks ties, not execution order
        selected = ([mapped[0]] if mapped else []) + [n for n in mapped[1:] if n['type'] in {'api', 'controller', 'integration'}]
        emit('### ' + step_label(step), [step['id']] + step['technical_step_refs'] + step['implementation'])
        emitted_symbols = set()
        for node in selected:
            if node['symbol'] in emitted_symbols:
                continue
            emitted_symbols.add(node['symbol'])
            detail = field(node, 'symbol', 'technical-flow', business=False)
            purpose = optional(node, 'purpose', 'technical-flow', business=False, code_value=False)
            emit(sentence(detail + (': ' + purpose if purpose else '')), [node['id'], node['component_id']])
        if not mapped:
            # Legacy projections can expose an explicit validated implementation ref.
            for i, value in enumerate(step['implementation']):
                if value in entities and value == clean(value) and not re.match(r'\w[\w-]*:', value):
                    emit(fact(value, step['attribute_claims'].get(f'implementation/{i}', []), business=False) + '.')
                    break
    used_entities = {eid for block in blocks for eid in block['derived_from'] if eid in entities}
    alias_entities = list(dict.fromkeys(selected_integration_ids + [eid for eid in terms if eid in used_entities and entities[eid]['type'] in {'Process', 'ApiOperation', 'CodeComponent', 'Integration'}]))
    for eid in alias_entities:
        aliases = terms.get(eid, entities[eid]).get('technical_aliases', [])
        if aliases:
            emit(name(eid) + ': ' + ', '.join(code(v) for v in aliases) + '.', [eid])
    for rule in selected_rules:
        emit(rule_label(rule['id']) + ': ' + field(rule, 'technical_condition' if 'technical_condition' in rule else 'condition', 'business-rules', business=False) + '.', [rule['id']])
    for check_id in scenario.get('runtime_confirmation_refs', []):
        check, review = runtime_checks[check_id], runtime_reviews[check_id]
        if not review['reviewed'] or review['result'] == 'NOT_REQUIRED':
            continue
        use(check, 'trace_refs', 'knowledge')
        for key in ('environment', 'application_version', 'time_from', 'time_to'):
            use(check, key, 'knowledge')
        emit('Наблюдение выполнения: ' + code(review['result']) + '; окружение: ' + cell(check['environment']) +
             '; версия: ' + cell(check['application_version']) + '; период: ' + cell(check['time_from']) + ' — ' + cell(check['time_to']) +
             '; независимых кейсов=' + str(review['sample_size']) + '. Наблюдение ограничено этой выборкой.',
             [check_id] + check['claim_ids'] + check['static_claim_ids'] + check['trace_refs'])
        sequences = list(dict.fromkeys(tuple(row['event'] for row in runtime_traces[tid]['timeline']) for tid in check['trace_refs']))
        for sequence in sequences:
            emit('В исследованных случаях наблюдалось: ' + ' → '.join(code(event) for event in sequence) + '.', [check_id] + check['trace_refs'])
    heading(10)
    # Helpful source links only, chosen from claims actually used in this article.
    included_claims = {cid for block in blocks for cid in block['derived_from'] if cid in claims}
    included_evidence = {support['evidence_id'] for cid in included_claims for support in claims[cid]['support']}
    source_types = set()
    seen_urls = set()
    for evidence in k['evidence']:
        if evidence['id'] not in included_evidence or evidence['source_type'] == 'OPENSEARCH':
            continue
        source_types.add(evidence['source_type'])
        locator = evidence['source_location']
        if evidence['source_type'] == 'CONFLUENCE' and re.fullmatch(r'https?://[^\s<>]+', locator) and '.mmd' not in locator:
            if locator not in seen_urls:
                seen_urls.add(locator)
                safe_url = locator.replace('(', '%28').replace(')', '%29')
                emit('- [Описание процесса в Confluence](' + safe_url + ').', [evidence['id'], evidence['snapshot_id']])
    labels = {'CODE': 'техническая реализация', 'CONFIG': 'конфигурация', 'TEST': 'автоматизированные проверки',
              'JIRA': 'требования', 'GIT': 'история изменений'}
    available_sources = [labels[t] for t in labels if t in source_types]
    if available_sources:
        emit('Основания описания: ' + ', '.join(available_sources) + '.', sorted(included_evidence))
    heading(11)
    publication_gap_ids = set(gaps['publication_subset']['gap_ids'])
    publication_finding_ids = set(gaps['publication_subset']['finding_ids'])
    linked_findings = {link['finding_id'] for link in gaps['finding_gap_links'] if set(link['gap_ids']) & publication_gap_ids}
    questions = {}

    def add_question(record, key, artifact):
        text = business_text(record[key])
        questions.setdefault(text, []).append((artifact, record, key, set(pending), list(fields)))
        pending.clear()
        fields.clear()

    for gap in gaps['gaps']:
        if gap['id'] in publication_gap_ids:
            add_question(gap, 'question', 'validation-gaps')
    for finding in report['findings']:
        if finding['id'] in publication_finding_ids and finding['id'] not in linked_findings:
            add_question(finding, 'reason', 'validation-report')
    for text, rows in questions.items():
        ids = set()
        for artifact, record, key, name_refs, name_fields in rows:
            pending.update(name_refs)
            fields.extend(ref for ref in name_fields if ref not in fields)
            use(record, key, artifact)
            use(record, 'publication_relevance', artifact)
            ids.update(record.get('affected_ids', record.get('claim_ids', [])))
        emit('- ' + text, sorted(ids))
    material_claims = {ref for gap in gaps['gaps'] if gap['id'] in publication_gap_ids for ref in gap['affected_ids']}
    material_claims.update(cid for finding in report['findings'] if finding['id'] in publication_finding_ids for cid in finding['claim_ids'])
    conflicts = [c for c in report['comparisons'] if c['status'] in {'CONFLICT', 'UNRESOLVED'}]
    conflicts += [c for c in k['conflicts'] if c['status'] == 'unresolved']
    seen_conflicts = set()
    for conflict in conflicts:
        cids = conflict['claim_ids']
        if set(cids) & material_claims and tuple(sorted(cids)) not in seen_conflicts:
            seen_conflicts.add(tuple(sorted(cids)))
            emit('Источники расходятся [CONFLICT]:', [conflict['id']] + cids)
            for i, cid in enumerate(cids, 1):
                refs([cid])
                emit('- Версия ' + str(i) + ': ' + business_text(claims[cid]['value']) + '.', [cid])
    document = '\n'.join(lines) + '\n'
    provenance = copy.deepcopy(dict(sorted(dict(inputs, **{
        'validation-report': report, 'validation-gaps': gaps, 'glossary': glossary}).items())))
    manifest = {'schema_version': '1.0', 'document_profile': 'reviewed-draft-v1',
                'scope_ref': scenario['scope_ref'], 'package_ref': scenario['package_ref'],
                'report_ref': report['id'], 'report_hash': digest(report), 'gaps_hash': digest(gaps),
                'inputs': report['inputs'], 'claim_ids': report['claim_inventory'],
                'document_hash': hashlib.sha256(document.encode('utf-8')).hexdigest(),
                'publication_gate': report['summary']['publication_gate'],
                'document': dict(scenario_id=scenario['scenario_id'],
                    domain_ids=sorted(e['id'] for e in k['entities'] if e['type'] == 'Domain'),
                    source_revision=k['scope']['revisions'],
                    glossary=dict(id=glossary['id'], revision=glossary['revision'], content_hash=digest(glossary)),
                    template_hash=hashlib.sha256(template.encode('utf-8')).hexdigest(),
                    writing_style_hash=hashlib.sha256(style.encode('utf-8')).hexdigest(),
                    blocks=blocks, provenance=provenance, unresolved=sorted({g['id'] for g in gaps['gaps']} |
                        {r['gap']['id'] for r in glossary['unresolved'] if r['entity_ref'] in entities}))}
    errors = schema_errors('documentation-manifest', manifest)
    if errors:
        raise ValueError('\n'.join(errors))
    return document, manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    kinds = (REQUIRED_INPUTS - {'source-map'}) | {'domain-tree'}
    for kind in sorted(kinds):
        parser.add_argument('--' + kind, type=Path, required=True)
    parser.add_argument('--source-map', type=Path)
    parser.add_argument('--scenario-definition', type=Path)
    parser.add_argument('--glossary', type=Path, required=True)
    parser.add_argument('--template', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--gaps', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args()
    try:
        inputs = {kind: load(getattr(args, kind.replace('-', '_'))) for kind in kinds}
        for kind in ('source-map', 'scenario-definition'):
            path = getattr(args, kind.replace('-', '_'))
            if path is not None:
                inputs[kind] = load(path)
        document, manifest = compose(inputs, load(args.report), load(args.gaps), load(args.glossary),
                                     template=args.template.read_text(encoding='utf-8') if args.template else None)
        paths = [args.output_dir / '08-draft-document.md', args.output_dir / 'documentation-manifest.json',
                 args.output_dir / '08-draft-document.meta.yaml']
        if not args.overwrite and any(p.exists() for p in paths):
            raise ValueError('Existing outputs retained; use another output directory or explicit --overwrite')
        args.output_dir.mkdir(parents=True, exist_ok=True)
        paths[0].write_bytes(document.encode('utf-8'))
        paths[1].write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        paths[2].write_text(yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False), encoding='utf-8')
        print('Reviewed artifacts rendered; no new claims or publication.')
    except (ValueError, OSError, yaml.YAMLError) as exc:
        parser.exit(2, f'{exc}\n')


if __name__ == '__main__':
    main()
