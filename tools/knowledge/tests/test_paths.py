"""Resource discovery for standalone and installed skill layouts."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import contracts_root, skill_resource
from orchestrate import DEFAULT_PIPELINE, resolve_skill_path, pipeline_errors
from validate import SCHEMAS, load
from compose import STANDARDS
from confluence_render import PROFILE


class ResourcePathsTests(unittest.TestCase):
    def test_all_supported_layouts(self):
        for prefix in ('', '.codex', '.cursor'):
            with self.subTest(prefix=prefix), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                contracts = root / prefix / 'knowledge-contracts'
                contracts.mkdir(parents=True)
                resource = root / prefix / 'skills/example/SKILL.md'
                resource.parent.mkdir(parents=True)
                resource.write_text('example', encoding='utf8')
                self.assertEqual(contracts_root(root), contracts)
                self.assertEqual(skill_resource('example', 'SKILL.md', root=root), resource)

    def test_existing_resource_wins_over_partial_layout(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'skills/example').mkdir(parents=True)
            resource = root / '.codex/skills/example/SKILL.md'
            resource.parent.mkdir(parents=True)
            resource.write_text('example', encoding='utf8')
            self.assertEqual(skill_resource('example', 'SKILL.md', root=root), resource)

    def test_checkout_dependencies_and_pipeline_are_resolved(self):
        self.assertTrue(SCHEMAS.is_dir())
        self.assertTrue((STANDARDS / 'documentation-template.md').is_file())
        self.assertTrue(PROFILE.is_file())
        pipeline = load(DEFAULT_PIPELINE)
        self.assertEqual(pipeline_errors(pipeline), [])
        for stage in pipeline['stages']:
            if stage.get('skill'):
                self.assertTrue(Path(resolve_skill_path(stage['skill'])).is_file(), stage['skill'])


if __name__ == '__main__':
    unittest.main()
