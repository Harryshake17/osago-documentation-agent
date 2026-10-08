Профиль новых выходов — scoped-knowledge-v1. [Shared standards](../../../knowledge-contracts/standards/knowledge-model.md)
задают terminology, evidence, статусы, identity и checkpoints. Ниже описан существующий
алгоритм исследования; legacy scalar/projection поля не заменяют новые business representations.
В новом профиле inference хранится в claims, не Evidence; business_rationale — knowledge_value.

# Реконструкция сценария

## Чтение входов

Проверь scope/versions и provenance входов. Начни с trigger/entry state/actors ScenarioDefinition и accepted sources. Прочитай technical-flow relations и business-rules conditions/effects. Confluence знание и тесты подтверждай конкретными snapshots; старый KB prose нужен для навигации, не как замена evidence.

Отсутствующий technical-flow или rules — missing input Gap и незавершённая задача. Не придумывай rules/flow в процессе реконструкции. Для дополнительной проверки разрешено открыть code/config/test/Confluence внутри scope; новый источник сначала должен попасть в accepted source-map и согласованную ревизию всех projections.
Это правило относится к новым статическим источникам. Optional OPENSEARCH observations
сохраняются отдельно в shared RuntimeTrace/confirmation по
[runtime policy](../../../knowledge-contracts/standards/runtime-evidence-policy.md),
без добавления runtime logs в static source-map categories и без замены static transitions.

## От технических компонентов к шагам

- Группируй технические операции до осмысленного действия/результата процесса, если объединение, граница и порядок подтверждены. Не создавай отдельный ScenarioStep на method/class/pipeline stage; technical details остаются только в 03 nodes. Свяжи шаг со всеми participating implementation IDs и technical_step_refs. Технический helper не обязан становиться отдельным действием пользователя.
- Actor action требует Actor и evidence участия; внутреннему вызову не приписывай пользователя. actor=null означает unknown либо evidence-backed not_applicable. Для внутреннего system-to-system processing actor не требуется: зафиксируй неприменимость на уровне процесса, не ищи бизнес-актора для internal method.
- action/system_behavior отражают действия, business_meaning — отдельно подтверждённый смысл. Запрет на придуманную причину распространяется и на «чтобы», «для предотвращения», «поэтому».
- Decision имеет decision_ref и evaluated_rules. Technical guard без подтверждения назначения остаётся technical decision. Для business decision требуется минимум business_rule/eligibility с прямым подтверждением назначения.
- Integration связывается с Integration entity и вызовом реализации, а не с наличием NuGet package или именем системы. Дополнительно проверь внешнюю response/error mapping. Нет источника → [] + unknown Gap.
- state_before/state_after — State IDs конкретного объекта. Название статуса или наличие enum недостаточны для доказательства фактического перехода. Разные объекты могут иметь разные состояния: не объявляй их единой state machine.
- User result выводится из response/contract/test/document с правильной modality. Exception не означает, что актор увидит validation error. Различай actor-visible capability «может перейти к оплате» и факт выполнения оплаты.

## Flows и transitions

