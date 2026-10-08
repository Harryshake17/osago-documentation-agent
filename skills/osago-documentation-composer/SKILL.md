---
name: osago-documentation-composer
description: Собрать draft KB-статьи ОСАГО из validated Domain, Scenario, Business Rules, Technical Model, Validation и glossary с provenance, статусами и бизнес/техническим разделением; без исследования кода и новых claims.
---

# Documentation Composer

## Normalized runtime inputs

Прочитай [runtime evidence policy](../../knowledge-contracts/standards/runtime-evidence-policy.md).
Upstream optional capability: OpenSearch MCP для production runtime verification при
unresolved material ambiguity after static analysis. **Composer не вызывает MCP**.
Он получает shared RuntimeTrace, OPENSEARCH Evidence и validation.runtime_reviews.
По scenario.runtime_confirmation_refs отобрази validated current observed flow отдельно
от static model, с environment/version/period, independent sample size и provenance.
VARIABLE/conflict/insufficient/unverified сохраняются с gaps, без выбора одного пути
и без универсальных утверждений. Raw log lines, query, identifiers, excerpts и quotes
OPENSEARCH не выводить в пользовательскую статью. Business terms бери из прежнего
glossary Curator; log marker не превращать в новый термин или business rationale.

Прочитай [общий контракт](../../knowledge-contracts/contract.md),
[шаблон](../../knowledge-contracts/standards/documentation-template.md),
[базовый стиль](../../knowledge-contracts/standards/writing-style.md),
[терминологию](../../knowledge-contracts/standards/terminology.md),
[evidence policy](../../knowledge-contracts/standards/evidence-policy.md) и
[knowledge model](../../knowledge-contracts/standards/knowledge-model.md).
Обязательные входы: 01-domain-map, 03-technical-flow, 04-business-rules, 05-scenario,
06-validation (validation-report + gaps), glossary.yaml после osago-glossary-curator,
а также существующий knowledge.yaml с Entity/Claim/Evidence registry.
Используй фактические пути run: numbered names не требуют переименования legacy inputs.
02-source-map и ScenarioDefinition — дополнительные structured sidecars.
Отсутствующий обязательный input — validation failure; не компенсируй его анализом кода.

Не ищи новые факты, не открывай код/Confluence для самостоятельного исследования, не объясняй отсутствующий бизнес-смысл и не дополняй knowledge. Если входы повреждены, ревизии расходятся или review не завершён — верни диагностику предыдущему skill. Completed review допускает UNKNOWN/INFERRED/CONFLICT; blocked publication gate допускает review-документ, но не публикацию.

Из корня repo запускай детерминированный renderer:
```text
python tools/knowledge/compose.py --knowledge <folder>/knowledge.yaml --domain-tree <folder>/01-domain-map.yaml --technical-flow <folder>/03-technical-flow.json --business-rules <folder>/04-business-rules.json --scenario <folder>/05-scenario.json --report <folder>/validation-report.json --gaps <folder>/gaps.json --glossary <global-or-run>/glossary.yaml --output-dir <folder>/documentation
```

При наличии sidecars добавь --source-map и --scenario-definition. Их отсутствие
не отменяет hashes первоначального review: каждый предоставленный input обязан
совпадать с manifest отчёта, а исходные refs и Evidence сохраняются. Не создавай
фиктивный source-map. Glossary проверяется общими schemas и функциями Curator;
stable Entity ID/identity не меняется. Допустима отдельно validated новая revision
glossary без изменения Scenario/Technical Model. Имена из code/config и search_aliases
не создают preferred term. CONFIRMED preferred_name используется в бизнес-тексте;
PARTIALLY_CONFIRMED — с оговоркой. INFERRED/UNKNOWN/CONFLICT не становятся canonical
названием: technical identifier показывается с явной пометкой. Не выбирай локально
одно значение при конфликте и не редактируй glossary.

Выходы: 08-draft-document.md, существующий documentation-manifest.json и его
YAML-проекция 08-draft-document.meta.yaml. Manifest сохраняет прежние hashes,
claim inventory/publication gate и добавляет glossary id/revision/hash, source
revisions, template/style hashes, line spans, derived_from и source_fields блоков.
Это provenance, не новые Evidence/Terminology/KnowledgeStatus models.
Существующие файлы сохраняются без явного --overwrite. Renderer не обращается
к исходному коду/источникам и не вызывает LLM.

