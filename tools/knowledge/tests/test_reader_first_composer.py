"""Reader-first composition over the existing frozen Link2 Scenario fixture."""
import copy
import hashlib
from pathlib import Path
import re
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit import manifest as input_manifest
from compose import compose, STANDARDS
from validate import load, SCHEMAS
from test_composer_contracts import section

FOLDER = Path(__file__).parent / 'fixtures/composer/link2'
UPSTREAM = Path(__file__).parent / 'fixtures/scenario/link2'


def fixture():
    inputs = load(UPSTREAM / 'inputs.json')
    inputs['scenario'] = load(UPSTREAM / '05-scenario.json')
    return (inputs, load(FOLDER / 'validation-report.json'), load(FOLDER / 'gaps.json'),
            load(FOLDER / 'glossary.yaml'))


class ReaderFirstComposerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = fixture()

    def setUp(self):
        self.inputs, self.report, self.gaps, self.glossary = copy.deepcopy(self.base)

    def render(self):
        return compose(self.inputs, self.report, self.gaps, self.glossary)

    def test_one_main_flow_without_appended_uc(self):
        document, manifest = self.render()
        body = section(document, 5)
        rows = [line for line in body.splitlines() if line.startswith('|')]
        self.assertEqual(len(rows), 7)  # header, separator, exactly five canonical steps
        self.assertEqual(document.count('## 5. Основной бизнес-процесс'), 1)
        self.assertNotRegex(document.lower(), r'happy[ _-]?path|uc main flow|use case|основной поток scenario')
        flow = next(f for f in self.inputs['scenario']['flows'] if f['id'] == self.inputs['scenario']['main_flow'])
        actual = [b['source_fields'] for b in manifest['document']['blocks'] if b['section'] == 'main-flow']
        actual = [f['record'] for fields in actual for f in fields if f['field'] == 'business_action']
        self.assertEqual(actual, flow['step_refs'])

    def test_main_flow_refs_override_registry_order(self):
        document, _ = self.render()
        self.inputs['scenario']['steps'].reverse()
        self.report['inputs'] = input_manifest(self.inputs)
        changed, _ = self.render()
        self.assertEqual(section(document, 5), section(changed, 5))

    def test_overview_not_full_technical_dump(self):
        document, _ = self.render()
        technical = section(document, 10)
        symbols = [n['symbol'] for n in self.inputs['technical-flow']['nodes']]
        shown = [symbol for symbol in symbols if symbol in technical]
        self.assertEqual(len(symbols), 12)
        self.assertEqual(len(shown), 5)
        self.assertIn('`FixtureCalculateController.Calculate`', technical)
        self.assertIn('`FixturePostPaymentHandler.Handle`', technical)
        self.assertNotIn('FixturePolicyRepository.Save', document)
        self.assertNotIn('FixtureCalculateHandler.Handle', document)
        self.assertNotRegex(technical, r'Implementation mapping|configuration_reads:|async_events:|source_ids:|symbol:')
        self.assertIn('`accuracy < 7`', technical)

    def test_only_publication_questions_are_printed(self):
        document, manifest = self.render()
        subset = set(self.gaps['publication_subset']['gap_ids'])
        self.assertEqual(len(subset), 1)
        for gap in self.gaps['gaps']:
            if gap['id'] in subset:
                self.assertIn(gap['question'], section(document, 12))
            else:
                self.assertNotIn(gap['question'], document)
            self.assertIn(gap, manifest['document']['provenance']['validation-gaps']['gaps'])
            self.assertIn(gap['id'], manifest['document']['unresolved'])

    def test_no_internal_identifiers_paths_or_diagram_filename(self):
        document, _ = self.render()
        for record in self.inputs['knowledge']['claims'] + self.inputs['knowledge']['evidence']:
            self.assertNotIn(record['id'], document)
        for entity in self.inputs['knowledge']['entities']:
            if re.match(r'[a-z][\w-]*:', entity['id']):
                self.assertNotIn(entity['id'], document)
        self.assertNotRegex(document, r'\.\./|\.\.\\|\.mmd|\.spec\.ts|\.cs\b|pageId|derived_from|source_fields|\b[PEA]\d+\b')
        narrative = document.split('## 10.', 1)[0]
        for node in self.inputs['technical-flow']['nodes']:
            self.assertNotIn(node['symbol'], narrative)

    def test_full_provenance_and_input_immutability(self):
        before = copy.deepcopy((self.inputs, self.report, self.gaps, self.glossary))
        document, manifest = self.render()
        self.assertEqual(before, (self.inputs, self.report, self.gaps, self.glossary))
        provenance = manifest['document']['provenance']
        for key, artifact in self.inputs.items():
            self.assertEqual(provenance[key], artifact)
        self.assertEqual(provenance['validation-report'], self.report)
        self.assertEqual(provenance['validation-gaps'], self.gaps)
        self.assertEqual(provenance['glossary'], self.glossary)
        self.assertEqual(manifest['claim_ids'], self.report['claim_inventory'])
        self.assertEqual(manifest['publication_gate'], self.report['summary']['publication_gate'])
        self.assertEqual(manifest['document_hash'], hashlib.sha256(document.encode()).hexdigest())

    def test_pending_relevance_returns_to_validation(self):
        next(g for g in self.gaps['gaps'] if g['id'] in self.gaps['publication_subset']['gap_ids'])['publication_relevance']['reviewed'] = False
        with self.assertRaisesRegex(ValueError, 'publication relevance review'):
            self.render()

    def test_no_research_or_network_and_deterministic_output(self):
        original = Path.open
        def guarded(path, *args, **kwargs):
            if not any(path.resolve().is_relative_to(root.resolve()) for root in (SCHEMAS, STANDARDS)):
                raise AssertionError('Source read attempted: ' + str(path))
            return original(path, *args, **kwargs)
        with patch.object(Path, 'open', guarded), patch('socket.socket', side_effect=AssertionError('Network forbidden')):
            self.assertEqual(self.render(), self.render())

    def test_frozen_before_after(self):
        document, manifest = self.render()
        self.assertEqual(document, (FOLDER / 'after.md').read_text(encoding='utf-8'))
        self.assertEqual(manifest, load(FOLDER / 'documentation-manifest.json'))
        before = (FOLDER / 'before.md').read_text(encoding='utf-8')
        self.assertIn('### technical-step:link2:', before)
        self.assertIn('Evidence locators', before)
        self.assertGreater(len(before), len(document) * 10)


if __name__ == '__main__':
    unittest.main()
