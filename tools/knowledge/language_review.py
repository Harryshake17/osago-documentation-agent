"""Offline, conservative language review of existing OSAGO documentation.

Only exact, evidence-backed terminology mappings and a small stylistic whitelist
are automated. Checks replay that whitelist; they are not a general semantic
proof. No source, log, configuration or connector access.
"""
import argparse
import copy
import hashlib
import re
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import yaml
from audit import digest, STATUSES
from compose import STANDARDS, SECTION_IDS, template_sections
from glossary import glossary_errors
from validate import load, schema_errors

STANDARD_NAMES = ('terminology', 'writing-style', 'documentation-template',
                  'evidence-policy', 'knowledge-model')
SEMANTIC_FIELDS = ('new_claims_detected', 'removed_critical_claims', 'removed_gaps',
                   'status_changes', 'scope_limitations_changed', 'scenario_order_changes')
MAIN_TABLE = '| Шаг | Кто | Что происходит | Правила | Интеграции | Результат |'
HEADING = re.compile(r'^## (\d+)\. (.+?)(?:\r?\n)?$')
ABBREVIATION = re.compile(r'(?<![\w])(?:[A-ZА-ЯЁ]{2,})(?![\w])')
CONTRACT_TAGS = set(STATUSES) | {'CODE', 'CONFIG', 'TEST', 'GIT', 'CONFLUENCE',
    'OPENSEARCH', 'INFERENCE', 'SUCCESS', 'FAILURE', 'SUPPORTS', 'CONTRADICTS',
    'PARTIAL_SUPPORT', 'UNAVAILABLE', 'NOT_CHECKED', 'ANALYST_REVIEW'}


