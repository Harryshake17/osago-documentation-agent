"""Presentation regression on a small, explicit Link2 fixture. No page mutations."""
import copy
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from confluence_render import RenderError, make_plan, approve, render, write_bundle, check_storage, sha, digest, AC, RI
from validate import load, schema_errors

HERE = Path(__file__).parent/'fixtures/confluence-render'

class ConfluenceRenderTests(unittest.TestCase):
    def setUp(self):
        self.document = (HERE/'link2-reviewed.md').read_bytes().decode('utf8')
        self.manifest = load(HERE/'documentation-manifest.json')
        self.plan = approve(make_plan(self.document,self.manifest))
        self.presentation = load(HERE/'presentation-metadata.yaml')

    def run_render(self, **kwargs):
        return render(self.document,self.manifest,self.plan,
            metadata=kwargs.pop('metadata',self.presentation),asset_root=HERE,**kwargs)

    def test_link2_actual_heading_hierarchy(self):
        body,meta,_ = self.run_render()
        root = check_storage(body)
        expected = [h['text'] for h in self.plan['headings']]
        actual = [''.join(e.itertext()) for e in root.iter() if e.tag in {'h1','h2','h3'}]
        self.assertEqual(actual,expected)
        self.assertEqual(len(root.findall('h1')),1)
        self.assertEqual(len(root.findall('h2')),12)
        self.assertEqual(len(root.findall('.//h3')),2)
        self.assertEqual(schema_errors('confluence-render',meta),[])

    def test_table_cell_shape_and_order(self):
        root = check_storage(self.run_render()[0])
        rows = root.findall('.//table//tr')
        self.assertEqual([len(list(r)) for r in rows],[6,6,6])
        self.assertEqual([''.join(r[0].itertext()) for r in rows],['Шаг','1','2'])
        self.assertEqual(''.join(rows[2][5].itertext()),'ReadyForSign')

    def test_lists_including_nested_and_ordered_survive(self):
        root = check_storage(self.run_render()[0])
        self.assertTrue(root.findall('.//ul/li/ul/li'))
        self.assertEqual([ ''.join(x.itertext()) for x in root.findall('.//ol/li')],
                         ['Получение ссылки на оплату.','Переход клиента на Universal Online Payment.'])

    def test_inline_and_block_code_preserve_technical_spelling(self):
        root = check_storage(self.run_render()[0])
        codes = [''.join(c.itertext()) for c in root.findall('.//code')]
        for value in ['POST /api/link2/import','RegisterPolicyContractNSIS','ReadyForSign','addressRecognitionAccuracy >= 7','UNKNOWN','CONFLICT']:
            self.assertIn(value,codes)
        self.assertIn('RegisterPolicyContractNSIS',''.join(root.find('.//pre').itertext()))
        self.assertNotIn('RegisterPolicyContractNsis',self.run_render()[0])

    def test_rules_are_normal_blocks_and_material_warning_is_separate(self):
        root = check_storage(self.run_render()[0])
        rules = list(root)[list(root).index(root.find("h2[.='6. Бизнес-правила и точки принятия решений']"))+1]
        self.assertEqual(rules.tag,'h3')
        macros = root.findall('.//{'+AC+'}structured-macro')
        warning = [e for e in macros if e.get('{'+AC+'}name')=='warning']
        info = [e for e in macros if e.get('{'+AC+'}name')=='info']
        self.assertTrue(warning)
        self.assertTrue(info)
        self.assertIn('Источники расходятся',''.join(warning[0].itertext()))
        self.assertIn('пяти исследованных production-кейсах',''.join(root.itertext()))

    def test_no_markdown_paths_ids_in_body_traceability_stays_private(self):
        body,meta,_ = self.run_render()
        for fragment in ['# Новый','## ','**','`','[!WARNING]','[!NOTE]','| ---','claim:osago','entity:osago','evidence:link2','sources/Link2','U:','link2-flow.mmd']:
            self.assertNotIn(fragment,body)
        self.assertTrue(meta['traceability']['hidden_references'])
        self.assertEqual(meta['traceability']['claim_ids'],self.manifest['claim_ids'])
        self.assertIn('sources/Link2/Import.cs',json.dumps(meta,ensure_ascii=False))

    def test_confluence_link_uses_readable_label(self):
        root = check_storage(self.run_render()[0])
        link = root.find('.//a')
        self.assertEqual(link.get('href'),'https://confluence.example.invalid/pages/viewpage.action?pageId=1012451678')
        self.assertEqual(''.join(link.itertext()),'Статья о новом бизнесе eОСАГО Link2')

    def test_diagram_attachment_is_real_image_not_mmd_text(self):
        body,meta,assets = self.run_render()
        root = check_storage(body)
        resource = root.find('.//{'+RI+'}attachment')
        name = resource.get('{'+RI+'}filename')
        self.assertIn(name,assets)
        self.assertTrue(assets[name].startswith(b'\x89PNG'))
        self.assertEqual(meta['attachments'][0]['content_hash'],sha(assets[name]))
        self.assertNotIn('.mmd',body)

    def test_gate_cannot_be_promoted_by_rendering(self):
        _,meta,_ = self.run_render()
        self.assertEqual(meta['publisher']['publication_gate'],'blocked')
        self.assertFalse(meta['publisher']['eligible'])

    def test_approval_and_stale_inputs_block_render(self):
        with self.assertRaises(RenderError):
            render(self.document,self.manifest,make_plan(self.document,self.manifest))
        modified = copy.deepcopy(self.plan)
        modified['technical_expand'] = True
        with self.assertRaises(RenderError):
            render(self.document,self.manifest,modified)
        with self.assertRaises(RenderError):
            render(self.document+'\nNew fact',self.manifest,self.plan)

    def test_missing_manifest_or_inputs_do_not_trigger_research(self):
        with self.assertRaises((RenderError,TypeError)):
            make_plan(self.document,{})
        with patch('urllib.request.urlopen',side_effect=AssertionError('network')), patch('subprocess.run',side_effect=AssertionError('source access')):
            self.run_render()

    def test_expand_is_opt_in_and_keeps_gaps_outside(self):
        self.plan = approve(make_plan(self.document,self.manifest,technical_expand=True))
        body,_,_ = self.run_render()
        root = check_storage(body)
        expand = root.find('.//{'+AC+'}structured-macro[@{'+AC+'}name="expand"]')
        self.assertIsNotNone(expand)
        self.assertIn('RegisterPolicyContractNSIS',''.join(expand.itertext()))
        self.assertNotIn('Источники расходятся',''.join(expand.itertext()))

    def test_unprepared_mermaid_does_not_fall_back_to_plaintext(self):
        data = copy.deepcopy(self.presentation)
        data['diagrams']['link2-flow.mmd'].pop('rendered_file')
        with patch('shutil.which',return_value=None), self.assertRaises(RenderError):
            self.run_render(metadata=data)

    def test_path_traversal_and_invalid_diagram_fail(self):
        data = copy.deepcopy(self.presentation)
        data['diagrams']['link2-flow.mmd']['rendered_file']='../cases.yaml'
        with self.assertRaises(RenderError):
            self.run_render(metadata=data)
        data['diagrams']['link2-flow.mmd']['rendered_file']='link2-flow.mmd'
        with self.assertRaises(RenderError):
            self.run_render(metadata=data)

    def test_unsafe_markup_is_escaped_and_body_is_deterministic(self):
        result = self.run_render()
        self.assertEqual(result,self.run_render())
        doc = self.document.replace('Партнёр Link2 передаёт данные анкеты.','Партнёр Link2 передаёт данные анкеты. <script>alert(1)</script>')
        manifest = copy.deepcopy(self.manifest)
        manifest['document_hash']=sha(doc)
        body,_,_ = render(doc,manifest,approve(make_plan(doc,manifest)),metadata=self.presentation,asset_root=HERE)
        self.assertNotIn('<script>',body)

    def test_artifact_dump_is_not_presented_as_reviewed_content(self):
        doc = self.document.replace('Бизнес-причина проверки точности адреса пока не подтверждена: UNKNOWN.',
            'Comparison: {"claim_ids": ["claim:osago-link2:purpose"], "status": "CONFLICT"}')
        manifest = copy.deepcopy(self.manifest); manifest['document_hash']=sha(doc)
        with self.assertRaises(RenderError):
            render(doc,manifest,approve(make_plan(doc,manifest)),metadata=self.presentation,asset_root=HERE)

    def test_rule_nested_scenario_list_is_not_flattened(self):
        doc = self.document.replace('- Причина: UNKNOWN.', '- Причина: UNKNOWN.\n\n- Первый вариант\n  - Проверка\n- Второй вариант')
        manifest = copy.deepcopy(self.manifest); manifest['document_hash']=sha(doc)
        # This altered synthetic document needs adjusted line spans, not forged source lineage.
        extra = len(doc.splitlines())-len(self.document.splitlines())
        for block in manifest['document']['blocks']:
            if block['section']=='business-rules': block['end_line']+=extra
            elif block['start_line']>40: block['start_line']+=extra;block['end_line']+=extra
        body,_,_=render(doc,manifest,approve(make_plan(doc,manifest)),metadata=self.presentation,asset_root=HERE)
        root=check_storage(body)
        self.assertTrue(any('Первый вариант' in ''.join(e.itertext()) for e in root.findall('.//ul/li/ul/..')))

    def test_language_review_final_hash_binding(self):
        from test_composer_contracts import fixture
        from compose import compose
        from language_review import review
        inputs,validation,gaps,glossary=fixture()
        draft,manifest=compose(inputs,validation,gaps,glossary)
        final,report=review(draft,glossary,inputs['scenario'],validation,manifest=manifest)
        self.assertEqual(report['review']['status'],'COMPLETED')
        make_plan(final,manifest,report)
        report['final_hash']='0'*64
        with self.assertRaises(RenderError): make_plan(final,manifest,report)

    def test_private_metadata_lines_do_not_leave_empty_artifact_labels(self):
        body,meta,_=self.run_render()
        self.assertNotIn('Внутренняя трассировка:',body)
        self.assertNotIn('Локальный путь:',body)
        self.assertNotIn('<code></code>',body)
        self.assertIn('Подтверждение назначения.',body)
        self.assertTrue(any(r['kind']=='private-metadata-line' for r in meta['traceability']['hidden_references']))

    def test_substantive_private_id_without_a_reviewed_label_stops_render(self):
        doc=self.document.replace('| Партнёр Link2 | Первичный расчёт','| entity:osago-link2:scenario | Первичный расчёт')
        manifest=copy.deepcopy(self.manifest);manifest['document_hash']=sha(doc)
        with self.assertRaises(RenderError):
            render(doc,manifest,approve(make_plan(doc,manifest)),metadata=self.presentation,asset_root=HERE)

    def test_explicit_line_break_stays_inside_its_paragraph(self):
        doc=self.document.replace('Оформление нового полиса eОСАГО для партнёра Link2.\n', 'Оформление нового полиса eОСАГО для партнёра Link2.  \n')
        manifest=copy.deepcopy(self.manifest);manifest['document_hash']=sha(doc)
        body,_,_=render(doc,manifest,approve(make_plan(doc,manifest)),metadata=self.presentation,asset_root=HERE)
        root=check_storage(body)
        self.assertIsNotNone(root.find('.//p/br'))

    def test_code_symbol_is_preserved_even_when_it_is_a_codecomponent_id(self):
        manifest=copy.deepcopy(self.manifest)
        for block in manifest['document']['blocks']:
            if block['section']=='technical': block['derived_from'].extend(['RegisterPolicyContractNSIS','7'])
        body,_,_=render(self.document,manifest,approve(make_plan(self.document,manifest)),metadata=self.presentation,asset_root=HERE)
        codes=[''.join(e.itertext()) for e in check_storage(body).findall('.//code')]
        self.assertIn('RegisterPolicyContractNSIS',codes)
        self.assertIn('addressRecognitionAccuracy >= 7',codes)

    def test_diagram_source_hash_detects_stale_bundle(self):
        import shutil
        with tempfile.TemporaryDirectory() as directory:
            shutil.copytree(HERE,Path(directory)/'assets')
            root=Path(directory)/'assets'
            body,first,_=render(self.document,self.manifest,self.plan,metadata=self.presentation,asset_root=root)
            source=root/'link2-flow.mmd'
            source.write_bytes(source.read_bytes()+b'\n%% presentation fixture revision\n')
            same_body,changed,_=render(self.document,self.manifest,self.plan,metadata=self.presentation,asset_root=root)
            self.assertEqual(body,same_body)
            self.assertNotEqual(first['attachments'][0]['source_hash'],changed['attachments'][0]['source_hash'])

    def test_cli_plan_approval_render_and_check(self):
        script = Path(__file__).resolve().parents[1]/'confluence_render.py'
        with tempfile.TemporaryDirectory() as tmp:
            plan = str(Path(tmp)/'plan.yaml')
            output = str(Path(tmp)/'bundle')
            base = [sys.executable,'-X','utf8',str(script)]
            args = ['--document',str(HERE/'link2-reviewed.md'),'--manifest',str(HERE/'documentation-manifest.json'),'--plan',plan]
            def call(mode,extra):
                return subprocess.run(base+[mode]+extra,text=True,capture_output=True)
            self.assertEqual(call('plan',args).returncode,0)
            self.assertNotEqual(call('approve',['--plan',plan]).returncode,0)
            self.assertEqual(call('approve',['--plan',plan,'--human-agreement']).returncode,0)
            extra = args+['--metadata',str(HERE/'presentation-metadata.yaml'),'--asset-root',str(HERE),'--output-dir',output]
            result = call('render',extra)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(call('check',extra).returncode,0)
            self.assertNotEqual(call('render',extra).returncode,0)
            Path(output,'10-confluence-body.storage.xhtml').write_text('<p>Tampered</p>',encoding='utf8')
            self.assertNotEqual(call('check',extra).returncode,0)
