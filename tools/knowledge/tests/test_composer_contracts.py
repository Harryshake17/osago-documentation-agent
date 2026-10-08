"""Composer contracts on synthetic structured knowledge, with shared glossary fixtures."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from audit import calculate_summary, check_report, digest, draft
from publication import candidate
from compose import compose, STANDARDS, anchor, cell
from glossary import curate, empty_glossary
from test_audit import add_counterpart, mark_reviewed
from test_composer import reviewed_fixture, review_relevance
from test_glossary import DOMAIN, glossary_fixture
from test_model import sync_evidence
from validate import load, schema_errors, SCHEMAS


def fixture(case='confirmed'):
    base, _, inputs, _ = glossary_fixture(case)
    k, scenario = inputs['knowledge'], inputs['scenario']
    concept = next(e for e in k['entities'] if e['id'].startswith('integration:glossary:'))
    step = scenario['steps'][0]
    c = copy.deepcopy(k['claims'][0])
    c.update(id='claim:composer:action', subject_id=step['id'], predicate='business_action',
             value='Система выполняет ' + concept['technical_aliases'][0] + '.',
             text='Synthetic source-stated fixture action.', modality='source_statement')
    k['claims'].append(c)
    step['business_action'] = dict(value=c['value'], status='CONFIRMED', claim_ids=[c['id']],
                                   evidence_ids=['evidence:fixture'])
    if concept['type'] == 'Integration':
        c = copy.deepcopy(c)
        c.update(id='claim:composer:integration', predicate='integrations', value=concept['id'])
        k['claims'].append(c)
        step['integrations'] = [concept['id']]
        step['attribute_claims']['integrations/0'] = [c['id']]
        step['attribute_claims'].pop('not_applicable/integrations')
        step['not_applicable_fields'].remove('integrations')
    sync_evidence(k)
    report, gaps = draft(inputs)
    for cid in report['claim_inventory']:
        mark_reviewed(inputs, report, cid)
    review_relevance(report, gaps)
    _, glossary = curate(base, dict(knowledge=k, scenario=scenario, validation=report), DOMAIN)
    return inputs, report, gaps, glossary


def manifest_status(report, cid):
    return next(r['status'] for r in report['claim_reviews'] if r['claim_id'] == cid)


def section(document, index):
    return document.split(f'\n## {index}. ', 1)[1].split('\n## ', 1)[0]


class ComposerContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = fixture()

    def setUp(self):
        self.inputs, self.report, self.gaps, self.glossary = copy.deepcopy(self.base)

    def render(self):
        return compose(self.inputs, self.report, self.gaps, self.glossary)

    def test_01_glossary_mapping_and_technical_alias(self):
        doc, _ = self.render()
        self.assertIn('Система выполняет скоринг.', section(doc, 5))
        self.assertNotIn('SAS', section(doc, 5))
        self.assertIn('SAS', section(doc, 10))
        self.assertIn('скоринг', section(doc, 9))

    def test_02_unknown_term_never_invents_russian_name(self):
        doc, _ = compose(*fixture('unknown'))
        self.assertNotIn('SomeEligibilityInvoker', section(doc, 5))
        self.assertIn('SomeEligibilityInvoker', section(doc, 10))
        self.assertIn('UNKNOWN', section(doc, 5))
        self.assertNotIn('Проверка доступности оформления', doc)
        self.assertNotIn('Проверка права', doc)

    def test_03_validation_conflict_is_not_a_fact(self):
        inputs, _, _ = reviewed_fixture()
        a, b = add_counterpart(inputs, 'CONFLUENCE')
        report, gaps = draft(inputs)
        for cid in report['claim_inventory']:
            mark_reviewed(inputs, report, cid)
        comparison = report['comparisons'][0]
        comparison.update(reviewed=True, status='CONFLICT', context_comparison='overlap')
        for cid in (a, b):
            row = mark_reviewed(inputs, report, cid, 'CONFLICT')
            row.update(comparison_ids=[comparison['id']], required_action='analyst_review')
        review_relevance(report, gaps)
        doc, manifest = compose(inputs, report, gaps, empty_glossary())
        self.assertNotIn(cell(a), doc)
        self.assertNotIn(cell(b), doc)
        self.assertIn('CONFLICT', section(doc, 12))
        self.assertIn('Версия 1', section(doc, 12))
        self.assertIn('Версия 2', section(doc, 12))
        self.assertEqual(manifest['publication_gate'], 'blocked')

    def test_04_no_source_access_and_optional_source_map(self):
        self.inputs.pop('source-map')
        self.inputs.pop('scenario-definition')
        original = Path.open
        def guarded(path, *args, **kwargs):
            resolved = path.resolve()
            allowed = (SCHEMAS.resolve(), STANDARDS.resolve())
            if not any(resolved.is_relative_to(root) for root in allowed):
                raise AssertionError('Composer attempted source access: ' + str(path))
            return original(path, *args, **kwargs)
        with patch.object(Path, 'open', guarded):
            doc, manifest = self.render()
        self.assertIn('скоринг', doc)
        self.assertEqual(manifest['inputs'], self.report['inputs'])
        self.assertTrue(check_report(self.report, self.gaps, self.inputs))  # strict upstream remains strict

    def test_05_no_new_claims_entities_rules_or_causality(self):
        before = copy.deepcopy((self.inputs, self.report, self.gaps, self.glossary))
        doc, manifest = self.render()
        self.assertEqual(before, (self.inputs, self.report, self.gaps, self.glossary))
        self.assertEqual(manifest['claim_ids'], self.report['claim_inventory'])
        known = {self.report['id'], self.inputs['knowledge']['scope']['id']}
        def collect(data):
            if isinstance(data, dict):
                if isinstance(data.get('id'), str):
                    known.add(data['id'])
                for value in data.values():
                    collect(value)
            elif isinstance(data, (list, tuple)):
                for value in data:
                    collect(value)
        collect(before)
        for block in manifest['document']['blocks']:
            self.assertTrue(set(block['derived_from']) <= known, block)
            self.assertTrue(1 <= block['start_line'] <= block['end_line'] <= len(doc.splitlines()))
        business = section(doc, 5)
        self.assertNotIn('FixtureHandler', business)
        self.assertNotIn('Evaluate accuracy', business)
        self.assertNotIn('потому что', business)
        self.assertIn('UNKNOWN', section(doc, 6))  # raw rule statement cannot invent business meaning
        self.assertIn('accuracy', section(doc, 10))

    def test_06_glossary_update_without_scenario_changes(self):
        # A separately validated terminology package, preserving stable Entity IDs.
        alternative = copy.deepcopy(self.inputs)
        k = alternative['knowledge']
        k['package_id'] = 'kb:composer:terminology-update'
        for kind, artifact in alternative.items():
            if kind != 'knowledge':
                artifact['package_ref']['id'] = k['package_id']
        c = next(c for c in k['claims'] if c['predicate'] == 'preferred_name' and
                 c['subject_id'] == 'integration:glossary:scoring')
        c.update(id='claim:composer:preferred-update', value='скоринговая проверка',
                 text='Synthetic revised glossary term.')
        old_evidence = next(e for e in k['evidence'] if e['id'] == c['support'][0]['evidence_id'])
        old_snapshot = next(s for s in k['sources'] if s['id'] == old_evidence['snapshot_id'])
        snapshot = copy.deepcopy(old_snapshot)
        text = snapshot['excerpt'].replace('скоринг', 'скоринговая проверка')
        snapshot.update(id='snapshot:composer:preferred-update', locator='fixture:preferred-update',
                        revision='fixture:preferred-update:v2', excerpt=text,
                        content_hash=hashlib.sha256(text.encode()).hexdigest())
        evidence = copy.deepcopy(old_evidence)
        evidence.update(id='evidence:composer:preferred-update', snapshot_id=snapshot['id'],
                        source_ref=snapshot['id'], source_location=snapshot['locator'],
                        version=snapshot['revision'], excerpt=text)
        k['sources'].append(snapshot)
        k['evidence'].append(evidence)
        c['support'] = [dict(evidence_id=evidence['id'], role='supports')]
        c['context']['revision'] = snapshot['revision']
        sync_evidence(k)
        report, gaps = draft(alternative)
        for cid in report['claim_inventory']:
            mark_reviewed(alternative, report, cid)
        review_relevance(report, gaps)
        _, updated = curate(empty_glossary(), dict(knowledge=k, scenario=alternative['scenario'], validation=report), DOMAIN)
        before = copy.deepcopy(self.inputs)
        doc1, m1 = compose(self.inputs, self.report, self.gaps, updated)
        doc2, m2 = self.render()
        self.assertIn('Система выполняет скоринговая проверка.', section(doc1, 5))
        self.assertIn('Система выполняет скоринг.', section(doc2, 5))
        self.assertEqual(self.inputs, before)
        self.assertNotEqual(m1['document']['glossary']['content_hash'], m2['document']['glossary']['content_hash'])

    def test_missing_required_inputs_are_validation_failure(self):
        for kind in ('knowledge', 'domain-tree', 'technical-flow', 'business-rules', 'scenario'):
            inputs = copy.deepcopy(self.inputs)
            inputs.pop(kind)
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, 'Missing required'):
                compose(inputs, self.report, self.gaps, self.glossary)
        with self.assertRaisesRegex(ValueError, 'glossary'):
            compose(self.inputs, self.report, self.gaps)

    def test_glossary_requires_shared_evidence_and_identity(self):
        self.glossary['terms'][0]['preferred_name']['value'] = 'Непроверенное имя'
        with self.assertRaises(ValueError):
            self.render()

    def test_current_UNKNOWN_review_cannot_be_upgraded_by_old_glossary(self):
        cid = next(c['id'] for c in self.inputs['knowledge']['claims'] if
                   c['subject_id'] == 'integration:glossary:scoring' and c['predicate'] == 'preferred_name')
        row = next(r for r in self.report['claim_reviews'] if r['claim_id'] == cid)
        gap = dict(id='gap:composer:term-review', reason='unverified',
                   question='Which term is confirmed for this scenario?',
                   affected_ids=['integration:glossary:scoring'], next_action='Analyst terminology review.', status='open',
                   publication_relevance=dict(classification='PUBLICATION_RELEVANT',reviewed=True,reason='Current term is unresolved for a main process action.',impacts=[dict(aspect='MAIN_FLOW',target_refs=[self.inputs['scenario']['steps'][0]['id']])]))
        self.gaps['gaps'].append(gap)
        self.report['gap_ids'] = sorted(self.report['gap_ids'] + [gap['id']])
        from publication import refresh_publication_subset
        refresh_publication_subset(self.report, self.gaps)
        row.update(status='UNKNOWN', gap_ids=[gap['id']])
        review_relevance(self.report, self.gaps)
        doc, _ = self.render()
        self.assertNotIn('Система выполняет скоринг.', section(doc, 5))
        self.assertIn('UNKNOWN', section(doc, 5))
        self.assertNotIn(cell(cid), doc)
        self.assertIn('Which term is confirmed for this scenario?', section(doc, 12))

    def test_PARTIALLY_CONFIRMED_is_cautious_and_visible_in_gaps(self):
        cid = 'claim:composer:action'
        row = next(r for r in self.report['claim_reviews'] if r['claim_id'] == cid)
        row.update(status='PARTIALLY_CONFIRMED', supported_parts=['Supplied action'],
                   unsupported_parts=['Domain applicability'], required_action='add_evidence')
        review_relevance(self.report, self.gaps)
        doc, _ = self.render()
        self.assertIn('[PARTIALLY_CONFIRMED — подтверждено частично]', section(doc, 5))
        self.assertNotIn(cell(cid), doc)
        self.assertEqual(manifest_status(self.report, cid), 'PARTIALLY_CONFIRMED')

    def test_INFERRED_claim_is_kept_as_hypothesis_without_new_evidence(self):
        c = copy.deepcopy(self.inputs['knowledge']['claims'][0])
        c.update(id='claim:composer:hypothesis', predicate='hypothesis', value='Синтетическая гипотеза',
                 knowledge_status='INFERRED', inference=True, modality='inferred', support=[],
                 basis_claim_ids=['claim:trigger'], inference_rationale='Synthetic basis for test only.')
        self.inputs['knowledge']['claims'].append(c)
        self.report, self.gaps = draft(self.inputs)
        for cid in self.report['claim_inventory']:
            mark_reviewed(self.inputs, self.report, cid, 'INFERRED' if cid == c['id'] else 'CONFIRMED')
        review_relevance(self.report, self.gaps)
        doc, manifest = self.render()
        self.assertNotIn(cell(c['id']), doc)
        self.assertNotIn(cell(c['basis_claim_ids'][0]), section(doc, 11))
        self.assertIn(c, manifest['document']['provenance']['knowledge']['claims'])
        self.assertIn(c['id'], manifest['claim_ids'])

    def test_invalid_or_incomplete_template_is_validation_failure(self):
        with self.assertRaisesRegex(ValueError, 'twelve ordered sections'):
            compose(self.inputs, self.report, self.gaps, self.glossary, template='## 1. Назначение')

    def test_malformed_input_is_validation_failure(self):
        self.inputs['knowledge'] = None
        with self.assertRaises(ValueError):
            self.render()

    def test_stale_projection_without_source_map_refused(self):
        self.inputs.pop('source-map')
        self.inputs['scenario']['steps'][0]['business_action']['value'] = 'Новый необоснованный факт'
        with self.assertRaisesRegex(ValueError, 'stale'):
            self.render()

    def test_only_main_flow_steps_are_in_main_table(self):
        doc, _ = self.render()
        self.assertNotIn(cell('scenario-step:return-one'), section(doc, 5))
        self.assertEqual(len([line for line in section(doc, 5).splitlines() if line.startswith('|')]), 4)
        self.assertNotIn(cell('scenario-step:return-zero'), section(doc, 5))
        self.assertNotIn(cell('scenario-step:return-zero'), section(doc, 8))
        self.assertIn('Условие:', section(doc, 8))

    def test_step_to_implementation_and_field_provenance(self):
        doc, manifest = self.render()
        step = self.inputs['scenario']['steps'][0]
        self.assertNotIn(anchor('implementation', step['id']), doc)
        self.assertIn(step['implementation'][0], section(doc, 10))
        blocks = [b for b in manifest['document']['blocks'] if b['section'] == 'main-flow']
        row = next(b for b in blocks if 'claim:composer:action' in b['derived_from'])
        self.assertIn(dict(artifact='scenario', record=step['id'], field='business_action'), row['source_fields'])
        self.assertIn('integration:glossary:scoring', row['derived_from'])
        term = next(t for t in self.glossary['terms'] if t['entity_ref'] == 'integration:glossary:scoring')
        self.assertIn(term['id'], row['derived_from'])

    def test_determinism_and_manifest_contract(self):
        self.assertEqual(self.render(), self.render())
        doc, manifest = self.render()
        self.assertEqual(schema_errors('documentation-manifest', manifest), [])
        self.assertEqual(manifest['document_hash'], hashlib.sha256(doc.encode()).hexdigest())
        without_provenance = copy.deepcopy(manifest)
        without_provenance.pop('document')
        self.assertTrue(schema_errors('documentation-manifest', without_provenance))
        manifest['document']['glossary']['content_hash'] = 'not-a-hash'
        self.assertTrue(schema_errors('documentation-manifest', manifest))

    def test_source_alias_substring_is_not_rewritten(self):
        # Token boundaries: a technical alias is not a fuzzy translation dictionary.
        c = next(c for c in self.inputs['knowledge']['claims'] if c['id'] == 'claim:composer:action')
        c['value'] = 'NS.SAS / SAS2 / SAS'
        self.inputs['scenario']['steps'][0]['business_action']['value'] = c['value']
        self.report, self.gaps = draft(self.inputs)
        for cid in self.report['claim_inventory']:
            mark_reviewed(self.inputs, self.report, cid)
        review_relevance(self.report, self.gaps)
        _, self.glossary = curate(empty_glossary(), dict(knowledge=self.inputs['knowledge'],
            scenario=self.inputs['scenario'], validation=self.report), DOMAIN)
        doc, _ = self.render()
        self.assertIn('NS.SAS / SAS2 / скоринг', section(doc, 5))

    def test_integration_response_requires_an_explicit_scoped_claim(self):
        doc, _ = self.render()
        self.assertNotIn('Получаемые данные:', section(doc, 9))
        c = copy.deepcopy(self.inputs['knowledge']['claims'][0])
        c.update(id='claim:composer:integration-response', subject_id='integration:glossary:scoring',
                 predicate='integration_response', value='Синтетический ответ',
                 text='Synthetic integration response for this fixture scenario.', modality='source_statement')
        self.assertEqual(self.inputs['knowledge']['scope']['scenarios'], [self.inputs['scenario']['scenario_id']])
        self.inputs['knowledge']['claims'].append(c)
        sync_evidence(self.inputs['knowledge'])
        self.report, self.gaps = draft(self.inputs)
        for cid in self.report['claim_inventory']:
            mark_reviewed(self.inputs, self.report, cid)
        review_relevance(self.report, self.gaps)
        doc, _ = self.render()
        self.assertIn('Получаемые данные: Синтетический ответ', section(doc, 9))
        self.assertNotIn('Роль: [UNKNOWN', section(doc, 9))

    def test_cli_in_isolated_directory_with_only_structured_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            scripts = root / 'tools/knowledge'
            scripts.mkdir(parents=True)
            for path in Path(__file__).parents[1].glob('*.py'):
                shutil.copyfile(path, scripts / path.name)
            shutil.copytree(SCHEMAS.parent, root / '.codex/knowledge-contracts')
            args = []
            for kind, artifact in dict(self.inputs, glossary=self.glossary, report=self.report, gaps=self.gaps).items():
                if kind in {'source-map', 'scenario-definition'}:
                    continue
                path = root / (kind + '.json')
                path.write_text(json.dumps(artifact, ensure_ascii=False), encoding='utf-8')
                args += ['--' + kind, str(path)]
            command = [sys.executable, '-X', 'utf8', str(scripts / 'compose.py')] + args + ['--output-dir', str(root / 'out')]
            self.assertEqual(list(root.rglob('*.cs')), [])
            result = subprocess.run(command, capture_output=True, text=True, timeout=60, cwd=root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            md = root / 'out/08-draft-document.md'
            manifest = load(root / 'out/documentation-manifest.json')
            self.assertEqual(manifest, load(root / 'out/08-draft-document.meta.yaml'))
            self.assertEqual(hashlib.sha256(md.read_bytes()).hexdigest(), manifest['document_hash'])
            before = {p.name: p.read_bytes() for p in (root / 'out').iterdir()}
            result = subprocess.run(command, capture_output=True, text=True, timeout=60, cwd=root)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(before, {p.name: p.read_bytes() for p in (root / 'out').iterdir()})
            result = subprocess.run(command + ['--overwrite'], capture_output=True, text=True, timeout=60, cwd=root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(before, {p.name: p.read_bytes() for p in (root / 'out').iterdir()})


if __name__ == '__main__':
    unittest.main()
