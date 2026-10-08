# Acceptance и границы проверки

Автоматические проверки: `tools/knowledge/tests/test_orchestrate.py` проверяет совместимость
с сохранённым девятиэтапным pipeline snapshot и использует synthetic
shared artifacts и producer doubles вместо реального IDE-агента. Validator, Curator и
Composer и Language Reviewer в этих тестах работают через существующие implementations. Production sources,
Confluence и OpenSearch не опрашиваются. Автотесты подтверждают контроль workflow и contracts;
они не подтверждают качество предметного анализа или автоматический выбор skill в IDE.
`test_orchestrate_confluence.py` проверяет расширенный canonical pipeline после принятой
Link2 boundary: upstream — fixture doubles; реальные Renderer, schemas и Run выполняют
plan/checkpoint/render/finish/resume/invalidation. Полный agent E2E остаётся ручным.

| AC | Покрытие автоматической проверкой |
|---|---|
| ORCH-01 | CLI init с одним domain выдаёт Domain task |
| ORCH-02 | Task loop выдаёт следующие skills без ручного выбора пользователя; сам IDE loop проверяется вручную |
| ORCH-03 | Historical snapshot: девять producers; canonical pipeline продолжает Reviewer presentation plan/checkpoint/render |
| ORCH-04 | Ограниченные task.inputs; Curator/Composer/Reviewer без Source Map и полного request |
| ORCH-05 | Scope approval обязателен; start downstream до него отклоняется |
| ORCH-06 | Чистый report пропускает review; UNKNOWN/CONFLICT блокируют downstream |
| ORCH-07 | Scope correction и evidence correction обновляют KB; response/applied artifacts переживают reload |
| ORCH-08 | Upstream drift и correction инвалидируют transitive dependents |
| ORCH-09 | Повторный resume completed run не добавляет attempts |
| ORCH-10 | Новая Run session восстанавливает тот же evidence checkpoint и RUNNING attempt |
| ORCH-11 | Failed Technical stage сохраняет Source bundle и partial attempt |
| ORCH-12 | Retry создаёт только следующую attempt failed stage |
| ORCH-13 | Rerun Rules сохраняет Domain/Source/Technical; glossary dependencies учитывают другие Scenario |
| ORCH-14 | Engine принимает artifacts producers; не исследует источники и не генерирует предметные outputs |
| ORCH-15 | Happy path работает при запрещённом network socket; helper не содержит connector execution |
| ORCH-16 | Каждый accepted bundle проверяется shared schemas; drift проверяется перед следующей task |
| ORCH-17 | Отсутствующий BusinessRule в Scenario блокирует запуск Validator |
| ORCH-18 | Все bindings находятся внутри одного run directory/run_id; path escape отклоняется |
| ORCH-19 | Дополнительный future stage добавляется через pipeline config без изменения dispatcher |
| ORCH-20 | Happy path завершается final-document/review report; multi-Scenario run содержит все финальные статьи |
| ORCH-21 | Failure Reviewer сохраняет COMPLETED Composer и блокирует run; retry запускает только Reviewer |
| ORCH-22 | Самообъявленный COMPLETED report не скрывает изменение protected content |
| ORCH-23 | Rerun Composer и drift финала инвалидируют Reviewer; новый session восстанавливает stage |
| ORCH-24 | Reviewer получает только current-run structured artifacts/glossary/standards; без source connectors |
| ORCH-25 | Renderer stage декларативен; plan/render получают только reviewed content и presentation inputs |
| ORCH-26 | Hierarchy checkpoint не пропускается; approval связан с обоими sidecars и принадлежит текущему Scenario |
| ORCH-27 | Fake preapproval, forged checkpoint, raw body и повышенный publication gate блокируют finish |
| ORCH-28 | Renderer failure сохраняет Composer/Reviewer; retry повторяет rendering |
| ORCH-29 | Reload RUNNING сохраняет mode, approval, directory и номер attempt |
| ORCH-30 | Selected asset drift инвалидирует plan/approval/render даже при cached validation |
| ORCH-31 | Attachment tamper инвалидирует render; approved неизменный plan сохраняется |
| ORCH-32 | Presentation correction делегируется plan producer и требует нового checkpoint |
| ORCH-33 | COMPLETED возвращает final-document, storage body и publisher metadata; repeated resume не добавляет attempts |

Дополнительные invariants: concurrent sessions не перезаписывают state; прерванный RUNNING
attempt не запускается второй раз; correction без содержательного изменения отклоняется;
циклы, undeclared inputs и замена обязательного checkpoint обычным skill запрещены.

## Ручной E2E в IDE

Требуют реального агента и доступны после установки/обнаружения нового skill:

1. **AC-01–04:** написать «Документируй домен Новый бизнес eОСАГО Link2». Проверить
   implicit activation, автоматическую передачу управления профильным skills и фактическое
   соблюдение inputs, а не только правильную task envelope.
2. **AC-05–07:** проверить отображение scope/evidence вопросов, реальное ожидание ответа,
   correction owning skill в KB/Domain Map и повторную валидацию. Agent не отправляет
   APPROVE от имени человека и не повышает factual status по одному approval.
3. **AC-10–13:** закрыть IDE на checkpoint/RUNNING, продолжить по run_id, выполнить
   retry и «Перезапусти с Source Discovery»; убедиться, что агент использует сохранённый run.
4. **AC-14–15:** на runtime ambiguity проверить, что OpenSearch вызывает профильный
   skill согласно своей policy; orchestration получает только результаты. Проверить,
   что новые domain claims создают профильные producers, а не control loop.
5. **AC-20:** проверить итоговые статьи реального домена, ссылки/provenance, terminology,
   unresolved gaps и короткий ответ пользователя. Итог — `09-final-document.md`,
   Canonical COMPLETED означает финальную редактуру и Confluence representation
   с сохранёнными ограничениями и publication gate.
   Проверь failure Reviewer: Composer остаётся COMPLETED, run не завершён, retry не
   повторяет предметное исследование. Публикация страницы остаётся отдельным шагом.

6. **ORCH-25–33:** после Reviewer проверь plan/task handoff, согласование исходной
   иерархии, отсутствие повторного вопроса для сохранённого согласия, реальные headings/
   tables/panels и attachments. При renderer failure Reviewer остаётся COMPLETED;
   restart/retry продолжают ту же Scenario. Страница сама не публикуется.

Результат ручного E2E не следует объявлять успешным по прохождению unit/contract tests.


## Gates regression

`tools/knowledge/tests/test_pipeline_gates.py` использует существующие validated
Link2 inputs, реальные Composer/Language Reviewer и read-only gates: Technical,
Scenario, Validation → Composer → Reviewer → final invariants. No source/network
access или synthetic LLM score. Fixtures upstream не перезаписываются.

Проверяются competing collections/IDs, main selectors/refs и namespaces,
publication relevance, порядок sections и rows, appended UC/table, private IDs/
locators, internal gaps, material question/conflict disappearance, forged hashes/
COMPLETED reports, сохранение provenance и исходного publication gate. Run tests
проверяют persisted failure, остановку canonical presentation graph, сохранение
upstream, Composer COMPLETED при failure Reviewer и диагностику на resume старого
некорректного output. Это механические contract tests, не новое fact verification.
