# Проверка сохранения смысла

До редактирования сопоставь draft с переданными structured inputs и Composer
manifest. Рассматривай уже сформированное знание; source verification и исправление
фактов принадлежат предыдущим стадиям. Для спорного draft/model mapping запиши
warning в review report с existing refs, не создавай новый claim. Не добавляй refs
в narrative и не исследуй источники. Reader-first отбор Composer уже выполнен:
не возвращай скрытые internal gaps, IDs, alias inventory или evidence dump.

Для каждого логического блока сравни:

| Проверяемое содержание | Что должно сохраниться |
|---|---|
| Сущность | stable Entity ID и различие объектов; замена лишь подтверждённого alias |
| Действие | субъект, условие, outcome, error и modality |
| Правило | condition, true/false result, affected step, threshold/operator, status |
| Сценарий | порядок отображения и исходные directed transitions, branches и states |
| Источники | refs и provenance в artifacts/manifest; только существующие читабельные источники в статье |
| Uncertainty | статусы включённых утверждений, publication-relevant вопросы и ограничения draft |
| Runtime | «наблюдалось»/«в исследованных случаях», независимая выборка и её контекст |
| Реализация | точные symbols/endpoints/config/events/processes, исходный порядок |

Каждое factual statement final семантически выводится из draft/validated model.
Входная модель не даёт разрешения добавить в документ ранее не изложенный факт.
Не делай implicit claim explicit без подтверждённого mapping. Не добавляй «обычно»,
«всегда», «как правило», новые причины, гарантии или outcome. Разделение предложения
не должно создавать новый causal claim. Объединение повторов не удаляет разные
contexts, provenance и статусы. При сомнении сохраняй исходное предложение и warning
AMBIGUOUS_SENTENCE вместо творческой правки.

Примеры границ:

- «После Import выполняется SAS» → «После Import выполняется скоринг», если
  подтверждён только SAS → скоринг. «После получения анкеты» допустимо лишь при
  подтверждённом соответствии Import именно этому действию, не из знания английского.
  «Система» допустима лишь при уже установленном actor; helper не добавляет её из догадки.
- ReadyForSign с UNKNOWN preferred_name, уже включённый в draft, остаётся с пометкой;
  «Готово к подписанию» не возникает. Скрытый alias не добавляется вместо нейтрального имени Composer.
- addressRecognitionAccuracy >= 7 сохраняет порог и сравнение. «Полностью распознан»
  добавляет интерпретацию и запрещено.
- «В 5 исследованных production traces ...» сохраняет число и ограничение наблюдения.
- «Источники расходятся по порядку X и Y» сохраняет CONFLICT; не выбирай X → Y.
- UNKNOWN business_rationale остаётся неподтверждённой причиной без объяснения «зачем».

Редакционное введение преобразуется без интерпретации бизнес-полей:

```text
Workflow: оформление договора ОСАГО
Область: расчёт стоимости и приём анкеты
Вне scope: оплата
```

```text
Документ описывает сценарий «оформление договора ОСАГО».
Область действия документа — расчёт стоимости и приём анкеты.
За пределами описания — оплата.
```

Эти соседние строки — один Markdown paragraph. Subject редакционных предложений —
документ, не придуманная система/actor. Текст после labels сохраняется, включая
UNKNOWN, предположение, conflict, число и контекст выборки. Не нормализуй такие
labels в fenced code, таблицах, цитатах, списках или техническом/evidence/gaps разделе.
Точное соседнее повторение редакционного предложения убирается только внутри
одного provenance блока; повтор действий и различающиеся ограничения сохраняются.

Подтверждённый alias `RegisterPolicyContractNSIS` в «Система выполняет …» может
замениться бизнес-термином, только если glossary доказывает exact identity mapping.
В technical implementation тот же symbol сохраняется byte-for-byte. Endpoints,
state/status names, comparisons/assignments и диагностические употребления остаются
защищёнными. Неизвестный symbol сохраняется с warning, без выдуманного перевода.

При языковой замене учитывай управление падежом. «После SAS» нельзя автоматически
превратить в «После скоринг». Helper сохраняет alias и LANGUAGE_FORM_NEEDS_REVIEW;
он не использует локальный словарь выдуманных предметных названий. Сокращение
«осуществляет выполнение скоринга» также не должно давать «выполняет скоринга».
Неподдержанные стилистические правки не обходят replay checker.

Непереведённые английские фрагменты в business prose видны в
UNTRANSLATED_BUSINESS_TEXT. Это языковая диагностика, не новый термин или
подтверждение бизнес-смысла; исходный текст и его ограничения сохраняются.

Оформление следует shared template. Не подменяй Language quality разработкой
Confluence layout. Не создавай Confluence renderer, API client или RAG exporter.

## Отчёт и остановка

В 09-language-review.yaml сохраняются input/standard hashes, final hash, исходный
publication gate, claim inventory и remapped manifest blocks. Review.changes
перечисляет подтверждённые replacements и их occurrences, reductions, simplified
sentences и resolved abbreviations. Warnings содержат type/value/section/text;
diagnostics объясняют blocking failures. Protected и semantic counters не являются
самостоятельной аттестацией: checker воспроизводит review по тем же inputs.

Новые claims, потеря critical content/gaps/status/ограничений, изменение сценария
или protected identifiers блокируют успех. Не пытайся исправить upstream facts.
Заменить FAILED/WAITING_FOR_REVIEW на COMPLETED вручную нельзя. Общая review
модель run сохраняется; новая classification знания не вводится.

Повторный запуск на final должен оставить текст неизменным. Для такой проверки
не передавай Composer manifest прежнего draft как manifest final: он описывает
другие bytes. Повторный запуск на оригинальных inputs воспроизводит report/final
без случайных timestamps и вариативного переписывания.

## Acceptance / fixtures

| Критерии | Проверка |
|---|---|
| AC-LANG-01/02/14/15 | confirmed preferred_name, aliases только при доказанном едином entity mapping |
| AC-LANG-03/13 | UNKNOWN не переводится; сокращение раскрыто только по glossary либо warning |
| AC-LANG-04/12/16 | technical symbols и traceability bytes неизменны, manifest lineage сохраняется |
| AC-LANG-05/06/07/10 | rule/state/order/content mutation отвергается replay checker |
| AC-LANG-08/09/17 | uncertainty, gaps, sample limitations сохраняются |
| AC-LANG-11/18 | business prose нормализована, сложные/неоднозначные места видны в warnings |
| AC-LANG-19/20 | текст идемпотентен, одинаковые inputs дают детерминированный результат |

Fixtures в tools/knowledge/tests/fixtures/language-review/ и contract tests
tools/knowledge/tests/test_language_review.py проверяют десять заданных cases:
business alias, UNKNOWN term, CONFLICT, runtime sample, threshold, exact symbol,
UNKNOWN rationale, INFERRED, glossary consistency и semantic diff. Дополнительно
проверяются missing/stale inputs, no source access, tampered reports, защищённые
evidence/material gaps и повторный review. Reader-first fixture reader-first.yaml
и regression tests дополнительно проверяют введение, hierarchy, scope/modality,
inline-code aliases, точные symbols, сохранение spans, повторные действия и Link2:
internal research gaps/IDs/provenance не возвращаются в reader sections. Проверки run/retry/invalidation — в
tools/knowledge/tests/test_orchestrate.py.