Сборка section-centric: Domain, Scenario, Rules, Technical Model и Validation являются
lookup sources для смысловых разделов статьи, а не самостоятельными приложениями.
Источник единственного основного процесса — только Scenario.main_flow и step_refs выбранного
Flow, в указанном порядке. Не сортируй main steps по order registry, не добавляй Happy path,
UC Main flow или второй narrative из Technical Flow. alternative_flows/exception_flows задают
значимые варианты: условие отклонения, действие и исход. business_action/business_result не
заполняются action/system_behavior. Сначала цель/scope и процесс, затем правила, состояния,
альтернативы, интеграции, обзор реализации, полезные источники и material open questions.

Следуй shared template и heading contract downstream Language Reviewer. Не создавай пустые
таблицы, перечни unknown schema fields или field/value dumps. Scenario actors — участники
процесса; не ищи actor для метода. Одно правило описывается один раз в смысловом блоке и
связывается с человеческим номером шага. Только Rules, явно используемые выбранными Scenario
steps, входят в эти блоки. Точные условия, outcomes и thresholds сохраняются. Неизвестные
business statement/rationale не выводятся из technical condition; не печатай rationale-заглушку.

Technical Model поясняет эти steps: один основной mapped компонент на шаг и явные mapped
API/controller/integration boundaries. Выбор по typed metadata — навигационный обзор, не
доказательство execution order. Покажи точные symbols/entry points и нужные технические
условия, но не каждый helper, method, extension, pipeline stage, call, config key или node.
Порядок и полный mapping сохраняются в structured provenance. Technical aliases находятся
только в разделе реализации, кроме значимого внешнего state/status/endpoint как inline code.
UNKNOWN preferred term не переводится: используй нейтральное описание с uncertainty;
точный выбранный технический alias сохраняй в technical section. Не используй labels вместо
confirmed preferred_name. Заголовок — preferred_name, confirmed business goal или нейтральное
«Описание сценария ОСАГО»; описательный заголовок не становится новым preferred term.

06 publication relevance обязательна к review перед сборкой: открытый UNASSESSED или
reviewed=false возвращается Skill 6. Читай точный gaps.publication_subset; в статье только
его открытые Gap/Finding questions. Не выводи все nonconfirmed claims, comparisons, conflicts
или glossary unresolved автоматически. Material conflicts сохраняют существенные версии
без выбора одной. INTERNAL_RESEARCH остаётся в artifacts/manifest. Severity/confidence/status
не определяют публикационную релевантность. Blocked publication gate сохраняется в manifest.

Каждое включённое утверждение сохраняет effective UNKNOWN/INFERRED/CONFLICT/
PARTIALLY_CONFIRMED, ограничения и modality. Runtime observation отличается от static flow:
сохрани version/environment/period и independent sample size; variability и ограничения
показываются без гарантий. Raw logs, query, case IDs и timelines остаются provenance.
Отбор текста не повышает status/confidence и не создаёт causal claims.

Narrative не содержит Entity/Claim/Evidence/stable IDs, source paths, pageId, source_fields,
derived_from или raw evidence. Человеческие номера шагов/правил — только navigation, не IDs.
Не добавляй ссылку/имя .mmd вместо диаграммы: Composer не получает presentation assets;
диаграммы и attachments готовит отдельный Confluence Renderer по approved metadata.
Источники в статье — выбранные полезные ссылки с понятной подписью; без полного inventory.

Manifest сохраняет полный claim inventory, unresolved inventory, hashes/gate, glossary
revision, реальную block provenance и line spans. document.provenance содержит неизменные
structured inputs, validation-report, gaps и glossary по прежним shared schemas: включая
невключённые internal gaps, evidence/snapshots, statuses, aliases, source fields и mappings.
Не создавай фиктивные spans для невключённого материала; не меняй upstream artifacts.

Composer не исследует код/источники и не разрешает неизвестное. Фактическое изменение требует
нового upstream review, а языковые правки формы выполняет stage 09. Документ для human review
не считается опубликованной KB.

Передай draft и metadata следующему [osago-language-reviewer](../osago-language-reviewer/SKILL.md), последнему stage 09. Его выход 09-final-document.md является итоговым документом; 08-draft-document.md остается draft. Composer не выполняет
финальную стилистическую редактуру. Проверки: python -m unittest discover -s
tools/knowledge/tests. Зависимости: tools/knowledge/requirements.txt.