1. main_flow — единственный selector (Flow ID) основного пути в flows; alternative_flows/exception_flows — списки Flow IDs типов alternative/error. Сами определения и step_refs хранятся в flows ровно один раз, ScenarioSteps — в steps. Не создавай happy_path/UC копию. Отсутствие подтверждённого main оставляет main_flow=null + affected Gap + partial; не выбирай его по успешному trace. Main flow — подтверждённый основной путь достижения цели, не просто первый найденный success test. Main entry_condition связывает trigger/условие через claim на Scenario entity. Для каждого flow type_claim_ids подтверждают классификацию claim subject=Scenario ID, predicate=flow_type, value={flow_id, type}.
2. Alternative flow — другое подтверждённое достижение/отказ/отмена той же цели. Независимая цель/lifecycle возвращается Domain Decomposer, не добавляется как альтернативный сценарий молча.
3. Error flow — ошибка, точка возникновения, обработка/компенсация и actor result, насколько они подтверждены. Не выдумывай rollback/retry/компенсацию из существования catch.
4. Для alternative/error с общим шагом используй один Step ID; branch_from указывает точку ответвления, entry_condition и condition claims объясняют условие. Standalone error на самом входе может иметь branch_from=null с прямым source claim условия.
5. Directed переход имеет claim subject=from_step, predicate=kind, value=to_step. Тип causes требует источника связи; precedes подтверждает лишь порядок. Все hops причинной цепочки проверяются отдельно.
6. rule_branch дополнительно содержит Decision, Rule, rule_outcome и condition. Claim branch_condition на from_step имеет value object {rule_id, outcome, condition}. UNKNOWN rule outcome/condition не считается известной ветвью.
7. Для asynchronous callback сохраняй correlation/continuation proof. Temporal coincidence не causality. Retry cycle явно обозначается retry; order не разворачивает бесконечный цикл. Объясни exit bounds по источнику либо Gap.
8. Если переход не подтверждён, сохрани unresolved + affected open Gap. Не выдавай соседство order/step_refs за установленную связь. Основной путь может быть partial с gap; это полезный результат, но не полное восстановление.
9. Каждый flow имеет упорядоченные step_refs; order — стабильный глобальный display index для unique steps. Общий step в нескольких flows не копируется ради другого order. Выполнение определяется transitions, а не глобальным order.
10. Не найденные alternative/error → not_found только после обследования sources; unavailable/incomplete не равны отсутствию этих путей.

## Claims и неизвестность

Каждый scalar и каждый элемент evaluated_rules/N, integrations/N, implementation/N связан через attribute_claims с Claim subject=Step ID, predicate=поле и value=значение. decision_kind тоже подтверждён, если не none.
business_meaning UNKNOWN требует unknown_reason Gap. UNKNOWN текст/null state/actor/пустой список имеют unknown_fields либо not_applicable_fields. Неизвестность требует open Gap; неприменимость — explicit claim predicate=not_applicable, value=имя поля. Известные поля нельзя одновременно помечать unknown.
technical_step_refs связывают ScenarioStep с canonical nodes 03-technical-flow. Many-to-one refs сохраняют все participating components, business rules и evidence, без копирования технического графа. Evidence field support раскрывается до accepted snapshots; evidence всех используемых claims перечисляется у step/transition.
Known business_meaning не может быть inferred. Business Rule rationale UNKNOWN нельзя заменить inferred объяснением в prose.
Каждый flow/переход/шаг имеет gaps/conflicts. Итог coverage partial при любом релевантном unknown/unresolved/conflict, включая входные ограничения.

## Финальная проверка

Открой все первичные фрагменты field/edge support, проверь модальность и semantic entailment. Сопоставь rules true/false effects с выбранными ветвями, state transition с объектом и actor result с контрактом/mapper. Проверь непрерывность каждого flow, branch origin, известные terminals, отсутствие недоказанных дополнительных узлов.
Не объявляй passage через технические условия полноценным business flow, если business_meaning/outcomes или участие применимого бизнес-актора unknown. Evidence-backed неприменимость actor к system step не является business gap. Выдай технически подтверждённый backbone и список missing business links.

Link2 regression fixture проверяет contract shape calculate → import → payment → post-payment/policy issuance → status/document и many-to-one mapping. Fixture синтетический; он не устанавливает production facts, states, thresholds или business rationale. Эта последовательность не hardcoded в общей генерации.

## Evaluation cases

Main/alternative/error с source-backed transitions; technical guard не становится бизнес-решением; неизвестный UI result остаётся UNKNOWN; integration не выводится из dependency; unresolved hop делает coverage partial; decision обязан иметь Rule; retry cycle не маскируется под линейный порядок; state mismatch не скрывается; inputs разных revisions отклоняются; inference не заполняет business_meaning.
