---
name: osago-domain-decomposer
description: Определить границы домена или сценария ОСАГО API, проверить атомарность и создать evidence-backed domain-tree.yaml. Использовать для выбора того, что документировать и как декомпозировать область.
---

# Domain Decomposer

Перед работой прочитай [shared knowledge model](../../knowledge-contracts/standards/knowledge-model.md),
[терминологию](../../knowledge-contracts/standards/terminology.md),
[evidence policy](../../knowledge-contracts/standards/evidence-policy.md) и
[границы/атомарность](../../knowledge-contracts/standards/domain-decomposition-rules.md).
Сущности получай из JSON/YAML входов, не из prose предыдущего skill. Перед передачей результата
сохрани checkpoint KB и согласованные upstream projections; проверь increment через
validate.py с --previous-knowledge <previous>/knowledge.yaml со второй стадии. При полном run запиши pipeline-run.json
и проверь все пять стадий командой tools/knowledge/pipeline.py из shared model.

Новые outputs используют model_profile=scoped-knowledge-v1. Domain nodes и ScenarioDefinition
содержат preferred_name, technical_aliases, search_aliases, terminology_candidates, evidence;
nodes дополнительно scope_ref. Registry entities имеет стабильные id/type/identity_key.
name остаётся совместимой навигационной проекцией: неизвестный preferred_name → proposed_fields.
Не переводи process/API name в business name; непонятные варианты сохраняй candidates.
Цель/trigger/lifecycle/outcomes по-прежнему подтверждаются attribute_claims и atomicity assessment.
Для нового run: runs/<domain>/01-domain-map.yaml и sidecars knowledge.yaml/scenario-definition.yaml;
при продолжении существующего run сохраняй его имена и папку.

Прочитай [общую модель и evidence policy](../../knowledge-contracts/contract.md), [контракт выхода](../../knowledge-contracts/schemas/domain-tree.schema.json) и [процедуру анализа](references/workflow.md). Используй общие schemas версии 1.0; не импортируй схемы старого прототипа osago-kb.

Вход: предполагаемое название области, scope и доступ к коду, Confluence, существующей KB. Название — поисковая гипотеза. Уточняй недостающие критичные границы, продолжая доступное исследование внутри явно указанного scope. Не расширяй область до всего проекта.

Результат: domain-tree.yaml и knowledge.yaml с claims/evidence/gaps, если общего пакета ещё нет. Для legacy run сохраняй прежнюю папку; используй папку пользователя, если задана. Дерево содержит domain/scenario/capability/business_rule. Каждый узел имеет все поля пользователя: id, name, type, parent, business_goal, trigger, entry_state, exit_states, actors, recommended_document, decomposition_reason, discovered_sources.

Определи цель, акторов, trigger, entry state, outcomes, независимые sub-scenarios и reusable capabilities/rules. Неизвестное значение — null/пустой список плюс Gap. Содержательные значения и связи требуют claim references; найденный источник не подтверждает все поля узла автоматически.

Scenario атомарен при одной бизнес-цели, одном основном trigger, ограниченном lifecycle и понятном outcome. Независимые цели/lifecycle требуют предложения декомпозиции; количество endpoints, retry и ветки ошибок сами по себе не требуют split. При непроверенном критерии atomicity=undetermined.

Проверь артефакт общей командой из корня репозитория:
```text
python tools/knowledge/validate.py domain-tree <folder>/01-domain-map.yaml --knowledge <folder>/knowledge.yaml
```
Зависимости: tools/knowledge/requirements.txt. Устанавливай их в изолированное окружение при необходимости. Выполни семантическую проверку полей и атомарности по источникам: валидатор проверяет форму/ссылки, а не истинность.

Передай дерево, coverage и unresolved gaps пользователю. Подготовь ScenarioDefinition для выбранного сценария, только если он нужен для последующего Source Discovery; не запускай остальные skills без соответствующей задачи. Документацию приложения и внешнюю публикацию этот skill не выполняет.