def text_hash(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def _standards():
    texts, hashes, errors = {}, {}, []
    for name in STANDARD_NAMES:
        try:
            texts[name] = (STANDARDS / (name + '.md')).read_text(encoding='utf-8')
            hashes[name] = text_hash(texts[name])
        except OSError as exc:
            hashes[name] = None
            errors.append(f'Missing required documentation standard {name}: {exc}')
    return texts, hashes, errors


def _safe_digest(value):
    try:
        return digest(value)
    except (TypeError, ValueError, OverflowError):
        return None


def _input_hashes(draft, glossary, scenario, validation, optionals):
    result = dict(draft_hash=text_hash(draft) if isinstance(draft, str) else None,
                  glossary_hash=_safe_digest(glossary) if glossary is not None else None,
                  scenario_hash=_safe_digest(scenario) if scenario is not None else None,
                  validation_hash=_safe_digest(validation) if validation is not None else None)
    for key, value in optionals.items():
        if value is not None:
            result[key + '_hash'] = _safe_digest(value)
    return result


def _base_report(inputs, standards_hashes, validation):
    inventory = validation.get('claim_inventory', []) if isinstance(validation, dict) else []
    inventory = inventory if isinstance(inventory, list) else []
    inventory = list(dict.fromkeys(value for value in inventory if isinstance(value, str) and value))
    return dict(schema_version='1.0', review=dict(status='FAILED', changes=dict(
        terminology_replacements=[], jargon_reductions=0, sentences_simplified=0,
        abbreviations_resolved=0), warnings=[], protected_content_changes=dict(count=0),
        semantic_validation=dict.fromkeys(SEMANTIC_FIELDS, 0), diagnostics=[]),
        inputs=inputs, standards_hashes=standards_hashes, final_hash=text_hash(''),
        publication_gate='blocked', blocks=[],
        claim_ids=inventory)


def _fence(line, current):
    match = re.match(r'^\s*(`{3,}|~{3,})', line)
    if not match:
        return False, current
    marker = match.group(1)
    if current is None:
        return True, (marker[0], len(marker))
    if marker[0] == current[0] and len(marker) >= current[1]:
        return True, None
    return True, current


def _sections(document):
    """Preserve physical lines and map them to the existing logical sections."""
    lines = document.splitlines(keepends=True)
    sections, found, section, fence = [], [], 'title', None
    for line in lines:
        boundary, next_fence = _fence(line, fence)
        match = HEADING.match(line) if not boundary and fence is None else None
        if match:
            number = int(match.group(1))
            found.append(number)
            section = SECTION_IDS[number - 1] if 1 <= number <= 12 else 'invalid'
        sections.append(section)
        fence = next_fence
    errors = [] if found == list(range(1, 13)) else [
        'Documentation requires twelve template sections once, in order; source structure needs review']
    if fence is not None:
        errors.append('Unclosed Markdown code fence; protected content boundaries need review')
    return lines, sections, errors


def _artifact_errors(glossary, scenario, validation, optionals):
    errors = []
    for key, value in (('glossary', glossary), ('scenario', scenario), ('validation-report', validation)):
        if value is None:
            errors.append('Missing mandatory input: ' + key)
        else:
            errors += glossary_errors(value) if key == 'glossary' else schema_errors(key, value)
    for key, kind in (('technical_flow', 'technical-flow'), ('business_rules', 'business-rules'),
                      ('glossary_increment', 'glossary-increment'), ('manifest', 'documentation-manifest')):
        if optionals.get(key) is not None:
            errors += schema_errors(kind, optionals[key])
    if errors:
        return errors
    if scenario['scope_ref'] != validation['scope_ref'] or scenario['package_ref'] != validation['package_ref']:
        errors.append('Scenario/Validation scope or package revision mismatch')
    entries = {row['kind']: row for row in validation['inputs']}
    if len(entries) != len(validation['inputs']):
        errors.append('Validation contains duplicate input kinds')
    for kind, artifact in (('scenario', scenario), ('technical-flow', optionals.get('technical_flow')),
                           ('business-rules', optionals.get('business_rules'))):
        if artifact is None:
            continue
        entry = entries.get(kind, {})
        if entry.get('content_hash') != digest(artifact) or entry.get('id') != artifact['id']:
            errors.append('Validation has stale or absent input hash: ' + kind)
        if artifact['scope_ref'] != scenario['scope_ref'] or artifact['package_ref'] != scenario['package_ref']:
            errors.append(kind + ': scope or package revision mismatch')
    for key, ref in (('technical_flow', 'technical_flow_ref'), ('business_rules', 'business_rules_ref')):
        if optionals.get(key) is not None and optionals[key]['id'] != scenario[ref]:
            errors.append('Scenario has mismatched upstream reference: ' + ref)
    increment = optionals.get('glossary_increment')
    if increment is not None and increment['result_hash'] != digest(glossary):
        errors.append('Glossary increment result_hash does not match supplied glossary')
    inventory, reviews = validation['claim_inventory'], validation['claim_reviews']
    if set(inventory) != {row['claim_id'] for row in reviews} or len(reviews) != len(inventory):
        errors.append('Validation requires exactly one review per inventoried claim')
    if validation['mechanical_errors'] or validation['summary']['review_status'] != 'complete' or any(
            not row['reviewed'] for row in reviews):
        errors.append('Language review requires completed upstream claim review and no mechanical errors')
    ids = [step['id'] for step in scenario['steps']]
    if len(set(ids)) != len(ids):
        errors.append('Scenario contains duplicate step identities')
    known = set(ids)
    for transition in scenario['transitions']:
        if transition['from_step'] not in known or transition['to_step'] not in known:
            errors.append('Scenario transition has dangling step reference: ' + transition['id'])
    for flow in scenario['flows']:
        if not set(flow['step_refs']) <= known:
            errors.append('Scenario flow has dangling step reference: ' + flow['id'])
    return errors


def _manifest_errors(manifest, draft, glossary, scenario, validation, standards, sections):
    if manifest is None:
        return []
    if manifest.get('document_profile') != 'reviewed-draft-v1' or not manifest.get('document'):
        return ['Language review requires Composer document blocks; legacy metadata needs review']
    errors, doc = [], manifest['document']
    expected = dict(id=glossary['id'], revision=glossary['revision'], content_hash=digest(glossary))
    comparisons = (
        (manifest['document_hash'] == text_hash(draft), 'draft content hash'),
        (manifest['report_hash'] == digest(validation), 'Validation content hash'),
        (manifest['report_ref'] == validation['id'], 'Validation reference'),
        (manifest['inputs'] == validation['inputs'], 'upstream input manifest'),
        (manifest['scope_ref'] == scenario['scope_ref'], 'scope reference'),
        (manifest['package_ref'] == scenario['package_ref'], 'package revision'),
        (manifest['claim_ids'] == validation['claim_inventory'], 'claim inventory'),
        (manifest['publication_gate'] == validation['summary']['publication_gate'], 'publication gate'),
        (doc['scenario_id'] == scenario['scenario_id'], 'scenario identity'),
        (doc['glossary'] == expected, 'glossary identity/revision/hash'),
        (doc['template_hash'] == standards['documentation-template'], 'documentation template hash'),
        (doc['writing_style_hash'] == standards['writing-style'], 'writing style hash'))
    for good, label in comparisons:
        if not good:
            errors.append('Composer manifest mismatch: ' + label)
    previous_end = 0
    for block in doc['blocks']:
        start, end = block['start_line'], block['end_line']
        if not 1 <= start <= end <= len(sections):
            errors.append('Composer manifest block has invalid line span')
        elif any(section != block['section'] for section in sections[start - 1:end]):
            errors.append('Composer manifest block crosses declared logical section')
        if start <= previous_end:
            errors.append('Composer manifest blocks overlap or are not ordered')
        previous_end = end
    return errors


def _alias_index(glossary):
    """No fuzzy matching, translation or new business terminology."""
    result = {}
    for term in glossary['terms']:
        aliases = set(term['technical_aliases'])
        # Curator has verified exact origins in immutable Entity provenance.
        # Related identities' search variants are not assumed interchangeable.
        aliases.update(row['value'] for row in term['search_alias_origins']
                       if row['entity_ref'] == term['entity_ref'])
        if term['preferred_name']['value']:
            aliases.add(term['preferred_name']['value'])
        for alias in aliases:
            result.setdefault(alias, {})[term['entity_ref']] = term
    for row in glossary['unresolved']:
        if row['term_id'] is None:
            for alias in row['technical_aliases']:
                result.setdefault(alias, {})[row['entity_ref']] = row
    return result


def _token_pattern(values):
    values = [value for value in values if re.search(r'[A-Za-zА-Яа-яЁё]', value)]
    if not values:
        return None
    return re.compile(r'(?<![\w\\./:#@-])(' + '|'.join(re.escape(value) for value in
        sorted(values, key=lambda value: (-len(value), value))) + r')(?![\w\\/:#@-]|\.[\w])')


def _protected_ranges(line):
    patterns = (
        r'^\s*Publication gate\s*:[^\r\n]*',
        r'\b[A-Za-z][A-Za-z0-9]*(?:\\_[A-Za-z0-9]+)+\b',
        r'(?<!\\)(`+).*?(?<!\\)\1', r'\\`.*?\\`',
        r'!?\[[^\]\n]*(?:\\\][^\]\n]*)*\]\([^\n]*?\)',
        r'\[[^\]\n]+\]\[[^\]\n]*\]', r'[A-Za-z][A-Za-z0-9+.-]*://[^\s<>]+', r'<[^>\n]*>',
        r'\[(?:CONFIRMED|PARTIALLY_CONFIRMED|INFERRED|UNKNOWN|CONFLICT)\b[^\]\n]*\]',
        r'\{[^\n]*\}', r'\\?\[[^\n\]]*"[^\n\]]*\\?\]',
        r"""[\w-]+\s*=\s*(?:"[^"\n]*"|'[^'\n]*'|[^\s;|]+)""",
        r'[\w.:-]+\s*(?:>=|<=|!=|==|>|<|≥|≤|&gt;=|&lt;=|&gt;|&lt;)\s*[+-]?\d+(?:\.\d+)?',
        r'(?i:технический идентификатор|техническое состояние)\s+(?:\\?`[^`\n]+\\?`|(?:\\.|[\w.:-])+)')
    ranges = sorted((m.start(), m.end()) for pattern in patterns for m in re.finditer(pattern, line))
    merged = []
    for start, end in ranges:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def _pieces(line):
    end = 0
    for start, stop in _protected_ranges(line):
        if start > end:
            yield False, line[end:start]
        yield True, line[start:stop]
        end = stop
    if end < len(line):
        yield False, line[end:]


def _stylistic(text, preferred_names=()):
    # Retain subject (including passive voice), action, object and modifiers.
    # No automatic sentence split can add conditionality or causal meaning.
    patterns = (
        (r'\b([Сс]истема) осуществляет выполнение\b', r'\1 выполняет'),
        (r'\b([Сс]истема) выполняет процесс выполнения\b', r'\1 выполняет'),
        (r'\b([Сс]истема) выполняет выполнение\b', r'\1 выполняет'),
        (r'\b([Оо])существляется осуществление\b', r'\1существляется'),
        (r'\b([Вв])ыполняется процесс выполнения\b', r'\1ыполняется'),
        (r'\b([Оо])существляется выполнение\b', lambda m: 'Выполняется' if m[1] == 'О' else 'выполняется'),
        (r'^Ограничения scope:', 'Ограничения области действия:'),
        (r'^Порядок строк — display order\.', 'Порядок строк — порядок отображения.'),
        (r'^Draft для Language Reviewer; публикация не выполнялась\.$',
         'Документ прошёл языковую проверку; публикация не выполнялась.'))
    count = 0
    for pattern, replacement in patterns:
        for _ in range(len(text) + 1):
            applied = 0
            def safe_style(match):
                nonlocal applied
                if 'scope:' not in pattern and 'display order' not in pattern and 'Draft для' not in pattern:
                    # Removing verbal nouns changes the governed grammatical case.
                    # Only an already nominative, exact confirmed object can be
                    # shortened mechanically; never invent an inflected form.
                    remainder = text[match.end():].lstrip()
                    names = [name for name in preferred_names
                             if re.fullmatch(r'[а-яё]+[бвгджзклмнпрстфхцчшщ]', name)]
                    allowed = _token_pattern(names)
                    if allowed is None or allowed.match(remainder) is None:
                        return match.group()
                proposed = replacement(match) if callable(replacement) else match.expand(replacement)
                applied += int(proposed != match.group())
                return proposed
            candidate = re.sub(pattern, safe_style, text)
            if candidate == text or any(candidate.count(name) != text.count(name) for name in preferred_names):
                break
            text = candidate
            count += applied
    return text, count


def _warn(report, kind, value, section, text):
    warning = dict(type=kind, value=value, section=section, text=text.strip())
    if warning not in report['review']['warnings']:
        report['review']['warnings'].append(warning)


def _reader_labels(line, section):
    """Editorial labels only: never interpret a field of the knowledge model."""
    if section not in {'purpose', 'scope'}:
        return line, 0
    ending = '\r\n' if line.endswith('\r\n') else '\n' if line.endswith('\n') else ''
    body = line.removesuffix(ending) if ending else line
    titles = {'workflow': 'Описание сценария', 'scope': 'Область действия',
              'out of scope': 'За пределами описания'}
    heading = re.fullmatch(r'(#{3,6}) (Workflow|Scope|Out of scope)', body, re.I)
    if heading:
        return heading[1] + ' ' + titles[heading[2].lower()] + ending, 1
    label = re.fullmatch(r'(Workflow|Область|Вне scope):\s*(\S.*)', body, re.I)
    if not label:
        return line, 0
    value = label[2]
    if label[1].lower() == 'workflow':
        # Quoting keeps the supplied name's case and grammatical form intact.
        value = value[:-1] if value.endswith('.') and not value.endswith('..') else value
        prose = 'Документ описывает сценарий «' + value + '».'
    else:
        prefix = 'Область действия документа — ' if label[1].lower() == 'область' else 'За пределами описания — '
        prose = prefix + value + ('' if value.endswith(('.', '!', '?')) else '.')
    return prose + ending, 1


def _deduplicate_overview(lines, sections, manifest):
    """Remove exact adjacent repeated editorial prose in one introduction block.

    Physical lines and their provenance spans stay intact. Lists, headings,
    tables, quoted/code text and independently sourced blocks are not merged.
    """
    # Without block lineage, identical prose can belong to different sources.
    # Leaving it alone also keeps a repeat review without the old manifest stable.
    if manifest is None:
        return list(lines), 0
    owners = [None] * len(lines)
    if manifest is not None:
        for number, block in enumerate(manifest['document']['blocks']):
            for index in range(block['start_line'] - 1, block['end_line']):
                owners[index] = number
    result, previous, count, fence = list(lines), None, 0, None
    for index, (line, section) in enumerate(zip(lines, sections)):
        boundary, fence = _fence(line, fence)
        if boundary or fence or section not in {'purpose', 'scope'}:
            previous = None
            continue
        body = line.strip()
        if not body:
            continue
        if not body.startswith(('Документ описывает сценарий «', 'Область действия документа — ',
                                'За пределами описания — ')) or _protected_ranges(line):
            previous = None
            continue
        owner = owners[index] if manifest is not None else section
        current = (section, owner, body)
        if current == previous and owner is not None:
            result[index] = '\r\n' if line.endswith('\r\n') else '\n' if line.endswith('\n') else ''
            count += 1
        else:
            previous = current
    return result, count


def _normalize(glossary, report, headings, lines, sections, standards, manifest=None):
    index = _alias_index(glossary)
    pattern = _token_pattern(index)
    known = {a for term in glossary['terms'] for a in term['abbreviations']}
    known |= {a for term in glossary['terms'] for a in term['technical_aliases'] if ABBREVIATION.fullmatch(a)}
    known |= {a for a in ABBREVIATION.findall('\n'.join(standards.values())) if re.fullmatch(r'[А-ЯЁ]+', a)}
    preferred_names = [term['preferred_name']['value'] for term in glossary['terms']
                       if term['preferred_name']['status'] == 'CONFIRMED' and term['preferred_name']['value']]
    entity_types = {entity['id']: entity['type'] for source in glossary['provenance']
                    for entity in source['knowledge']['entities']}
    replacements, result, fence, critical = {}, [], None, False
    for line, section in zip(lines, sections):
        title = headings[SECTION_IDS.index(section)].split('. ', 1)[1] if section in SECTION_IDS else 'Заголовок'
        boundary, next_fence = _fence(line, fence)
        if boundary or fence:
            fence = next_fence
            result.append(line)
            continue
        if section in {'technical', 'evidence', 'gaps'}:
            heading = HEADING.match(line)
            if heading and line.rstrip('\r\n') != headings[int(heading.group(1)) - 1]:
                _warn(report, 'TEMPLATE_HEADING_NEEDS_REVIEW', heading.group(2), title, line)
                critical = True
            result.append(line)
            continue
        if re.search(r'^\s*(?:[-*]\s*)?[Tt]echnical alias(?:es)?\s*:', line):
            if pattern:
                for match in pattern.finditer(line):
                    terms = index[match.group()]
                    if len(terms) != 1:
                        _warn(report, 'AMBIGUOUS_TERM', match.group(), title, line)
                        critical = True
                    elif next(iter(terms.values())).get('preferred_name', {'status': 'UNKNOWN'})['status'] != 'CONFIRMED':
                        _warn(report, 'UNRESOLVED_TERM', match.group(), title, line)
            for abbreviation in ABBREVIATION.findall(line):
                if abbreviation not in known and abbreviation not in CONTRACT_TAGS:
                    _warn(report, 'UNRESOLVED_ABBREVIATION', abbreviation, title, line)
            result.append(line)
            continue
        heading = HEADING.match(line)
        if heading:
            canonical = headings[int(heading.group(1)) - 1]
            if line.rstrip('\r\n') != canonical:
                _warn(report, 'TEMPLATE_HEADING_NORMALIZED', heading.group(2), title, line)
                line = canonical + ('\r\n' if line.endswith('\r\n') else '\n' if line.endswith('\n') else '')
        line, style_count = _reader_labels(line, section)

        def replace_alias(alias, prefix):
            nonlocal critical
            terms = index[alias]
            if len(terms) != 1:
                _warn(report, 'AMBIGUOUS_TERM', alias, title, line)
                critical = True
                return alias
            term = next(iter(terms.values()))
            preferred = term.get('preferred_name', dict(value=None, status='UNKNOWN'))
            if preferred['status'] != 'CONFIRMED' or not preferred['value'] or term.get('status', 'UNKNOWN') in {'CONFLICT', 'INFERRED'}:
                _warn(report, 'UNRESOLVED_TERM', alias, title, line)
                return alias
            value = preferred['value']
            if len(index.get(value, {})) != 1:
                _warn(report, 'AMBIGUOUS_TERM', value, title, line)
                critical = True
                return alias
            if alias != value and not ABBREVIATION.fullmatch(value) and re.search(
                    r'(?i)(?:\b(?:после|до|без|из|для|от|перед|при|по|к|с|в|на|о|об)|проверка)\s+$',
                    prefix):
                _warn(report, 'LANGUAGE_FORM_NEEDS_REVIEW', alias, title, line)
                critical = True
                return alias
            if alias != value:
                key = (alias, value)
                replacements[key] = replacements.get(key, 0) + 1
                if ABBREVIATION.fullmatch(alias):
                    report['review']['changes']['abbreviations_resolved'] += 1
            return value

        chunks, offset = [], 0
        for protected, text in _pieces(line):
            prefix = line[:offset]
            offset += len(text)
            if protected:
                code = re.fullmatch(r'(`+)([^`\n]+)\1', text)
                alias = code[2] if code else None
                terms = index.get(alias, {})
                # Formatting alone does not justify exposing a business alias.
                # Exact states/endpoints/config and diagnostic uses stay protected.
                eligible = (bool(terms) and alias not in CONTRACT_TAGS and re.fullmatch(r'[\w .-]+', alias)
                    and all(entity_types.get(entity) in
                    {'Integration', 'CodeComponent', 'Capability', 'Domain', 'Scenario'} for entity in terms)
                    and not re.search(r'(?i)(?:\b(?:статус|состояние|метод|endpoint|API|идентификатор|имя|alias))\s*$', prefix))
                if eligible:
                    value = replace_alias(alias, prefix)
                    if value != alias:
                        chunks.append(value)
                        continue
                if pattern:
                    for match in pattern.finditer(text):
                        terms = index[match.group()]
                        if len(terms) == 1 and next(iter(terms.values())).get('preferred_name', {'status': 'UNKNOWN'})['status'] != 'CONFIRMED':
                            _warn(report, 'UNRESOLVED_TERM', match.group(), title, line)
                code_abbreviation = re.fullmatch(r'\\?`+([A-ZА-ЯЁ]{2,})\\?`+', text)
                if code_abbreviation and code_abbreviation[1] not in known and code_abbreviation[1] not in CONTRACT_TAGS:
                    _warn(report, 'UNRESOLVED_ABBREVIATION', code_abbreviation[1], title, line)
                if code and not terms and re.fullmatch(r'[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*', alias) and (
                        re.search(r'[a-z][A-Z]|[._]', alias)):
                    _warn(report, 'TECHNICAL_IDENTIFIER_IN_BUSINESS_TEXT', alias, title, line)
                chunks.append(text)
                continue
            if pattern:
                text = pattern.sub(lambda match: replace_alias(match.group(), prefix + match.string[:match.start()]), text)
            text, count = _stylistic(text, preferred_names)
            style_count += count
            for abbreviation in ABBREVIATION.findall(text):
                if abbreviation not in known and abbreviation not in CONTRACT_TAGS:
                    _warn(report, 'UNRESOLVED_ABBREVIATION', abbreviation, title, line)
            chunks.append(text)
        normalized = ''.join(chunks)
        # A formerly protected inline alias is now ordinary business prose.
        # Re-run the same case-safe style rules across that newly joined phrase;
        # remaining code, links, conditions and statuses stay protected.
        styled = []
        for protected, fragment in _pieces(normalized):
            if not protected:
                fragment, count = _stylistic(fragment, preferred_names)
                style_count += count
            styled.append(fragment)
        normalized = ''.join(styled)
        # Flag untranslated business prose without inventing a translation or term.
        # IDs, locators, assignments and explicitly protected representations remain
        # outside this language-only diagnostic; confirmed preferred names are known.
        known_english = set(CONTRACT_TAGS) | known
        for name in preferred_names:
            known_english.update(re.findall(r'[A-Za-z][A-Za-z0-9]*', name))
        untranslated = []
        for protected, fragment in _pieces(normalized):
            if protected:
                continue
            for token in re.findall(r'(?<![\w:/.#@-])([A-Za-z][A-Za-z0-9]*)(?![\w:/.#@-])', fragment):
                if token not in known_english and not ABBREVIATION.fullmatch(token) and token not in untranslated:
                    untranslated.append(token)
        if untranslated:
            _warn(report, 'UNTRANSLATED_BUSINESS_TEXT', ', '.join(untranslated), title, normalized)
        report['review']['changes']['jargon_reductions'] += style_count
        report['review']['changes']['sentences_simplified'] += int(style_count > 0)
        if re.search(r'(?i)(?:^|[.!?]\s+|\|\s*|^\s*[-*]\s+)(?:это|они|он|она|оно|данный объект)\b', normalized):
            _warn(report, 'AMBIGUOUS_SENTENCE', '', title, normalized)
        if len(re.findall(r'\b[\w-]+\b', normalized)) > 45 and not normalized.lstrip().startswith('|'):
            _warn(report, 'COMPLEX_SENTENCE', '', title, normalized)
        if re.search(r'осуществляется осуществление|выполняется процесс выполнения|следует отметить|'
                     r'необходимо отметить|имеет место|в рамках данного этапа|осуществляет выполнение|осуществляется выполнение', normalized, re.IGNORECASE):
            _warn(report, 'MACHINE_LANGUAGE', '', title, normalized)
        result.append(normalized)
    result, duplicates = _deduplicate_overview(result, sections, manifest)
    report['review']['changes']['jargon_reductions'] += duplicates
    report['review']['changes']['terminology_replacements'] = [dict(
        **{'from': source, 'to': target}, occurrences=count)
        for (source, target), count in sorted(replacements.items())]
    return ''.join(result), critical


def review(draft, glossary, scenario, validation, *, technical_flow=None, business_rules=None,
           glossary_increment=None, manifest=None):
    """Return (candidate, shared report); invalid inputs fail closed.

    COMPLETED means the whitelist preserved supplied knowledge. It does not
    promote an upstream publication gate or prove the correctness of sources.
    """
    optionals = dict(technical_flow=technical_flow, business_rules=business_rules,
                     glossary_increment=glossary_increment, manifest=manifest)
    standards, hashes, errors = _standards()
    result = _base_report(_input_hashes(draft, glossary, scenario, validation, optionals), hashes, validation)
    if not isinstance(draft, str) or not draft.strip():
        errors.append('Missing mandatory input: 08-draft-document.md')
    errors += _artifact_errors(glossary, scenario, validation, optionals)
    if errors:
        result['review']['diagnostics'] = list(dict.fromkeys(errors))
        for message in errors:
            if any(fragment in message.lower() for fragment in ('mismatch', 'stale', 'dangling')):
                _warn(result, 'POTENTIAL_FACTUAL_ISSUE', '', 'Входные артефакты', message)
        return '', result
    try:
        headings = template_sections(standards['documentation-template'])
    except ValueError as exc:
        result['review']['diagnostics'] = [str(exc)]
        return '', result
    lines, sections, errors = _sections(draft)
    errors += _manifest_errors(manifest, draft, glossary, scenario, validation, hashes, sections)
    if errors:
        result['review']['diagnostics'] = list(dict.fromkeys(errors))
        for message in errors:
            if any(fragment in message.lower() for fragment in ('mismatch', 'stale', 'dangling')):
                _warn(result, 'POTENTIAL_FACTUAL_ISSUE', '', 'Входные артефакты', message)
        return '', result
    main_lines = [line.strip() for line, section in zip(lines, sections) if section == 'main-flow']
    if MAIN_TABLE not in main_lines:
        result['review']['diagnostics'] = ['Missing Composer main process table; return structure to Composer']
        return '', result
    final, needs_review = _normalize(glossary, result, headings, lines, sections, standards, manifest)
    if manifest is not None:
        # The whitelist adds/removes no physical lines: existing spans remap
        # exactly while derived_from/source_fields and their order stay intact.
        if len(final.splitlines()) != len(lines):
            result['review']['diagnostics'] = ['Line count changed; traceability cannot be remapped']
            return '', result
        result['blocks'] = copy.deepcopy(manifest['document']['blocks'])
    result['final_hash'] = text_hash(final)
    result['review']['status'] = 'WAITING_FOR_REVIEW' if needs_review else 'COMPLETED'
    result['publication_gate'] = 'blocked' if needs_review else validation['summary']['publication_gate']
    result['review']['diagnostics'] = ['Only exact glossary mappings, editorial labels and conservative stylistic whitelist '
        'were applied; arbitrary prose changes require separate semantic review.']
    problems = schema_errors('language-review', result)
    if problems:
        result['review']['status'] = 'FAILED'
        result['publication_gate'] = 'blocked'
        result['review']['diagnostics'] = problems
        result['final_hash'] = text_hash('')
        return '', result
    return final, result


def check_review(draft, final_text, report, glossary, scenario, validation, *, technical_flow=None,
                 business_rules=None, glossary_increment=None, manifest=None):
    """Check exact reproducibility/traceability, not arbitrary prose semantics."""
    errors = schema_errors('language-review', report)
    if errors:
        return errors
    expected_text, expected = review(draft, glossary, scenario, validation,
        technical_flow=technical_flow, business_rules=business_rules,
        glossary_increment=glossary_increment, manifest=manifest)
    if expected['review']['status'] == 'FAILED':
        return expected['review']['diagnostics']
    if final_text != expected_text:
        errors.append('Final text differs from conservative whitelist replay; new or removed claims, '
                      'statuses, scope and protected content require semantic review')
    if report != expected:
        errors.append('Language review report is stale or differs from deterministic replay '
                      '(hashes, statuses, counters, warnings or traceability)')
    if report['review']['status'] != 'COMPLETED':
        errors.append('Language review needs review; run cannot be marked COMPLETED')
    return errors


def _write_report(path, report):
    path.write_bytes(yaml.safe_dump(report, allow_unicode=True, sort_keys=False).encode('utf-8'))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', nargs='?', choices=('review', 'check'), default='review')
    for flag in ('draft', 'glossary', 'scenario', 'validation', 'technical-flow',
                 'business-rules', 'glossary-increment', 'manifest', 'final', 'review-report'):
        parser.add_argument('--' + flag, type=Path)
    parser.add_argument('--report', type=Path, help='Alias for --validation (upstream 06 review)')
    parser.add_argument('--output-dir', type=Path)
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args(argv)
    if args.validation and args.report and args.validation.resolve() != args.report.resolve():
        parser.error('--validation and --report must identify the same upstream report')
    args.validation = args.validation or args.report
    output = args.output_dir
    if args.mode == 'review' and output is None:
        parser.error('review requires --output-dir')
    if args.mode == 'check' and (args.final is None or args.review_report is None):
        parser.error('check requires --final and --review-report')
    report_path = output / '09-language-review.yaml' if output else None
    final_path = output / '09-final-document.md' if output else None
    try:
        keys = ('draft', 'glossary', 'scenario', 'validation', 'technical_flow',
                'business_rules', 'glossary_increment', 'manifest')
        resolved = {getattr(args, key).resolve() for key in keys if getattr(args, key) is not None}
        if output:
            if report_path.resolve() in resolved or final_path.resolve() in resolved:
                raise ValueError('Outputs must not overwrite an upstream artifact')
            if not args.overwrite and any(path.exists() for path in (report_path, final_path)):
                raise ValueError('Existing outputs retained; use another directory or explicit --overwrite')
        read_errors, data = [], {}
        for key in keys:
            path = getattr(args, key)
            try:
                data[key] = (path.read_bytes().decode('utf-8') if key == 'draft' else load(path)) if path else None
            except (OSError, ValueError, yaml.YAMLError, UnicodeError) as exc:
                data[key] = None
                read_errors.append(f'{key}: {exc}')
        optionals = {key: data[key] for key in keys[4:]}
        final, report = review(data['draft'], data['glossary'], data['scenario'], data['validation'], **optionals)
        if read_errors:
            report['review']['status'] = 'FAILED'
            report['review']['diagnostics'] = read_errors + report['review']['diagnostics']
            report['publication_gate'] = 'blocked'
            report['final_hash'] = text_hash('')
            final = ''
        if args.mode == 'check':
            if read_errors or report['review']['status'] == 'FAILED':
                raise ValueError('\n'.join(report['review']['diagnostics']))
            errors = check_review(data['draft'], args.final.read_bytes().decode('utf-8'), load(args.review_report),
                                  data['glossary'], data['scenario'], data['validation'], **optionals)
            if errors:
                raise ValueError('\n'.join(errors))
            print('Language review contracts passed; supplied knowledge and protected content preserved.')
            return 0
        output.mkdir(parents=True, exist_ok=True)
        _write_report(report_path, report)
        if report['review']['status'] != 'COMPLETED':
            # An explicit retry cannot leave a stale successful final artifact.
            if args.overwrite and final_path.exists():
                final_path.unlink()
            raise ValueError('\n'.join(report['review']['diagnostics']) or 'Language review needs review')
        final_path.write_bytes(final.encode('utf-8'))
        print('Final document and language review report created; no publication performed.')
        return 0
    except (OSError, ValueError, yaml.YAMLError, UnicodeError) as exc:
        parser.exit(2, f'{exc}\n')


if __name__ == '__main__':
    main()
