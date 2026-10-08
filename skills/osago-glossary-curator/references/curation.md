# Курация терминов

## Сначала входы и история

Входная knowledge.yaml — существующая scoped-knowledge-v1 registry, не новый glossary namespace бизнес-сущностей.
05-scenario/06-validation обязательны. Report содержит отдельную от producer knowledge_status оценку;
проверяй hashes KB, Scenario и всех переданных дополнительных артефактов, claim_inventory/claim_hash/source_checks.
Draft/partial report допустим для UNKNOWN/CONFLICT результата; publication_gate не делает glossary publication.
Нет входа/валидного binding → незавершённая курация, не выдуманная новая KB.

glossary.yaml глобален. provenance хранит неизменные snapshots прежних knowledge packages и validation reports
по их существующим schemas: так прежние verified terms из другого domain не теряют свои Evidence/Claim IDs.
Это сохранённые входы, не новая Evidence model. Не меняй их тексты под старым provenance ID.
Участие в текущем scope не требуется для сохранения несвязанных прежних terms.

## Кандидат и identity

Начни с entity.terminology_candidates, source-map.terminology_candidates и typed entity refs Scenario/Rules.
Регистр aliases сохраняется точно. Preferred/technical/search совпадения — discovery hints; сравни Entity ID,
identity_key и доказанные entity relations. Разные сущности с похожими именами не объединяются.
Технический alias, заново найденный для той же Entity, обновляет прежний TERM-*.
Для нового term ID определяется identity glossary+entity+identity_key, не выбранным названием.
Таким образом изменение предпочтительного слова не превращает TERM-SCORING в TERM-SAS.

technical_aliases требует отдельный matching Claim: subject_id=Entity ID, predicate=technical_aliases,
value=точный identifier, primary CODE/CONFIG/GIT и проверенный source_check в 06.
Наличие имени в прежнем raw technical_aliases без field evidence не означает, что соответствие проверено.
При нехватке evidence сохрани candidate/Gap и направь вопрос на scoped уточнение; не расширяй code search.
Unresolved с term_id=null обозначает ещё не установленное mapping; technical_aliases там — исходные
кандидаты Entity registry, а не подтверждённые aliases нового term. Такие кандидаты сохраняются между runs.
Relation to entity связывается через claims о той же Entity; дополнительные entity associations
не создаются по похожему слову. Не переносить алиас чужого объекта на существующий term.

Отбирай концепты для понимания документации или поиска: Domain/Scenario/Integration/Capability/Actor/State/Rule.
Неиндексируемые technical classes не становятся terms автоматически. Для целевого technical candidate
или selection сохрани reason и существующий Entity ID; selection — редакционная классификация, не бизнес-факт.
Term types включают DOMAIN, SCENARIO, SYSTEM, INTEGRATION, CAPABILITY, BUSINESS_ENTITY, STATE,
BUSINESS_PROCESS, BUSINESS_RULE_TERM, ABBREVIATION, TECHNICAL_CONCEPT.

## Preferred name и definition

Для полей используй common preferred_name/knowledge_value: value/status/claim_ids/evidence_ids.
subject существующей Entity, predicate=preferred_name либо definition. Строка из business_action не становится
preferred_name другого объекта без явного mapping claim. Evidence цепочка раскрывается до primary snapshots.
Producer UNKNOWN/INFERRED/CONFLICT нельзя повысить через glossary, даже при удачном написании.
Непроверенный report оставляет UNKNOWN. Confirmed/partial новые поля требуют source-stated business term
из CONFLUENCE или TEST с документированным предметным объяснением; CODE/CONFIG/GIT alias alone недостаточен.

Сначала сохраняй принятые confirmed поля glossary. Если новая проверенная формулировка отличается, сохрани
старое поле, обе поддержки и CONFLICT на term; не выбери новое слово по количеству упоминаний/приоритету.
Definitions не пересказывают source/class naming и не объясняют неизвестные мотивы правила.
Отсутствующая definition остаётся UNKNOWN отдельно от подтверждённого preferred term.
Term.status учитывает неполноту полей и текущий validation статус; confirmed историческое имя может
сохраняться, но relevant UNKNOWN/CONFLICT в новой проверке остаётся виден на term.

Различение standards: canonical Entity.preferred_name не принимает inferred бизнес-смысл.
Glossary может показать preferred_name.value со статусом INFERRED как неутверждённую гипотезу из 06.
Не записывай этот вариант назад как canonical Entity name. Status/Claim/Evidence contracts при этом те же.

## Search и конфликты

Search aliases — небольшое число реально найденных вариантов. CLI сохраняет preferred spelling,
technical spelling, уже зарегистрированные search aliases/candidates и casefold варианты;
каждый вариант имеет search_alias_origins с origin/entity_ref. Транслитерация и новые синонимы
не генерируются автоматически. Исторический confirmed term сохраняет прежние поисковые варианты.

Одна Entity с несколькими preferred terms/definitions, один alias или preferred name с разными entities,
новое и прежнее имя → Conflict view: общий Conflict record + variants/entity_refs/term_ids/Evidence refs,
knowledge_status=CONFLICT и required_action=ANALYST_REVIEW. General Conflict semantic не переопределяется.
Unresolved использует shared Gap с affected Entity ID. Не отправляй сообщения аналитикам автоматически.

## Increment и merge

Curate работает по структурированным inputs; исходные KB/Scenario/Rules/report не меняются.
updated.changes — patch только изменённых полей существующего term; added содержит новый term.
unchanged перечисляет все остальные baseline terms. Проверяй отсутствие overlap и loss aliases/IDs.
Increment привязан к glossary_ref/base_hash/result_hash и hashes входов. Merge детерминированно
применяет patch, дополняет provenance, проверяет весь glossary и итоговый hash. Stale base отклоняется.
Повторное применение к result — no-op; повторная curate с той же KB/report не повышает revision.
Параллельные глобальные updates требуют повторного curate на свежем baseline; last-write-wins запрещён.

## Ручная сверка

Source checks/hashes не доказывают смысл. Сверь соответствие SAS↔скоринг, предметность definition,
полезность technical aliases и сравнимость контекста конфликтов по фрагментам, а не тестовому примеру.
Fixtures в tools/knowledge/tests/fixtures/glossary синтетические. Они проверяют contracts/invariants,
а не корректность фактов ОСАГО. Existing Documentation Composer на этом этапе не меняется.
