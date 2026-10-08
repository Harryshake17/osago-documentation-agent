# Optional OpenSearch runtime evidence

OpenSearch — дополнительный источник OBSERVED_RUNTIME_BEHAVIOUR. CODE / CONFIG /
TEST / CONFLUENCE и доступные JIRA / GIT исследуются первыми. Не создавать отдельный
skill, HTTP client, SDK или MCP server. Старый pipeline без runtime-полей сохраняется.

Optional capability: **OpenSearch MCP** в IDE. Purpose: production runtime verification.
Invocation condition: **unresolved material ambiguity after static analysis**.
В проекте есть `search_iris_logs_raw(query_json)`; правила провайдера описаны в существующем
[iris-opensearch-logs](../../skills/iris-opensearch-logs/SKILL.md). Другой IDE mapping
может использовать эквивалентную подключённую read-only search capability.

## Процедура

1. Зафиксировать существенный unresolved question, рассмотренные static Evidence IDs,
   гипотезы и различающие варианты log events. Без ambiguity search не нужен:
   runtime-поля отсутствуют либо assessment NOT_REQUIRED.
2. Найти существующие correlation/lookup fields, задать environment, актуальную версию,
   период и критерии representative cases. Не придумывать имена log fields из терминов KB.
3. Выполнить bounded read-only MCP search: range, application/environment, case/correlation
   keys, ограниченные size и _source. Не хранить credentials, токены, mcp_auth и запросы
   с чувствительными значениями. При обрезке выдачи сузить запрос и проверить полноту.
4. Собрать минимум **3 независимых подходящих кейса**, если логи позволяют. Для критичных
   или вариативных веток стремиться к **5+**, повышая minimum_sample_size. Повторный запрос
   того же кейса не увеличивает выборку. Сохранить selection_reason; не выбирать только
   удобные совпадения и не удалять обнаруженные варианты.
5. Happy path: complete SUCCESS. Ошибки — отдельный ERROR cohort. Не смешивать production
   и test/beta, версии до/после rollout, успешные и незавершённые/ошибочные кейсы.
6. Коррелировать события с process/request/callback identifiers и static technical refs.
   Timestamp сам по себе не доказывает causal order для async; проверить retries, clock
   skew, полноту и correspondence event markers реальному excerpt. Сохранить timeline.
7. Сравнить все выбранные traces и static possible paths. Не переписывать code model.
   Unknown version, смешанные среды/версии, incomplete или timestamp-only ordering дают
   NOT_CHECKED + RUNTIME_UNVERIFIED, а не ложный static/runtime conflict.

Нет capability/доступа/логов/сопоставимого материала: diagnostic в limitations,
NOT_CHECKED + открытый **RUNTIME_UNVERIFIED** Gap. Дополнительная проверка не останавливает
построение статического flow. Значимый gap сохраняет существующий publication gate blocked.

## Shared contracts

`common.schema.json` расширяет существующий Evidence.source_type значением OPENSEARCH.
source_ref остаётся snapshot ID, supports — Claim IDs, metadata — прежняя проекция.
runtime хранит environment/index/query_description, обезличенный case_ref, период,
application_version и limitations. Snapshot.adapter=opensearch; excerpt/hash фиксируют
минимальный очищенный фрагмент реально прочитанных событий. Не подделывать snapshot/hash,
не сохранять полные log documents. Удалять PII/секреты **до** записи artifact. identifiers
представлять однонаправленными case/correlation/request/process refs; helper case_reference
не сохраняет исходное значение. Не публиковать исходные identifiers.

`knowledge.runtime_traces` — shared RuntimeTrace: scenario_id, environment/version/period,
identifiers, outcome, complete, ordering_basis, timeline (order/timestamp/event/
technical_step_ref/technical_refs/evidence_ids), aggregate evidence_ids и limitations.
event — нормализованный технический marker, не raw log line. Technical refs — существующие
scoped Entity/technical step IDs. Trace подтверждает кейс, не универсальность.

