Профиль новых выходов — scoped-knowledge-v1. [Shared standards](../../../knowledge-contracts/standards/knowledge-model.md)
задают terminology, evidence, статусы, identity и checkpoints. Ниже описан существующий
алгоритм исследования; legacy scalar/projection поля не заменяют новые business representations.
В новом профиле inference хранится в claims, не Evidence; business_rationale — knowledge_value.

# Извлечение без придуманного бизнес-смысла

## Проход по источникам

1. Зафиксируй scope и ревизии knowledge/source-map/technical-flow; проверь входные ссылки. Начни с flow steps и accepted source IDs. Открой реальную реализацию и фрагмент, а не поисковый заголовок.
2. Найди if/switch/guards, validators, rules/extensions, branches процесса, literal/config thresholds, blocking checks, eligibility и calculations. Для каждого места выпиши точное условие, порядок проверки, единицы, numeric type, округление, null/default поведение и config overrides, если они влияют на результат и подтверждены. Не заполняй неизвестное.
3. Сохрани ветви отдельно. Для guard результат true может означать rejection, а не успех. Отсутствующий else не доказывает success; нужно проследить фактическое продолжение. switch cases могут стать несколькими rules, если имеют разные условия/эффекты; default не равен любой false branch без подтверждения.
4. Определи границу правила: одно условие и его подтверждённые эффекты в контексте. Составные условия не разделяй так, чтобы поменять short-circuit/order. Коллективное правило validators не превращай в независимые бизнес-правила только из-за числа методов.
5. Отдельно найди actor/scenario/state и externally_visible_result. Return/exception не доказывает HTTP/UI-ошибку: trace к mapper/endpoint/test обязателен. Unknown mapping → UNKNOWN + Gap. Caller/component не равен бизнес-актору.
6. Различай modality: implementation/configured/test_expectation/documented_requirement. Несогласованные условия/пороги/ветви в разных версиях сохраняются как Conflict; не усредняй и не выбирай Confluence автоматически.
7. Для business_rationale нужен отдельный прямой source claim об объяснении, например конкретный section Confluence или явный комментарий автора. Нельзя выводить причину из технического эффекта. Нет такого источника → UNKNOWN, даже при высокой confidence и работающем тесте.
8. Сохраняй вычисления как exact formula/алгоритм + применимость/условие + эффект на результат. Подтверди коэффициенты, units, rounding и bounds. Не создавай искусственную false branch для безусловного расчёта: она UNKNOWN либо evidence-backed not_applicable.
9. Проверь каждое фактическое поле по фрагменту и пометь supported только после сверки. Затем запусти validator, исправь ошибки и выдай partial, если остаётся unknown/conflict.

## Классификация

technical_constraint — техническая проверка без подтверждённого бизнес-смысла.
business_rule — правило с явно подтверждённой бизнес-формулировкой, независимо от известности причины.
eligibility — проверка допустимости с подтверждённым назначением; любая блокировка не становится eligibility автоматически.
calculation — подтверждённое вычисление, влияющее на результат; арифметика логирования сюда не относится.

Для business_rule/eligibility требуется classification claim с documented_requirement или source_statement и прямым первичным evidence о смысле. INFERENCE не допускается для business_rationale и классификации этих двух видов.

## Формат

Rule ID одновременно ссылается на BusinessRule entity общей KB; тип technical_constraint сохраняется в rule_kind, без утверждения о бизнес-назначении entity label.
attribute_claims связывает scalar по имени поля; списки — affected_actor/0, affected_scenario/0, affected_state/0, implementation/0, parameters/0. Claim subject_id равен rule ID, predicate — имя поля, value — значение. Для rule_kind тоже есть claim.
Unknown scalar — UNKNOWN; неизвестный список — [] и поле в unknown_fields. UNKNOWN rationale всегда unknown_fields + открытый unknown_reason Gap для rule ID.
not_applicable_fields не пересекается с unknown_fields; каждый неприменимый field имеет claim с predicate=not_applicable и value=имя поля. Это не маркер для недоступного знания.
Фактические значения разрешаются в KB: actor → Actor, scenario → Scenario, state → State, implementation → CodeComponent/ConfigRule/ApiOperation. Релевантность источника не доказывает поле автоматически.
evidence перечисляет используемые Evidence IDs. Поддержка полей должна присутствовать в этом списке; inferred evidence раскрывает basis claims до accepted snapshots.
Пустой rules допустим только с partial coverage или явно исследованными not_found категориями. Не выдумывай правило ради непустого файла.

## Проверочные случаи

- Числовой порог найден: exact condition и effects, rationale UNKNOWN.
- Guard возвращает ошибку, UI mapping неизвестен: externally_visible_result UNKNOWN.
- false branch не просмотрена: false_result UNKNOWN, не автоматический success.
- Test ожидает другой порог: Conflict, не «среднее» значение.
- Config flag имеет окружение/override: не обобщать одно окружение на остальные.
- Арифметика меняет result: calculation; арифметика только для логирования не включается.
- Page объясняет бизнес-причину явно: отдельный rationale claim с locator/version.
- Похожий validator из candidates без подтверждённого relevance path: не включать.
- Значение UNKNOWN не скрывается в prose «предположительно для предотвращения риска».

## Пример пользователя

BR-ADDR-IMPORT-001, accuracy < 7, rejection и QuestionnaireExternalFunctionsInvoker — иллюстрация требуемого формата. Не сохраняй эти значения как факты ОСАГО без чтения соответствующих sources. Пользовательский пример не является CODE/TEST evidence.
