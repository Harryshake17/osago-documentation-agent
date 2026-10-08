---
name: osago-evidence-gap-validator
description: Проверить каждый claim ОСАГО API в source-map, scenario, business-rules и technical-flow по code/config/tests/Confluence, выявить gaps/conflicts и создать validation-report.json и gaps.json.
---

# Evidence / Gap / Conflict Validator

## Runtime assessment

Прочитай [runtime evidence policy](../../knowledge-contracts/standards/runtime-evidence-policy.md).
Optional capability: **OpenSearch MCP**, purpose: production runtime verification;
invocation condition: unresolved material ambiguity after static analysis. Проверяй уже
нормализованные RuntimeTrace/OPENSEARCH Evidence; reopen через bounded MCP только при
необходимости source verification. Нет MCP — проверяй captured sanitized snapshots,
если они доступны, иначе RUNTIME_UNVERIFIED, не failure статического pipeline.
Проверь independent sample count (>=3, critical aim 5+), complete SUCCESS отдельно от ERROR,
scenario scope, environment/version/period, event correlation/order и technical refs.
Сопоставь static possible paths со всеми traces, сохраняя их отдельные статусы. Заполни
validation.runtime_reviews с result/sample_size/trace_refs/reviewed/reason: draft OBSERVED
не даёт semantic approval. Проверяй каждый excerpt/hash обычными source_checks.
Выявляй RUNTIME_UNVERIFIED, STATIC_RUNTIME_CONFLICT, RUNTIME_VARIABILITY,
INSUFFICIENT_RUNTIME_SAMPLE. Один кейс не подтверждает current universal flow; logs не
подтверждают business rule/rationale/невозможность другой ветки. Проверь отсутствие
универсальных формулировок в statement; гарантированно механически это не проверяется.

Прочитай [общий контракт](../../knowledge-contracts/contract.md), [процедуру проверки](references/review.md), [report schema](../../knowledge-contracts/schemas/validation-report.schema.json) и [gaps schema](../../knowledge-contracts/schemas/validation-gaps.schema.json).

Входы: source-map, scenario, business-rules, technical-flow и связанная knowledge.yaml. Для полной проверки ссылок используй domain-tree и ScenarioDefinition, на которые ссылаются входы. Scope задаёт пакет; если пакет шире запроса, подготовь согласованный срез с transitive evidence до проверки, не аудируй весь проект молча. Проверяй каждый claim выбранного пакета, включая основания inference; старый validation_status=supported не заменяет новую проверку.

Инструменты: read-only code, tests, config и Confluence. Открой первичные фрагменты соответствующих версий, проверь hash/location и семантическую поддержку. Отдельно сравни реализацию, test expectations и документированные требования; не смешивай модальности/окружения. Недоступность источника фиксируется, не заменяется reasoning.

Начни с консервативного draft, из корня репозитория:
```text
python tools/knowledge/audit.py draft --knowledge <folder>/knowledge.yaml --source-map <folder>/source-map.json --scenario <folder>/scenario.json --business-rules <folder>/business-rules.json --technical-flow <folder>/technical-flow.json --domain-tree <folder>/domain-tree.yaml --scenario-definition <folder>/scenario-definition.yaml --output-dir <folder>
```
Tool не подтверждает факты автоматически: он создаёт inventory, структурные findings и UNKNOWN/непроверенные recorded CONFLICT. Повреждённые входы диагностируются; не исправляй их факты молча. Сохрани inputs неизменными во время review. При новых evidence/исправленных источниках подготовь новую согласованную revision и перегенерируй draft, не переносить подтверждения на изменённый claim.

Для каждого claim заполни source_checks, reviewed, reason, supported/unsupported_parts и одну классификацию:
- CONFIRMED — полный прямой допустимый support, проверены версия, контекст и смысл.
- PARTIALLY_CONFIRMED — поддерживается только часть; перечисли подтверждённое/неподтверждённое, предложи split.
- INFERRED — обоснованный проверенный вывод из подтверждённых оснований; всегда остаётся inference.
- CONFLICT — подтверждённое противоречие в сопоставимом контексте, обе версии/источника сохранены.
- UNKNOWN — подтверждения нет, источник недоступен/нерелевантен или verification не выполнена.

