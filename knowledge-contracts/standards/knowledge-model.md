# Shared knowledge model для пяти стадий

Нормативный формат остаётся JSON Schema Draft 2020-12, schema_version=1.0.
Новые выходы пяти skills обязательно задают model_profile=scoped-knowledge-v1
на knowledge package и всех inputs/outputs. Отсутствие профиля означает legacy input,
а не полный новый output. Не смешивай профили: migration выполняется явно с source review.

Используются существующие schemas: common, knowledge-package, domain-tree, scenario-definition,
source-map, technical-flow, business-rules, scenario. Новые общие definitions в common:
knowledge_status, knowledge_value, preferred_name, terminology_candidate, technical_representation.
Optional [runtime extension](runtime-evidence-policy.md) добавляет definitions RuntimeTrace,
RuntimeConfirmation и runtime context к тому же Evidence. knowledge.runtime_traces и
runtime_confirmations сохраняются отдельно от static entities/claims/relations; их IDs
неизменяемы между checkpoints. Source-map.runtime_lookup готовит MCP capability и keys;
technical-flow/scenario.runtime_confirmation_refs и rules.runtime_examples — только refs.
runtime_reviews в Validation не заменяет KnowledgeStatus и не меняет glossary terminology.

knowledge_value = {value, status, claim_ids, evidence_ids}. UNKNOWN value=null.
Содержательное значение связано с subject/predicate/value Claim, status совпадает с knowledge_status
этих claims. CONFLICT связывает оба conflicting claims, не выбирая одно значение.
Техническая representation = {implementation_refs, technical_step_refs, source_ids}; все refs — IDs,
process/API symbols находятся в aliases соответствующих CodeComponent/ApiOperation.
Не добавляй второй словарь свободных имён процессов вместо registry.

| Стадия | Структурированный выход |
|---|---|
| Domain Decomposer | nodes + общая терминология + scope_ref/evidence; существующие goal/trigger/states/actors и atomicity claims |
| Source Discovery | accepted sources, relevance_path, typed snapshots, terminology_candidates; без выбора preferred_name |
| Technical Flow Analyzer | nodes — canonical технические узлы (technical-step:, SystemBehaviour), execution fields, component_id/source_ids/claim_ids; relations отдельно; nodes.business_meaning (knowledge_value), technical_implementation, integrations; без steps projection и требования Actor |
| Business Rule Extractor | business_statement, technical_condition, business_rationale (knowledge_value), technical_implementation; condition/effects/parameters projection |
| Scenario Reconstructor | единственный process narrative: main_flow/alternative_flows/exception_flows (IDs в flows), unique steps; business_action, business_result, knowledge_status, state_transition {from,to}, technical_implementation; rules/integrations/flows/transitions и technical_step_refs |

BusinessRule.rule_statement — прежняя техническая или документированная формулировка.
Она не заполняет business_statement автоматически. technical_condition.value проецирует condition.
business_rationale — structured value в новом профиле, строка в legacy; валидатор использует
внутреннюю совместимую проекцию, не меняя input. Rationale никогда не копируется из condition.
Scenario action/system_behavior сохраняют техническое действие, business_action/result — отдельно
подтверждённое описание для аналитика. Неизвестность бизнеса не скрывается в техническом тексте.
state_transition ссылается на те же State IDs, что state_before/after; State registry хранит
preferred_name и aliases (например ReadyForSign). Не копируй State под новым ID ради языка.

Entity имеет стабильный id/type/identity_key и общую терминологию.
identity_key — идентичность объекта в scope (repo + locator + роль/контекст), не display name,
перевод или alias. Одинаковый type/identity_key под разными IDs запрещён.
Scope, Evidence, sources, claims, relations, gaps/conflicts передаются накопительно.
Новые значения claims сохраняются под новыми IDs; исходное утверждение не переписывается.

Для нового запуска сохраняй в runs/<domain>/:
01-domain-map.yaml, 02-source-map.json, 03-technical-flow.json, 04-business-rules.json, 05-scenario.json.
JSON сохраняется на стадиях, уже использующих JSON; YAML/JSON допускаются по одним schemas.
Существующую папку и имена артефактов сохраняй при продолжении legacy run.
knowledge.yaml и scenario-definition.yaml — sidecars; checkpoints/01..05/knowledge.yaml
содержат KB каждой стадии и projections upstream с согласованной package_ref.revision.
Это история существующей KB, не второе хранилище сущностей. Не извлекай entities из prose.

pipeline-run.json по pipeline-run.schema.json перечисляет пять стадий: kind/artifact/knowledge
и input paths domain_tree/scenario_definition/source_map/technical_flow/business_rules относительно
manifest. Можно ссылаться на checkpoint projections с прежними IDs и новой package_ref.
Single-stage проверка: validate.py ... --previous-knowledge <previous>/knowledge.yaml.
Полный проход: python tools/knowledge/pipeline.py runs/<domain>/pipeline-run.json.
Он проверяет schemas, scope, reference graph, upstream projections и сохранность increments.
Contract tests: python -m unittest discover -s tools/knowledge/tests.
Golden: tools/knowledge/tests/fixtures/registration-address/pipeline-run.json.
Механическая проверка не доказывает смысл source evidence и полноту исследования.

Glossary Curator использует эту модель после 06 Validation. 07-glossary-increment.yaml — patch глобального
glossary.yaml, не новый knowledge package. Term.entity_ref, related_entities и domains используют прежние
Entity IDs; preferred_name/definition/status/candidates — shared definitions common.schema.json.
Evidence/Claim registry сохраняется в immutable provenance по существующим schemas и проверяется
validate.py knowledge-package и общими source-check invariants 06. Словарь не изменяет upstream facts.
Unmapped candidate остаётся unresolved с term_id=null и shared Gap; подтверждённый term имеет mapping claims.
INFERRED preferred value в словаре — гипотеза, без повышения canonical Entity preferred_name.
