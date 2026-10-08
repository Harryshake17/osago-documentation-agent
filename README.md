# OSAGO Documentation Agent

Репозиторий skills и инструментов пайплайна документации ОСАГО.

- `skills/` — инструкции профильных агентов и декларативная конфигурация пайплайна.
- `tools/knowledge/` — оркестратор, генераторы, validators, pipeline gates и regression tests.
- `knowledge-contracts/` — общие JSON schemas, contracts и standards; единая модель знаний для всех skills.

## Запуск tools

Требуется Python 3.11+.

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .venv/Scripts/Activate.ps1
python -m pip install -r tools/knowledge/requirements.txt
python tools/knowledge/orchestrate.py --help
python tools/knowledge/orchestrate.py init --domain "Новый бизнес eОСАГО Link2" --run-id link2
python tools/knowledge/orchestrate.py resume --run runs/link2
```

Python controller выдаёт задачи для skills и проверяет их outputs. Сам controller не вызывает LLM/MCP, не исследует предметную систему и не публикует страницы через Confluence API.
Agent выполняет указанный skill по его `SKILL.md`, сохраняет артефакты и передаёт результат controller. Human checkpoints требуют реального ответа пользователя.

Tools поддерживают standalone layout этого репозитория (`skills/`, `knowledge-contracts/`) и IDE layouts (`.codex/` или `.cursor/`) без изменения модели знаний.
При переносе в другой проект копируйте tools, contracts и skills вместе. Относительные ссылки skills на contracts сохраняйте.

## Проверки

```bash
python -m unittest discover -s tools/knowledge/tests -p "test_*.py"
python -m unittest discover -s tools/knowledge/tests -p "test_pipeline_gates.py"
```

Tests используют локальные fixtures; production runs и application sources не входят в этот репозиторий.
Confluence renderer готовит storage XHTML и handoff metadata. Для Mermaid без готового изображения требуется установленный `mmdc`; API publication выполняется отдельным publisher.

## Пайплайн

<img width="1472" height="2788" alt="osago-documentation-pipeline-full" src="https://github.com/user-attachments/assets/8780c4b7-0b51-4022-bf57-9f371cd3e1db" />