Найди утверждения без evidence; Code↔Confluence и Test↔Code conflicts; UNKNOWN rationale; unknown state transitions; недокументированную config behaviour; технические ветки вне scenario; business scenario без найденной реализации. Для каждого finding укажи scope/location, evidence или явную нехватку, required_action и Gap. Отсутствие ссылки в артефакте не доказывает отсутствие реализации/документа во всём проекте.

Заполни comparisons после source/context сверки. Слово «всегда» требует проверки альтернатив, config flags и ошибок; chronology не доказывает order для всех путей. Не разрешай конфликт выбором Confluence/Code по умолчанию. Пример Signed/PolicyIssued/PaymentBeforeRsaContractUpload — иллюстрация, не факт проекта.

## Publication relevance перед Composer

Для каждого Gap/Finding заполни shared publication_relevance отдельно от KnowledgeStatus,
blocking/severity и confidence. Classification: PUBLICATION_RELEVANT, INTERNAL_RESEARCH или
UNASSESSED; это editorial impact, не новая модель достоверности. impacts перечисляет aspect и
existing target_refs; reason объясняет зависимость, reviewed фиксирует выполненную relevance review.

Publication-relevant только неопределённость, способная изменить основной/значимый alternative или
exception flow, существенное правило, внешний API/integration contract, значимый state/status transition,
бизнес-результат либо актуальность версии/окружения. Связывай оценку с canonical 05 и уже существующими
claims/refs; не создавай факты и не разрешай UNKNOWN/INFERRED/CONFLICT ради классификации.

Exact internal method, actor внутреннего вызова, helpers/extensions, generated graph и второстепенные
implementation details могут быть INTERNAL_RESEARCH, если процесс независимо подтверждён и reader impact
отсутствует. Не найденный дополнительный test/file тоже не становится material сам по себе.
UNKNOWN rationale не выводится автоматически: оцени, мешает ли он понимать подтверждённое правило.
INTERNAL_RESEARCH требует reviewed=true и явного обоснования. Если влияние не установлено — UNASSESSED;
не объявляй вопрос внутренним по умолчанию.

Draft создаёт PUBLICATION_RELEVANT candidates только по явным structured dependencies; reviewed=false
не означает semantic approval. Проверь каждую оценку перед handoff. Material conflict основного процесса
нельзя спрятать внутренним label, non-blocking severity или низкой confidence.

Сохрани все исходные gaps, включая internal/resolved, и finding_gap_links. gaps.json.publication_subset
содержит sorted gap_ids/finding_ids только открытых PUBLICATION_RELEVANT записей; это refs на полные
inventories, не их замена. Нельзя удалять research gaps, claims, limitations или provenance при отборе.
Composer сможет использовать этот subset; его код этим skill не меняется. Существующий conservative
publication_gate не ослабляется классификацией; pending relevance review не даёт gate=passed.

После review:
```text
python tools/knowledge/audit.py summarize --report <folder>/validation-report.json --gaps <folder>/gaps.json
python tools/knowledge/audit.py check --report <folder>/validation-report.json --gaps <folder>/gaps.json --knowledge <folder>/knowledge.yaml --source-map <folder>/source-map.json --scenario <folder>/scenario.json --business-rules <folder>/business-rules.json --technical-flow <folder>/technical-flow.json --domain-tree <folder>/domain-tree.yaml --scenario-definition <folder>/scenario-definition.yaml
```
summarize обновляет counts/gate и производный publication_subset, не evidence и не classification. check проверяет inventory, hashes, evidence/review consistency и gaps links. Он не проверяет semantic truth и не превращает draft в окончательный audit.

Результат — validation-report.json и gaps.json с новой классификацией отдельно от исходных claims. review_status=complete означает, что каждый claim рассмотрен, а не что все CONFIRMED. publication_gate не является разрешением публикации. Не меняй исходную KB/skills и не публикуй. Верни проверенное покрытие, conflicts, unknown и требуемые действия.
