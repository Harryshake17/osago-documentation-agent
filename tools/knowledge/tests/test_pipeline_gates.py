"""Pipeline gates over validated Link2 fixtures and real documentation producers."""
import copy
import hashlib
from pathlib import Path
import socket
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit import digest
from compose import compose
from language_review import review
from pipeline_gates import (PipelineGateError, technical_model, scenario_model,
    publication_relevance, document_structure, final_invariants, effective_gates)
from orchestrate import Run, DEFAULT_PIPELINE, pipeline_errors, save_data
from test_reader_first_composer import fixture as link2_fixture
from test_composer_contracts import fixture as glossary_fixture
from test_language_review import build_case
import test_orchestrate as orchestration_fixture
from validate import load


class PipelineGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = link2_fixture()
        inputs, report, gaps, glossary = cls.base
        cls.draft, cls.manifest = compose(inputs, report, gaps, glossary)
        cls.final, cls.review = review(cls.draft, glossary, inputs['scenario'], report,
            manifest=cls.manifest, technical_flow=inputs['technical-flow'], business_rules=inputs['business-rules'])

    def setUp(self):
        self.inputs, self.report, self.gaps, self.glossary = copy.deepcopy(self.base)
        self.context = dict(self.inputs, report=self.report, gaps=self.gaps, glossary=self.glossary)
        self.manifest = copy.deepcopy(self.__class__.manifest)
        self.result = copy.deepcopy(self.__class__.review)

    def document_gate(self, document):
        document_structure(document, self.manifest, self.context)

    def final_gate(self, document, result=None):
        result = copy.deepcopy(self.result if result is None else result)
        result['final_hash'] = hashlib.sha256(document.encode('utf-8')).hexdigest()
        final_invariants(document, self.draft, self.manifest, result, self.context)

    def test_validated_link2_composer_reviewer_gates_tail_without_research_or_repairs(self):
        before = copy.deepcopy((self.inputs, self.report, self.gaps, self.glossary))
        with patch.object(socket, 'socket', side_effect=AssertionError('No network allowed')):
            technical_model(self.inputs)
            scenario_model(self.inputs)
            publication_relevance(self.report, self.gaps, self.inputs)
            draft, manifest = compose(self.inputs, self.report, self.gaps, self.glossary)
            document_structure(draft, manifest, self.context)
            final, result = review(draft, self.glossary, self.inputs['scenario'], self.report,
                manifest=manifest, technical_flow=self.inputs['technical-flow'], business_rules=self.inputs['business-rules'])
            final_invariants(final, draft, manifest, result, self.context)
        self.assertEqual(result['review']['status'], 'COMPLETED')
        self.assertEqual(result['publication_gate'], self.report['summary']['publication_gate'])
        self.assertEqual(before, (self.inputs, self.report, self.gaps, self.glossary))
        self.assertEqual(result['blocks'], manifest['document']['blocks'])

    def test_technical_gate_rejects_competing_ids_namespaces_and_refs(self):
        for failure in ('competing', 'duplicate', 'namespace', 'refs'):
            with self.subTest(failure=failure):
                inputs = copy.deepcopy(self.inputs)
                flow = inputs['technical-flow']
                if failure == 'competing': flow['steps'] = copy.deepcopy(flow['nodes'])
                elif failure == 'duplicate': flow['nodes'].append(copy.deepcopy(flow['nodes'][0]))
                elif failure == 'namespace': flow['nodes'][0]['id'] = 'scenario-step:wrong-model'
                else: flow['nodes'][0]['component_id'] = 'component:missing'
                with self.assertRaisesRegex(PipelineGateError, 'technical-model/'):
                    technical_model(inputs)

    def test_scenario_gate_rejects_two_main_flows_null_main_refs_and_technical_steps(self):
        for failure in ('two mains', 'no main', 'dangling', 'technical step'):
            with self.subTest(failure=failure):
                inputs = copy.deepcopy(self.inputs)
                scenario = inputs['scenario']
                if failure == 'two mains':
                    extra = copy.deepcopy(next(f for f in scenario['flows'] if f['type'] == 'main'))
                    extra['id'] = 'scenario-flow:competing'
                    scenario['flows'].append(extra)
                elif failure == 'no main': scenario['main_flow'] = None
                elif failure == 'dangling': scenario['flows'][0]['step_refs'][0] = 'scenario-step:missing'
                else: scenario['steps'][0]['id'] = inputs['technical-flow']['nodes'][0]['id']
                with self.assertRaisesRegex(PipelineGateError, 'scenario-model/'):
                    scenario_model(inputs)

    def test_validation_gate_requires_reviewed_publication_relevance_and_exact_subset(self):
        next(g for g in self.gaps['gaps'] if g['id'] in self.gaps['publication_subset']['gap_ids'])['publication_relevance']['reviewed'] = False
        with self.assertRaisesRegex(PipelineGateError, 'publication-relevance/UNASSESSED'):
            publication_relevance(self.report, self.gaps, self.inputs)
        self.gaps = copy.deepcopy(self.base[2])
        self.gaps['publication_subset']['gap_ids'] = []
        with self.assertRaisesRegex(PipelineGateError, 'publication-relevance/SUBSET_OR_IMPACT'):
            publication_relevance(self.report, self.gaps, self.inputs)

    def test_composer_gate_rejects_duplicate_main_section_and_appended_uc_or_table(self):
        table = self.draft.split('| Шаг |', 1)[1].split('\n\n', 1)[0]
        cases = [('\n## 5. Основной бизнес-процесс\n', 'MAIN_FLOW_COUNT'),
                 ('\n### UC Main flow\nПовтор процесса.\n', 'APPENDED_PROCESS_COPY'),
                 ('\nHappy path: дубликат.\n', 'APPENDED_PROCESS_COPY'),
                 ('\n| Шаг |' + table + '\n', 'COMPETING_FLOW_TABLES')]
        for addition, code in cases:
            with self.subTest(code=code), self.assertRaisesRegex(PipelineGateError, code):
                self.document_gate(self.draft + addition)

    def test_composer_gate_rejects_implementation_before_reader_sections(self):
        document = self.draft.replace('## 1. Назначение', '## 10. Техническая реализация', 1)
        with self.assertRaisesRegex(PipelineGateError, 'READER_FIRST_SECTIONS'):
            self.document_gate(document)

    def test_composer_gate_rejects_internal_gaps_even_in_technical_section(self):
        gap = next(g for g in self.gaps['gaps'] if g['id'] == 'gap:composer:link2:internal')
        document = self.draft.replace('## 11.', gap['question'] + '\n\n## 11.', 1)
        with self.assertRaisesRegex(PipelineGateError, 'PROVENANCE_SPANS|INTERNAL_RESEARCH_GAP'):
            self.document_gate(document)
        # Plain internal question, no ID/path: raw-locator detection is insufficient.
        self.gaps['gaps'].append(dict(gap, id='gap:fixture:plain', question='Как работает второстепенный helper?'))
        document = self.draft + '\nКак работает второстепенный helper?\n'
        with self.assertRaisesRegex(PipelineGateError, 'INTERNAL_RESEARCH_GAP'):
            self.document_gate(document)

    def test_composer_gate_rejects_reader_paths_ids_and_metadata_but_keeps_endpoints(self):
        for text, code in [('../internal/Helper.cs', 'FILESYSTEM_PATH_IN_NARRATIVE'),
                           ('claim:fixture:private', 'INTERNAL_ID_IN_NARRATIVE'),
                           ('pageId=123', 'INTERNAL_ID_IN_NARRATIVE')]:
            with self.subTest(text=text), self.assertRaisesRegex(PipelineGateError, code):
                self.document_gate(self.draft + '\n' + text + '\n')
        self.document_gate(self.draft + '\nВнешний контракт: `/api/import`.\n')
        self.document_gate(self.draft + '\n[Описание процесса](https://kb.example/viewpage.action?pageId=123).\n')

    def test_final_gate_rejects_missing_sections_inventory_and_manifest_lineage(self):
        with self.assertRaisesRegex(PipelineGateError, 'final-invariants/READER_FIRST_SECTIONS'):
            self.final_gate(self.final.replace('## 2. Область действия', '## 2. Удалённый раздел'))
        for field, value in [('claim_ids', []), ('blocks', []), ('publication_gate', 'passed')]:
            with self.subTest(field=field):
                result = copy.deepcopy(self.result);result[field] = value
                with self.assertRaisesRegex(PipelineGateError, 'FACTUAL_LINEAGE_LOST'):
                    self.final_gate(self.final, result)

    def test_forged_success_and_hash_do_not_hide_material_question(self):
        gap = next(g for g in self.gaps['gaps'] if g['id'] in self.gaps['publication_subset']['gap_ids'])
        changed = self.final.replace(gap['question'], 'Открытых вопросов нет.')
        self.assertNotEqual(changed, self.final)
        with self.assertRaisesRegex(PipelineGateError, 'final-invariants/MATERIAL_GAP_HIDDEN'):
            self.final_gate(changed)
        with self.assertRaisesRegex(PipelineGateError, 'document-structure/MATERIAL_GAP_HIDDEN'):
            self.document_gate(changed)

    def test_final_gate_conflict_is_not_hidden_or_resolved_by_forged_report(self):
        document, inputs, report, glossary, manifest = build_case(glossary_fixture(),
            {'action': 'Источники расходятся по порядку X и Y.', 'status': 'CONFLICT'})
        gaps = manifest['document']['provenance']['validation-gaps']
        context = dict(inputs, report=report, gaps=gaps, glossary=glossary)
        final, result = review(document, glossary, inputs['scenario'], report, manifest=manifest)
        self.assertEqual(result['review']['status'], 'COMPLETED')
        final_invariants(final, document, manifest, result, context)
        changed = final.replace('Источники расходятся [CONFLICT]:', 'Последовательность подтверждена:')
        result['final_hash'] = hashlib.sha256(changed.encode('utf-8')).hexdigest()
        with self.assertRaisesRegex(PipelineGateError, 'MATERIAL_CONFLICT_HIDDEN'):
            final_invariants(changed, document, manifest, result, context)

    def test_material_question_operator_is_not_lost_during_visibility_check(self):
        question = 'Уточнить назначение проверки accuracy >= 7.'
        gap = next(g for g in self.gaps['gaps'] if g['id'] in self.gaps['publication_subset']['gap_ids'])
        gap['question'] = question
        document, manifest = compose(self.inputs, self.report, self.gaps, self.glossary)
        document_structure(document, manifest, self.context)
        changed = document.replace('accuracy &gt;= 7', 'accuracy &gt; 7')
        self.assertNotEqual(changed, document)
        with self.assertRaisesRegex(PipelineGateError, 'MATERIAL_GAP_HIDDEN'):
            document_structure(changed, manifest, self.context)

    def test_declarative_gates_and_historical_floor_cannot_be_disabled(self):
        config = load(DEFAULT_PIPELINE)
        self.assertEqual(pipeline_errors(config), [])
        for stage in config['stages']:
            if stage.get('gates'):
                saved = copy.deepcopy(stage);saved.pop('gates')
                self.assertEqual(effective_gates(saved), stage['gates'])
        next(s for s in config['stages'] if s['primary'] == 'documentation')['gates'] = []
        self.assertTrue(any('gates must match' in e for e in pipeline_errors(config)))


