---
name: osago-scenario-reconstructor
description: Восстановить основной, альтернативные и error business flows ОСАГО API из ScenarioDefinition, technical-flow, business-rules, Confluence и тестов в scenario.json с evidence каждого шага и перехода.
---

# Scenario Reconstructor

## Optional observed current flow

Прочитай [runtime evidence policy](../../knowledge-contracts/standards/runtime-evidence-policy.md).
Возможный вход: shared knowledge.runtime_traces/runtime_confirmations и OPENSEARCH Evidence.
Optional capability: **OpenSearch MCP**, purpose: production runtime verification;
invocation condition: unresolved material ambiguity after static analysis. Сначала используй
RuntimeTrace Technical Flow Analyzer. При собственной существенной ambiguity допустим
bounded MCP lookup напрямую по shared policy; normalized результаты передай Validator.
Сопоставь static model + business rules + все traces одного environment/version/period.
scenario.runtime_confirmation_refs сохраняет отдельный observed current flow, его status,
sample и provenance, без переписывания static ScenarioSteps/transitions или business meaning.
Не нормализуй разные timelines в один удобный вариант: VARIABLE/conditional behaviour
и gap; условие варианта требует evidence. Один trace — limited observation + sample Gap;
нет MCP — NOT_CHECKED + RUNTIME_UNVERIFIED; продолжай статическую реконструкцию.

Перед работой прочитай [shared knowledge model](../../knowledge-contracts/standards/knowledge-model.md),
[терминологию](../../knowledge-contracts/standards/terminology.md),
[evidence policy](../../knowledge-contracts/standards/evidence-policy.md) и
[границы/атомарность](../../knowledge-contracts/standards/domain-decomposition-rules.md).
Сущности получай из JSON/YAML входов, не из prose предыдущего skill. Перед передачей результата
сохрани checkpoint KB и согласованные upstream projections; проверь increment через
validate.py с --previous-knowledge <previous>/knowledge.yaml со второй стадии. При полном run запиши pipeline-run.json
и проверь все пять стадий командой tools/knowledge/pipeline.py из shared model.

Новые outputs и inputs используют model_profile=scoped-knowledge-v1. Каждый ScenarioStep имеет
business_action/business_result как knowledge_value, knowledge_status, technical_implementation
с implementation_refs/technical_step_refs/source_ids и state_transition={from:State ID|null,to:State ID|null}.
preferred_name и технический alias состояния берутся из State registry, не создаются заново.
05-scenario — единственный canonical источник человеческого описания процесса для Composer.
business_action/business_result — canonical narrative полей шага; action/system_behavior описывают
действие и реакцию системы на том же уровне процесса, а не второй UC или граф внутренних вызовов.
Техническая трассировка хранится в refs на 03 nodes; не копируй method/class/pipeline details в narrative.
Переиспользуй Domain Scenario ID, Rule/Integration/State IDs и claims/evidence upstream.
Сохрани достаточно claims, typed refs, effects/decisions, transitions, evidence snapshots и gaps,
чтобы будущий Composer мог работать только по артефактам. Новый выход — 05-scenario.json.

Прочитай [общий контракт](../../knowledge-contracts/contract.md), [scenario schema](../../knowledge-contracts/schemas/scenario.schema.json) и [процедуру реконструкции](references/reconstruction.md). Используй shared model 1.0. Business flow строится по доказательствам, а не по правдоподобию рассказа.

Вход: ScenarioDefinition, technical-flow, business-rules, Confluence knowledge и tests. Knowledge хранит snapshots/evidence; source-map и domain-tree нужны для проверки provenance предыдущих артефактов. Все входы относятся к одному scope и фиксированной ревизии KB. Confluence/tests могут быть недоступны: это Gap + partial coverage. Их отсутствие не восполняется LLM reasoning.

Восстанови цепочку Actor action → system reaction → business decision → external interaction → state transition → actor-visible result. Цепочка — цель исследования, не шаблон обязательных придуманных шагов. Локальное действие может не иметь интеграции; обоснуй not_applicable. Если business_meaning или user_result не подтверждены, сохрани UNKNOWN + Gap.

