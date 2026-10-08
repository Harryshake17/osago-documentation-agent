Профиль новых выходов — scoped-knowledge-v1. [Shared standards](../../../knowledge-contracts/standards/knowledge-model.md)
задают terminology, evidence, статусы, identity и checkpoints. Ниже описан существующий
алгоритм исследования; legacy scalar/projection поля не заменяют новые business representations.
В новом профиле inference хранится в claims, не Evidence; business_rationale — knowledge_value.

# Поиск и проверка связи

1. Проверь ScenarioDefinition и дерево: один scope, совместимые ID и точные input revisions. Поисковые aliases — подсказки. Для bootstrap допустим ограниченный индекс, но accepted source требует подтверждённого entry-point anchor.
2. Начни с anchor symbols: route/action → command → dispatch/handler registration; process identifier → process definition → subprocess reference. Прочитай фрагменты, сохрани locator, версию, hash и excerpt.
3. Кандидат включает объяснение предполагаемой связи, но не evidence о бизнес-смысле. Accepted source требует непрерывного relevance_path от anchor symbol до своего symbol/source ID. Ребро поддерживает discovery claim о данной связи; evidence role=context не принимается как supports.
4. Пройди каждую категорию:
   - endpoint: route/method и mapping action;
   - controller: конкретный action, не все методы;
   - commands_handlers: declaration + dispatch/registration;
   - process_definitions/subprocesses: определение и явный mapping/ref;
   - business_rule_implementations: вызов/регистрация validator/decision, без формулирования бизнес-правила;
   - configuration_keys: чтение/binding property → key; effective value не выдумывай;
   - integrations: call/client и DI mapping; наличие пакета не доказывает участие;
   - automated_tests: request/command/process из тела теста; имя теста недостаточно;
   - confluence_pages: fetch страницы и точный section с идентификатором/ссылкой. Заголовок и общее слово дают только candidate.
5. В reverse reference поиске сохраняй смысл направления: scenario operation ↔ test, использующий её; не утверждай, что production вызывает тест.
6. Соседний repo ищи по dependency reference внутри scope. Dynamic dispatch/reflection без разрешения mapping → Gap и candidate. Unknown version → hash + Gap, а не выдуманный commit.
7. Сохраняй search_runs: категория, adapter, запрос, scope, cursor, completion, snapshot refs и diagnostic. При not_found укажи реально завершённые поиски; unavailable не маскируй под not_found.
8. Запиши accepted sources, candidates и exclusions раздельно; source ID уникален по repo/locator/revision. Один source может участвовать в разных сценариях с отдельными relevance claims. Для source доступны confidence/rationale, но confidence не заменяет path evidence.
9. Остановись после обследования категорий и доступного frontier либо исчерпания бюджета. incomplete категории, unresolved frontier и coverage=partial обязательны при ограничениях.
10. Проверь источники по первичным фрагментам и запусти общий валидатор. Передай карту следующему анализу; не создавай знания о поведении.

# Negative cases

Похожее слово в чужом файле, общий термин Confluence, похожее имя теста для другого endpoint → candidate/exclusion. Command и handler с разными именами, но явной регистрацией → accepted. Неизвестный subprocess mapping → candidate + Gap. Config файл с одним используемым ключом → принять конкретный key, не весь список. Недоступное соседнее repo → unavailable frontier. Несовпадающие версии регистрации → Conflict, без молчаливого объединения.
