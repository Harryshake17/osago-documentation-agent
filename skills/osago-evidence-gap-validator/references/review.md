# Source review

## Каждый claim

1. Сверь identity/text/predicate/value/context/hash. Если утверждение составное, проверяй все части. Evidence для порога не подтверждает rationale/актёра/внешний результат.
2. Reopen code/config/test по exact revision или проверяемый immutable snapshot. Чтение одного слова поиска не считается verification. Для snapshot_only укажи ограничение актуальности; оно подтверждает лишь зафиксированную версию. Hash в source_check совпадает с сохранённым snapshot hash; иной hash означает drift, а не право переписать старое evidence.
3. source_check перечисляет evidence_id, snapshot_id, source_location/version, hash, verification, quote и result. Quote содержит фактически прочитанный фрагмент; rationale review не заменяет его. Для unavailable/not_checked quote=null. Для INFERENCE reasoning_checked оценивает сам вывод; primary support раскрывается через basis claims.
4. CONFIRMED относится к точной modality/context claim. Код не подтверждает runtime выполнения, тест не подтверждает production, Confluence requirement не доказывает реализацию. reviewer может классифицировать намерение автора как source_statement, но не заменить этим бизнес-факт.
   OPENSEARCH поддерживает только qualified observed_cases; проверяй shared RuntimeTrace
   и runtime_reviews по [runtime policy](../../../knowledge-contracts/standards/runtime-evidence-policy.md).
   Assessment OBSERVED не означает semantic approval; недостаточная выборка, вариативность,
   static mismatch и недоступность сохраняют отдельные runtime gaps.
5. PARTIALLY_CONFIRMED требует supported_parts и unsupported_parts. Не повышай в CONFIRMED весь текст; required_action=split_claim/add_evidence.
6. В scoped-knowledge-v1 INFERRED — Claim с inference=true, basis_claim_ids и inference_rationale; отдельное INFERENCE Evidence запрещено. Проверь каждый basis claim до CODE/CONFIG/TEST/CONFLUENCE без циклов. Legacy package может использовать INFERENCE Evidence по старому контракту. Вывод не становится CONFIRMED из-за убедительности. Business rationale/meaning нельзя обосновать inference.
7. UNKNOWN остаётся UNKNOWN при missing/irrelevant evidence. Можно reviewed=true, если попытка выполнена и ограничение явно установлено. Это не значит, что claim подтверждён.
8. Проверяй и отрицательные/универсальные claims («всегда», «никогда», «нет»): границы поиска, if/config/error/test альтернативы. Одна ветка не доказывает инвариант.

## Conflicts

Сравни claims по объекту/условию, версии, окружению, конфигурации и modality. Разные условия или исторические версии — context difference, а не автоматический conflict. Несоответствие требования реализации фиксируется как discrepancy/Gap; не выдавай документированное намерение за описание текущего поведения.
Для comparison CONFLICT нужны inspected evidence обеих сторон, context_comparison=overlap, reviewed=true, reason и required_action=analyst_review/resolve_conflict. Частично сопоставленный контекст → UNRESOLVED. CONSISTENT не выводится из одинаковых labels.
Code/config branch против document/test — сохраняй обе поддержки. В отчете указывай конкретные root evidence IDs и новые conflict comparisons; существующий KB Conflict сохраняется, пока не разрешён evidence-backed решением.
Проверенные контрпримеры могут относиться к одному универсальному claim: comparison.claim_ids допустим с одним ID, evidence_ids содержит обе стороны.

## Gaps и полнота flow

- Missing evidence: locators без фрагмента, dangling references, нераскрытые inference и нерелевантные citations.
- UNKNOWN business_rationale/meaning: неизвестная причина, не гипотеза «для снижения риска».
- State transition: объект, before/after, guard, persist/transaction и response. Enum/порядок строк не доказывает смену состояния.
- Config behaviour: key → reader/override → branch/effect → documented scope. Не найденная doc link в KB — Gap поиска, не доказательство отсутствия Confluence.
- Technical branches: проверь declared technical relations, if/switch/error branches первичного кода и их отражение в scenario. Группировка technical steps не должна скрывать изменение outcome. Если branch не влияет на бизнес-результат, обоснуй неприменимость source-backed resolution claim.
- Scenario without implementation: каждый шаг/решение/интеграция/state/result должен иметь доказанный implementation mapping. Ссылка на класс без конкретной ветки недостаточна. Не найденная ссылка — Gap, не утверждение «код отсутствует».
- Механические findings о пропусках — triage; проверь смысл в источнике перед объявлением бизнес-конфликта.

## Reader impact

Shared Gap и Finding получают publication_relevance={classification, reviewed, reason, impacts}.
impacts — список {aspect, target_refs}; refs указывают на существующие scoped artifacts/records.
Поддерживаемые аспекты: MAIN_FLOW, ALTERNATIVE_OR_EXCEPTION_FLOW, BUSINESS_RULE,
EXTERNAL_CONTRACT, STATE_TRANSITION, BUSINESS_RESULT, VERSION_ENVIRONMENT.
Это не Evidence и не KnowledgeStatus. blocking/severity/confidence не определяют видимость.

PUBLICATION_RELEVANT требует конкретного влияния на один из аспектов. INTERNAL_RESEARCH требует
проверки отсутствия reader impact и reviewed=true с обоснованием. Неизвестная релевантность — UNASSESSED.
Не делай technical gap material только из-за many-to-one mapping на ScenarioStep и не признавай его
внутренним только потому, что target — technical node: значимую branch/outcome проверяет reviewer.

Вопросы о helper/method/internal actor/generated graph остаются research, если main/значимые variants,
условия/результаты правил, внешний контракт и состояние независимо подтверждены. Пропущенный test/file
при другом достаточном evidence не обязательно material. Неизвестная business rationale может оставаться
research, когда точное правило понятно без неё; подтверждённая зависимость reader understanding делает
её material. Не придумывай rationale или акторов в процессе triage.

Механический index выявляет явные process/contract dependencies, competing claims и используемые runtime
confirmation refs. Он не доказывает semantic correctness и не исследует источники. Material conflict в
основном процессе сохраняется видимым; check запрещает INTERNAL_RESEARCH для таких dependencies.

После оценки summarize пересчитывает publication_subset refs без изменения полных inventories,
классификаций, facts/statuses/evidence. check требует точного subset, сохранения исходных Gap IDs/affected refs,
валидных impact refs и material finding↔Gap связей. Исходный conservative gate не повышается от фильтрации.
Reviewed=false/UNASSESSED не разрешают публикацию и не выводят автоматически весь inventory в статью.

## Reports

Draft tool проверяет структуру и генерирует candidates/comparisons с UNRESOLVED; не выполняет semantic source reading. Все schema-valid checks могут оставаться неверными по смыслу, поэтому ручная сверка обязательна.
Claim inventory = все уникально идентифицированные claims выбранной KB, включая source discovery и inference bases. Duplicate/missing IDs — structural finding и partial review. Не пропускай claim ради успешного gate.
Сохраняй все KB gaps в gaps.json, включая internal и resolved; публикационная классификация не меняет lifecycle. Дополнительные gaps используют ту же shared Gap model; finding_gap_links связывает отчет и gaps. affected_ids — существующие KB IDs; сырой artifact locator хранится в finding.target_refs.
review_status и publication_gate считаются отдельно: audit может завершиться с UNKNOWN/CONFLICT. Mechanical check может пройти для draft, но summary.review_status останется partial.
Не публикуй, не изменяй бизнес-факты автоматически и не превращай analyst_review в очередную обязательную permission prompt при реализации skill.