Сохрани один main_flow — ссылку на основной flow в реестре flows. alternative_flows и exception_flows —
ссылки на значимые alternative/error flows в том же реестре. Не копируй steps в эти поля, не создавай
happy_path, отдельный UC/main flow или parallel narrative. flows хранит каждое определение ровно один раз;
steps — единственный реестр ScenarioSteps. Основной путь задаёт последовательность через step_refs и
доказанные transitions. Если основной путь не подтверждён, main_flow=null + affected Gap + partial;
не выбирай первую успешную ветвь самостоятельно.

Укрупняй технические узлы до осмысленных действий/результатов процесса. Один ScenarioStep может ссылаться
на несколько technical nodes (many-to-one); граница группы, порядок и результат требуют evidence.
Не создавай step на каждый метод, класс или pipeline stage. Actor нужен на уровне Scenario/Use Case:
actor_action требует подтверждённого инициатора; system-to-system processing допускает один system_reaction
с actor=null и evidence-backed not_applicable. Не ищи actor для internal method и не создавай actor Gap
только из-за внутренней реализации. Неизвестное участие реального бизнес-актора по-прежнему UNKNOWN + Gap.

Найди значимые alternative и exception paths. Для каждого шага сохрани все поля пользователя: order, actor, action, business_meaning, system_behavior, evaluated_rules, integrations, state_before, state_after, user_result, implementation, evidence. Дополнительно сохрани ID, technical_step_refs, sources, attribute_claims, unknown/not_applicable и gaps/conflicts.

Каждый шаг связан через technical_step_refs с одним/несколькими canonical nodes 03-technical-flow; implementation refs не являются отдельными действиями. Каждый известный decision связан с Decision entity и BusinessRule из business-rules через evaluated_rules и claims. Rule kind technical_constraint не становится бизнес-решением: decision_kind=technical, business_meaning=UNKNOWN при отсутствии подтверждения. Известный business_meaning требует прямого source-stated evidence, не inference бизнес-мотива.

Каждый переход — отдельная запись transitions с source-backed directed claim. Не выводи порядок из списка файлов и causality из хронологии логов. order — позиция отображения; не доказательство причины. Недоказанный переход kind=unresolved + Gap, без причинного claim. Нельзя объявить такой flow полным.

Output: scenario.json рядом с knowledge.yaml и входами. Unknown rationale правила не переписывай и не скрывай в business_meaning. Не добавляй новые бизнес-правила; направляй missing rule к Business Rule Extractor, новые sources — Source Discovery, missing technical edges — на техническую проверку. Не реализуй этим skill отсутствующий Technical Flow Analyzer.

После проверки смысловых границ подготовь evidenced steps/flows/transitions и используй canonical writer:
```text
python tools/knowledge/scenario.py --input <folder>/prepared-scenario.json --knowledge <folder>/knowledge.yaml --scenario-definition <folder>/scenario-definition.yaml --technical-flow <folder>/03-technical-flow.json --business-rules <folder>/04-business-rules.json --source-map <folder>/02-source-map.json --domain-tree <folder>/01-domain-map.yaml --previous-knowledge <previous>/knowledge.yaml --output <folder>/05-scenario.json
```
Writer сохраняет source-backed классификацию flows и refs без исследования или автоматической группировки
методов/назначения акторов; validation выполняется до записи. Existing output требует явного --overwrite.
Historical Scenario получает selectors при явной миграции, без переименования Step/Claim/Evidence IDs.

Проверка из корня репозитория:
```text
python tools/knowledge/validate.py scenario <folder>/05-scenario.json --knowledge <folder>/knowledge.yaml --scenario-definition <folder>/scenario-definition.yaml --technical-flow <folder>/03-technical-flow.json --business-rules <folder>/04-business-rules.json --source-map <folder>/02-source-map.json --domain-tree <folder>/01-domain-map.yaml
```
Зависимости — tools/knowledge/requirements.txt. После проверки формы/ссылок семантически сверь все field claims и переходы с первичными фрагментами. Передай main/alternative/error paths, evidence и непокрытое; не публикуй и не создавай финальную документацию.
