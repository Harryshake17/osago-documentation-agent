# Agent loop и persisted contracts

`orchestrate.py` запускает только контроль workflow. EXECUTE_SKILL — task envelope для
IDE-агента, не фиктивное утверждение «skill выполнен». Агент читает указанный SKILL.md,
выполняет его и возвращает реальные artifacts. Все schemas существующих outputs сохранены.
Новые schemas documentation-request/pipeline/run/stage-result описывают только control state.
Эти schemas не содержат новых Evidence, Claim, Terminology или KnowledgeStatus.

## Первый запуск

Из корня репозитория; CLI запускает агент, пользователь передаёт лишь название домена:

```text
python tools/knowledge/orchestrate.py init --domain "Новый бизнес eОСАГО Link2"
python tools/knowledge/orchestrate.py resume --run runs/<run_id>
python tools/knowledge/orchestrate.py start --run runs/<run_id> --node <ready-node>
python tools/knowledge/orchestrate.py finish --run runs/<run_id> --node <ready-node> --result <attempt>/result.yaml
```

Optional --request читает документационный request (domain, scope_hints, known_sources,
existing_document); допускается wrapper documentation_request. --runs-dir/--run-id сохраняют
папку, явно выбранную пользователем. --glossary копирует текущий validated glossary в
immutable run baseline; init без glossary использует empty_glossary существующего Curator.
Run не обновляет внешний global файл. Зависимости — tools/knowledge/requirements.txt (включая Markdown parser Renderer).
Standalone confluence-renderer-requirements.txt включает тот же набор.
`tools/knowledge/tests/test_orchestrate.py` запускается через unittest discover; остальные
shared contract tests проверяют совместимость с прежней архитектурой.

Пример persisted layout:

```text
runs/osago-20261001-<id>/
  run.yaml
  inputs/documentation-request.yaml
  inputs/glossary-baseline.yaml
  stages/domain-decomposition/attempt-0001/
    01-domain-map.yaml
    knowledge.yaml
    scenarios/<work-item>/01-domain-map.yaml
    scenarios/<work-item>/knowledge.yaml
    scenarios/<work-item>/scenario-definition.yaml
  stages/source-discovery@<work-item>/attempt-0001/...
  stages/technical-flow@<work-item>/attempt-0001/...
  stages/business-rules@<work-item>/attempt-0001/...
  stages/scenario-reconstruction@<work-item>/attempt-0001/...
  stages/evidence-validation@<work-item>/attempt-0001/validation-report.json
  stages/evidence-validation@<work-item>/attempt-0001/gaps.json
  stages/glossary@<work-item>/attempt-0001/07-glossary-increment.yaml
  stages/glossary@<work-item>/attempt-0001/glossary.yaml
  stages/documentation@<work-item>/attempt-0001/08-draft-document.md
  stages/documentation@<work-item>/attempt-0001/documentation-manifest.json
  stages/documentation@<work-item>/attempt-0001/08-draft-document.meta.yaml
  stages/language-review@<work-item>/attempt-0001/09-final-document.md
  stages/language-review@<work-item>/attempt-0001/09-language-review.yaml
```

Numbered names и sidecars соответствуют действующим conventions; попытки сохраняют историю,
run.yaml связывает все paths с run_id и фиксирует canonical content hashes JSON/YAML,
byte hashes Markdown, input fingerprints, dependencies, approvals, corrections и ошибки.
Не добавляй run_id в предметные schemas: provenance workflow хранится в artifact bindings.
Pipeline snapshot сохраняется в run.yaml, чтобы обновление skill не меняло порядок старого run.

## Domain producer и multi-Scenario domain

Domain task получает только Documentation Request и output_dir. Попроси профильный skill
сохранить общий domain map/KB и для каждого scoped Scenario подготовить отдельные
domain-tree/knowledge/ScenarioDefinition по **существующим** schemas. Отдельные scoped KB
имеют distinct package IDs: их revisions не являются ветками одного package. Повторно
используй Domain/Scenario Entity IDs и identity_key; source snapshots сохраняют идентичность.
В master knowledge.scope.scenarios перечислены все документируемые сценарии. Для одного
Scenario также нужны master scope и один scoped package; не копируй/переписывай KB сам.

