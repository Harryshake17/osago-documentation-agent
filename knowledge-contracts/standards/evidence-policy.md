# Evidence и статусы

В профиле scoped-knowledge-v1 Evidence — фрагмент реального CODE, CONFIG, TEST,
CONFLUENCE, JIRA, GIT или OPENSEARCH с доступным versioned SourceSnapshot, locator и excerpt.
GIT фиксирует историческую версию/изменение, не современное поведение.
JIRA допускается как контекст; текущие primary roots: CODE/CONFIG/TEST/CONFLUENCE/GIT.
Тест подтверждает expectation; чтение теста не доказывает успешное выполнение.
OPENSEARCH поддерживает только ограниченное runtime observation. Статические primary roots
для business claims прежние. Применяй [runtime policy](runtime-evidence-policy.md): static first,
optional IDE MCP, >=3 независимых сопоставимых кейса, environment/version/period,
отдельные RuntimeTrace/assessment; без raw log lines в статье и business rationale из логов.

source_ref=snapshot_id; metadata — точная проекция repository/file/class.method/version/page.
supports содержит IDs claims, реально использующих Evidence с role=supports.
Claim.support остаётся нормативным направлением с roles supports/contradicts/context.
Поддержка каждого field claim сохраняется в evidence списка соответствующей записи.
Snapshots и содержимое evidence неизменяемы: новый текст/версия → новый ID.
supports может накопительно расширяться, старые связи не удаляются.

Inference НЕ является evidence. Мнение агента, уверенность, review, имена классов,
поисковое совпадение и prose предыдущей стадии не заменяют источник.
Вывод хранится в Claim: knowledge_status=INFERRED, inference=true, modality=inferred,
basis_claim_ids и inference_rationale. Цепочка оснований ациклична и достигает primary roots.
Legacy INFERENCE evidence допускается только при чтении старого профиля 1.0;
миграция явная, без автоматического повышения достоверности.

Единый knowledge_status: CONFIRMED / PARTIALLY_CONFIRMED / INFERRED / UNKNOWN / CONFLICT.
Это оценка производителя знания; independent review не выполняется этим pipeline.
CONFIRMED требует current/supported claim и прямую поддержку; business meaning/name/rationale
дополнительно требуют source_statement/documented_requirement, а не имя технического символа.
PARTIALLY_CONFIRMED сохраняет известную часть и открытые gaps; не означает полноту результата.
UNKNOWN допустим: value=null, claim не supported. Отсутствие business rationale — UNKNOWN + Gap.

Unresolved конфликт или contradicts evidence → CONFLICT с обоими утверждениями.
Не выбирай источник по confidence, типу или удобству. Новое evidence само по себе не даёт
аналитической стадии права разрешить CONFLICT. Решение конфликта — отдельный будущий этап.
Не повышай UNKNOWN/INFERRED/PARTIALLY_CONFIRMED без новой прямой поддержки.
Изменение значения/оснований claim требует нового claim ID с сохранением старого;
сохранение статуса проверяется по прежнему ID, а новое утверждение проверяется отдельно.

## Publication relevance

Stage 06 дополняет shared Gap/Finding полем publication_relevance:
{classification, reviewed, reason, impacts:[{aspect,target_refs}]}. Это оценка reader impact,
отдельная от KnowledgeStatus, Gap reason/status, blocking/severity и confidence.
PUBLICATION_RELEVANT / INTERNAL_RESEARCH / UNASSESSED не заменяют статусы знания.
Upstream Gap может не иметь этого поля; outputs 06 обязаны иметь его.

Material uncertainty способна изменить main flow, значимый alternative/exception flow,
существенное business rule, внешний API/integration contract, значимый state/status transition,
бизнес-результат или актуальность версии/окружения. Только такие открытые вопросы входят в
validation-gaps.publication_subset (gap_ids/finding_ids); полный inventory и provenance сохраняются.
INTERNAL_RESEARCH требует явного reviewed обоснования отсутствия reader impact. Не установленное
влияние остаётся UNASSESSED; не выводи внутреннюю релевантность из технического типа, severity или confidence.
Конфликт основного процесса обязательно видим. Relevance review не разрешает конфликт, не повышает
confidence/status и не ослабляет существующий publication_gate. Pending relevance блокирует gate.
