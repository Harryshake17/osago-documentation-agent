# Синтетические glossary fixtures

Каждый каталог содержит `inputs.json` (current glossary, knowledge, 05 scenario, 06 validation),
ожидаемый `07-glossary-increment.yaml` и ожидаемый `glossary.yaml`.

| Fixture | Проверяемое поведение |
|---|---|
| confirmed | CODE alias SAS и source-stated CONFLUENCE term «скоринг» связываются через одну Entity |
| unknown | SomeEligibilityInvoker сохраняется как alias, preferred_name остаётся UNKNOWN |
| existing | TERM-NSIS переиспользуется, повторный запуск unchanged |
| conflict | Два CONFLUENCE названия одной Entity остаются CONFLICT / ANALYST_REVIEW |
| similar | Похожие business names разных Entity IDs не объединяются |

Фрагменты и source_checks синтетические: они проверяют контракт и не утверждают факты проекта ОСАГО.
В conflict producer уже сохранил общий Conflict; 06 оставляет его видимым и непроверенным.
Текущая comparison schema 06 не представляет CONFLUENCE↔CONFLUENCE review как отдельный comparison.

`test_glossary.py` строит аналогичные inputs для negative/invariant tests и сравнивает frozen fixtures
с результатом curate и merge. Tests не перезаписывают fixtures.

```text
python -X utf8 -m unittest discover -s tools/knowledge/tests -p test_glossary.py
```