Domain result.yaml (пути относительно конкретной attempt folder):

```yaml
artifacts:
  domain-tree: 01-domain-map.yaml
  knowledge: knowledge.yaml
work_items:
  - id: calculation
    scenario_id: <existing-Scenario-ID>
    domain_id: <existing-Domain-ID>
    artifacts:
      domain-tree: scenarios/calculation/01-domain-map.yaml
      knowledge: scenarios/calculation/knowledge.yaml
      scenario-definition: scenarios/calculation/scenario-definition.yaml
```

Domain producer решает границы/атомарность. Orchestrator проверяет ссылки, наличие всех
scoped Scenario packages и schema/invariants, не принимает Domain decision за него.
В новой ревизии scope unit IDs сохраняются для тех же Scenario. Снятые из scope units
архивируются в state как inactive; их files/attempts остаются. После принятия Domain
следует обязательный human checkpoint, даже если был один Scenario и нет gaps.

## Outputs стадий 2–9

Каждая task перечисляет точные inputs и outputs в pipeline.yaml. registry knowledge и
ScenarioDefinition — необходимые реальные sidecars, а не расширение business input scope.
Стадии 2–5 возвращают собственный artifact плюс согласованные KB/upstream projections
новой revision. Копирование/rebinding делается профильным skill; engine сравнивает
projection через существующий pipeline.projection и increment_errors, не правит facts.

Пример Source Discovery result:

```yaml
artifacts:
  domain-tree: 01-domain-map.yaml
  knowledge: knowledge.yaml
  scenario-definition: scenario-definition.yaml
  source-map: 02-source-map.json
```

Validator result содержит validation-report и gaps. `audit.py draft` недостаточен:
профильный Validator обязан завершить source/semantic review и `audit.py check`.
UNKNOWN/INFERRED/CONFLICT/partial и runtime gaps допустимы как reviewed unresolved knowledge,
но механические ошибки или незавершённый inventory блокируют завершение стадии.

Curator возвращает glossary-increment и run-local glossary; engine проверяет merge,
input hashes и existing glossary invariants. Следующий Scenario читает результат предыдущего
Curator; эта dependency явно добавляется в compiled graph. Документирование следующего
Scenario не меняет snapshots первого. Все articles относятся к одному workflow run.

Composer получает свой ограниченный набор, без Source Map/ScenarioDefinition (optional
sidecars у Composer). Engine проверяет manifest/input/glossary/report hashes, Markdown bytes
и YAML metadata; не вызывает renderer сам и не генерирует собственную прозу.

## Human checkpoint, correction и resume

Сначала покажи concrete review, затем дождись ответа. Не отправляй эти команды автоматически:

```text
python tools/knowledge/orchestrate.py review --run runs/<run_id> --node scope-review --decision APPROVE --response "Утверждаю этот scope"
python tools/knowledge/orchestrate.py review --run runs/<run_id> --node scope-review --decision CORRECT --response "Андеррайтинг вне scope" --target domain-decomposition
python tools/knowledge/orchestrate.py review --run runs/<run_id> --node evidence-review@calculation --decision CORRECT --response "<ответ человека>" --target business-rules@calculation
```

CORRECT сохраняется до выполнения owning skill. Task содержит pending correction IDs,
response и previous_outputs. Используй прежний accepted KB как baseline для сохранения
claims/evidence, дополни новую revision, обнови соответствующий structured artifact.
Result обязан содержать applied_review_ids; primary artifact или связанная KB должны
измениться по содержанию, а не только revision. Scope.exclusions хранится в прежней KB,
Domain Map ссылается на этот Scope ID.
Сам orchestrator не создаёт factual Evidence из ответа человека. Без подходящего source
статус остаётся UNKNOWN/INFERRED/CONFLICT, даже при человеческом approval ограничения.

