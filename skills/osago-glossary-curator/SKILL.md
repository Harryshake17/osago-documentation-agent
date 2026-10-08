---
name: osago-glossary-curator
description: Поддерживать evidence-backed глоссарий ОСАГО по Scenario, Validation и terminology candidates. Сопоставлять preferred terms с technical/search aliases, сохранять stable IDs и формировать glossary increment; без реконструкции процессов и изменения бизнес-фактов.
---

# Glossary Curator

Прочитай [общие contracts](../../knowledge-contracts/contract.md), [терминологию](../../knowledge-contracts/standards/terminology.md),
[evidence policy](../../knowledge-contracts/standards/evidence-policy.md), [knowledge model](../../knowledge-contracts/standards/knowledge-model.md)
и [процедуру курации](references/curation.md). Выходы используют shared schemas:
[glossary](../../knowledge-contracts/schemas/glossary.schema.json),
[term](../../knowledge-contracts/schemas/glossary-term.schema.json),
[increment](../../knowledge-contracts/schemas/glossary-increment.schema.json).

Вход: текущий глобальный glossary.yaml, 05-scenario и 06-validation (существующий validation-report.json),
связанная knowledge.yaml с Entity/Claim/Evidence registry. Дополнительно — 01-domain-map, 02-source-map,
03-technical-flow, 04-business-rules. Используй фактические пути run: numbered names не требуют
переименования старых артефактов. KB, Scenario и report относятся к одной revision; report hashes должны совпадать.
Для domain_id используй существующий Domain Entity ID. Если глобальный glossary отсутствует, создай пустой
через init; не превращай произвольный список названий без provenance в confirmed glossary.

Собери кандидатов из структурированных terminology_candidates и entity registry, включая integrations,
states, actors, capabilities и business names. Не извлекай их из prose и не восстанавливай knowledge model заново.
Проверяй существующие preferred_name → technical_aliases → search_aliases → stable Entity ID.
Текстовый match помогает найти запись, но не разрешает объединять разные Entity IDs без доказанного соответствия.
TERM ID — identity записи словаря; Entity ID остаётся прежним. Сохраняй aliases и уже принятые terms накопительно.

Приоритет имени: принятый confirmed glossary → source-stated термин из Confluence/утверждённой KB →
validated business terminology → UNKNOWN. Code/config проверяют technical aliases, а не каноническое имя.
Определение короткое и предметное; имя класса, самостоятельно придуманный перевод и rationale не добавляй.
INFERRED/PARTIALLY_CONFIRMED/UNKNOWN/CONFLICT из 06 не скрывай. Inferred preferred value в glossary —
видимая гипотеза; она не обновляет canonical preferred_name entity registry.

Используй доступные read-only repository/config/Confluence/KB инструменты только для терминологического
уточнения. Сначала открой указанные source-map locators. Отсутствующий connector → unresolved/Gap.
Новый терминологический source/claim фиксируется существующими Evidence/Claim contracts и проверяется
Validator в новой согласованной revision; старый report не подтверждает новую citation.
Не изменяй Scenario/Business Rules, identifiers, фактическое поведение и не исследуй весь домен повторно.

CodeComponent/ApiOperation/ConfigRule не включаются автоматически. Явно отмеченный terminology candidate
или selection с объяснением значимости позволяет включить TECHNICAL_CONCEPT. Для иных специальных типов
SYSTEM/BUSINESS_PROCESS/ABBREVIATION можно использовать
[selection schema](../../knowledge-contracts/schemas/glossary-selection.schema.json): entity_ref/type/reason,
без создания новой бизнес-сущности. Не добавляй методы только ради числа aliases.

Из корня репозитория:
```text
python tools/knowledge/glossary.py init --output <global>/glossary.yaml
python tools/knowledge/glossary.py curate --glossary <global>/glossary.yaml --knowledge <run>/knowledge.yaml --scenario <run>/05-scenario.json --validation <run>/validation-report.json --domain-id <Domain-ID> --output-dir <run>
python tools/knowledge/glossary.py check --glossary <run>/glossary.yaml --increment <run>/07-glossary-increment.yaml
python tools/knowledge/glossary.py merge --glossary <global>/glossary.yaml --increment <run>/07-glossary-increment.yaml --output <global>/glossary.yaml --overwrite
```
init применяется только при отсутствии glossary; --overwrite означает авторизованное обновление выбранного
артефакта. Перед глобальным merge проверь результат и unresolved/conflicts. Conflict — аналитическая задача,
а не необходимость отдельного permission prompt. CLI не публикует результат.

Выход: 07-glossary-increment.yaml и обновлённый glossary.yaml. Increment сохраняет added/updated/unchanged,
общие Conflict/Gap records, statistics, base/result hashes и immutable provenance snapshots из существующей KB.
Merge проверяет ревизию и сохранность; повторный apply идемпотентен. Search aliases сохраняют происхождение,
без искусственных синонимов. Передай список новых/изменённых terms, conflicts/unresolved и ограничения.
Проверки: python -m unittest discover -s tools/knowledge/tests. Зависимости: tools/knowledge/requirements.txt.
