# Терминология

Язык кода не определяет язык документации. Если существует подтверждённый термин
предметной области, он используется как preferred_name. Технические идентификаторы
сохраняются как aliases. Если preferred_name не доказан, он остаётся UNKNOWN.

`preferred_name` использует shared `preferred_name`: value/status/claim_ids/evidence_ids.
UNKNOWN → value=null. Подтверждённое имя требует отдельного source-stated claim
с predicate=preferred_name; имя класса, перевод агента и search hit этого не доказывают.
Термин с INFERRED смыслом сохраняй кандидатом, не каноническим именем.
CONFLICT содержит refs обоих утверждений; value может быть null, автоматического выбора нет.

`technical_aliases` — точные имена кода/API/process/config, включая регистр и namespace.
`search_aliases` — поисковые формулировки, не claims о бизнес-смысле.
`terminology_candidates` — value/entity_ref/source_type/source_ref/evidence_ids.
source_ref указывает SourceSnapshot, evidence фиксирует реальное употребление варианта,
но не делает его каноническим. Source Discovery только добавляет варианты и aliases.

Entity registry knowledge.yaml — единственное место идентичности и терминологии.
Domain nodes и ScenarioDefinition содержат согласованную проекцию этих полей.
Другие стадии ссылаются на entity ID, в том числе Integration/State/BusinessRule.
Обнаруженное SAS остаётся technical_alias; «скоринг» допустим только при отдельном
подтверждении. То же правило действует для NSIS/«НСИС» и OSS/«ОСС».
Aliases и candidates передаются накопительно; переименование не меняет ID.
Legacy name/label — навигация: при неизвестном preferred_name name входит в proposed_fields.

Глобальный glossary — проекция проверенной терминологии из Entity/Claim/Evidence, а не второй registry.
TERM-* идентифицирует запись словаря; entity_ref/related_entities сохраняют исходные Entity IDs.
Для glossary technical_alias требуется matching Claim с predicate=technical_aliases и exact identifier,
проверенный по CODE/CONFIG/GIT в 06. Raw alias без mapping evidence остаётся unresolved candidate.
Search aliases сохраняют origin; частота упоминаний и самостоятельный перевод не подтверждают preferred term.

В glossary разрешена видимая гипотеза preferred_name со статусом INFERRED из 06;
она остаётся неутверждённой и не записывается в canonical Entity.preferred_name.
Все значения используют общие knowledge_value/preferred_name и KnowledgeStatus contracts.
Конфликт сохраняет оба Claim/Evidence refs, общий Conflict и ANALYST_REVIEW; unresolved использует общий Gap.