Изменённые scope/evidence требуют review новых hashes. Старое approval не подтверждает
новую revision. Если человек согласен продолжить с unresolved gaps, APPROVE означает
принятие ограничений draft, publication gate остаётся blocked и gaps видимы в статье.
Human response хранится в structured workflow record; factual correction попадает в KB
через профильный skill, не только в chat context.

```text
python tools/knowledge/orchestrate.py fail --run runs/<run_id> --node technical-flow@calculation --error-type SkillFailure --message "<diagnostic>"
python tools/knowledge/orchestrate.py retry --run runs/<run_id> --node technical-flow@calculation
python tools/knowledge/orchestrate.py rerun --run runs/<run_id> --node source-discovery@calculation
```

Retry сохранит valid upstream и создаст новую attempt. Rerun инвалидирует только graph
descendants, включая dependent glossary snapshots других Scenario; их technical models
не пересчитываются без зависимости. FAILED не продолжается без явного retry. RUNNING
после interrupted session не вызывается повторно: закончить тот же attempt либо явно
fail Interrupted и retry. Редактирование accepted files вне protocol обнаруживается как
drift; producer становится STALE. Файлы не удаляются и не исправляются engine reasoning.

## Language Reviewer — финальный content stage

Authoritative declaration — pipeline.yaml: `documentation` → `language-review`.
Stage работает для каждой Scenario. task.inputs содержит draft, Composer manifest,
run-local glossary, Scenario, Validation, Technical Flow, Business Rules и glossary
increment; Source Map, code/config/tests, OpenSearch/Confluence/Jira/Git search запрещены.
Имена JSON/YAML входов сохраняются как в run: `05-scenario` и `validation-report`
являются существующими contracts, а не альтернативной моделью `06-validation`.
Отсутствующий обязательный input — failure без компенсирующего исследования.

Language Reviewer возвращает ровно два объявленных artifacts:

```yaml
artifacts:
  final-document: 09-final-document.md
  language-review: 09-language-review.yaml
```

`validator: language_review` вызывает `language_review.check_review` по текущим input
bindings. Проверяются schema, hashes, report completion и language/semantic invariants,
а не только самообъявленный положительный status. Повреждённый или незавершённый report,
изменённые protected content, новые claims и утрата uncertainty/gaps блокируют finish.
Report `FAILED` или `WAITING_FOR_REVIEW` фиксируется как неуспешная attempt через прежний
node/run `FAILED`; отдельный `NEEDS_REVIEW` state в workflow не вводится. После исправления
языка retry повторяет только Reviewer. Если проблема относится к knowledge, correction
передаётся владельцу upstream artifact; Reviewer не исправляет факты самостоятельно.

Composer и его draft/manifest остаются COMPLETED и неизменными при failure Reviewer.
Reviewer завершает content stage; новый run станет COMPLETED после принятого
Confluence Renderer каждой Scenario. Пользовательский
итог — `final-document`, review report прилагается. В results совместимый key
`documentation` указывает на тот же финал; `draft-document` сохраняет Composer draft
как вход и provenance.
Не публикуй страницу и не реализуй Confluence API: COMPLETED означает reviewed текст и проверенное Confluence representation
с сохранённым publication gate, а не разрешение публикации.

Rerun Composer/Curator/Scenario/Validation инвалидирует Reviewer по dependency graph;
reload продолжает ту же attempt/retry policy. Старые run.yaml используют свой сохранённый
pipeline snapshot; init нового run использует текущий canonical .codex pipeline, а .cursor
служит fallback только при его отсутствии. Добавление будущих stages по-прежнему выполняется
декларативно через pipeline config (--pipeline при init), без изменения stage order в engine.


## Confluence Renderer — финальный presentation stage

Canonical pipeline содержит декларативные узлы:

```text
08 documentation → 09 language-review → confluence-plan
    → presentation-review (human checkpoint) → confluence-render → COMPLETED
```

