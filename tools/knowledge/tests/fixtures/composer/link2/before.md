# Технический идентификатор scenario:fixture [UNKNOWN — предметное название требует уточнения]

Draft для Language Reviewer; публикация не выполнялась.
Publication gate: **blocked**.

## 1. Назначение

Цель: Process fixture request — [claim:business\_goal](#claim-d87783e8006c5d4a)
Результат: fixture done — [claim:exit\_states](#claim-a6fc5d532fdd1252)
Начало: [UNKNOWN — предметные данные не предоставлены] — [claim:trigger](#claim-694fbbc472dc8c68)

## 2. Область действия

Сценарий: Технический идентификатор scenario:fixture [UNKNOWN — предметное название требует уточнения]
Ограничения scope: \["production"\]
Связанные сценарии и переиспользуемые возможности: [UNKNOWN — предметные данные не предоставлены]

## 3. Участники и системы

Участники: Технический идентификатор actor:fixture [UNKNOWN — предметное название требует уточнения] — [claim:actors](#claim-c4e6f3d899da2121)
Системы шага scenario-step:link2:calculate: Не применимо — [claim:link2:81](#claim-fe3f1c76df4df6d2)
Системы шага scenario-step:link2:import: Не применимо — [claim:link2:112](#claim-198a156e916460c0)
Системы шага scenario-step:link2:payment: Не применимо — [claim:link2:140](#claim-acfa887f2c1fc821)
Системы шага scenario-step:link2:issuance: Не применимо — [claim:link2:176](#claim-428ee426fd6e35ef)
Системы шага scenario-step:link2:status-document: Не применимо — [claim:link2:206](#claim-c9683249c6f912b7)

## 4. Предусловия и запуск сценария

Запуск: Технический идентификатор FixtureCommand [UNKNOWN — предметное название требует уточнения] — [claim:trigger](#claim-694fbbc472dc8c68)
Исходное состояние: fixture pending — [claim:entry\_state](#claim-9e7ec671981f0a3d)
Обязательные входы и дополнительные предусловия: [UNKNOWN — предметные данные не предоставлены]

## 5. Основной бизнес-процесс

Порядок строк — display order. Выполнение определяется доказанными переходами в разделе 7.
Основной поток scenario-flow:link2:main — [claim:link2:211](#claim-f5e5f7edf26365a0); вход: Выполнены условия синтетического основного сценария. — [claim:link2:212](#claim-a0ffe62af10d8ad3)

| Шаг | Кто | Что происходит | Правила | Интеграции | Результат |
| --- | --- | --- | --- | --- | --- |
| [scenario-step:link2:calculate](#implementation-9c4244ea013da709) | Технический идентификатор actor:fixture [UNKNOWN — предметное название требует уточнения] — [claim:link2:70](#claim-2acb3ad00b12164c) | Рассчитать стоимость оформления — [claim:link2:83](#claim-0096b79359b8f775) | Не применимо — [claim:link2:82](#claim-21577c13e4dfffaa) | Не применимо — [claim:link2:81](#claim-fe3f1c76df4df6d2) | Расчёт подготовлен. — [claim:link2:84](#claim-8088cbf07da8ff83) |
| [scenario-step:link2:import](#implementation-1d44685c84bbe372) | Технический идентификатор actor:fixture [UNKNOWN — предметное название требует уточнения] — [claim:link2:98](#claim-96dacbe4a9fa47cf) | Принять анкету для оформления — [claim:link2:113](#claim-5551df1194135346) | Технический идентификатор BR-FIXTURE-001 [UNKNOWN — предметное название требует уточнения] — [claim:link2:105](#claim-ace256abc5a80c75) | Не применимо — [claim:link2:112](#claim-198a156e916460c0) | Анкета принята. — [claim:link2:114](#claim-ed48ff101fb0541c) |
| [scenario-step:link2:payment](#implementation-2a8e436a3c51cc65) | Технический идентификатор actor:fixture [UNKNOWN — предметное название требует уточнения] — [claim:link2:129](#claim-3e9badd9c4f7e624) | Подтвердить оплату — [claim:link2:142](#claim-a82ca5d94eb23c06) | Не применимо — [claim:link2:141](#claim-eb849ec55f36937c) | Не применимо — [claim:link2:140](#claim-acfa887f2c1fc821) | Оплата подтверждена. — [claim:link2:143](#claim-e9b5fdfd8f95605a) |
| [scenario-step:link2:issuance](#implementation-d97c90c4cacd9950) | Не применимо — [claim:link2:177](#claim-9d4a67fd2cda91e3) | Выпустить полис после оплаты — [claim:link2:179](#claim-6849beb3404db193) | Не применимо — [claim:link2:178](#claim-0c77cdbabb867319) | Не применимо — [claim:link2:176](#claim-428ee426fd6e35ef) | Полис выпущен. — [claim:link2:180](#claim-81a7cb50c91c3688) |
| [scenario-step:link2:status-document](#implementation-fc8cdb7709d1432c) | Технический идентификатор actor:fixture [UNKNOWN — предметное название требует уточнения] — [claim:link2:195](#claim-c030843f971a5854) | Получить статус и документ — [claim:link2:208](#claim-745391c860f73b99) | Не применимо — [claim:link2:207](#claim-31c3be65a0903f7b) | Не применимо — [claim:link2:206](#claim-c9683249c6f912b7) | Статус и документ доступны. — [claim:link2:209](#claim-feed060787d60188) |

## 6. Бизнес-правила и точки принятия решений

### Технический идентификатор BR-FIXTURE-001 [UNKNOWN — предметное название требует уточнения]
- Правило: [UNKNOWN — предметные данные не предоставлены]
- Условие: [UNKNOWN — предметные данные не предоставлены] — [claim:rule:condition](#claim-b486cdf6559d5327)
- При выполнении: [UNKNOWN — предметные данные не предоставлены] — [claim:rule:true\_result](#claim-db74364c88fd1563)
- При невыполнении: [UNKNOWN — предметные данные не предоставлены] — [claim:rule:false\_result](#claim-17789db3ccf28909)
- Причина: [UNKNOWN — предметные данные не предоставлены]
- Шаги: \["scenario-step:link2:import"\]

## 7. Состояния и переходы

- Шаг scenario-step:link2:calculate: Технический идентификатор state:link2:initial [UNKNOWN — предметное название требует уточнения] — [claim:link2:74](#claim-ddb608dc12eb2fa4) → Технический идентификатор state:link2:calculate [UNKNOWN — предметное название требует уточнения] — [claim:link2:75](#claim-92ecae80d548463c); результат: Расчёт подготовлен. — [claim:link2:84](#claim-8088cbf07da8ff83)
- Шаг scenario-step:link2:import: Технический идентификатор state:link2:calculate [UNKNOWN — предметное название требует уточнения] — [claim:link2:102](#claim-be70770b45258c78) → Технический идентификатор state:link2:import [UNKNOWN — предметное название требует уточнения] — [claim:link2:103](#claim-76a96f06ca4281c0); результат: Анкета принята. — [claim:link2:114](#claim-ed48ff101fb0541c)
- Шаг scenario-step:link2:payment: Технический идентификатор state:link2:import [UNKNOWN — предметное название требует уточнения] — [claim:link2:133](#claim-316fc6d6fb1120c7) → Технический идентификатор state:link2:payment [UNKNOWN — предметное название требует уточнения] — [claim:link2:134](#claim-009e5bcd52f7f2d9); результат: Оплата подтверждена. — [claim:link2:143](#claim-e9b5fdfd8f95605a)
- Шаг scenario-step:link2:issuance: Технический идентификатор state:link2:payment [UNKNOWN — предметное название требует уточнения] — [claim:link2:167](#claim-263892879b62019e) → Технический идентификатор state:link2:issuance [UNKNOWN — предметное название требует уточнения] — [claim:link2:168](#claim-a0433e6f2e77cbe3); результат: Полис выпущен. — [claim:link2:180](#claim-81a7cb50c91c3688)
- Шаг scenario-step:link2:status-document: Технический идентификатор state:link2:issuance [UNKNOWN — предметное название требует уточнения] — [claim:link2:199](#claim-be496e096af7f25c) → Технический идентификатор state:link2:status-document [UNKNOWN — предметное название требует уточнения] — [claim:link2:200](#claim-f5f91633503fe259); результат: Статус и документ доступны. — [claim:link2:209](#claim-feed060787d60188)
- Состояние: Технический идентификатор state:link2:calculate [UNKNOWN — предметное название требует уточнения]; technical alias: \[\]
- Состояние: Технический идентификатор state:link2:import [UNKNOWN — предметное название требует уточнения]; technical alias: \[\]
- Состояние: Технический идентификатор state:link2:initial [UNKNOWN — предметное название требует уточнения]; technical alias: \[\]
- Состояние: Технический идентификатор state:link2:issuance [UNKNOWN — предметное название требует уточнения]; technical alias: \[\]
- Состояние: Технический идентификатор state:link2:payment [UNKNOWN — предметное название требует уточнения]; technical alias: \[\]
- Состояние: Технический идентификатор state:link2:status-document [UNKNOWN — предметное название требует уточнения]; technical alias: \[\]

### Доказанные переходы между шагами
- scenario-step:link2:calculate → scenario-step:link2:import; тип: precedes; [claim:link2:115](#claim-ee017e542a4372ed)
- scenario-step:link2:import → scenario-step:link2:payment; тип: precedes; [claim:link2:144](#claim-30ea14f7e58867e2)
- scenario-step:link2:payment → scenario-step:link2:issuance; тип: precedes; [claim:link2:181](#claim-d552ef13edf04c08)
- scenario-step:link2:issuance → scenario-step:link2:status-document; тип: precedes; [claim:link2:210](#claim-1a422370ddfeeb1e)

## 8. Альтернативные и ошибочные сценарии

### Альтернативный бизнес-поток
[UNKNOWN — предметные данные не предоставлены]
### Ошибочный поток — бизнесовая или техническая причина требует отдельного подтверждения
[UNKNOWN — предметные данные не предоставлены]
### Блокирующее бизнес-условие
[UNKNOWN — предметные данные не предоставлены]
### Техническая ошибка
[UNKNOWN — предметные данные не предоставлены]
### Неизвестный или конфликтный случай
См. раздел 12.

## 9. Интеграции

[UNKNOWN — предметные данные не предоставлены]

## 10. Техническая реализация

### Mapping бизнес-шаг → реализация
<a id="implementation-9c4244ea013da709"></a>
- scenario-step:link2:calculate → заявленные refs (metadata): {"implementation\_refs": \["component:link2:calculate:0", "component:link2:calculate:1"\], "source\_ids": \["source:handler"\], "technical\_step\_refs": \["technical-step:link2:calculate:0", "technical-step:link2:calculate:1"\]} — component:link2:calculate:0 — [claim:link2:77](#claim-fff09ade99137813); component:link2:calculate:1 — [claim:link2:78](#claim-bea9f81461209da7)
- Техническое действие: Рассчитать стоимость оформления — [claim:link2:71](#claim-1de6d1d3bf71883e); поведение: Система: Расчёт подготовлен. — [claim:link2:73](#claim-52040b933352dbd3)
<a id="implementation-1d44685c84bbe372"></a>
- scenario-step:link2:import → заявленные refs (metadata): {"implementation\_refs": \["FixtureHandler.Handle", "component:link2:import:1", "component:link2:import:2"\], "source\_ids": \["source:handler"\], "technical\_step\_refs": \["technical-step:guard", "technical-step:link2:import:1", "technical-step:link2:import:2"\]} — FixtureHandler.Handle — [claim:link2:106](#claim-32137785de278088); component:link2:import:1 — [claim:link2:107](#claim-dca7b6c2ff27949e); component:link2:import:2 — [claim:link2:108](#claim-1e6932a288524016)
- Техническое действие: Принять анкету для оформления — [claim:link2:99](#claim-9ed873fb8e903b12); поведение: Система: Анкета принята. — [claim:link2:101](#claim-3c642b4448abc373)
<a id="implementation-2a8e436a3c51cc65"></a>
- scenario-step:link2:payment → заявленные refs (metadata): {"implementation\_refs": \["component:link2:payment:0", "component:link2:payment:1"\], "source\_ids": \["source:handler"\], "technical\_step\_refs": \["technical-step:link2:payment:0", "technical-step:link2:payment:1"\]} — component:link2:payment:0 — [claim:link2:136](#claim-f5b23ad28eb96804); component:link2:payment:1 — [claim:link2:137](#claim-f999297b8ffe7b56)
- Техническое действие: Подтвердить оплату — [claim:link2:130](#claim-f14812a45f8489b6); поведение: Система: Оплата подтверждена. — [claim:link2:132](#claim-12b3ac05e846e53d)
<a id="implementation-d97c90c4cacd9950"></a>
- scenario-step:link2:issuance → заявленные refs (metadata): {"implementation\_refs": \["component:link2:issuance:0", "component:link2:issuance:1", "component:link2:issuance:2"\], "source\_ids": \["source:handler"\], "technical\_step\_refs": \["technical-step:link2:issuance:0", "technical-step:link2:issuance:1", "technical-step:link2:issuance:2"\]} — component:link2:issuance:0 — [claim:link2:170](#claim-b4968cfc9ce2923d); component:link2:issuance:1 — [claim:link2:171](#claim-d6aa093e1de18e32); component:link2:issuance:2 — [claim:link2:172](#claim-5ab6d96f0048ab4a)
- Техническое действие: Выпустить полис после оплаты — [claim:link2:164](#claim-192a37d6d09f4de3); поведение: Система: Полис выпущен. — [claim:link2:166](#claim-72f108e56fd1f6b1)
<a id="implementation-fc8cdb7709d1432c"></a>
- scenario-step:link2:status-document → заявленные refs (metadata): {"implementation\_refs": \["component:link2:status-document:0", "component:link2:status-document:1"\], "source\_ids": \["source:handler"\], "technical\_step\_refs": \["technical-step:link2:status-document:0", "technical-step:link2:status-document:1"\]} — component:link2:status-document:0 — [claim:link2:202](#claim-da5df457d4750ac2); component:link2:status-document:1 — [claim:link2:203](#claim-62470629858b3580)
- Техническое действие: Получить статус и документ — [claim:link2:196](#claim-9c698be6e82c24b2); поведение: Система: Статус и документ доступны. — [claim:link2:198](#claim-758567e19057fc0c)
### technical-step:guard
- type: rule — [claim:technical:type](#claim-d5f918c81eb338c4)
- symbol: FixtureHandler.Handle — [claim:technical:symbol](#claim-25c41d33dfe62cf4)
- purpose: Return a value after checking fixture accuracy. — [claim:technical:purpose](#claim-953381d15920c005)
- inputs: command — [claim:technical:inputs/0](#claim-be6f72ababd97bde); accuracy — [claim:technical:inputs/1](#claim-48076ce9fbe1165e)
- outputs: 0 or 1 — [claim:technical:outputs/0](#claim-81cb23699bd702c4)
- conditions: accuracy &lt; 7 — [claim:technical:conditions/0](#claim-f23ad11258aa5625)
- calls: [UNKNOWN — предметные данные не предоставлены]
- state_changes: [UNKNOWN — предметные данные не предоставлены]
- configuration_reads: [UNKNOWN — предметные данные не предоставлены]
- checks: accuracy &lt; 7 — [claim:technical:checks/0](#claim-5e28bc6bbc131ae9)
- external_calls: [UNKNOWN — предметные данные не предоставлены]
- async_events: [UNKNOWN — предметные данные не предоставлены]
### technical-step:link2:calculate:0
- type: process — [claim:link2:57](#claim-fb1e5e7352f51ca2)
- symbol: FixtureCalculateController.Calculate — [claim:link2:58](#claim-11fc4a8d95111411)
- purpose: Perform the synthetic calculate operation. — [claim:link2:59](#claim-3e77a85b9ac7d40e)
- inputs: synthetic request — [claim:link2:60](#claim-025142c1140fd015)
- outputs: synthetic result — [claim:link2:61](#claim-f3dfcacf1dacf62f)
- conditions: [UNKNOWN — предметные данные не предоставлены]
- calls: [UNKNOWN — предметные данные не предоставлены]
- state_changes: [UNKNOWN — предметные данные не предоставлены]
- configuration_reads: [UNKNOWN — предметные данные не предоставлены]
- checks: [UNKNOWN — предметные данные не предоставлены]
- external_calls: [UNKNOWN — предметные данные не предоставлены]
- async_events: [UNKNOWN — предметные данные не предоставлены]
### technical-step:link2:calculate:1
- type: process — [claim:link2:63](#claim-1d273bd75283252f)
- symbol: FixtureCalculateHandler.Handle — [claim:link2:64](#claim-8239e6b84d36aee9)
- purpose: Perform the synthetic calculate operation. — [claim:link2:65](#claim-939985fdafc43c7b)
- inputs: synthetic request — [claim:link2:66](#claim-d00e3120317d6e44)
- outputs: synthetic result — [claim:link2:67](#claim-4b58173f41a31276)
- conditions: [UNKNOWN — предметные данные не предоставлены]
- calls: [UNKNOWN — предметные данные не предоставлены]
- state_changes: [UNKNOWN — предметные данные не предоставлены]
- configuration_reads: [UNKNOWN — предметные данные не предоставлены]
- checks: [UNKNOWN — предметные данные не предоставлены]
- external_calls: [UNKNOWN — предметные данные не предоставлены]
- async_events: [UNKNOWN — предметные данные не предоставлены]
### technical-step:link2:import:1
- type: process — [claim:link2:85](#claim-ee7de307e21cf090)
- symbol: FixtureImportMapper.Map — [claim:link2:86](#claim-819937e7b0eea3b1)
- purpose: Perform the synthetic import operation. — [claim:link2:87](#claim-9c9d2cc6901c4582)
- inputs: synthetic request — [claim:link2:88](#claim-c6a5f71fb0e5b501)
- outputs: synthetic result — [claim:link2:89](#claim-c78229e50c5444a1)
- conditions: [UNKNOWN — предметные данные не предоставлены]
- calls: [UNKNOWN — предметные данные не предоставлены]
- state_changes: [UNKNOWN — предметные данные не предоставлены]
- configuration_reads: [UNKNOWN — предметные данные не предоставлены]
- checks: [UNKNOWN — предметные данные не предоставлены]
- external_calls: [UNKNOWN — предметные данные не предоставлены]
- async_events: [UNKNOWN — предметные данные не предоставлены]
### technical-step:link2:import:2
- type: process — [claim:link2:91](#claim-21c524f1e2799eb6)
- symbol: FixtureImportRepository.Save — [claim:link2:92](#claim-12b816c1a65fd288)
- purpose: Perform the synthetic import operation. — [claim:link2:93](#claim-6bbe41867e194176)
- inputs: synthetic request — [claim:link2:94](#claim-308f3f487739b380)
- outputs: synthetic result — [claim:link2:95](#claim-aefaeed87af60089)
- conditions: [UNKNOWN — предметные данные не предоставлены]
- calls: [UNKNOWN — предметные данные не предоставлены]
- state_changes: [UNKNOWN — предметные данные не предоставлены]
- configuration_reads: [UNKNOWN — предметные данные не предоставлены]
- checks: [UNKNOWN — предметные данные не предоставлены]
- external_calls: [UNKNOWN — предметные данные не предоставлены]
- async_events: [UNKNOWN — предметные данные не предоставлены]
### technical-step:link2:payment:0
- type: process — [claim:link2:116](#claim-e8b7055f100e57ff)
- symbol: FixturePaymentController.Confirm — [claim:link2:117](#claim-c179bbbb086d0c3c)
- purpose: Perform the synthetic payment operation. — [claim:link2:118](#claim-0ea30ee6401875ca)
- inputs: synthetic request — [claim:link2:119](#claim-6407fedc8850f92d)
- outputs: synthetic result — [claim:link2:120](#claim-acecbcdd6b0e5e65)
- conditions: [UNKNOWN — предметные данные не предоставлены]
- calls: [UNKNOWN — предметные данные не предоставлены]
- state_changes: [UNKNOWN — предметные данные не предоставлены]
- configuration_reads: [UNKNOWN — предметные данные не предоставлены]
- checks: [UNKNOWN — предметные данные не предоставлены]
- external_calls: [UNKNOWN — предметные данные не предоставлены]
- async_events: [UNKNOWN — предметные данные не предоставлены]
### technical-step:link2:payment:1
- type: process — [claim:link2:122](#claim-1fa93941df9b8afb)
- symbol: FixturePaymentHandler.Handle — [claim:link2:123](#claim-96b8944c57d8d9d7)
- purpose: Perform the synthetic payment operation. — [claim:link2:124](#claim-5f220a40eb36fc1b)
- inputs: synthetic request — [claim:link2:125](#claim-f5a29ef34321cb25)
- outputs: synthetic result — [claim:link2:126](#claim-30e3bd54984853e6)
- conditions: [UNKNOWN — предметные данные не предоставлены]
- calls: [UNKNOWN — предметные данные не предоставлены]
- state_changes: [UNKNOWN — предметные данные не предоставлены]
- configuration_reads: [UNKNOWN — предметные данные не предоставлены]
- checks: [UNKNOWN — предметные данные не предоставлены]
- external_calls: [UNKNOWN — предметные данные не предоставлены]
- async_events: [UNKNOWN — предметные данные не предоставлены]
### technical-step:link2:issuance:0
- type: process — [claim:link2:145](#claim-4134f2e8fe3723b3)
- symbol: FixturePostPaymentHandler.Handle — [claim:link2:146](#claim-7fd9d32cbf96e1a7)
- purpose: Perform the synthetic issuance operation. — [claim:link2:147](#claim-4a3e56a3125bb99b)
- inputs: synthetic request — [claim:link2:148](#claim-07ab6f077282ad82)
- outputs: synthetic result — [claim:link2:149](#claim-d7bd20047085ed70)
- conditions: [UNKNOWN — предметные данные не предоставлены]
- calls: [UNKNOWN — предметные данные не предоставлены]
- state_changes: [UNKNOWN — предметные данные не предоставлены]
- configuration_reads: [UNKNOWN — предметные данные не предоставлены]
- checks: [UNKNOWN — предметные данные не предоставлены]
- external_calls: [UNKNOWN — предметные данные не предоставлены]
- async_events: [UNKNOWN — предметные данные не предоставлены]
### technical-step:link2:issuance:1
- type: process — [claim:link2:151](#claim-70868e67f6175ba3)
- symbol: FixturePolicyIssuer.Issue — [claim:link2:152](#claim-18c6388a449d4f29)
- purpose: Perform the synthetic issuance operation. — [claim:link2:153](#claim-ffb94cc8cf5eff70)
- inputs: synthetic request — [claim:link2:154](#claim-ae7d237575f6537a)
- outputs: synthetic result — [claim:link2:155](#claim-4b935e1453f66f8c)
- conditions: [UNKNOWN — предметные данные не предоставлены]
- calls: [UNKNOWN — предметные данные не предоставлены]
- state_changes: [UNKNOWN — предметные данные не предоставлены]
- configuration_reads: [UNKNOWN — предметные данные не предоставлены]
- checks: [UNKNOWN — предметные данные не предоставлены]
- external_calls: [UNKNOWN — предметные данные не предоставлены]
- async_events: [UNKNOWN — предметные данные не предоставлены]
### technical-step:link2:issuance:2
- type: process — [claim:link2:157](#claim-f88615fdcf36befa)
- symbol: FixturePolicyRepository.Save — [claim:link2:158](#claim-40a1e47477cc8143)
- purpose: Perform the synthetic issuance operation. — [claim:link2:159](#claim-566eb20a362009f5)
- inputs: synthetic request — [claim:link2:160](#claim-5a8dd69d7ef50a86)
- outputs: synthetic result — [claim:link2:161](#claim-57cafd9be84e900c)
- conditions: [UNKNOWN — предметные данные не предоставлены]
- calls: [UNKNOWN — предметные данные не предоставлены]
- state_changes: [UNKNOWN — предметные данные не предоставлены]
- configuration_reads: [UNKNOWN — предметные данные не предоставлены]
- checks: [UNKNOWN — предметные данные не предоставлены]
- external_calls: [UNKNOWN — предметные данные не предоставлены]
- async_events: [UNKNOWN — предметные данные не предоставлены]
### technical-step:link2:status-document:0
- type: process — [claim:link2:182](#claim-8a31a242172d80a3)
- symbol: FixtureStatusHandler.Read — [claim:link2:183](#claim-8effbb5c9e8cb9fb)
- purpose: Perform the synthetic status-document operation. — [claim:link2:184](#claim-49dbe00ff932a572)
- inputs: synthetic request — [claim:link2:185](#claim-d0a0d3ed6226ddb0)
- outputs: synthetic result — [claim:link2:186](#claim-7cb75b632a497654)
- conditions: [UNKNOWN — предметные данные не предоставлены]
- calls: [UNKNOWN — предметные данные не предоставлены]
- state_changes: [UNKNOWN — предметные данные не предоставлены]
- configuration_reads: [UNKNOWN — предметные данные не предоставлены]
- checks: [UNKNOWN — предметные данные не предоставлены]
- external_calls: [UNKNOWN — предметные данные не предоставлены]
- async_events: [UNKNOWN — предметные данные не предоставлены]
### technical-step:link2:status-document:1
- type: process — [claim:link2:188](#claim-442945a15aaa201f)
- symbol: FixtureDocumentHandler.Read — [claim:link2:189](#claim-35e43924399fea47)
- purpose: Perform the synthetic status-document operation. — [claim:link2:190](#claim-3b4afadb57bec4e7)
- inputs: synthetic request — [claim:link2:191](#claim-0b47bed9286fd8f8)
- outputs: synthetic result — [claim:link2:192](#claim-8d21f4db1291a0d5)
- conditions: [UNKNOWN — предметные данные не предоставлены]
- calls: [UNKNOWN — предметные данные не предоставлены]
- state_changes: [UNKNOWN — предметные данные не предоставлены]
- configuration_reads: [UNKNOWN — предметные данные не предоставлены]
- checks: [UNKNOWN — предметные данные не предоставлены]
- external_calls: [UNKNOWN — предметные данные не предоставлены]
- async_events: [UNKNOWN — предметные данные не предоставлены]
- Implementation mapping technical-step:guard / FixtureHandler.Handle — [claim:flow-implementation](#claim-a65f71b909b84fb8); [claim:technical:type](#claim-d5f918c81eb338c4); [claim:technical:symbol](#claim-25c41d33dfe62cf4); [claim:technical:purpose](#claim-953381d15920c005); [claim:technical:inputs/0](#claim-be6f72ababd97bde); [claim:technical:inputs/1](#claim-48076ce9fbe1165e); [claim:technical:outputs/0](#claim-81cb23699bd702c4); [claim:technical:conditions/0](#claim-f23ad11258aa5625); [claim:technical:checks/0](#claim-5e28bc6bbc131ae9)
- Implementation mapping technical-step:link2:calculate:0 / component:link2:calculate:0 — [claim:link2:62](#claim-9473f186645c10e3); [claim:link2:57](#claim-fb1e5e7352f51ca2); [claim:link2:58](#claim-11fc4a8d95111411); [claim:link2:59](#claim-3e77a85b9ac7d40e); [claim:link2:60](#claim-025142c1140fd015); [claim:link2:61](#claim-f3dfcacf1dacf62f)
- Implementation mapping technical-step:link2:calculate:1 / component:link2:calculate:1 — [claim:link2:68](#claim-39f0c0e13a1694b1); [claim:link2:63](#claim-1d273bd75283252f); [claim:link2:64](#claim-8239e6b84d36aee9); [claim:link2:65](#claim-939985fdafc43c7b); [claim:link2:66](#claim-d00e3120317d6e44); [claim:link2:67](#claim-4b58173f41a31276)
- Implementation mapping technical-step:link2:import:1 / component:link2:import:1 — [claim:link2:90](#claim-4bde106a65a4d187); [claim:link2:85](#claim-ee7de307e21cf090); [claim:link2:86](#claim-819937e7b0eea3b1); [claim:link2:87](#claim-9c9d2cc6901c4582); [claim:link2:88](#claim-c6a5f71fb0e5b501); [claim:link2:89](#claim-c78229e50c5444a1)
- Implementation mapping technical-step:link2:import:2 / component:link2:import:2 — [claim:link2:96](#claim-c2ece3911290f14b); [claim:link2:91](#claim-21c524f1e2799eb6); [claim:link2:92](#claim-12b816c1a65fd288); [claim:link2:93](#claim-6bbe41867e194176); [claim:link2:94](#claim-308f3f487739b380); [claim:link2:95](#claim-aefaeed87af60089)
- Implementation mapping technical-step:link2:payment:0 / component:link2:payment:0 — [claim:link2:121](#claim-7d95ab676b77bc70); [claim:link2:116](#claim-e8b7055f100e57ff); [claim:link2:117](#claim-c179bbbb086d0c3c); [claim:link2:118](#claim-0ea30ee6401875ca); [claim:link2:119](#claim-6407fedc8850f92d); [claim:link2:120](#claim-acecbcdd6b0e5e65)
- Implementation mapping technical-step:link2:payment:1 / component:link2:payment:1 — [claim:link2:127](#claim-ea17bf2df3bfc243); [claim:link2:122](#claim-1fa93941df9b8afb); [claim:link2:123](#claim-96b8944c57d8d9d7); [claim:link2:124](#claim-5f220a40eb36fc1b); [claim:link2:125](#claim-f5a29ef34321cb25); [claim:link2:126](#claim-30e3bd54984853e6)
- Implementation mapping technical-step:link2:issuance:0 / component:link2:issuance:0 — [claim:link2:150](#claim-56766367790c7f2b); [claim:link2:145](#claim-4134f2e8fe3723b3); [claim:link2:146](#claim-7fd9d32cbf96e1a7); [claim:link2:147](#claim-4a3e56a3125bb99b); [claim:link2:148](#claim-07ab6f077282ad82); [claim:link2:149](#claim-d7bd20047085ed70)
- Implementation mapping technical-step:link2:issuance:1 / component:link2:issuance:1 — [claim:link2:156](#claim-20ed4fdbec50f56f); [claim:link2:151](#claim-70868e67f6175ba3); [claim:link2:152](#claim-18c6388a449d4f29); [claim:link2:153](#claim-ffb94cc8cf5eff70); [claim:link2:154](#claim-ae7d237575f6537a); [claim:link2:155](#claim-4b935e1453f66f8c)
- Implementation mapping technical-step:link2:issuance:2 / component:link2:issuance:2 — [claim:link2:162](#claim-11dc1ae1304144e8); [claim:link2:157](#claim-f88615fdcf36befa); [claim:link2:158](#claim-40a1e47477cc8143); [claim:link2:159](#claim-566eb20a362009f5); [claim:link2:160](#claim-5a8dd69d7ef50a86); [claim:link2:161](#claim-57cafd9be84e900c)
- Implementation mapping technical-step:link2:status-document:0 / component:link2:status-document:0 — [claim:link2:187](#claim-88682e4d649c6c10); [claim:link2:182](#claim-8a31a242172d80a3); [claim:link2:183](#claim-8effbb5c9e8cb9fb); [claim:link2:184](#claim-49dbe00ff932a572); [claim:link2:185](#claim-d0a0d3ed6226ddb0); [claim:link2:186](#claim-7cb75b632a497654)
- Implementation mapping technical-step:link2:status-document:1 / component:link2:status-document:1 — [claim:link2:193](#claim-9a85bb774ff797e6); [claim:link2:188](#claim-442945a15aaa201f); [claim:link2:189](#claim-35e43924399fea47); [claim:link2:190](#claim-3b4afadb57bec4e7); [claim:link2:191](#claim-0b47bed9286fd8f8); [claim:link2:192](#claim-8d21f4db1291a0d5)
- BR-FIXTURE-001; technical condition: accuracy &lt; 7 — [claim:rule:condition](#claim-b486cdf6559d5327); rule statement: Return 0 when fixture accuracy is below 7. — [claim:rule:rule\_statement](#claim-615aa51279a80c8c)
Scope/revisions (metadata): {"components": \["fixture"\], "environments": \["test"\], "exclusions": \["production"\], "id": "scope:fixture", "repositories": \["fixture"\], "revisions": {"fixture": "fixture-v1"}, "scenarios": \["scenario:fixture"\], "time\_range": null, "unresolved\_constraints": \[\]}

## 11. Источники и доказательства

### Claims и классификации
<a id="claim-c4e6f3d899da2121"></a>
- claim:actors **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic: scenario:fixture actors actor:fixture»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-836c538be6ad500c"></a>
- claim:anchor **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic: scenario:fixture entry\_point FixtureCommand»; modality=discovery; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-d87783e8006c5d4a"></a>
- claim:business\_goal **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic: scenario:fixture business\_goal Process fixture request»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-ffc7774c867b4c9f"></a>
- claim:edge **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic: FixtureCommand registered\_handler FixtureHandler.Handle»; modality=discovery; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-5aca52197ce0ad5a"></a>
- claim:edge:0 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic: rule\_branch scenario-step:return-one»; modality=implemented; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-27ad3e5d413ff2ba"></a>
- claim:edge:0:condition **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic: branch\_condition {'rule\_id': 'BR-FIXTURE-001', 'outcome': 'false', 'condition': 'accuracy &gt;= 7'}»; modality=implemented; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-163d3001c7faf4e9"></a>
- claim:edge:1 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic: rule\_branch scenario-step:return-zero»; modality=implemented; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-28278b8062aaae28"></a>
- claim:edge:1:condition **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic: branch\_condition {'rule\_id': 'BR-FIXTURE-001', 'outcome': 'true', 'condition': 'accuracy &lt; 7'}»; modality=implemented; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-9e7ec671981f0a3d"></a>
- claim:entry\_state **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic: scenario:fixture entry\_state fixture pending»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-a6fc5d532fdd1252"></a>
- claim:exit\_states **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic: scenario:fixture exit\_states fixture done»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-75c8afb43e326571"></a>
- claim:expected\_outcomes **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic: scenario:fixture expected\_outcomes fixture done»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-a65f71b909b84fb8"></a>
- claim:flow-implementation **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic: implementation FixtureHandler.Handle»; modality=implemented; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-dc75dce0d05274f6"></a>
- claim:flow:alternative **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic: flow\_condition accuracy &lt; 7»; modality=implemented; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-f97a79481204fd47"></a>
- claim:flow:alternative:type **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic: flow\_type {'flow\_id': 'scenario-flow:alternative', 'type': 'alternative'}»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-a1652c40e02449ac"></a>
- claim:flow:main **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic: flow\_condition accuracy &gt;= 7»; modality=implemented; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-c224f69493e729e1"></a>
- claim:flow:main:type **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic: flow\_type {'flow\_id': 'scenario-flow:main', 'type': 'main'}»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-97bd7a40a80ffec9"></a>
- claim:link2:100 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: business\_meaning Принять анкету для оформления»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-3c642b4448abc373"></a>
- claim:link2:101 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: system\_behavior Система: Анкета принята.»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-be70770b45258c78"></a>
- claim:link2:102 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: state\_before state:link2:calculate»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-76a96f06ca4281c0"></a>
- claim:link2:103 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: state\_after state:link2:import»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-30ae053391dd6fff"></a>
- claim:link2:104 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: user\_result Анкета принята.»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-ace256abc5a80c75"></a>
- claim:link2:105 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: evaluated\_rules BR-FIXTURE-001»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-32137785de278088"></a>
- claim:link2:106 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: implementation FixtureHandler.Handle»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-dca7b6c2ff27949e"></a>
- claim:link2:107 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: implementation component:link2:import:1»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-1e6932a288524016"></a>
- claim:link2:108 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: implementation component:link2:import:2»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-21c6f8147e59546b"></a>
- claim:link2:109 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: technical\_step\_refs technical-step:guard»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-2243a7ff6fa2edd7"></a>
- claim:link2:110 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: technical\_step\_refs technical-step:link2:import:1»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-fbedcedd0bb31968"></a>
- claim:link2:111 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: technical\_step\_refs technical-step:link2:import:2»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-198a156e916460c0"></a>
- claim:link2:112 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: not\_applicable integrations»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-5551df1194135346"></a>
- claim:link2:113 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: business\_action Принять анкету для оформления»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-ed48ff101fb0541c"></a>
- claim:link2:114 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: business\_result Анкета принята.»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-ee017e542a4372ed"></a>
- claim:link2:115 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: precedes scenario-step:link2:import»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-e8b7055f100e57ff"></a>
- claim:link2:116 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: type process»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-c179bbbb086d0c3c"></a>
- claim:link2:117 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: symbol FixturePaymentController.Confirm»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-0ea30ee6401875ca"></a>
- claim:link2:118 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: purpose Perform the synthetic payment operation.»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-6407fedc8850f92d"></a>
- claim:link2:119 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: inputs synthetic request»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-acecbcdd6b0e5e65"></a>
- claim:link2:120 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: outputs synthetic result»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-7d95ab676b77bc70"></a>
- claim:link2:121 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: implementation component:link2:payment:0»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-1fa93941df9b8afb"></a>
- claim:link2:122 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: type process»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-96b8944c57d8d9d7"></a>
- claim:link2:123 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: symbol FixturePaymentHandler.Handle»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-5f220a40eb36fc1b"></a>
- claim:link2:124 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: purpose Perform the synthetic payment operation.»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-f5a29ef34321cb25"></a>
- claim:link2:125 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: inputs synthetic request»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-30e3bd54984853e6"></a>
- claim:link2:126 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: outputs synthetic result»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-ea17bf2df3bfc243"></a>
- claim:link2:127 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: implementation component:link2:payment:1»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-dc1279397320709a"></a>
- claim:link2:128 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: kind actor\_action»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-3e9badd9c4f7e624"></a>
- claim:link2:129 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: actor actor:fixture»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-f14812a45f8489b6"></a>
- claim:link2:130 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: action Подтвердить оплату»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-3550794d5df45c79"></a>
- claim:link2:131 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: business\_meaning Подтвердить оплату»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-12b3ac05e846e53d"></a>
- claim:link2:132 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: system\_behavior Система: Оплата подтверждена.»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-316fc6d6fb1120c7"></a>
- claim:link2:133 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: state\_before state:link2:import»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-009e5bcd52f7f2d9"></a>
- claim:link2:134 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: state\_after state:link2:payment»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-0c1913376013fac2"></a>
- claim:link2:135 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: user\_result Оплата подтверждена.»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-f5b23ad28eb96804"></a>
- claim:link2:136 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: implementation component:link2:payment:0»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-f999297b8ffe7b56"></a>
- claim:link2:137 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: implementation component:link2:payment:1»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-b0d66c4dad757c0d"></a>
- claim:link2:138 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: technical\_step\_refs technical-step:link2:payment:0»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-8556519011a1266d"></a>
- claim:link2:139 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: technical\_step\_refs technical-step:link2:payment:1»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-acfa887f2c1fc821"></a>
- claim:link2:140 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: not\_applicable integrations»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-eb849ec55f36937c"></a>
- claim:link2:141 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: not\_applicable evaluated\_rules»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-a82ca5d94eb23c06"></a>
- claim:link2:142 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: business\_action Подтвердить оплату»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-e9b5fdfd8f95605a"></a>
- claim:link2:143 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: business\_result Оплата подтверждена.»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-30ea14f7e58867e2"></a>
- claim:link2:144 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: precedes scenario-step:link2:payment»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-4134f2e8fe3723b3"></a>
- claim:link2:145 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: type process»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-7fd9d32cbf96e1a7"></a>
- claim:link2:146 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: symbol FixturePostPaymentHandler.Handle»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-4a3e56a3125bb99b"></a>
- claim:link2:147 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: purpose Perform the synthetic issuance operation.»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-07ab6f077282ad82"></a>
- claim:link2:148 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: inputs synthetic request»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-d7bd20047085ed70"></a>
- claim:link2:149 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: outputs synthetic result»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-56766367790c7f2b"></a>
- claim:link2:150 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: implementation component:link2:issuance:0»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-70868e67f6175ba3"></a>
- claim:link2:151 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: type process»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-18c6388a449d4f29"></a>
- claim:link2:152 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: symbol FixturePolicyIssuer.Issue»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-ffb94cc8cf5eff70"></a>
- claim:link2:153 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: purpose Perform the synthetic issuance operation.»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-ae7d237575f6537a"></a>
- claim:link2:154 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: inputs synthetic request»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-4b935e1453f66f8c"></a>
- claim:link2:155 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: outputs synthetic result»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-20ed4fdbec50f56f"></a>
- claim:link2:156 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: implementation component:link2:issuance:1»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-f88615fdcf36befa"></a>
- claim:link2:157 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: type process»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-40a1e47477cc8143"></a>
- claim:link2:158 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: symbol FixturePolicyRepository.Save»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-566eb20a362009f5"></a>
- claim:link2:159 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: purpose Perform the synthetic issuance operation.»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-5a8dd69d7ef50a86"></a>
- claim:link2:160 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: inputs synthetic request»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-57cafd9be84e900c"></a>
- claim:link2:161 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: outputs synthetic result»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-11dc1ae1304144e8"></a>
- claim:link2:162 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: implementation component:link2:issuance:2»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-7e027b381ac25225"></a>
- claim:link2:163 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: kind system\_reaction»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-192a37d6d09f4de3"></a>
- claim:link2:164 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: action Выпустить полис после оплаты»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-b1fdd6f5d0a6cf72"></a>
- claim:link2:165 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: business\_meaning Выпустить полис после оплаты»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-72f108e56fd1f6b1"></a>
- claim:link2:166 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: system\_behavior Система: Полис выпущен.»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-263892879b62019e"></a>
- claim:link2:167 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: state\_before state:link2:payment»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-a0433e6f2e77cbe3"></a>
- claim:link2:168 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: state\_after state:link2:issuance»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-1643b06e0655c57f"></a>
- claim:link2:169 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: user\_result Полис выпущен.»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-b4968cfc9ce2923d"></a>
- claim:link2:170 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: implementation component:link2:issuance:0»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-d6aa093e1de18e32"></a>
- claim:link2:171 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: implementation component:link2:issuance:1»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-5ab6d96f0048ab4a"></a>
- claim:link2:172 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: implementation component:link2:issuance:2»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-f48b1b676ef9a799"></a>
- claim:link2:173 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: technical\_step\_refs technical-step:link2:issuance:0»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-b1e447e2024f7e8a"></a>
- claim:link2:174 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: technical\_step\_refs technical-step:link2:issuance:1»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-36049724ac44c189"></a>
- claim:link2:175 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: technical\_step\_refs technical-step:link2:issuance:2»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-428ee426fd6e35ef"></a>
- claim:link2:176 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: not\_applicable integrations»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-9d4a67fd2cda91e3"></a>
- claim:link2:177 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: not\_applicable actor»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-0c77cdbabb867319"></a>
- claim:link2:178 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: not\_applicable evaluated\_rules»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-6849beb3404db193"></a>
- claim:link2:179 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: business\_action Выпустить полис после оплаты»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-81a7cb50c91c3688"></a>
- claim:link2:180 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: business\_result Полис выпущен.»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-d552ef13edf04c08"></a>
- claim:link2:181 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: precedes scenario-step:link2:issuance»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-8a31a242172d80a3"></a>
- claim:link2:182 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: type process»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-8effbb5c9e8cb9fb"></a>
- claim:link2:183 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: symbol FixtureStatusHandler.Read»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-49dbe00ff932a572"></a>
- claim:link2:184 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: purpose Perform the synthetic status-document operation.»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-d0a0d3ed6226ddb0"></a>
- claim:link2:185 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: inputs synthetic request»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-7cb75b632a497654"></a>
- claim:link2:186 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: outputs synthetic result»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-88682e4d649c6c10"></a>
- claim:link2:187 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: implementation component:link2:status-document:0»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-442945a15aaa201f"></a>
- claim:link2:188 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: type process»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-35e43924399fea47"></a>
- claim:link2:189 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: symbol FixtureDocumentHandler.Read»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-3b4afadb57bec4e7"></a>
- claim:link2:190 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: purpose Perform the synthetic status-document operation.»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-0b47bed9286fd8f8"></a>
- claim:link2:191 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: inputs synthetic request»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-8d21f4db1291a0d5"></a>
- claim:link2:192 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: outputs synthetic result»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-9a85bb774ff797e6"></a>
- claim:link2:193 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: implementation component:link2:status-document:1»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-74d3c5045e84a50f"></a>
- claim:link2:194 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: kind actor\_action»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-c030843f971a5854"></a>
- claim:link2:195 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: actor actor:fixture»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-9c698be6e82c24b2"></a>
- claim:link2:196 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: action Получить статус и документ»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-7e59e93c36149266"></a>
- claim:link2:197 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: business\_meaning Получить статус и документ»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-758567e19057fc0c"></a>
- claim:link2:198 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: system\_behavior Система: Статус и документ доступны.»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-be496e096af7f25c"></a>
- claim:link2:199 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: state\_before state:link2:issuance»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-f5f91633503fe259"></a>
- claim:link2:200 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: state\_after state:link2:status-document»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-c325932d83e8e609"></a>
- claim:link2:201 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: user\_result Статус и документ доступны.»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-da5df457d4750ac2"></a>
- claim:link2:202 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: implementation component:link2:status-document:0»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-62470629858b3580"></a>
- claim:link2:203 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: implementation component:link2:status-document:1»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-eef3de34933484ac"></a>
- claim:link2:204 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: technical\_step\_refs technical-step:link2:status-document:0»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-0b453dd0f2012a5f"></a>
- claim:link2:205 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: technical\_step\_refs technical-step:link2:status-document:1»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-c9683249c6f912b7"></a>
- claim:link2:206 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: not\_applicable integrations»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-31c3be65a0903f7b"></a>
- claim:link2:207 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: not\_applicable evaluated\_rules»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-745391c860f73b99"></a>
- claim:link2:208 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: business\_action Получить статус и документ»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-feed060787d60188"></a>
- claim:link2:209 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: business\_result Статус и документ доступны.»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-1a422370ddfeeb1e"></a>
- claim:link2:210 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: precedes scenario-step:link2:status-document»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-f5e5f7edf26365a0"></a>
- claim:link2:211 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: flow\_type {'flow\_id': 'scenario-flow:link2:main', 'type': 'main'}»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-a0ffe62af10d8ad3"></a>
- claim:link2:212 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: flow\_condition Выполнены условия синтетического основного сценария.»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-fb1e5e7352f51ca2"></a>
- claim:link2:57 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: type process»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-11fc4a8d95111411"></a>
- claim:link2:58 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: symbol FixtureCalculateController.Calculate»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-3e77a85b9ac7d40e"></a>
- claim:link2:59 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: purpose Perform the synthetic calculate operation.»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-025142c1140fd015"></a>
- claim:link2:60 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: inputs synthetic request»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-f3dfcacf1dacf62f"></a>
- claim:link2:61 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: outputs synthetic result»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-9473f186645c10e3"></a>
- claim:link2:62 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: implementation component:link2:calculate:0»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-1d273bd75283252f"></a>
- claim:link2:63 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: type process»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-8239e6b84d36aee9"></a>
- claim:link2:64 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: symbol FixtureCalculateHandler.Handle»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-939985fdafc43c7b"></a>
- claim:link2:65 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: purpose Perform the synthetic calculate operation.»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-d00e3120317d6e44"></a>
- claim:link2:66 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: inputs synthetic request»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-4b58173f41a31276"></a>
- claim:link2:67 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: outputs synthetic result»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-39f0c0e13a1694b1"></a>
- claim:link2:68 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: implementation component:link2:calculate:1»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-45af0abf85f8169b"></a>
- claim:link2:69 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: kind actor\_action»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-2acb3ad00b12164c"></a>
- claim:link2:70 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: actor actor:fixture»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-1de6d1d3bf71883e"></a>
- claim:link2:71 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: action Рассчитать стоимость оформления»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-a279c0d661c89b24"></a>
- claim:link2:72 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: business\_meaning Рассчитать стоимость оформления»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-52040b933352dbd3"></a>
- claim:link2:73 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: system\_behavior Система: Расчёт подготовлен.»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-ddb608dc12eb2fa4"></a>
- claim:link2:74 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: state\_before state:link2:initial»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-92ecae80d548463c"></a>
- claim:link2:75 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: state\_after state:link2:calculate»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-afe5c2b4172fb398"></a>
- claim:link2:76 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: user\_result Расчёт подготовлен.»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-fff09ade99137813"></a>
- claim:link2:77 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: implementation component:link2:calculate:0»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-bea9f81461209da7"></a>
- claim:link2:78 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: implementation component:link2:calculate:1»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-a6c00f49a70c4f23"></a>
- claim:link2:79 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: technical\_step\_refs technical-step:link2:calculate:0»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-8888d44bd39d8301"></a>
- claim:link2:80 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: technical\_step\_refs technical-step:link2:calculate:1»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-fe3f1c76df4df6d2"></a>
- claim:link2:81 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: not\_applicable integrations»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-21577c13e4dfffaa"></a>
- claim:link2:82 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: not\_applicable evaluated\_rules»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-0096b79359b8f775"></a>
- claim:link2:83 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: business\_action Рассчитать стоимость оформления»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-8088cbf07da8ff83"></a>
- claim:link2:84 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: business\_result Расчёт подготовлен.»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-ee7de307e21cf090"></a>
- claim:link2:85 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: type process»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-819937e7b0eea3b1"></a>
- claim:link2:86 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: symbol FixtureImportMapper.Map»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-9c9d2cc6901c4582"></a>
- claim:link2:87 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: purpose Perform the synthetic import operation.»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-c6a5f71fb0e5b501"></a>
- claim:link2:88 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: inputs synthetic request»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-c78229e50c5444a1"></a>
- claim:link2:89 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: outputs synthetic result»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-4bde106a65a4d187"></a>
- claim:link2:90 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: implementation component:link2:import:1»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-21c524f1e2799eb6"></a>
- claim:link2:91 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: type process»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-12b816c1a65fd288"></a>
- claim:link2:92 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: symbol FixtureImportRepository.Save»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-6bbe41867e194176"></a>
- claim:link2:93 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: purpose Perform the synthetic import operation.»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-308f3f487739b380"></a>
- claim:link2:94 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: inputs synthetic request»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-aefaeed87af60089"></a>
- claim:link2:95 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: outputs synthetic result»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-c2ece3911290f14b"></a>
- claim:link2:96 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: implementation component:link2:import:2»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-63ededcc7ddbf950"></a>
- claim:link2:97 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: kind actor\_action»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-96dacbe4a9fa47cf"></a>
- claim:link2:98 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: actor actor:fixture»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-9ed873fb8e903b12"></a>
- claim:link2:99 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic fixture statement: action Принять анкету для оформления»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-5905935558d6a4ab"></a>
- claim:rule:affected\_actor:0 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic: affected\_actor actor:fixture»; modality=implemented; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-43a4c0894a341be2"></a>
- claim:rule:affected\_scenario:0 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic: affected\_scenario scenario:fixture»; modality=implemented; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-b486cdf6559d5327"></a>
- claim:rule:condition **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic: condition accuracy &lt; 7»; modality=implemented; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-17789db3ccf28909"></a>
- claim:rule:false\_result **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic: false\_result return 1»; modality=implemented; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-75766c411a8cd6be"></a>
- claim:rule:implementation:0 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic: implementation FixtureHandler.Handle»; modality=implemented; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-f81dfaa70255f81a"></a>
- claim:rule:parameters:0 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic: parameters {'name': 'accuracy threshold', 'value': 7, 'unit': None, 'origin': 'literal'}»; modality=implemented; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-8c43153f7de87eec"></a>
- claim:rule:rule\_kind **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic: rule\_kind technical\_constraint»; modality=implemented; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-615aa51279a80c8c"></a>
- claim:rule:rule\_statement **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic: rule\_statement Return 0 when fixture accuracy is below 7.»; modality=implemented; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-db74364c88fd1563"></a>
- claim:rule:true\_result **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic: true\_result return 0»; modality=implemented; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-c1ac041eef07277d"></a>
- claim:scenario-step:guard:action **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic: action Check accuracy»; modality=implemented; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-30e08762a8dabbe9"></a>
- claim:scenario-step:guard:decision\_kind **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic: decision\_kind technical»; modality=implemented; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-d266987c9a33d245"></a>
- claim:scenario-step:guard:decision\_ref **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic: decision\_ref decision:accuracy»; modality=implemented; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-03c0fafd7221b345"></a>
- claim:scenario-step:guard:evaluated\_rules:0 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic: evaluated\_rules BR-FIXTURE-001»; modality=implemented; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-f5c53056440940de"></a>
- claim:scenario-step:guard:implementation:0 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic: implementation FixtureHandler.Handle»; modality=implemented; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-b5622dc85362e3b5"></a>
- claim:scenario-step:guard:kind **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic: kind decision»; modality=implemented; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-a7f8e414e228e8a9"></a>
- claim:scenario-step:guard:na:actor **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic: not\_applicable actor»; modality=implemented; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-5cd22dc10d294448"></a>
- claim:scenario-step:guard:na:integrations **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic: not\_applicable integrations»; modality=implemented; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-bac633cb4f97a757"></a>
- claim:scenario-step:guard:system\_behavior **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic: system\_behavior Evaluate accuracy &lt; 7»; modality=implemented; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-5ffab412f0c039b9"></a>
- claim:scenario-step:return-one:action **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic: action Return fixture result»; modality=implemented; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-4a730077e577cbdc"></a>
- claim:scenario-step:return-one:implementation:0 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic: implementation FixtureHandler.Handle»; modality=implemented; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-7b7a7cd3c3adcce9"></a>
- claim:scenario-step:return-one:kind **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic: kind system\_reaction»; modality=implemented; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-73f90372d2858221"></a>
- claim:scenario-step:return-one:na:actor **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic: not\_applicable actor»; modality=implemented; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-89c81b0aa581f085"></a>
- claim:scenario-step:return-one:na:evaluated\_rules **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic: not\_applicable evaluated\_rules»; modality=implemented; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-60ae5f30a85de732"></a>
- claim:scenario-step:return-one:na:integrations **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic: not\_applicable integrations»; modality=implemented; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-b66c40c517f6e997"></a>
- claim:scenario-step:return-one:system\_behavior **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic: system\_behavior return 1»; modality=implemented; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-47ab76c6a26afcbd"></a>
- claim:scenario-step:return-zero:action **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic: action Return fixture result»; modality=implemented; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-20f1abd9b657fe12"></a>
- claim:scenario-step:return-zero:implementation:0 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic: implementation FixtureHandler.Handle»; modality=implemented; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-021ee30e8045b808"></a>
- claim:scenario-step:return-zero:kind **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic: kind system\_reaction»; modality=implemented; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-63ff48494775df88"></a>
- claim:scenario-step:return-zero:na:actor **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic: not\_applicable actor»; modality=implemented; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-469c54608a204a2b"></a>
- claim:scenario-step:return-zero:na:evaluated\_rules **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic: not\_applicable evaluated\_rules»; modality=implemented; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-08634867c0716525"></a>
- claim:scenario-step:return-zero:na:integrations **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic: not\_applicable integrations»; modality=implemented; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-5465ab3586105630"></a>
- claim:scenario-step:return-zero:system\_behavior **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic: system\_behavior return 0»; modality=implemented; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-5e28bc6bbc131ae9"></a>
- claim:technical:checks/0 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic technical observation.»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-f23ad11258aa5625"></a>
- claim:technical:conditions/0 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic technical observation.»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-be6f72ababd97bde"></a>
- claim:technical:inputs/0 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic technical observation.»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-48076ce9fbe1165e"></a>
- claim:technical:inputs/1 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic technical observation.»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-81cb23699bd702c4"></a>
- claim:technical:outputs/0 **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic technical observation.»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-953381d15920c005"></a>
- claim:technical:purpose **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic technical observation.»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-25c41d33dfe62cf4"></a>
- claim:technical:symbol **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic technical observation.»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-d5f918c81eb338c4"></a>
- claim:technical:type **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic technical observation.»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].
<a id="claim-694fbbc472dc8c68"></a>
- claim:trigger **[CONFIRMED; reviewed=true]**: проверяемое утверждение «Synthetic: scenario:fixture trigger FixtureCommand»; modality=source\_statement; inference=false; knowledge_status=CONFIRMED; confidence={"rationale": "Direct synthetic fixture statement.", "score": 1.0}; support=\[{"evidence\_id": "evidence:fixture", "role": "supports"}\]; basis=\[\].
  Review: Synthetic inspected evidence for fixed fixture version.; supported parts=\[\]; unsupported parts=\[\].

### Evidence locators (метаданные источников)
- {"basis\_claim\_ids": \[\], "class": "FixtureHandler", "commit": null, "confidence": {"rationale": "Direct synthetic fixture statement.", "score": 1.0}, "excerpt": "// Synthetic fixture: one goal = process the fixture request.\\n// Trigger = FixtureCommand. Entry = fixture pending. Outcome = fixture done.\\n// Actor = fixture client. No OSAGO business knowledge is asserted.\\n// Synthetic technical main path: accuracy &gt;= 7; alternative path: accuracy &lt; 7.\\nrecord FixtureCommand();\\nclass FixtureHandler {\\n    // Synthetic technical threshold, not an OSAGO business rule.\\n    public int Handle(FixtureCommand command, int accuracy) {\\n        if (accuracy &lt; 7) return 0;\\n        return 1;\\n    }\\n}\\n// Registration: FixtureCommand -&gt; FixtureHandler.Handle\\n\\n// SYNTHETIC LINK2 CONTRACT DATA\\n{\\n  \\"kind\\": \\"synthetic contract fixture, not production evidence\\",\\n  \\"phases\\": \[\\n    \[\\n      \\"calculate\\",\\n      \\"Рассчитать стоимость оформления\\",\\n      \\"Расчёт подготовлен.\\",\\n      \[\\n        \\"FixtureCalculateController.Calculate\\",\\n        \\"FixtureCalculateHandler.Handle\\"\\n      \]\\n    \],\\n    \[\\n      \\"import\\",\\n      \\"Принять анкету для оформления\\",\\n      \\"Анкета принята.\\",\\n      \[\\n        \\"FixtureHandler.Handle\\",\\n        \\"FixtureImportMapper.Map\\",\\n        \\"FixtureImportRepository.Save\\"\\n      \]\\n    \],\\n    \[\\n      \\"payment\\",\\n      \\"Подтвердить оплату\\",\\n      \\"Оплата подтверждена.\\",\\n      \[\\n        \\"FixturePaymentController.Confirm\\",\\n        \\"FixturePaymentHandler.Handle\\"\\n      \]\\n    \],\\n    \[\\n      \\"issuance\\",\\n      \\"Выпустить полис после оплаты\\",\\n      \\"Полис выпущен.\\",\\n      \[\\n        \\"FixturePostPaymentHandler.Handle\\",\\n        \\"FixturePolicyIssuer.Issue\\",\\n        \\"FixturePolicyRepository.Save\\"\\n      \]\\n    \],\\n    \[\\n      \\"status-document\\",\\n      \\"Получить статус и документ\\",\\n      \\"Статус и документ доступны.\\",\\n      \[\\n        \\"FixtureStatusHandler.Read\\",\\n        \\"FixtureDocumentHandler.Read\\"\\n      \]\\n    \]\\n  \],\\n  \\"actor\_policy\\": \\"The issuance phase is internal system processing, with no business initiator.\\",\\n  \\"mapping\\": \[\\n    {\\n      \\"step\\": \\"scenario-step:link2:calculate\\",\\n      \\"nodes\\": \[\\n        \\"technical-step:link2:calculate:0\\",\\n        \\"technical-step:link2:calculate:1\\"\\n      \],\\n      \\"result\\": \\"Расчёт подготовлен.\\"\\n    },\\n    {\\n      \\"step\\": \\"scenario-step:link2:import\\",\\n      \\"nodes\\": \[\\n        \\"technical-step:guard\\",\\n        \\"technical-step:link2:import:1\\",\\n        \\"technical-step:link2:import:2\\"\\n      \],\\n      \\"result\\": \\"Анкета принята.\\"\\n    },\\n    {\\n      \\"step\\": \\"scenario-step:link2:payment\\",\\n      \\"nodes\\": \[\\n        \\"technical-step:link2:payment:0\\",\\n        \\"technical-step:link2:payment:1\\"\\n      \],\\n      \\"result\\": \\"Оплата подтверждена.\\"\\n    },\\n    {\\n      \\"step\\": \\"scenario-step:link2:issuance\\",\\n      \\"nodes\\": \[\\n        \\"technical-step:link2:issuance:0\\",\\n        \\"technical-step:link2:issuance:1\\",\\n        \\"technical-step:link2:issuance:2\\"\\n      \],\\n      \\"result\\": \\"Полис выпущен.\\"\\n    },\\n    {\\n      \\"step\\": \\"scenario-step:link2:status-document\\",\\n      \\"nodes\\": \[\\n        \\"technical-step:link2:status-document:0\\",\\n        \\"technical-step:link2:status-document:1\\"\\n      \],\\n      \\"result\\": \\"Статус и документ доступны.\\"\\n    }\\n  \]\\n}", "file": "fixtures/flow.cs", "id": "evidence:fixture", "inference": false, "metadata": {"file": "fixtures/flow.cs", "page": null, "repository": "fixture", "revision": "fixture-v1", "symbol": "FixtureHandler.Handle"}, "method": "Handle", "page": null, "rationale": null, "repository": "fixture", "section": null, "snapshot\_id": "snapshot:fixture", "source\_location": "fixtures/flow.cs:1", "source\_ref": "snapshot:fixture", "source\_type": "CODE", "supports": \["claim:business\_goal", "claim:trigger", "claim:entry\_state", "claim:exit\_states", "claim:actors", "claim:anchor", "claim:edge", "claim:expected\_outcomes", "claim:flow-implementation", "claim:rule:rule\_kind", "claim:rule:rule\_statement", "claim:rule:condition", "claim:rule:true\_result", "claim:rule:false\_result", "claim:rule:affected\_actor:0", "claim:rule:affected\_scenario:0", "claim:rule:parameters:0", "claim:rule:implementation:0", "claim:scenario-step:guard:kind", "claim:scenario-step:guard:action", "claim:scenario-step:guard:system\_behavior", "claim:scenario-step:guard:decision\_ref", "claim:scenario-step:guard:decision\_kind", "claim:scenario-step:guard:evaluated\_rules:0", "claim:scenario-step:guard:implementation:0", "claim:scenario-step:guard:na:actor", "claim:scenario-step:guard:na:integrations", "claim:scenario-step:return-one:kind", "claim:scenario-step:return-one:action", "claim:scenario-step:return-one:system\_behavior", "claim:scenario-step:return-one:implementation:0", "claim:scenario-step:return-one:na:actor", "claim:scenario-step:return-one:na:integrations", "claim:scenario-step:return-one:na:evaluated\_rules", "claim:scenario-step:return-zero:kind", "claim:scenario-step:return-zero:action", "claim:scenario-step:return-zero:system\_behavior", "claim:scenario-step:return-zero:implementation:0", "claim:scenario-step:return-zero:na:actor", "claim:scenario-step:return-zero:na:integrations", "claim:scenario-step:return-zero:na:evaluated\_rules", "claim:edge:0", "claim:edge:0:condition", "claim:edge:1", "claim:edge:1:condition", "claim:flow:main", "claim:flow:alternative", "claim:flow:main:type", "claim:flow:alternative:type", "claim:technical:type", "claim:technical:symbol", "claim:technical:purpose", "claim:technical:inputs/0", "claim:technical:inputs/1", "claim:technical:outputs/0", "claim:technical:conditions/0", "claim:technical:checks/0", "claim:link2:57", "claim:link2:58", "claim:link2:59", "claim:link2:60", "claim:link2:61", "claim:link2:62", "claim:link2:63", "claim:link2:64", "claim:link2:65", "claim:link2:66", "claim:link2:67", "claim:link2:68", "claim:link2:69", "claim:link2:70", "claim:link2:71", "claim:link2:72", "claim:link2:73", "claim:link2:74", "claim:link2:75", "claim:link2:76", "claim:link2:77", "claim:link2:78", "claim:link2:79", "claim:link2:80", "claim:link2:81", "claim:link2:82", "claim:link2:83", "claim:link2:84", "claim:link2:85", "claim:link2:86", "claim:link2:87", "claim:link2:88", "claim:link2:89", "claim:link2:90", "claim:link2:91", "claim:link2:92", "claim:link2:93", "claim:link2:94", "claim:link2:95", "claim:link2:96", "claim:link2:97", "claim:link2:98", "claim:link2:99", "claim:link2:100", "claim:link2:101", "claim:link2:102", "claim:link2:103", "claim:link2:104", "claim:link2:105", "claim:link2:106", "claim:link2:107", "claim:link2:108", "claim:link2:109", "claim:link2:110", "claim:link2:111", "claim:link2:112", "claim:link2:113", "claim:link2:114", "claim:link2:115", "claim:link2:116", "claim:link2:117", "claim:link2:118", "claim:link2:119", "claim:link2:120", "claim:link2:121", "claim:link2:122", "claim:link2:123", "claim:link2:124", "claim:link2:125", "claim:link2:126", "claim:link2:127", "claim:link2:128", "claim:link2:129", "claim:link2:130", "claim:link2:131", "claim:link2:132", "claim:link2:133", "claim:link2:134", "claim:link2:135", "claim:link2:136", "claim:link2:137", "claim:link2:138", "claim:link2:139", "claim:link2:140", "claim:link2:141", "claim:link2:142", "claim:link2:143", "claim:link2:144", "claim:link2:145", "claim:link2:146", "claim:link2:147", "claim:link2:148", "claim:link2:149", "claim:link2:150", "claim:link2:151", "claim:link2:152", "claim:link2:153", "claim:link2:154", "claim:link2:155", "claim:link2:156", "claim:link2:157", "claim:link2:158", "claim:link2:159", "claim:link2:160", "claim:link2:161", "claim:link2:162", "claim:link2:163", "claim:link2:164", "claim:link2:165", "claim:link2:166", "claim:link2:167", "claim:link2:168", "claim:link2:169", "claim:link2:170", "claim:link2:171", "claim:link2:172", "claim:link2:173", "claim:link2:174", "claim:link2:175", "claim:link2:176", "claim:link2:177", "claim:link2:178", "claim:link2:179", "claim:link2:180", "claim:link2:181", "claim:link2:182", "claim:link2:183", "claim:link2:184", "claim:link2:185", "claim:link2:186", "claim:link2:187", "claim:link2:188", "claim:link2:189", "claim:link2:190", "claim:link2:191", "claim:link2:192", "claim:link2:193", "claim:link2:194", "claim:link2:195", "claim:link2:196", "claim:link2:197", "claim:link2:198", "claim:link2:199", "claim:link2:200", "claim:link2:201", "claim:link2:202", "claim:link2:203", "claim:link2:204", "claim:link2:205", "claim:link2:206", "claim:link2:207", "claim:link2:208", "claim:link2:209", "claim:link2:210", "claim:link2:211", "claim:link2:212"\], "version": "fixture-v1"}

## 12. Известные пробелы и спорные места

- Gap: {"affected\_ids": \["BR-FIXTURE-001"\], "id": "gap:rationale", "next\_action": "Find explicit documented rationale.", "publication\_relevance": {"classification": "INTERNAL\_RESEARCH", "impacts": \[\], "reason": "Synthetic fixture review: internal implementation/source research; independently supported process fields do not depend on this detail.", "reviewed": true}, "question": "Why this threshold?", "reason": "unknown\_reason", "status": "open"}
- Gap: {"affected\_ids": \["BR-FIXTURE-001"\], "id": "gap:external", "next\_action": "Trace caller and result mapping.", "publication\_relevance": {"classification": "INTERNAL\_RESEARCH", "impacts": \[\], "reason": "Synthetic fixture review: internal implementation/source research; independently supported process fields do not depend on this detail.", "reviewed": true}, "question": "What is the external result/state?", "reason": "unknown\_field", "status": "open"}
- Gap: {"affected\_ids": \["scenario-step:guard"\], "id": "gap:scenario-step:guard", "next\_action": "Find documents and caller/result mapping.", "publication\_relevance": {"classification": "INTERNAL\_RESEARCH", "impacts": \[\], "reason": "Synthetic fixture review: internal implementation/source research; independently supported process fields do not depend on this detail.", "reviewed": true}, "question": "Business meaning, states and actor result?", "reason": "unknown\_reason", "status": "open"}
- Gap: {"affected\_ids": \["scenario-step:return-one"\], "id": "gap:scenario-step:return-one", "next\_action": "Find documents and caller/result mapping.", "publication\_relevance": {"classification": "INTERNAL\_RESEARCH", "impacts": \[\], "reason": "Synthetic fixture review: internal implementation/source research; independently supported process fields do not depend on this detail.", "reviewed": true}, "question": "Business meaning, states and actor result?", "reason": "unknown\_reason", "status": "open"}
- Gap: {"affected\_ids": \["scenario-step:return-zero"\], "id": "gap:scenario-step:return-zero", "next\_action": "Find documents and caller/result mapping.", "publication\_relevance": {"classification": "INTERNAL\_RESEARCH", "impacts": \[\], "reason": "Synthetic fixture review: internal implementation/source research; independently supported process fields do not depend on this detail.", "reviewed": true}, "question": "Business meaning, states and actor result?", "reason": "unknown\_reason", "status": "open"}
- Gap: {"affected\_ids": \["technical-step:guard", "technical-step:link2:calculate:0", "technical-step:link2:calculate:1", "technical-step:link2:import:1", "technical-step:link2:import:2", "technical-step:link2:payment:0", "technical-step:link2:payment:1", "technical-step:link2:issuance:0", "technical-step:link2:issuance:1", "technical-step:link2:issuance:2", "technical-step:link2:status-document:0", "technical-step:link2:status-document:1"\], "id": "gap:technical", "next\_action": "Inspect remaining technical dimensions.", "publication\_relevance": {"classification": "INTERNAL\_RESEARCH", "impacts": \[\], "reason": "Synthetic fixture review: internal implementation/source research; independently supported process fields do not depend on this detail.", "reviewed": true}, "question": "Which other technical effects exist?", "reason": "unknown\_field", "status": "open"}
- Gap: {"affected\_ids": \["claim:link2:211"\], "id": "gap:composer:link2:version", "next\_action": "Review scenario version applicability.", "publication\_relevance": {"classification": "PUBLICATION\_RELEVANT", "impacts": \[{"aspect": "VERSION\_ENVIRONMENT", "target\_refs": \["claim:link2:211"\]}, {"aspect": "MAIN\_FLOW", "target\_refs": \["claim:link2:211"\]}\], "reason": "Synthetic fixture review: referenced process/contract assertion is material.", "reviewed": true}, "question": "Уточнить применимость порядка этапов к описываемой версии.", "reason": "unknown\_version", "status": "open"}
- Gap: {"affected\_ids": \["technical-step:link2:calculate:0"\], "id": "gap:composer:link2:internal", "next\_action": "Internal investigation only.", "publication\_relevance": {"classification": "INTERNAL\_RESEARCH", "impacts": \[\], "reason": "Synthetic fixture review: referenced process/contract assertion is material.", "reviewed": true}, "question": "Как устроен внутренний helper ../internal/Helper.cs?", "reason": "unknown\_field", "status": "open"}
- Finding: {"blocking": true, "claim\_ids": \[\], "evidence\_ids": \["evidence:fixture"\], "id": "finding:c25bd948b9ac3d83d0ee", "kind": "unknown\_business\_rationale", "publication\_relevance": {"classification": "INTERNAL\_RESEARCH", "impacts": \[\], "reason": "Synthetic fixture review: internal implementation/source research; independently supported process fields do not depend on this detail.", "reviewed": true}, "reason": "Business rationale is explicitly UNKNOWN in the supplied rule; no motive is inferred.", "required\_action": "analyst\_review", "resolution\_claim\_ids": \[\], "status": "open", "target\_refs": \["BR-FIXTURE-001"\], "verification": "observed\_structure"}
Coverage (metadata): {"frontier": \[\], "limitations": \["Synthetic technical backbone; business meaning unknown."\], "status": "partial"}
