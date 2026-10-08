# Link2: canonical process regression fixture

Синтетический contract fixture, не реконструкция production Link2. Общая генерация не содержит этой последовательности или имён компонентов.

`05-scenario.json` содержит один main_flow (ID в реестре flows) с последовательностью calculate → import → payment → post-payment/policy issuance → status/document. `inputs.json` сохраняет upstream artifacts, knowledge, Claims, Evidence и provenance. `contract-source.txt` фиксирует синтетические границы групп.

12 technical nodes маппятся в 5 meaningful ScenarioSteps. Например, `FixturePostPaymentHandler.Handle`, `FixturePolicyIssuer.Issue` и `FixturePolicyRepository.Save` связаны refs с одним шагом «Выпустить полис после оплаты». Actor этого system step неприменим и явно подтверждён через not_applicable claim; actor Gap не создаётся.

Business-rule refs сохранены в import step. Coverage остаётся partial: fixture не утверждает полноту production alternatives/exceptions или бизнес-смысл upstream технических деталей.

`test_scenario.py` проверяет canonical selectors, порядок, many-to-one mapping, Rule/Evidence refs, неприменимость actor, запрет второго main/happy_path/UC и копирования technical node в Scenario.
