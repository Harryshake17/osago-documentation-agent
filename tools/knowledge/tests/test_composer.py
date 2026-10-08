"""Composer consumes fixed reviewed artifacts; never invents application knowledge."""
import copy
import hashlib
import unittest
from test_audit import audit_inputs, mark_reviewed
from audit import draft, calculate_summary
from compose import compose, badge, cell
from glossary import empty_glossary
from publication import UNASSESSED, INTERNAL, refresh_publication_subset


def review_relevance(report, gaps):
    """Explicit editorial assessment of these synthetic test fixtures only."""
    for item in report['findings'] + gaps['gaps']:
        metadata = item['publication_relevance']
        metadata['reviewed'] = True
        if metadata['classification'] == UNASSESSED:
            metadata.update(classification=INTERNAL,
                            reason='Synthetic fixture review: internal implementation/source research; independently supported process fields do not depend on this detail.')
        else:
            metadata['reason'] = 'Synthetic fixture review: referenced process/contract assertion is material.'
    refresh_publication_subset(report, gaps)
    report['summary'] = calculate_summary(report, gaps)


def reviewed_fixture():
    inputs = audit_inputs()
    report, gaps = draft(inputs)
    for cid in report['claim_inventory']:
        mark_reviewed(inputs, report, cid)
    review_relevance(report, gaps)
    return inputs, report, gaps


class ComposerTests(unittest.TestCase):
    def setUp(self):
        self.inputs, self.report, self.gaps = reviewed_fixture()
        self.glossary = empty_glossary()

    def test_twelve_sections_and_hash(self):
        document, manifest = compose(self.inputs, self.report, self.gaps, self.glossary)
        self.assertEqual(document.count('\n## '), 12)
        self.assertIn('Основной бизнес-процесс', document)
        self.assertIn('Бизнес-правила и точки принятия решений', document)
        self.assertEqual(manifest['document_hash'], hashlib.sha256(document.encode()).hexdigest())

    def test_input_not_mutated_and_deterministic(self):
        before = copy.deepcopy((self.inputs, self.report, self.gaps))
        first = compose(self.inputs, self.report, self.gaps, self.glossary)
        self.assertEqual(first, compose(self.inputs, self.report, self.gaps, self.glossary))
        self.assertEqual(before, (self.inputs, self.report, self.gaps))

    def test_unreviewed_refused(self):
        report, gaps = draft(self.inputs)
        with self.assertRaisesRegex(ValueError, 'completed claim review'):
            compose(self.inputs, report, gaps, self.glossary)

    def test_stale_input_refused(self):
        self.inputs['knowledge']['claims'][0]['text'] = 'Invented changed text.'
        with self.assertRaises(ValueError):
            compose(self.inputs, self.report, self.gaps, self.glossary)

    def test_unknown_field_remains_unknown(self):
        document, _ = compose(self.inputs, self.report, self.gaps, self.glossary)
        self.assertNotIn('Причина: [UNKNOWN', document)
        self.assertNotIn('Legacy technical-flow', document)
        self.assertIn('UNKNOWN', document)
        self.assertIn('FixtureHandler.Handle', document)
        self.assertNotIn('Prevent underwriting risk', document)

    def test_unknown_claim_visible(self):
        row = next(r for r in self.report['claim_reviews'] if r['claim_id'] == 'claim:business_goal')
        row.update(status='UNKNOWN', gap_ids=[self.gaps['gaps'][0]['id']])
        self.report['summary'] = calculate_summary(self.report, self.gaps)
        document, _ = compose(self.inputs, self.report, self.gaps, self.glossary)
        self.assertIn('[UNKNOWN — значение не установлено]', document)

    def test_all_nonconfirmed_badges_explicit(self):
        for status in ('UNKNOWN', 'INFERRED', 'CONFLICT', 'PARTIALLY_CONFIRMED'):
            self.assertIn(status, badge({'status': status, 'reviewed': True}))

    def test_full_claim_and_evidence_inventory_in_manifest_only(self):
        document, manifest = compose(self.inputs, self.report, self.gaps, self.glossary)
        for cid in self.report['claim_inventory']:
            self.assertNotIn(cell(cid), document)
        for e in self.inputs['knowledge']['evidence']:
            self.assertIn(e, manifest['document']['provenance']['knowledge']['evidence'])
        self.assertEqual(manifest['claim_ids'], self.report['claim_inventory'])

    def test_blocked_gate_preserved(self):
        document, manifest = compose(self.inputs, self.report, self.gaps, self.glossary)
        self.assertNotIn('Publication gate:', document)
        self.assertEqual(manifest['publication_gate'], 'blocked')

    def test_source_text_cannot_inject_html_or_table(self):
        value = cell('<script>bad</script> | fake\n# header [link](https://evil.test)')
        self.assertNotIn('<script>', value)
        self.assertNotIn('|', value)
        self.assertNotIn('\n#', value)
        self.assertIn('\\[link\\]', value)


if __name__ == '__main__':
    unittest.main()