`knowledge.runtime_confirmations` связывает question, static_review_evidence_ids,
static_claim_ids/static_sequences, event_filter, trace_refs, selection_reason,
minimum_sample_size, claim_ids/gap_ids и assessment status. Static sequence должна иметь
собственный current static-backed Claim этого Scenario. Если порядок не доказан,
static_sequences пуст, гипотезы записаны в question/limitations без повышения до facts.
Это отдельная оценка наблюдения, **не новый KnowledgeStatus**:

| result | Смысл | Gap |
| --- | --- | --- |
| NOT_REQUIRED | Нет существенной ambiguity; search не выполняется | Нет |
| NOT_CHECKED | Capability/сопоставимый материал недоступен | RUNTIME_UNVERIFIED |
| OBSERVED | >=minimum_sample_size совпадающих независимых сопоставимых traces | Нет по sample |
| VARIABLE | Разные пути; сохранить каждый вариант | RUNTIME_VARIABILITY |
| STATIC_RUNTIME_CONFLICT | Сопоставимые traces расходятся с заявленными static paths | STATIC_RUNTIME_CONFLICT |
| INSUFFICIENT_SAMPLE | Недостаточно независимых кейсов, включая один trace | INSUFFICIENT_RUNTIME_SAMPLE |

Не разрешать variability/conflict выбором одного пути. Conditional behaviour требует
отдельно доказанных условий. Trace/confirmation неизменяемы: новая выборка/версия/вопрос
→ новые IDs, старые сохраняются. Согласованно повысить package revision/checkpoints.

## Claims и validation

OPENSEARCH — support только для modality=runtime_observation,
predicate=observed_runtime_sequence, subject=Scenario, value={confirmation_ref,
extent:observed_cases,statement,sequence}. Сохранять все traces и их Evidence.
Старые static-backed claims с этой modality читаются с прежним value; OPENSEARCH
требует новую нормализованную форму и scoped-knowledge-v1, без неявной миграции legacy.
Один trace допускает только PARTIALLY_CONFIRMED ограниченное наблюдение + sample Gap.
CONFIRMED — лишь для достаточной сопоставимой OBSERVED выборки после source review.
Не выводить «всегда», невозможность альтернатив, business rule или rationale из логов.
Для static/business claims логи допустимы как context; правила/rationale требуют прежних
источников. Runtime observations не служат основанием inferred universal rule.

Validator повторно проверяет scope, period/version/environment, независимый sample count,
cohort/completeness, technical/Evidence refs и static comparison. validation.runtime_reviews
содержит result/sample_size/trace_refs, reviewed/reason. Draft reviewed=false: механическое
OBSERVED не является semantic approval. Ревьюер проверяет capture, correlation, актуальность
static version, репрезентативность и отсутствие universal claims в statement. Каждый excerpt
инспектируется обычными source_checks; ограничения не исчезают после ревью.

Source Discovery готовит capability/lookup keys; Technical Flow — основной collector;
Rules используют runtime_examples; Scenario хранит отдельный current observed flow.
Composer **не вызывает MCP**: получает validated normalized Trace/Evidence/assessment.
По reader-first [template](documentation-template.md) включает наблюдение, если оно
поясняет Scenario или существенное расхождение. У включённого наблюдения обязательны
bounded scope, environment/version/period, sample и ограничения достоверности.
Полные traces, provenance и research gaps сохраняются в structured artifacts/manifest;
в статье показываются только ограничения, значимые для понимания описанного процесса.
Отбор не меняет runtime assessment, Evidence, KnowledgeStatus или publication gate.
Raw log lines, query, identifiers, excerpts и quote OpenSearch не выводятся в статью.
Glossary Curator сохраняет прежние правила preferred terminology; log marker не становится
business term. Новых Evidence/Terminology/KnowledgeStatus models нет.

Contract/invariant tests: `python -m unittest discover -s tools/knowledge/tests -p test_runtime.py`.
Семь обязательных случаев и дополнительные invariants используют synthetic offline fixtures.
Полная регрессия: `python -m unittest discover -s tools/knowledge/tests`.
