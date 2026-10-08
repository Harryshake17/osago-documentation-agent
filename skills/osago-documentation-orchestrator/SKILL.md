---
name: osago-documentation-orchestrator
description: Запустить и продолжить полный workflow документации домена ОСАГО API по одному запросу пользователя, например «Документируй домен Новый бизнес eОСАГО Link2». Последовательно применять существующие osago skills, сохранять run/artifacts, ждать human checkpoints, выполнять retry/resume, инвалидировать stale outputs и подготовить Confluence representation без API publication.
---

# Documentation Orchestrator

Управляй workflow и persisted state; предметную работу выполняют существующие skills.
В роли controller не исследуй code/config/Confluence/OpenSearch, не создавай business knowledge и terminology,
не исправляй смысл outputs сам. OpenSearch MCP вызывают профильные skills по shared runtime policy.
Перед работой прочитай [workflow](references/workflow.md),
[pipeline configuration](references/pipeline.yaml) и
[shared knowledge model](../../knowledge-contracts/standards/knowledge-model.md).

Одного названия домена достаточно. Не требуй classes, methods, process names, accountNumber,
queries или source URLs. Optional scope_hints/known_sources/existing_document передай Domain
Decomposer без собственной интерпретации. Новый run хранится в runs/<run_id>/; для resume
используй указанную папку/run_id, не начинай исследование заново.

Оркестратор — IDE/AI-agent loop над `tools/knowledge/orchestrate.py`. Python helper не вызывает
LLM/skills/MCP и не заменяет агента: он выдаёт следующую ready task, принимает artifacts,
проверяет их существующими validators и обязательными pipeline gates, сохраняет state. Агент читает SKILL.md указанного
профильного skill и применяет его в текущей задаче; пользователю не нужно запускать skills.
На время EXECUTE_SKILL выполняй предметную работу по инструкциям этого producer;
исследование источников относится к его stage, а не к orchestration/resume/review logic.
Не создавать отдельные чаты и не предполагать доступность delegation/tool API для вызова skills.

1. Создай run через `init --domain "<область>"`; optional structured request — через --request.
   Если пользователь указал current glossary, передай --glossary; иначе baseline пустой,
   созданный существующим Curator initializer. Global glossary не перезаписывается автоматически.
2. Читай action из `resume`. Для EXECUTE_SKILL вызови `start`, прочитай task.skill_path,
   передай ровно task.inputs плюс output_dir, previous_outputs для сохранения истории и
   pending corrections. Выполни профильный skill до полного результата и semantic checks.
   У каждого stage собственная immutable attempt folder; inputs не перезаписываются.
3. Сохрани result.yaml с ровно task.outputs, относительными к output_dir paths; подай в
   `finish`. Только ACCEPTED после всех gates разрешает следующий stage. Gates декларативны
   в pipeline.yaml; исторический snapshot без поля gates сохраняет обязательные
   проверки по producer contract, без изменения DAG. Ошибку профильного
   skill запиши через `fail`; не запускай downstream и не удаляй прежние artifacts.
4. **После Domain Decomposer всегда остановись на scope review.** Покажи scope, scenarios,
   capabilities, exclusions и ambiguous boundaries из ready review; дождись реального
   APPROVE/correction. Не отправляй APPROVE от имени пользователя. Требование остановки
   задано ТЗ orchestrator, а не permission flow предметного skill.
5. Evidence review показывай только при action WAITING_FOR_USER с unresolved questions.
   Confirmed claims не показывай. При APPROVE пользователь принимает сохранённые ограничения
   draft; это не повышает KnowledgeStatus, не разрешает Conflict и не разрешает публикацию.
6. Сохрани ответ через `review`. CORRECT направь владельцу structured artifact; engine
   создаст pending correction task и инвалидирует dependents. Профильный skill должен
   применить correction к artifact и указать applied_review_ids. Для новых evidence/claims
   соблюдай прежние contracts/revisions; снова выполни Validator. При изменении reviewed
   scope/evidence потребуется approval нового результата; старое approval связано с hashes.
7. Для FAILED нужен явный retry; RUNNING после session interruption не запускай второй раз:
   продолжи recorded attempt либо явно запиши interrupted failure и затем retry. Rerun from
   stage инвалидирует только transitively dependent nodes. COMPLETED с неизменными inputs
   не повторяй. Рабочую папку, run_id и stage IDs сохраняй после новой IDE session.
8. После Composer выполняй декларативный stage `language-review` по его SKILL.md.
   Передай только draft/manifest, glossary, Scenario, Validation и предусмотренные config
   structured sidecars. Reviewer не исследует источники и не исправляет knowledge.
   `finish` принимает stage только при успешных language/semantic checks и COMPLETED report.
   FAILED или WAITING_FOR_REVIEW report не завершает run; Composer остаётся COMPLETED.
9. После Language Reviewer выполни presentation stages из pipeline config:
   `confluence-plan` (osago-confluence-renderer, presentation_mode=plan),
   `presentation-review` (human checkpoint), `confluence-render` (тот же skill,
   presentation_mode=render). План получает только reviewed document, Composer manifest
   и Language Review report. Diagram/link metadata — presentation sidecar этого stage,
   собранный из уже предоставленных reviewed материалов; новые facts не искать.
   Покажи H1/H2/H3, порядок разделов, technical expand и выбранные диаграммы. Сохрани
   реальное согласие через review; уже полученное согласие этой конкретной структуре
   можно записать без повторного вопроса. Согласование связано с hashes обоих sidecars.
   В render task используй hierarchy_approval из state. Не изменяй accepted plan:
   копию для CLI approve положи в новую attempt folder. Approval структуры не разрешает
   API publication. Render failure сохраняет COMPLETED Composer и Language Reviewer;
   retry повторяет только rendering. Run завершён после принятого render каждой Scenario.
10. COMPLETED возвращает paths согласованных artifacts каждой Scenario. Итоговая статья —
   `final-document` (`09-final-document.md`), draft сохраняется для provenance.
   Confluence representation — `confluence-body` (`10-confluence-body.storage.xhtml`),
   handoff — `publisher-metadata` (`10-publisher-metadata.yaml`) с attachment bundle.
   Ответ короткий: ссылки на финальные статьи, review reports и Confluence bundles, число added/updated terms,
   unresolved gaps и publication gate. Не выдавай финальный текст за опубликованную KB
   и не выводи внутренние engine logs.

Domain Decomposer готовит общий domain map и отдельные scoped пакеты **всех** Scenario,
используя существующие schemas и Entity IDs. Workflow work_items — только указатели на эти
артефакты; не второй domain model. Если домен не атомарен, не документируй только первый
Scenario: профильный Domain skill должен завершить decomposition/подготовить определения.
Scope approval охватывает все work_items. Glossary increments применяются последовательно
к run-local curated snapshots; global merge выполняется профильным Curator только при
отдельном запросе обновления выбранного global glossary.

Команды, result formats, восстановление после ошибок, Language Reviewer и финальный Renderer
описаны в [workflow](references/workflow.md). Gate failure сохраняет конкретные
stage/gate/code и owner skill в diagnostics, блокирует publication/presentation и
run COMPLETED. Не исправляй текст, refs, classification или source facts внутри
controller; return-to-producer и явный retry используют прежнюю модель attempts.
Финальный gate проверяет invariants по Markdown/manifest/structured inputs,
без субъективного LLM score. Проверки и AC/E2E границы — в
[acceptance](references/acceptance.md). Существующие предметные skills не переписывать.
