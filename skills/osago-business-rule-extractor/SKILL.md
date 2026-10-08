---
name: osago-business-rule-extractor
description: Извлечь проверяемые правила и технические ограничения ОСАГО API из technical-flow и source-map в business-rules.json. Неизвестную бизнес-причину сохранять как UNKNOWN.
---

# Business Rule Extractor

## Optional runtime examples

Прочитай [runtime evidence policy](../../knowledge-contracts/standards/runtime-evidence-policy.md).
Optional capability: **OpenSearch MCP**; purpose: production runtime verification;
invocation condition: unresolved material ambiguity after static analysis. Предпочитай
уже собранные Technical Flow RuntimeTrace. Rule.runtime_examples содержит shared Trace IDs
того же Scenario; это примеры наблюдаемого срабатывания, отдельно от condition/rationale.
Если необходим direct MCP lookup, применяй shared bounded sampling/correlation protocol
и передавай нормализованные Trace/Evidence/confirmation в Validator. Условие, threshold,
business classification и rationale подтверждаются прежними rule sources, не логами.
Нельзя создать business rule из runtime case или вывести его мотив. При unavailable MCP
сохрани RUNTIME_UNVERIFIED Gap, продолжая статическое извлечение правил.

Перед работой прочитай [shared knowledge model](../../knowledge-contracts/standards/knowledge-model.md),
[терминологию](../../knowledge-contracts/standards/terminology.md),
[evidence policy](../../knowledge-contracts/standards/evidence-policy.md) и
[границы/атомарность](../../knowledge-contracts/standards/domain-decomposition-rules.md).
Сущности получай из JSON/YAML входов, не из prose предыдущего skill. Перед передачей результата
сохрани checkpoint KB и согласованные upstream projections; проверь increment через
validate.py с --previous-knowledge <previous>/knowledge.yaml со второй стадии. При полном run запиши pipeline-run.json
и проверь все пять стадий командой tools/knowledge/pipeline.py из shared model.

Новые outputs и inputs используют model_profile=scoped-knowledge-v1. Каждое правило содержит
business_statement и technical_condition как knowledge_value; business_rationale становится
knowledge_value вместо legacy строки. technical_condition.value точно проецирует condition;
business_statement требует собственного source-stated claim, не копии rule_statement.
Отдельный business_rationale.value=null/status=UNKNOWN допустим при полностью известном condition.
technical_implementation сохраняет implementation_refs/technical_step_refs/source_ids с существующими IDs.
Unknown/CONFLICT не скрывай в положительной бизнес-формулировке. Новый выход — 04-business-rules.json.

Прочитай [общие contracts](../../knowledge-contracts/contract.md), [правила извлечения](references/extraction.md), [входной technical-flow](../../knowledge-contracts/schemas/technical-flow.schema.json) и [business-rules schema](../../knowledge-contracts/schemas/business-rules.schema.json). Используй shared schemas 1.0, не локальные типы старого osago-kb.

Вход: technical-flow, source-map и фиксированная revision knowledge.yaml. К source-map также нужны domain-tree и ScenarioDefinition для проверки его provenance. Если technical-flow уже есть в другой форме, приведи явно предоставленные факты к входному контракту с сохранением evidence. Отсутствующий flow не восстанавливай молча: сохрани missing input Gap, запроси вход и не объявляй извлечение завершённым. Skill 3 не считается реализованным этим skill.

Инструменты: read-only code, configuration, tests, Confluence. Исследуй accepted sources карты, открывая первичные фрагменты. Candidates не становятся источниками автоматически; новый источник возвращается Source Discovery для подтверждения релевантности и новой согласованной ревизии входов.

Обязательно исследуй guards (if/switch/guards), validators, rules/extensions, process branches, thresholds, configuration-driven behaviour, blocking checks, eligibility rules и calculations, влияющие на результат. Для каждой категории сохрани coverage. Поиск не требует выдумывать отсутствующее правило.

Каждое правило имеет rule_statement, condition, true_result, false_result, affected_actor, affected_scenario, affected_state, externally_visible_result, implementation и evidence. Поля утверждений и каждый элемент списков имеют attribute_claims. implementation — IDs конкретных CodeComponent/ConfigRule/ApiOperation, связанные с flow и evidence; не только свободное имя класса.

Если техническое условие подтверждено, но бизнес-смысл неизвестен:
```yaml
business_rationale:
  value: null
  status: UNKNOWN
  claim_ids: []
  evidence_ids: []
```
Создай unknown_reason Gap. Запрещено выводить rationale из имени, порога, поведения validator или собственной оценки риска. Техническую проверку сохраняй как technical_constraint; не повышай её до business_rule без подтверждения бизнес-смысла. Документированное правило может иметь UNKNOWN rationale: само правило и его причина — разные claims.

Нет подтверждения false branch, внешнего результата или актора → UNKNOWN/пустой список + Gap; не додумывай обратное действие или UI-ошибку. Неприменимость фиксируется отдельно с evidence. UNKNOWN — зарезервированный маркер, не claim о поведении.

Сохрани business-rules.json рядом с входными артефактами и knowledge.yaml. Проверка из корня репозитория:
```text
python tools/knowledge/validate.py business-rules <folder>/04-business-rules.json --knowledge <folder>/knowledge.yaml --technical-flow <folder>/03-technical-flow.json --source-map <folder>/02-source-map.json --domain-tree <folder>/01-domain-map.yaml --scenario-definition <folder>/scenario-definition.yaml
```
Зависимости — tools/knowledge/requirements.txt. Проверь смысл всех claims вручную; успешно проверенная схема не доказывает бизнес-логику. Выдай правила, evidence, unknown rationale, conflicts и покрытие. Не генерируй документацию и не публикуй результат.
