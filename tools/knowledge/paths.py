"""Resolve resources in a standalone checkout or an installed IDE skill layout."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def contracts_root(root=ROOT):
    candidates = [Path(root) / prefix / 'knowledge-contracts'
                  for prefix in ('', '.codex', '.cursor')]
    return next((path for path in candidates if path.is_dir()), candidates[0])


def skill_resource(name, *parts, root=ROOT):
    candidates = [Path(root) / prefix / 'skills' / name / Path(*parts)
                  for prefix in ('', '.codex', '.cursor')]
    return next((path for path in candidates if path.is_file()), candidates[0])
