---
name: osago-source-discovery
description: Построить source-map.json для сценария ОСАГО API по ScenarioDefinition и domain tree. Найти релевантный код, процессы, конфигурацию, тесты и Confluence; не создавать документацию поведения.
---

# Source Discovery

Перед работой прочитай [shared knowledge model](../../knowledge-contracts/standards/knowledge-model.md),
[терминологию](../../knowledge-contracts/standards/terminology.md),
[evidence policy](../../knowledge-contracts/standards/evidence-policy.md) и
[границы/атомарность](../../knowledge-contracts/standards/domain-decomposition-rules.md).
Сущности получай из JSON/YAML входов, не из prose предыдущего skill. Перед передачей результата
сохрани checkpoint KB и согласованные upstream projections; проверь increment через
validate.py с --previous-knowledge <previous>/knowledge.yaml со второй стадии. При полном run запиши pipeline-run.json
и проверь все пять стадий командой tools/knowledge/pipeline.py из shared model.

Новые outputs и inputs используют model_profile=scoped-knowledge-v1. Поиск учитывает registry
technical_aliases/search_aliases и уже найденные terminology_candidates. Добавляй обнаруженные
варианты в source-map.terminology_candidates и тот же entity registry: value/entity_ref/source_type/
source_ref/evidence_ids. Не выбирай и не меняй preferred_name, даже если найден более читаемый вариант.
Сохраняй snapshot, тип источника и доказанный relevance_path; текстовое совпадение не расширяет scope.
Для нового run выход — 02-source-map.json рядом с 01-domain-map.yaml и sidecars.

Этот skill строит карту источников. Он не описывает бизнес-поведение, не извлекает бизнес-правила и не пишет документацию приложения.

Прочитай [общие контракты](../../knowledge-contracts/contract.md), [ScenarioDefinition schema](../../knowledge-contracts/schemas/scenario-definition.schema.json), [source-map schema](../../knowledge-contracts/schemas/source-map.schema.json) и [процедуру поиска](references/workflow.md). Общая версия 1.0; схемы старого osago-kb не используются.

Вход: ScenarioDefinition, domain-tree.yaml и соответствующая ревизия knowledge.yaml. Если файлов ещё нет, нормализуй имеющиеся входные сведения в эти контракты; неизвестную бизнес-цель не додумывай. При отсутствии подтверждённого anchor сохрани clarification Gap и карту partial; не выдавай словесные совпадения за релевантные sources.

Инструменты: repository file search, symbol/reference search, configuration search, test search, Confluence search/read. Используй доступные CLI/MCP read-only инструменты; конкретное имя коннектора не является частью модели. Похожие имена и embedding similarity дают candidates, а не accepted sources.

Обязательно исследуй все 10 категорий: api_endpoints, controllers, commands_handlers, process_definitions, subprocesses, business_rule_implementations, configuration_keys, integrations, automated_tests, confluence_pages. Для каждой укажи coverage и search_runs либо unavailable diagnostic. not_found относится только к обследованным границам, не доказывает отсутствие в системе.

Для каждого accepted source объясни связь со сценарием и сохрани relevance_path от подтверждённого anchor. Каждое ребро имеет evidence и discovery claim. Разреши регистрации/dispatch/DI/process identifiers; неизвестное разрешение остаётся candidate + Gap. Не включай весь файл/общую библиотеку из-за одного связанного символа.

Результат: source-map.json с собственным стабильным id и обновлённая ревизия knowledge.yaml, содержащая только служебные claims о найденных источниках и их связи. Не меняй бизнес-claims. PROCESS — artifact_kind=process_definition, evidence type CODE/CONFIG по реальному формату, а не новый тип evidence. Старой карте без id явно добавь идентификатор перед передачей downstream; не вычисляй её идентичность только из имени файла.

Из корня репозитория:
```text
python tools/knowledge/validate.py source-map <folder>/02-source-map.json --knowledge <folder>/knowledge.yaml --domain-tree <folder>/01-domain-map.yaml --scenario-definition <folder>/scenario-definition.yaml
```
Зависимости: tools/knowledge/requirements.txt. После механической проверки вручную разреши relevance paths и проверь релевантность. Передай карту, candidates, coverage, gaps и необследованный frontier. Не называй partial map полной.

## Optional OpenSearch MCP capability

Прочитай [runtime evidence policy](../../knowledge-contracts/standards/runtime-evidence-policy.md).
Purpose: production runtime verification. Invocation condition downstream: unresolved
material ambiguity after static analysis. Здесь только подготовь возможность lookup:
source-map.runtime_lookup={capability,lookup_keys,representative_case_refs,diagnostic}.
Определи capability по подключённым IDE tools без обязательного search. lookup_keys —
реальные имена полей accountNumber/correlationId/processId/requestId проекта, подтверждённые
источниками; передай evidence этих полей в обычной карте. Известные representative cases
передавай обезличенными refs, без исходных account numbers и токенов. Не анализируй timeline
и не добавляй runtime claims. unavailable/not_checked не делает статическую карту failure.
Только значимая ambiguity на следующем этапе запускает MCP по shared policy; runtime
не является одиннадцатой обязательной static search category.
