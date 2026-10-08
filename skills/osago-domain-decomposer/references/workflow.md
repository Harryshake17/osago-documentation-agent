Профиль новых выходов — scoped-knowledge-v1. [Shared standards](../../../knowledge-contracts/standards/knowledge-model.md)
задают terminology, evidence, статусы, identity и checkpoints. Ниже описан существующий
алгоритм исследования; legacy scalar/projection поля не заменяют новые business representations.
В новом профиле inference хранится в claims, не Evidence; business_rationale — knowledge_value.

# Процедура

1. Зафиксируй scope: репозитории/версии, компоненты, сценарии, окружение, исключения и бюджет. Пустой список не означает «всё». Недоступный источник и неизвестная граница — Gap.
2. Найди первичные anchors в репозитории и существующей KB. Начни с rg/поиска файлов и символов, затем открой конкретные фрагменты. KB и названия нужны для навигации; проверяй её факты по коду/config/test/Confluence. Confluence ищи/читай через доступный инструмент; отсутствие доступа отрази в coverage.
3. Для цели, участника, trigger, состояния и результата создай отдельные атомарные claims. Техническая роль caller не доказывает бизнес-актора; return/validator не доказывает бизнес-причину. CODE поддерживает implemented, тест — test_expectation, документ — documented_requirement; не смешивай их.
4. Построй кандидаты узлов. Для scenario оцени четыре критерия atomicity. Укажи lifecycle start/end через claim IDs. Если критерий неизвестен, запиши missing критерий и Gap. atomic допускается только при всех satisfied; decompose — при подтверждённой независимости целей/lifecycle. Составной верхний узел может стать domain, дочерние сценарии — самостоятельными.
5. Для каждого split в decomposition_reason объясни редакционное решение и укажи recommendation_basis_claim_ids. Сохрани scope неизвестного, не выдумывай дочерние ветки. Успех/отказ/отмена одной цели могут быть outcomes одного сценария.
6. Capability создавай один раз; reuse привязывай uses_capability relations с evidence. business_rule обозначает подтверждённое правило либо кандидата с null и Gap; имя метода недостаточно. Использование правила — applies_rule. parent определяет дерево документов; иерархия не означает порядок выполнения.
7. Заполни attribute_claims: для scalar ключ равен имени поля; для списков — actors/0, exit_states/0 и т.д. Name требует claim о термине либо включения в proposed_fields; не скрывай бизнес-факт в имени. Parent/recommended_document/decomposition_reason — редакционные предложения, с basis IDs, когда основания известны.
8. Открой каждый подтверждающий фрагмент, сравни версию и контекст. Противоречия сохраняй Conflict, не выбирай Confluence автоматически. Неподдержанный claim оставь proposed/needs_review; нельзя использовать его как установленное поле.
9. Запусти механическую проверку. Сверь семантически цель, атомарность и предложенные границы. Сохрани partial coverage, если источники/бюджет ограничены.

# Обязательные различения

- Два endpoints одной цели и lifecycle → не split только по endpoints.
- Независимые цели и отдельные triggers/lifecycle → split с evidence.
- Есть код, но нет бизнес-цели → business_goal=null, Gap, undetermined.
- Разные triggers в Confluence/коде → отдельные claims + Conflict.
- Общая capability → один узел и несколько подтверждённых uses_capability.
- Искомый домен шире исследованного scope → обозначить границы, не объявлять полноту.