`confluence-plan` и `confluence-render` используют skill osago-confluence-renderer;
режим указан в task.presentation_mode. Это presentation layer: extraction/Scenario/
Technical Flow/Composer/Language Reviewer не меняются. Engine проверяет результаты,
но prose, presentation plan и representation создаёт профильный producer.

В plan task inputs ровно document, manifest, language-review. Metadata links/diagrams
получи из уже выбранных reviewed artifacts, без нового source research. Если diagram
metadata отсутствуют, а reviewed документ ссылается на диаграмму, не публикуй .mmd
именем/текстом: stage должен подготовить настоящую PNG или вернуть failure.
Скопируй только выбранные source/PNG assets в output_dir; пути sidecar относительны
этой папке, файлы остаются неизменными после принятия. Для отсутствующих assets
не искать код или другие источники знания. Metadata не вставлять в public body.

План и sidecar создаются локальным helper. `--metadata` — уже предоставленные
presentation metadata; `--asset-root` — output_dir с выбранными файлами. Если
metadata не нужны, пропусти --metadata: всё равно будет записан sidecar с asset_hashes.

```text
python tools/knowledge/confluence_render.py plan --document <task.inputs.document> --manifest <task.inputs.manifest> --language-review <task.inputs.language-review> --plan <output_dir>/presentation-plan.yaml --metadata <selected-metadata.yaml> --asset-root <output_dir> --output-dir <output_dir>
```

Профильный producer возвращает ровно:

```yaml
artifacts:
  presentation-plan: presentation-plan.yaml
  presentation-metadata: presentation-metadata.yaml
```

Оба artifacts проверяются shared schemas. План должен быть точным make_plan по
текущим reviewed inputs и иметь WAITING_FOR_REVIEW, а не самоподтверждённое approval.
Sidecar содержит hashes выбранных source/image assets; при resume они проверяются
повторно, даже если semantic validation уже есть в cache.

`presentation-review@<item>` показывает конкретную иерархию, порядок, technical
expand и выбранные diagrams. Дождись человеческого согласия (либо используй уже
данное конкретному плану согласие), затем сохрани ответ. Нельзя создавать fictitious
APPROVE или автоматически пропускать checkpoint. Пример команды после ответа:

```text
python tools/knowledge/orchestrate.py review --run runs/<run_id> --node presentation-review@link2 --decision APPROVE --response "<полученный ответ человека>"
```

Correction представления направляй `confluence-plan@<item>`. Producer применяет её,
возвращает applied_review_ids; после новой версии снова согласуется конкретный plan.
Knowledge correction передаётся прежнему владельцу knowledge; renderer не правит facts.

Render task получает document, manifest, language-review, presentation-plan,
presentation-metadata и hierarchy_approval: сохранённое APPROVE текущего checkpoint,
связанное с hashes обоих inputs. Не переутверждай и не редактируй accepted plan.
Скопируй его в output_dir/approved-presentation-plan.yaml; только эту локальную копию
обработай CLI approve --human-agreement на основании task.hierarchy_approval.
Затем выполняй render по copy plan и исходным immutable metadata/assets:

```text
python tools/knowledge/confluence_render.py approve --plan <output_dir>/approved-presentation-plan.yaml --human-agreement
python tools/knowledge/confluence_render.py render --document <task.inputs.document> --manifest <task.inputs.manifest> --language-review <task.inputs.language-review> --plan <output_dir>/approved-presentation-plan.yaml --metadata <task.inputs.presentation-metadata> --asset-root <parent-of-task.inputs.presentation-metadata> --output-dir <output_dir>
```

```yaml
artifacts:
  confluence-body: 10-confluence-body.storage.xhtml
  publisher-metadata: 10-publisher-metadata.yaml
```

