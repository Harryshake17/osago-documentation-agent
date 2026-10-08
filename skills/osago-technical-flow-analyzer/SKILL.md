---
name: osago-technical-flow-analyzer
description: Восстановить execution path ОСАГО API по source-map и scenario scope в technical-flow.json с evidence шагов, вызовов, config, веток, state changes и async связей; без придуманного бизнес-смысла.
---

# Technical Flow Analyzer

Перед работой прочитай [shared knowledge model](../../knowledge-contracts/standards/knowledge-model.md),
[терминологию](../../knowledge-contracts/standards/terminology.md),
[evidence policy](../../knowledge-contracts/standards/evidence-policy.md) и
[границы/атомарность](../../knowledge-contracts/standards/domain-decomposition-rules.md).
Сущности получай из JSON/YAML входов, не из prose предыдущего skill. Перед передачей результата
сохрани checkpoint KB и согласованные upstream projections; проверь increment через
validate.py с --previous-knowledge <previous>/knowledge.yaml со второй стадии. При полном run запиши pipeline-run.json
и проверь все пять стадий командой tools/knowledge/pipeline.py из shared model.

Новые outputs и inputs используют model_profile=scoped-knowledge-v1.
Каждый node имеет business_meaning={value,status,claim_ids,evidence_ids}, отдельно
technical_implementation={implementation_refs,technical_step_refs,source_ids} и integrations с IDs.
implementation_refs указывает component_id самого canonical node; symbols/process/API
остаются aliases соответствующих registry entities. Для RegisterPolicyContractNSIS без отдельного
источника смысла business_meaning={value:null,status:UNKNOWN,claim_ids:[],evidence_ids:[]}.
UNKNOWN бизнес-смысл требует Gap и partial, даже при известном техническом purpose.
Не реконструируй бизнес-сценарий в этом skill. Новый выход — 03-technical-flow.json.

Прочитай [общий контракт](../../knowledge-contracts/contract.md), [схему](../../knowledge-contracts/schemas/technical-flow.schema.json) и [процедуру](references/analysis.md).

Входы: принятый source-map и scenario scope; связанная knowledge.yaml, domain-tree и ScenarioDefinition нужны для ссылок и проверки границ. Все артефакты одной revision. Инструменты: code navigation, references/call hierarchy, repository/config search, test inspection. Не предполагай наличие IDE/MCP; используй доступные read-only инструменты.

Восстанови доказанный путь API → controller → command → pipeline → process → subprocess → rule → integration → state modification. Это ориентир поиска, не обязательные узлы: пропускай неприменимые уровни только с подтверждением; неизвестные оставляй Gap. Отдельно найди external calls, configuration reads, checks/branches, entity/state changes, callbacks/events.

Не пытайся объяснять бизнес-смысл неизвестного кода. Это задача следующего skill. purpose описывает техническую операцию, а не бизнес-цель; неизвестный purpose=null + Gap. Не выводи rationale из названий методов, guards или ошибок.

Выход technical-flow.json использует analysis_profile=execution-path-v1 и nodes с id, type, symbol, purpose, inputs, outputs, conditions, calls, state_changes, evidence; дополнительно configuration_reads, checks, external_calls, async_events, attribute_claims, unknown_fields, not_applicable_fields, gap_ids. nodes — единственная canonical коллекция технических узлов; каждый node также содержит component_id, source_ids и claim_ids. Поле steps запрещено. ID node имеет namespace technical-step: и соответствует registry entity типа SystemBehaviour; ScenarioStep и scenario steps принадлежат только 05-scenario. Actor не является полем технического узла: не определяй бизнес-актора для каждого класса, метода или вызова. Сохраняй связи в relations: каждый переход имеет отдельный claim, не только evidence узлов.

Каждое известное поле/элемент списка связано с точным subject/predicate/value claim и evidence из принятых source snapshots. Новые источники возвращай Source Discovery для relevance проверки перед включением. Пустой список означает unknown или evidence-backed not_applicable, а не автоматически отсутствие поведения. Unknown/unresolved пути требуют partial coverage и frontier.

Генерация: после исследования подготовь structured input с nodes и relations из уже доказанных фактов. Из корня репозитория сохрани validated output через canonical writer (он не исследует систему, не создаёт evidence и не переписывает IDs):
```text
python tools/knowledge/technical_flow.py --input <folder>/prepared-technical-flow.json --knowledge <folder>/knowledge.yaml --source-map <folder>/02-source-map.json --domain-tree <folder>/01-domain-map.yaml --scenario-definition <folder>/scenario-definition.yaml --previous-knowledge <previous>/knowledge.yaml --output <folder>/03-technical-flow.json
```
Не создавай вторую steps projection. Historical flows с steps требуют явной миграции структуры и согласованных refs; не переименовывай immutable KB IDs автоматически и не перезаписывай historical checkpoints. Существующий output writer сохраняет только при явном --overwrite.

Из корня репозитория проверь результат:
```text
python tools/knowledge/validate.py technical-flow <folder>/03-technical-flow.json --knowledge <folder>/knowledge.yaml --source-map <folder>/02-source-map.json --domain-tree <folder>/01-domain-map.yaml --scenario-definition <folder>/scenario-definition.yaml
```

Structural validation не доказывает semantic support. Проверь фрагменты вручную, передай technical-flow/source-map в Business Rule Extractor и Scenario Reconstructor, затем весь пакет в Evidence / Gap / Conflict Validator. Не публикуй и не меняй приложение.

## Optional runtime verification

Основной consumer **OpenSearch MCP**; purpose: production runtime verification;
invocation condition: unresolved material ambiguity after static analysis. Прочитай
[runtime evidence policy](../../knowledge-contracts/standards/runtime-evidence-policy.md).
Сначала заверши static possible flow; зафиксируй вопрос о ordering/branches/callback/config,
static_review_evidence_ids, гипотезы и различающие events. Используй lookup metadata Source
Discovery, затем bounded IDE MCP search напрямую. Минимум 3 independent complete SUCCESS
кейса одного environment/version/period; для critical/variable branches стремись к 5+.
ERROR cohort отдельно. Сохрани normalized shared RuntimeTrace и OPENSEARCH Evidence
со snapshot/hash в knowledge; technical-flow.runtime_confirmation_refs — IDs shared
runtime_confirmations. Static nodes/relations остаются прежними: observations отдельны.
Runtime snapshots не проходят static Source Map categories/relevance_path; проверяй
scenario scope, correlation и technical refs по runtime policy. Новые статические источники
по-прежнему возвращай Source Discovery. Traces совпали → OBSERVED, различаются → VARIABLE
+ RUNTIME_VARIABILITY; static mismatch → STATIC_RUNTIME_CONFLICT; один trace → sample Gap.
При unavailable MCP — NOT_CHECKED + RUNTIME_UNVERIFIED, продолжи static skill.
Не объявляй поведение универсальным и не выводи business meaning/rationale из логов.
