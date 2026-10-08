Профиль новых выходов — scoped-knowledge-v1. [Shared standards](../../../knowledge-contracts/standards/knowledge-model.md)
задают terminology, evidence, статусы, identity и checkpoints. Ниже описан существующий
алгоритм исследования; legacy scalar/projection поля не заменяют новые business representations.
В новом профиле inference хранится в claims, не Evidence; business_rationale — knowledge_value.

# Проверка execution path

1. Проверь scope, revisions и accepted sources. Начинай от доказанного API operation/trigger; если entry не найден, сохраняй подтверждённые фрагменты и Gap, не объявляй end-to-end flow.
2. Читай тела методов, callers и registration/dispatch wiring. Имя команды и reference сами по себе не доказывают вызов. Для DI, middleware/pipeline ordering, процессных definitions, extensions и runtime dispatch проверяй регистрацию/условия выбора реализации. Неизвестную dynamic target фиксируй frontier.
3. Сохраняй ветки true/false/case/error с точными conditions и отдельными relations claims. Не превращай display order в execution order. Для loops/retries укажи проверенные bounds/exit условия; если они неизвестны, Gap. Exception, catch/finally и early return не теряй.
4. У external call проверяй client invocation, request/response mapping, timeout/error handling. Тело внешнего сервиса вне scope не восстанавливай по имени клиента. Config key, default, provider/override и место чтения подтверждай отдельно; отсутствие deployment config оставляет effective value UNKNOWN. Разделяй configured и implemented claims.
5. Для state changes проверяй объект, поле, значение/выражение и путь присваивания. Присваивание не доказывает persistence/commit: найдите save/transaction boundary либо Gap. Не выводи бизнес-состояние из технического return value.
6. Для callbacks/events фиксируй publish/subscribe/handler wiring, correlation и доступные ordering/idempotency условия. Publish не доказывает delivery, async await не доказывает callback, callback не обязательно продолжение того же запроса. Неподтверждённые связи не добавляй как calls/sequence.
7. Tests помогают выявить пути и ожидаемый результат; test_expectation не становится implemented без code support. Чтение теста не означает успешный test run. Противоречия сохраняй с обоими evidence и контекстом для Skill 6.

## Представление

nodes — единственная canonical коллекция технических узлов; id имеет namespace technical-step: и соответствует SystemBehaviour entity. ScenarioStep существует только в 05-scenario. component_id самого node указывает CodeComponent/ConfigRule/ApiOperation. Actor не требуется; не выводи бизнес-актора из класса, метода или вызова. type — роль шага в этом пути; один символ может участвовать в нескольких условиях. Нет необходимости создавать отсутствующие уровни архитектуры.

Для scalar type/symbol/purpose и каждого элемента inputs/outputs/conditions/calls/state_changes/configuration_reads/checks/external_calls/async_events создай attribute_claims. В values можно сохранять точное выражение/техническое описание, не бизнес-трактовку. calls содержит node IDs; relation_type=calls с matching claim фиксирует направление. Для rule веток используй rule_branch/true_branch/false_branch/error_branch/switch_case; для async publish/subscribe/callback и persistence используй отдельные точные predicates. Все отношения связывают доказанные entities и имеют evidence через claims.

Для пустого поля: unknown_fields + открытый affected Gap либо not_applicable_fields + claim predicate=not_applicable, value=имя поля. Не помечай необследованный код not_applicable. Node claim_ids содержит весь набор field claims и implementation claim; node source_ids покрывают их evidence. Второй коллекции steps в technical-flow быть не должно. Node evidence перечисляет подтверждающие supporting evidence. Схема принимает compact nodes без analysis_profile как legacy inputs; старые steps-only/dual flows требуют явной структурной миграции с сохранением Evidence/Claim/provenance и согласованности всех refs; новые результаты этого skill обязательно имеют analysis_profile и nodes.

Coverage complete допустим только после проверки всех достижимых путей внутри scope; непросмотренные handlers, динамические targets, внешние границы, неизвестные config значения и state persistence — partial + limitations/frontier/Gaps. Полнота структуры не подтверждает полноту поиска. Skill 6 выполняет независимую классификацию всех claims.
