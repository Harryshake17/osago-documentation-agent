# Границы и атомарность

Один scenario = одна бизнес-цель + основной trigger + ограниченный lifecycle + понятный outcome.
Каждый критерий имеет claims; atomic требует satisfied всех четырёх и lifecycle start/end refs.
Undetermined означает недоказанный критерий и Gap. Независимые цели/lifecycle требуют decompose
с основаниями независимости; число endpoints, retries и ветки отказа не определяют split.

Scope фиксирует repositories/revisions/components/scenarios/environments/exclusions.
Пустой список не означает весь проект. Node.scope_ref и все artifact scope_ref равны scope.id.
Downstream сохраняет весь Scope, а не только его имя. Расширение возвращается Domain Decomposer
как явная новая область/запуск, а не скрытое расширение текущего increment.

Domain/Scenario/Capability/BusinessRule создаются один раз в entity registry.
Общая capability переиспользуется через uses_capability с claim; parent — дерево документации,
не порядок исполнения. Соседний scenario со знакомым термином остаётся candidate/exclusion,
пока не доказан relevance_path от anchor выбранного ScenarioDefinition.