class PipelineGateRunTests(unittest.TestCase):
    def setUp(self):
        self.workflow = orchestration_fixture.OrchestratorTests(methodName='test_01_happy_path_order_and_conditional_review')
        self.workflow.setUp()
        self.addCleanup(self.workflow.cleanup_directory)
        self.workflow.run = Run.create(Path(self.workflow.tmp.name) / 'canonical',
            {'domain': 'Synthetic gate workflow'}, run_id='gates-test')

    def test_composer_failure_stops_downstream_preserves_inputs_and_returns_producer_diagnostic(self):
        workflow = self.workflow
        workflow.through_validation();workflow.produce()
        def bad_document(task, result):
            directory = Path(task['output_dir'])
            path = directory / result['artifacts']['documentation']
            text = path.read_bytes().decode('utf-8') + '\n### UC Main flow\nПовтор процесса.\n'
            path.write_bytes(text.encode('utf-8'))
            for key in ('documentation-manifest', 'documentation-meta'):
                target = directory / result['artifacts'][key]
                metadata = load(target);metadata['document_hash'] = hashlib.sha256(text.encode()).hexdigest()
                save_data(target, metadata)
        before = copy.deepcopy(workflow.run.state['nodes']['scenario-reconstruction@fixture']['bundle'])
        accepted, task, outputs = workflow.producer.produce(workflow.run, mutate=bad_document)
        self.assertEqual(accepted['action'], 'FAILED')
        self.assertIn('document-structure/APPENDED_PROCESS_COPY', accepted['error'])
        self.assertIn('osago-documentation-composer', accepted['error'])
        self.assertEqual(workflow.run.plan()['action'], 'FAILED')
        self.assertEqual(workflow.run.state['nodes']['language-review@fixture']['status'], 'PENDING')
        self.assertEqual(workflow.run.state['nodes']['confluence-plan@fixture']['status'], 'PENDING')
        self.assertEqual(before, workflow.run.state['nodes']['scenario-reconstruction@fixture']['bundle'])
        document = Path(task['output_dir']) / outputs['artifacts']['documentation']
        self.assertIn('UC Main flow', document.read_text(encoding='utf-8'))
        with self.assertRaises(ValueError): workflow.run.start('language-review@fixture')

    def test_resume_rejects_previously_accepted_bad_tail_and_keeps_diagnostics(self):
        workflow = self.workflow
        workflow.through_validation();workflow.produce()
        def historical_bad_document(task, result):
            folder = Path(task['output_dir'])
            path = folder / result['artifacts']['documentation']
            text = path.read_bytes().decode('utf-8') + '\n### UC Main flow\nПовтор процесса.\n'
            path.write_bytes(text.encode('utf-8'))
            for key in ('documentation-manifest', 'documentation-meta'):
                target = folder / result['artifacts'][key]
                metadata = load(target);metadata['document_hash'] = hashlib.sha256(text.encode()).hexdigest()
                save_data(target, metadata)
        # Simulate an accepted pre-gate bundle without rewriting its bytes on resume.
        with patch('orchestrate.run_gate', return_value=None):
            accepted, task, result = workflow.producer.produce(workflow.run, mutate=historical_bad_document)
        self.assertEqual(accepted['action'], 'ACCEPTED')
        path = Path(task['output_dir']) / result['artifacts']['documentation']
        before = path.read_bytes()
        resumed = Run(workflow.run.root)
        plan = resumed.plan()
        self.assertEqual(plan['action'], 'FAILED')
        self.assertEqual(plan['node_id'], 'documentation@fixture')
        self.assertIn('document-structure/APPENDED_PROCESS_COPY', plan['error']['message'])
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(resumed.state['nodes']['confluence-plan@fixture']['status'], 'STALE')
        self.assertEqual(Run(workflow.run.root).plan()['action'], 'FAILED')

    def test_failed_final_invariant_keeps_composer_completed(self):
        workflow = self.workflow
        workflow.through_validation();workflow.produce();workflow.produce()
        def lost_lineage(task, result):
            path = Path(task['output_dir']) / result['artifacts']['language-review']
            report = load(path);report['claim_ids'] = []
            save_data(path, report)
        accepted, _, _ = workflow.producer.produce(workflow.run, mutate=lost_lineage)
        self.assertEqual(accepted['action'], 'FAILED')
        self.assertIn('final-invariants/FACTUAL_LINEAGE_LOST', accepted['error'])
        self.assertEqual(workflow.run.state['nodes']['documentation@fixture']['status'], 'COMPLETED')
        self.assertEqual(workflow.run.plan()['action'], 'FAILED')


if __name__ == '__main__':
    unittest.main()