Дополнительные attachments/*.png лежат в том же bundle. Engine проверяет точное
storage XHTML и publisher metadata against approved inputs, общий каталог body/
metadata и hashes attachments. Markdown/plain-text, fake COMPLETED report,
повышенный gate и отсутствующий attachment не принимаются. Publisher metadata
сохраняют private traceability и исходный publication gate; blocked остаётся blocked.

FAILED renderer блокирует COMPLETED run, оставляя Composer/Reviewer COMPLETED.
Retry повторяет только failed stage; незавершённый RUNNING продолжает ту же attempt
с presentation_mode и сохранённым hierarchy_approval. Изменение reviewed inputs,
plan, metadata или выбранных assets инвалидирует approval и downstream representation.
Изменение готового attachment инвалидирует render; согласование неизменного plan
сохраняется. Rerun Reviewer/Composer инвалидирует presentation graph декларативно.

Старые run.yaml сохраняют прежний pipeline snapshot, без скрытого добавления новых
stages на resume. Новый init использует расширенный default pipeline. Миграция
старого run требует отдельного явного изменения snapshot; helper не мигрирует его
самостоятельно. Content output по-прежнему 09-final-document.md; representation
и API publication разделены. Не вызывай publisher API в этом workflow.


## Обязательные gates при приёмке outputs

`stages[].gates` в pipeline.yaml перечисляет read-only gates. Они выполняются на
`finish` до ACCEPTED и повторно при проверке accepted bundles на resume. Новые
control stages, предметные schemas или knowledge statuses не вводятся.
Обязательные gates нельзя выключить пустым списком. Snapshot без этого поля
использует тот же safety floor по producer contract; DAG и artifacts не мигрируются.

| После producer | Gate | Проверяемый invariant |
| --- | --- | --- |
| Technical Flow | technical-model | Только nodes; уникальные technical-step IDs; shared schema и refs |
| Scenario | scenario-model | Один main Flow и selector; уникальные Scenario records; refs; technical node не является Scenario step |
| Validation | scenario-model + publication-relevance | Cross-artifact Scenario consistency; весь inventory сохранён; relevance reviewed, без UNASSESSED; publication_subset точен |
| Composer | document-structure | Один main section/table из main_flow; template order и row lineage; нет appended UC/happy path, internal research questions и raw reader paths/IDs |
| Language Reviewer | final-invariants | Обязательные sections; exact input/final/manifest hashes, Claim inventory, blocks и gate; видимые publication gaps/conflicts и contested versions |

Document gate использует Markdown parser и shared template, не LLM score.
Publication visibility проверяется по source_fields/derived_from, расположению
блока и сохранённым lexical anchors исходного question/claim после подтверждённых
терминологических display substitutions. Это воспроизводимая проверка известных
producer outputs, не доказательство произвольного пересказа. Если mapping нельзя
проверить, вернуть output producer; не переинтерпретировать вопрос или факт.
Raw locators разрешены по reader contract лишь в предназначенном technical/evidence
разделе. Человеческая подпись remote Confluence link не считается raw pageId dump;
локальный target в reader section не допускается. Internal research questions
не возвращаются даже в technical section. Полная inventory/provenance остаётся
в structured artifacts/manifest.

Reviewer task обязан получить accepted Composer manifest. Controller проверяет
финал с accepted Composer inputs, включая полный Validation gaps sidecar; этот
контекст не расширяет инструменты или inputs Language Reviewer. Прежний
`check_review` дополнительно контролирует детерминированный replay разрешённых
языковых замен и exact symbols; новые gates не меняют semantic logic Reviewer.

Failure возвращает FAILED с producer node/skill, gate и конкретным code/detail.
Примеры: COMPETING_COLLECTIONS, TECHNICAL_AS_SCENARIO, UNASSESSED,
APPENDED_PROCESS_COPY, MATERIAL_GAP_HIDDEN, FACTUAL_LINEAGE_LOST.
Schema failure при binding также содержит producer и его gates. Все outputs
failed attempt сохраняются без исправления; upstream COMPLETED не откатывается.
Downstream rendering/publication и COMPLETED запрещены до исправленного output
и явного retry. На resume ранее accepted, но нарушающий gate bundle сохраняет
FAILED/diagnostics; dependents становятся STALE, bytes не перезаписываются.
Нельзя заменить FAILED на COMPLETED, обнулить counters или чинить документ в engine.
