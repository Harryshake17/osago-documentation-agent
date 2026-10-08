"""Language-only review on synthetic facts and the shared Composer/Curator fixture."""
import copy
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
import re
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit import calculate_summary, draft as audit_draft
from compose import compose, STANDARDS, cell
from glossary import curate, empty_glossary, glossary_errors
from language_review import review, check_review
from test_audit import mark_reviewed, add_counterpart
from test_composer_contracts import fixture, section
from test_composer import review_relevance
from test_glossary import DOMAIN
from test_model import sync_evidence
from validate import load, schema_errors, SCHEMAS

FIXTURES = Path(__file__).parent / 'fixtures/language-review'


def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def replace_section(document, number, transform):
    pattern = re.compile(r'(\n## ' + str(number) + r'\. [^\n]*\n)(.*?)(?=\n## |\Z)', re.S)
    return pattern.sub(lambda m: m[1] + transform(m[2]), document)


def build_case(base, case):
    """Supply synthetic upstream action knowledge; the reviewer cannot invent it."""
    inputs, validation, gaps, glossary = copy.deepcopy(base)
    step = inputs['scenario']['steps'][0]
    claim = next(c for c in inputs['knowledge']['claims'] if c['id'] == 'claim:composer:action')
    value, status = case['action'], case.get('status', 'CONFIRMED')
    conflict_ids = add_counterpart(inputs, 'CONFLUENCE') if status == 'CONFLICT' else ()
    if conflict_ids:
        # Disagreement is confirmed knowledge; the contested source claims remain CONFLICT.
        status = 'CONFIRMED'
    if status == 'INFERRED':
        # The shared model keeps inferred business meanings as candidates.
        # Supply a separate inferred Claim instead of promoting an action value.
        hypothesis = copy.deepcopy(claim)
        hypothesis.update(id='claim:language-fixture:hypothesis', predicate='hypothesis',
            value=value, text=value, knowledge_status='INFERRED', inference=True,
            modality='inferred', support=[], basis_claim_ids=['claim:trigger'],
            inference_rationale='Synthetic upstream hypothesis; reviewer cannot promote it.')
        inputs['knowledge']['claims'].append(hypothesis)
    else:
        claim.update(value=value, text='Synthetic fixture action: ' + value, knowledge_status=status)
        step['business_action'].update(value=value, status=status)
    if case.get('mapped_alias'):
        # Explicit validated identity mapping, never an invented search synonym.
        entity = next(e for e in inputs['knowledge']['entities'] if e['id'] == 'integration:glossary:scoring')
        alias = case['mapped_alias']
        entity['technical_aliases'].append(alias)
        c = copy.deepcopy(next(c for c in inputs['knowledge']['claims']
                               if c['subject_id'] == entity['id'] and c['predicate'] == 'technical_aliases'))
        c.update(id='claim:language-fixture:alias', value=alias,
                 text='Synthetic alias of an existing entity: ' + alias)
        original_evidence = next(e for e in inputs['knowledge']['evidence']
                                 if e['id'] == c['support'][0]['evidence_id'])
        snapshot = copy.deepcopy(next(s for s in inputs['knowledge']['sources']
                                     if s['id'] == original_evidence['snapshot_id']))
        text = '// Synthetic alias mapping: ' + alias + ' denotes ' + entity['id'] + '.'
        snapshot.update(id='snapshot:language-fixture:alias', locator='fixtures/language-alias.cs',
                        revision='fixture:language-alias:v1', excerpt=text, content_hash=sha(text))
        evidence = copy.deepcopy(original_evidence)
        evidence.update(id='evidence:language-fixture:alias', snapshot_id=snapshot['id'],
                        source_ref=snapshot['id'], source_location=snapshot['locator'],
                        file=snapshot['locator'], version=snapshot['revision'], excerpt=text)
        c['support'] = [dict(evidence_id=evidence['id'], role='supports')]
        c['context']['revision'] = snapshot['revision']
        inputs['knowledge']['sources'].append(snapshot)
        inputs['knowledge']['evidence'].append(evidence)
        inputs['knowledge']['claims'].append(c)
    sync_evidence(inputs['knowledge'])
    validation, gaps = audit_draft(inputs)
    for cid in validation['claim_inventory']:
        c = next(c for c in inputs['knowledge']['claims'] if c['id'] == cid)
        mark_reviewed(inputs, validation, cid, c['knowledge_status'])
    if conflict_ids:
        comp = next(c for c in validation['comparisons'] if set(conflict_ids) <= set(c['claim_ids']))
        comp.update(reviewed=True, status='CONFLICT', context_comparison='overlap')
        for cid in conflict_ids:
            row = next(r for r in validation['claim_reviews'] if r['claim_id'] == cid)
            row.update(status='CONFLICT', comparison_ids=[comp['id']], required_action='analyst_review')
    if case.get('status') == 'INFERRED':
        # Explicit publication relevance review, not automatic printing of hypotheses.
        gap = dict(id='gap:language-fixture:hypothesis', reason='unverified',
            question='Предположение [INFERRED]: ' + value, affected_ids=[hypothesis['id'], step['id']],
            next_action='Review the material process hypothesis.', status='open',
            publication_relevance=dict(classification='PUBLICATION_RELEVANT', reviewed=True,
                reason='Synthetic hypothesis affects understanding of a main process transition.',
                impacts=[dict(aspect='MAIN_FLOW',target_refs=[step['id']])]))
        gaps['gaps'].append(gap)
        validation['gap_ids'] = sorted(g['id'] for g in gaps['gaps'])
    review_relevance(validation, gaps)
    if validation['mechanical_errors']:

        raise ValueError(str(validation['mechanical_errors']))
    _, glossary = curate(empty_glossary(), dict(knowledge=inputs['knowledge'],
                         scenario=inputs['scenario'], validation=validation), DOMAIN)
    document, manifest = compose(inputs, validation, gaps, glossary)
    # Composer already renders preferred terminology. Supply equivalent upstream
    # aliases in business sections while preserving the fact and block lineage.
    if 'SAS' in value:
        normalized_action = cell(value).replace('SAS', 'скоринг')
        if case.get('mapped_alias'):
            normalized_action = normalized_action.replace(case['mapped_alias'], 'скоринг')
        for number in (5, 9):
            document = replace_section(document, number,
                lambda t: t.replace(normalized_action, cell(value)))
    manifest['document_hash'] = sha(document)
    return document, inputs, validation, glossary, manifest


class LanguageReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = fixture()
        cls.unknown_base = fixture('unknown')
        cls.specs = {c['id']: c for c in load(FIXTURES / 'cases.yaml')['cases']}
        cls.cases = {}
        inputs, validation, gaps, glossary = cls.base
        cls.base_document, cls.base_manifest = compose(inputs, validation, gaps, glossary)

    def setUp(self):
        self.inputs, self.validation, self.gaps, self.glossary = copy.deepcopy(self.base)
        self.document, self.manifest = self.base_document, copy.deepcopy(self.base_manifest)

    def run_review(self, document=None, glossary=None, manifest=True):
        return review(self.document if document is None else document,
                      self.glossary if glossary is None else glossary,
                      self.inputs['scenario'], self.validation,
                      technical_flow=self.inputs['technical-flow'], business_rules=self.inputs['business-rules'],
                      **({'manifest': self.manifest} if manifest else {}))

    def case(self, name):
        if name not in self.cases:
            self.cases[name] = build_case(self.base, self.specs[name])
        return copy.deepcopy(self.cases[name])

    def reviewed_case(self, name):
        doc, inputs, validation, glossary, manifest = self.case(name)
        final, report = review(doc, glossary, inputs['scenario'], validation,
                               technical_flow=inputs['technical-flow'],
                               business_rules=inputs['business-rules'], manifest=manifest)
        self.assertEqual(report['review']['status'], 'COMPLETED', report)
        self.assertEqual(check_review(doc, final, report, glossary, inputs['scenario'], validation,
                         technical_flow=inputs['technical-flow'],
                         business_rules=inputs['business-rules'], manifest=manifest), [])
        return doc, final, report

    def test_01_business_alias_and_supplied_import_meaning(self):
        doc, final, _ = self.reviewed_case('technical-alias')
        self.assertIn('скоринг', section(final, 5))
        self.assertNotIn('SAS', section(final, 5))
        self.assertIn('SAS', section(final, 10))
        self.assertEqual(section(final, 10), section(doc, 10))
        self.assertIn('После Import', section(final, 5))
        self.assertNotIn('После получения анкеты', section(final, 5))
        _, supplied, _ = self.reviewed_case('supplied-import-meaning')
        self.assertIn('После получения анкеты', section(supplied, 5))

    def test_02_unknown_name_never_gets_an_invented_translation(self):
        inputs, validation, gaps, glossary = copy.deepcopy(self.unknown_base)
        def rename(data):
            if isinstance(data, dict):
                return {k: rename(v) for k, v in data.items()}
            if isinstance(data, list):
                return [rename(v) for v in data]
            return data.replace('SomeEligibilityInvoker', 'ReadyForSign') if isinstance(data, str) else data
        inputs = rename(inputs)
        for snapshot in inputs['knowledge']['sources']:
            snapshot['content_hash'] = sha(snapshot['excerpt'])
        sync_evidence(inputs['knowledge'])
        validation, gaps = audit_draft(inputs)
        for cid in validation['claim_inventory']:
            mark_reviewed(inputs, validation, cid)
        review_relevance(validation, gaps)
        _, glossary = curate(empty_glossary(), dict(knowledge=inputs['knowledge'],
                             scenario=inputs['scenario'], validation=validation), DOMAIN)
        doc, manifest = compose(inputs, validation, gaps, glossary)
        self.assertNotIn('ReadyForSign', section(doc, 5))
        # Standalone Reviewer coverage: reintroduce the exact source alias without
        # inventing a preferred name or changing the source action.
        doc = replace_section(doc, 5, lambda t: t.replace(
            'Предметное название [UNKNOWN — предметное название требует уточнения]',
            'ReadyForSign [UNKNOWN — предметное название требует уточнения]'))
        manifest['document_hash'] = sha(doc)
        final, report = review(doc, glossary, inputs['scenario'], validation, manifest=manifest)
        self.assertEqual(report['review']['status'], 'COMPLETED', report)
        self.assertIn('ReadyForSign', final)
        self.assertIn('ReadyForSign', section(final, 5))
        self.assertIn('UNKNOWN', section(final, 5))
        for invented in ('Готово к подписанию', 'Готов к подписанию', 'готов к подписанию'):
            self.assertNotIn(invented, final)
        self.assertTrue(any(w['type'] == 'UNRESOLVED_TERM' for w in report['review']['warnings']))

    def test_03_conflict_does_not_choose_an_order(self):
        doc, final, _ = self.reviewed_case('conflict')
        self.assertIn('CONFLICT', final)
        self.assertIn('Источники расходятся', section(final, 5))
        self.assertNotIn('X → Y', final)
        self.assertNotIn('Y → X', final)
        self.assertEqual(section(doc, 12), section(final, 12))

    def test_04_runtime_limitation_is_not_universal(self):
        _, final, report = self.reviewed_case('runtime-limitation')
        self.assertIn('В 5 исследованных production traces', section(final, 5))
        self.assertIn('до Import', section(final, 5))
        self.assertNotIn('всегда', section(final, 5))
        self.assertEqual(report['review']['semantic_validation']['scope_limitations_changed'], 0)

    def test_05_threshold_and_operator_preserved(self):
        _, final, _ = self.reviewed_case('threshold')
        self.assertIn('addressRecognitionAccuracy &gt;= 7', section(final, 5))
        self.assertNotIn('addressRecognitionAccuracy &gt; 7', final)
        self.assertNotIn('полностью распознан', final)

    def test_06_protected_identifier_byte_exact(self):
        doc = replace_section(self.document, 10,
            lambda t: t.replace('FixtureHandler.Handle', 'RegisterPolicyContractNSIS'))
        final, report = self.run_review(doc, manifest=False)
        self.assertEqual(report['review']['status'], 'COMPLETED', report)
        self.assertIn('RegisterPolicyContractNSIS', section(final, 10))
        self.assertNotIn('RegisterPolicyContractNsis', final)
        self.assertEqual(section(doc, 10).encode(), section(final, 10).encode())

    def test_07_unknown_rationale_is_not_explained(self):
        final, report = self.run_review()
        self.assertEqual(report['review']['status'], 'COMPLETED', report)
        self.assertIsNone(self.inputs['business-rules']['rules'][0]['business_rationale']['value'])
        self.assertNotIn('Причина: [UNKNOWN', section(final, 6))
        self.assertNotIn('потому что', final)
        self.assertEqual(section(self.document, 6), section(final, 6))

    def test_08_inferred_remains_a_hypothesis(self):
        _, final, report = self.reviewed_case('inferred')
        self.assertIn('Предположительно', final)
        self.assertIn('INFERRED', final)
        self.assertEqual(report['review']['semantic_validation']['status_changes'], 0)

    def test_09_glossary_identity_consistency(self):
        doc, final, report = self.reviewed_case('glossary-consistency')
        for alias in ('SAS', 'скоринг', 'скоринговый сервис'):
            self.assertIn(alias, section(doc, 5))
        changes = report['review']['changes']['terminology_replacements']
        self.assertEqual({c['from'] for c in changes}, {'SAS', 'скоринговый сервис'})
        self.assertTrue(all(c['to'] == 'скоринг' and c['occurrences'] > 0 for c in changes))
        self.assertIn('скоринг', section(final, 5))
        self.assertNotIn('SAS', section(final, 5))
        self.assertNotIn('скоринговый сервис', section(final, 5))
        self.assertIn('SAS', section(final, 10))
        self.assertIn('скоринговый сервис', section(final, 10))

    def test_10_semantic_diff_and_report_contract(self):
        final, report = self.run_review()
        self.assertEqual(schema_errors('language-review', report), [])
        self.assertEqual(report['claim_ids'], self.validation['claim_inventory'])
        self.assertEqual(report['publication_gate'], self.manifest['publication_gate'])
        self.assertEqual(report['final_hash'], sha(final))
        self.assertTrue(report['blocks'])
        self.assertEqual(report['review']['protected_content_changes']['count'], 0)
        for key in ('new_claims_detected', 'removed_critical_claims', 'removed_gaps',
                    'status_changes', 'scope_limitations_changed', 'scenario_order_changes'):
            self.assertEqual(report['review']['semantic_validation'][key], 0, key)
        self.assertEqual(check_review(self.document, final, report, self.glossary,
                         self.inputs['scenario'], self.validation,
                         technical_flow=self.inputs['technical-flow'],
                         business_rules=self.inputs['business-rules'], manifest=self.manifest), [])

    def test_substantive_fixture_language_outcomes(self):
        for name, spec in self.specs.items():
            with self.subTest(case=name):
                _, final, report = self.reviewed_case(name)
                business = section(final, 12 if name == 'inferred' else spec.get('section', 5))
                for value in spec.get('must_contain', []):
                    self.assertIn(value, business)
                for value in spec.get('must_not_contain', []):
                    self.assertNotIn(value, business)
                if spec.get('warning'):
                    self.assertTrue(any(w['type'] == spec['warning'] for w in report['review']['warnings']), report)

    def test_untranslated_business_text_is_visible_without_an_invented_translation(self):
        doc, inputs, validation, glossary, manifest = self.case('technical-alias')
        final, report = review(doc, glossary, inputs['scenario'], validation, manifest=manifest)
        self.assertEqual(report['review']['status'], 'COMPLETED', report)
        self.assertIn('После Import', section(final, 5))
        self.assertNotIn('После получения анкеты', section(final, 5))
        self.assertTrue(any(w['type'] == 'UNTRANSLATED_BUSINESS_TEXT'
                            and 'Import' in w['value'] for w in report['review']['warnings']))
        self.assertEqual(section(doc, 10), section(final, 10))
        self.assertEqual(check_review(doc, final, report, glossary,
                                     inputs['scenario'], validation, manifest=manifest), [])

    def test_service_metadata_is_preserved_without_language_warning_noise(self):
        final, report = self.run_review()
        self.assertEqual(report['review']['status'], 'COMPLETED', report)
        for fragment in ('Publication gate:', 'Technical alias:', r'rule\_branch'):
            self.assertNotIn(fragment, self.document)
            self.assertNotIn(fragment, final)
        self.assertEqual(report['publication_gate'], self.manifest['publication_gate'])
        self.assertEqual(report['claim_ids'], self.manifest['claim_ids'])
        tokens = {token.strip() for warning in report['review']['warnings']
                  if warning['type'] == 'UNTRANSLATED_BUSINESS_TEXT'
                  for token in warning['value'].split(',')}
        self.assertTrue(tokens.isdisjoint({'Publication', 'blocked', 'Technical', 'rule'}), tokens)

    def test_reader_first_introduction_is_prose_without_scope_changes(self):
        spec = load(FIXTURES / 'reader-first.yaml')['introduction']
        doc = replace_section(self.document, 1, lambda t: '\n' + spec['before'] + '\n')
        before = copy.deepcopy((self.inputs, self.validation, self.glossary))
        final, report = self.run_review(doc, manifest=False)
        self.assertEqual(report['review']['status'], 'COMPLETED', report)
        self.assertEqual(section(final, 1).partition('\n')[2].strip(), spec['after'].strip())
        self.assertNotRegex(section(final, 1), r'Workflow:|Область:|Вне scope:')
        self.assertEqual(section(doc, 2), section(final, 2))
        self.assertEqual(before, (self.inputs, self.validation, self.glossary))
        self.assertGreaterEqual(report['review']['changes']['jargon_reductions'], 3)
        self.assertEqual(check_review(doc, final, report, self.glossary,
                                     self.inputs['scenario'], self.validation,
                                     technical_flow=self.inputs['technical-flow'],
                                     business_rules=self.inputs['business-rules']), [])
        repeated, _ = self.run_review(final, manifest=False)
        self.assertEqual(repeated, final)
        self.assertEqual(self.run_review(doc, manifest=False), (final, report))

    def test_reader_first_labels_keep_unknown_conflict_and_runtime_modality(self):
        spec = load(FIXTURES / 'reader-first.yaml')['uncertainty']
        doc = replace_section(self.document, 1, lambda t: '\n' + spec['before'] + '\n')
        final, report = self.run_review(doc, manifest=False)
        self.assertEqual(report['review']['status'], 'COMPLETED', report)
        for fragment in spec['must_contain']:
            self.assertIn(fragment, section(final, 1))
        for status in ('UNKNOWN', 'INFERRED', 'CONFLICT'):
            self.assertEqual(doc.count(status), final.count(status))
        self.assertNotIn('X → Y', final)
        self.assertNotIn('всегда', final)

    def test_reader_first_heading_levels_and_noneditorial_fields_are_preserved(self):
        text = ('### Workflow\n#### Scope\n### Out of scope\n'
                'Workflow: оформление\n'
                '| Workflow: поле | Область: значение |\n'
                '- Вне scope: элемент списка\n'
                '> Workflow: цитата\n'
                '```text\nWorkflow: защищённый пример\n```\n')
        doc = replace_section(self.document, 1, lambda t: '\n' + text + '\n')
        final, report = self.run_review(doc, manifest=False)
        self.assertEqual(report['review']['status'], 'COMPLETED', report)
        self.assertIn('### Описание сценария\n#### Область действия\n### За пределами описания', final)
        for unchanged in ('| Workflow: поле | Область: значение |', '- Вне scope: элемент списка',
                          '> Workflow: цитата', '```text\nWorkflow: защищённый пример\n```'):
            self.assertIn(unchanged, final)
        for number in (5, 6, 7, 8, 10, 11, 12):
            self.assertEqual(section(doc, number), section(final, number))

    def test_confirmed_inline_code_alias_becomes_business_term_only_in_overview(self):
        spec = load(FIXTURES / 'reader-first.yaml')['identifier']
        doc, inputs, validation, glossary, manifest = build_case(self.base, spec)
        doc = replace_section(doc, 1, lambda t: t + '\n' + spec['overview'] + '\n')
        doc = replace_section(doc, 10, lambda t: t.replace('FixtureHandler.Handle', spec['mapped_alias']))
        self.assertIn('`' + spec['mapped_alias'] + '`', section(doc, 10))
        final, report = review(doc, glossary, inputs['scenario'], validation,
            technical_flow=inputs['technical-flow'], business_rules=inputs['business-rules'])
        self.assertEqual(report['review']['status'], 'COMPLETED', report)
        self.assertIn(spec['expected'], section(final, 1))
        self.assertNotIn(spec['mapped_alias'], section(final, 1))
        self.assertEqual(section(doc, 10).encode(), section(final, 10).encode())
        self.assertTrue(any(c['from'] == spec['mapped_alias'] and c['to'] == 'скоринг'
            for c in report['review']['changes']['terminology_replacements']))
        repeated, _ = review(final, glossary, inputs['scenario'], validation)
        self.assertEqual(repeated, final)
        forged = replace_section(final, 10, lambda t: t.replace('NSIS', 'Nsis'))
        self.assertTrue(check_review(doc, forged, report, glossary, inputs['scenario'], validation,
            technical_flow=inputs['technical-flow'], business_rules=inputs['business-rules']))

    def test_inline_code_replacement_checks_grammar_and_preserves_technical_uses(self):
        text = ('После `SAS` выполняется проверка.\n'
                'API `SAS`; метод `SAS`; статус `SAS`; состояние `SAS`.\n'
                'Технический идентификатор `SAS`.\n'
                'Система использует `/api/import` и `addressRecognitionAccuracy >= 7`.\n'
                'Значение `key=SAS` остаётся прежним.\n'
                'Система вызывает `SomeUnknownInvoker`.\n')
        doc = replace_section(self.document, 1, lambda t: '\n' + text + '\n')
        final, report = self.run_review(doc, manifest=False)
        self.assertEqual(report['review']['status'], 'WAITING_FOR_REVIEW', report)
        self.assertEqual(section(final, 1).partition('\n')[2].strip(), text.strip())
        warnings = {w['type'] for w in report['review']['warnings']}
        self.assertIn('LANGUAGE_FORM_NEEDS_REVIEW', warnings)
        self.assertIn('TECHNICAL_IDENTIFIER_IN_BUSINESS_TEXT', warnings)
        self.assertNotIn('После скоринг', final)

    def test_editorial_repetition_keeps_provenance_spans_and_process_repetitions(self):
        blocks = self.manifest['document']['blocks']
        block = next(b for b in blocks if b['section'] == 'purpose')
        start, end = block['start_line'] - 1, block['end_line']
        lines = self.document.splitlines(keepends=True)
        value = ''.join(lines[start:end]).strip()
        # Same source block, exact repeated editorial meaning. Different scope
        # limitations and repeated process actions must remain separate.
        replacement = ['Workflow: ' + value + '\n', '\n', 'Workflow: ' + value + '\n',
                       'Область: версия X\n', 'Область: версия Y\n',
                       'Система выполняет скоринг.\n', 'Система выполняет скоринг.\n']
        delta = len(replacement) - (end - start)
        lines[start:end] = replacement
        block['end_line'] += delta
        for other in blocks:
            if other['start_line'] > end:
                other['start_line'] += delta
                other['end_line'] += delta
        doc = ''.join(lines)
        self.manifest['document_hash'] = sha(doc)
        before = copy.deepcopy(self.manifest)
        final, report = self.run_review(doc)
        self.assertEqual(report['review']['status'], 'COMPLETED', report)
        self.assertEqual(section(final, 1).count('Документ описывает сценарий'), 1)
        self.assertIn('Область действия документа — версия X.', final)
        self.assertIn('Область действия документа — версия Y.', final)
        self.assertEqual(section(final, 1).count('Система выполняет скоринг.'), 2)
        self.assertEqual(len(doc.splitlines()), len(final.splitlines()))
        self.assertEqual(report['blocks'], before['document']['blocks'])
        self.assertEqual(self.manifest, before)
        self.assertEqual(check_review(doc, final, report, self.glossary, self.inputs['scenario'],
            self.validation, technical_flow=self.inputs['technical-flow'],
            business_rules=self.inputs['business-rules'], manifest=self.manifest), [])
        repeated, _ = self.run_review(final, manifest=False)
        self.assertEqual(repeated, final)

    def test_link2_review_does_not_restore_internal_gaps_ids_or_provenance(self):
        from test_reader_first_composer import fixture as link2_fixture, FOLDER
        inputs, validation, gaps, glossary = link2_fixture()
        document = (FOLDER / 'after.md').read_text(encoding='utf-8')
        manifest = load(FOLDER / 'documentation-manifest.json')
        original = copy.deepcopy((inputs, validation, gaps, glossary, manifest))
        final, report = review(document, glossary, inputs['scenario'], validation,
            technical_flow=inputs['technical-flow'], business_rules=inputs['business-rules'], manifest=manifest)
        self.assertEqual(report['review']['status'], 'COMPLETED', report)
        internal = [g for g in gaps['gaps']
                    if g['publication_relevance']['classification'] == 'INTERNAL_RESEARCH']
        self.assertGreater(len(internal), 2)
        for gap in internal:
            self.assertNotIn(gap['question'], final)
            self.assertNotIn(gap['id'], final)
        material = set(gaps['publication_subset']['gap_ids'])
        for gap in gaps['gaps']:
            if gap['id'] in material:
                self.assertIn(gap['question'], final)
        self.assertNotRegex(final, r'claim:|evidence:|technical-step:|step:flow:|derived_from|source_fields|\.\./')
        for number in (5, 10, 11, 12):
            self.assertEqual(section(document, number), section(final, number))
        self.assertEqual(report['claim_ids'], validation['claim_inventory'])
        self.assertEqual(report['publication_gate'], manifest['publication_gate'])
        self.assertEqual(report['blocks'], manifest['document']['blocks'])
        self.assertEqual(original, (inputs, validation, gaps, glossary, manifest))

    def test_identical_editorial_text_with_distinct_provenance_is_not_merged(self):
        from language_review import _deduplicate_overview
        lines = ['Документ описывает сценарий «оформление».\n'] * 2
        manifest = {'document': {'blocks': [
            {'start_line': 1, 'end_line': 1}, {'start_line': 2, 'end_line': 2}]}}
        self.assertEqual(_deduplicate_overview(lines, ['purpose'] * 2, manifest), (lines, 0))
        self.assertEqual(_deduplicate_overview(lines, ['purpose'] * 2, None), (lines, 0))

    def test_unknown_inline_code_term_is_not_given_a_business_translation(self):
        inputs, validation, gaps, glossary = copy.deepcopy(self.unknown_base)
        doc, _ = compose(inputs, validation, gaps, glossary)
        symbol = 'SomeEligibilityInvoker'
        doc = replace_section(doc, 1, lambda t: t + '\nТехническое состояние `' + symbol + '` [UNKNOWN].\n')
        final, report = review(doc, glossary, inputs['scenario'], validation)
        self.assertEqual(report['review']['status'], 'COMPLETED', report)
        self.assertIn('`' + symbol + '` [UNKNOWN]', section(final, 1))
        self.assertNotIn('проверка пригодности', final)
        self.assertTrue(any(w['type'] == 'UNRESOLVED_TERM' and w['value'] == symbol
                            for w in report['review']['warnings']))
        self.assertEqual(section(doc, 10), section(final, 10))

    def test_inline_code_alias_and_machine_verb_form_a_natural_sentence(self):
        doc = replace_section(self.document, 1,
            lambda t: t + '\nСистема осуществляет выполнение `SAS`.\n')
        final, report = self.run_review(doc, manifest=False)
        self.assertEqual(report['review']['status'], 'COMPLETED', report)
        self.assertIn('Система выполняет скоринг.', section(final, 1))
        self.assertNotIn('осуществляет выполнение скоринг', section(final, 1))
        self.assertEqual(section(doc, 10), section(final, 10))
        self.assertEqual(self.run_review(final, manifest=False)[0], final)

    def test_missing_inputs_fail_without_research(self):
        for missing in ('draft', 'glossary', 'scenario', 'validation'):
            values = dict(draft=self.document, glossary=self.glossary,
                          scenario=self.inputs['scenario'], validation=self.validation)
            values[missing] = None
            with self.subTest(input=missing):
                final, report = review(values['draft'], values['glossary'], values['scenario'], values['validation'])
                self.assertEqual((final, report['review']['status']), ('', 'FAILED'))

    def test_unvalidated_glossary_cannot_introduce_a_new_term(self):
        glossary = copy.deepcopy(self.glossary)
        glossary['terms'][0]['preferred_name']['value'] = 'Новое непроверенное название'
        self.assertTrue(glossary_errors(glossary))
        final, report = self.run_review(glossary=glossary)
        self.assertEqual((final, report['review']['status']), ('', 'FAILED'))

    def test_determinism_idempotency_and_input_immutability(self):
        doc, inputs, validation, glossary, manifest = self.case('explicit-subject-style')
        before = copy.deepcopy((doc, inputs, validation, glossary, manifest))
        first = review(doc, glossary, inputs['scenario'], validation, manifest=manifest)
        self.assertEqual(first, review(doc, glossary, inputs['scenario'], validation, manifest=manifest))
        self.assertEqual(before, (doc, inputs, validation, glossary, manifest))
        final, report = first
        repeated, second_report = review(final, glossary, inputs['scenario'], validation)
        self.assertEqual(repeated, final)
        self.assertEqual(second_report['review']['status'], 'COMPLETED', second_report)

    def test_checker_rejects_semantic_and_provenance_mutations(self):
        final, report = self.run_review()
        mutations = {
            'new rationale': replace_section(final, 6, lambda t: t + '\nПричина: правило предотвращает страховое мошенничество.\n'),
            'threshold': final.replace('accuracy &gt;= 7', 'accuracy &gt;= 8'),
            'status': final.replace('[UNKNOWN', '[INFERRED', 1),
            'gaps': replace_section(final, 12, lambda t: '\nПробелы отсутствуют.\n'),
            'identifier': replace_section(final, 10, lambda t: t.replace('FixtureHandler.Handle', 'FixtureHandler.handle')),
            'evidence': replace_section(final, 11, lambda t: '\nВсе источники подтверждены.\n'),
            'transition': replace_section(final, 7, lambda t: t + '\nШаг 2 выполняется перед шагом 1.\n'),
            'scope': replace_section(final, 5, lambda t: t.replace('Система выполняет', 'Система всегда выполняет')),
            'new claim': final + '\nСистема автоматически возвращает все платежи.\n',
        }
        lines = final.splitlines(keepends=True)
        rows = [i for i, t in enumerate(lines) if re.match(r'^\| \d+ \|', t)]
        self.assertGreaterEqual(len(rows), 2)
        changed = list(lines)
        changed[rows[0]], changed[rows[1]] = changed[rows[1]], changed[rows[0]]
        mutations['scenario order'] = ''.join(changed)
        for name, changed in mutations.items():
            with self.subTest(mutation=name):
                forged = copy.deepcopy(report)
                forged['final_hash'] = sha(changed)
                self.assertTrue(check_review(self.document, changed, forged, self.glossary,
                    self.inputs['scenario'], self.validation, technical_flow=self.inputs['technical-flow'],
                    business_rules=self.inputs['business-rules'], manifest=self.manifest), name)

    def test_report_tampering_is_rejected(self):
        final, report = self.run_review()
        changes = [
            lambda r: r['review']['semantic_validation'].update(new_claims_detected=1),
            lambda r: r['review']['protected_content_changes'].update(count=1),
            lambda r: r.update(claim_ids=[]), lambda r: r.update(blocks=[]),
            lambda r: r.update(publication_gate='allowed'), lambda r: r.update(final_hash='0' * 64),
        ]
        for change in changes:
            with self.subTest(mutation=change):
                forged = copy.deepcopy(report)
                change(forged)
                self.assertTrue(check_review(self.document, final, forged, self.glossary,
                    self.inputs['scenario'], self.validation, technical_flow=self.inputs['technical-flow'],
                    business_rules=self.inputs['business-rules'], manifest=self.manifest))

    def test_no_source_or_network_access(self):
        original = Path.open
        def guarded(path, *args, **kwargs):
            target = path.resolve()
            if not any(target.is_relative_to(root.resolve()) for root in (SCHEMAS, STANDARDS)):
                raise AssertionError('Reviewer attempted source access: ' + str(path))
            return original(path, *args, **kwargs)
        with patch.object(Path, 'open', guarded), \
             patch('socket.socket', side_effect=AssertionError('Reviewer attempted network access')), \
             patch('subprocess.run', side_effect=AssertionError('Reviewer attempted external source tool')):
            final, report = self.run_review()
        self.assertEqual(report['review']['status'], 'COMPLETED', report)
        self.assertTrue(final)

    def test_critical_alias_collision_requires_review(self):
        inputs, _, _, _ = fixture('similar')
        def duplicate_alias(data):
            if isinstance(data, dict):
                return {k: duplicate_alias(v) for k, v in data.items()}
            if isinstance(data, list):
                return [duplicate_alias(v) for v in data]
            return data.replace('EligibilityCheck', 'SAS') if isinstance(data, str) else data
        inputs = duplicate_alias(inputs)
        for snapshot in inputs['knowledge']['sources']:
            snapshot['content_hash'] = sha(snapshot['excerpt'])
        sync_evidence(inputs['knowledge'])
        validation, gaps = audit_draft(inputs)
        for cid in validation['claim_inventory']:
            mark_reviewed(inputs, validation, cid)
        review_relevance(validation, gaps)
        _, glossary = curate(empty_glossary(), dict(knowledge=inputs['knowledge'],
                             scenario=inputs['scenario'], validation=validation), DOMAIN)
        self.assertEqual(glossary_errors(glossary), [])
        document, manifest = compose(inputs, validation, gaps, glossary)
        document = replace_section(document, 5,
                                   lambda t: t.replace('Система выполняет [UNKNOWN — неоднозначная терминология].',
                                                       'Система выполняет SAS.'))
        manifest['document_hash'] = sha(document)
        final, report = review(document, glossary, inputs['scenario'], validation, manifest=manifest)
        self.assertEqual(report['review']['status'], 'WAITING_FOR_REVIEW', report)
        self.assertTrue(any(w['type'] == 'AMBIGUOUS_TERM' for w in report['review']['warnings']))
        self.assertIn('Система выполняет SAS.', section(final, 5))
        self.assertTrue(check_review(document, final, report, glossary,
                                    inputs['scenario'], validation, manifest=manifest))

    def test_cli_creates_final_and_report_in_isolated_artifact_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            scripts = root / 'tools/knowledge'
            scripts.mkdir(parents=True)
            for source in Path(__file__).parents[1].glob('*.py'):
                shutil.copyfile(source, scripts / source.name)
            shutil.copytree(SCHEMAS.parent, root / '.codex/knowledge-contracts')
            draft_path = root / '08-draft-document.md'
            draft_path.write_bytes(self.document.encode('utf-8'))
            args = ['--draft', str(draft_path)]
            data = dict(glossary=self.glossary, scenario=self.inputs['scenario'],
                        validation=self.validation, manifest=self.manifest,
                        **{'technical-flow': self.inputs['technical-flow'],
                           'business-rules': self.inputs['business-rules']})
            for kind, artifact in data.items():
                target = root / (kind + '.json')
                target.write_text(json.dumps(artifact, ensure_ascii=False), encoding='utf-8')
                args += ['--' + kind, str(target)]
            originals = {p.name: p.read_bytes() for p in root.iterdir() if p.is_file()}
            self.assertEqual(list(root.rglob('*.cs')), [])
            executable = [sys.executable, '-X', 'utf8', str(scripts / 'language_review.py')]
            out = root / 'out'
            command = executable + args + ['--output-dir', str(out)]
            run = subprocess.run(command, capture_output=True, text=True, timeout=60, cwd=root)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            final_path, report_path = out / '09-final-document.md', out / '09-language-review.yaml'
            self.assertTrue(final_path.is_file())
            report = load(report_path)
            self.assertEqual(report['review']['status'], 'COMPLETED')
            self.assertEqual(report['final_hash'], sha(final_path.read_bytes().decode('utf-8')))
            check = subprocess.run(executable + ['check'] + args + ['--final', str(final_path),
                                   '--review-report', str(report_path)],
                                   capture_output=True, text=True, timeout=60, cwd=root)
            self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
            self.assertEqual(originals, {p.name: p.read_bytes() for p in root.iterdir() if p.is_file()})
            before = {p.name: p.read_bytes() for p in out.iterdir()}
            rerun = subprocess.run(command, capture_output=True, text=True, timeout=60, cwd=root)
            self.assertEqual(rerun.returncode, 2)
            self.assertEqual(before, {p.name: p.read_bytes() for p in out.iterdir()})
            rerun = subprocess.run(command + ['--overwrite'], capture_output=True,
                                   text=True, timeout=60, cwd=root)
            self.assertEqual(rerun.returncode, 0, rerun.stdout + rerun.stderr)
            self.assertEqual(before, {p.name: p.read_bytes() for p in out.iterdir()})
            missing = subprocess.run(executable + ['--output-dir', str(root / 'missing')],
                                     capture_output=True, text=True, timeout=60, cwd=root)
            self.assertEqual(missing.returncode, 2)
            self.assertEqual(load(root / 'missing/09-language-review.yaml')['review']['status'], 'FAILED')
            self.assertFalse((root / 'missing/09-final-document.md').exists())

    def test_stale_scenario_and_manifest_fail(self):
        scenario = copy.deepcopy(self.inputs['scenario'])
        scenario['steps'][0]['business_action']['value'] = 'Новый факт'
        final, report = review(self.document, self.glossary, scenario, self.validation)
        self.assertEqual((final, report['review']['status']), ('', 'FAILED'))
        self.assertTrue(any(w['type'] == 'POTENTIAL_FACTUAL_ISSUE'
                            for w in report['review']['warnings']), report)
        self.assertEqual(scenario['steps'][0]['business_action']['value'], 'Новый факт')
        manifest = copy.deepcopy(self.manifest)
        manifest['document_hash'] = '0' * 64
        final, report = review(self.document, self.glossary, self.inputs['scenario'], self.validation, manifest=manifest)
        self.assertEqual((final, report['review']['status']), ('', 'FAILED'))


class LanguageReviewPromptTests(unittest.TestCase):
    def test_agent_prompt_is_loadable_and_invokes_the_existing_skill(self):
        from paths import skill_resource
        config = load(skill_resource('osago-language-reviewer', 'agents', 'openai.yaml'))
        self.assertIsInstance(config['interface'], dict)
        self.assertEqual(config['interface']['display_name'], 'Language Reviewer')
        self.assertIsInstance(config['interface']['default_prompt'], str)
        self.assertIn('$osago-language-reviewer', config['interface']['default_prompt'])


if __name__ == '__main__':
    unittest.main()
