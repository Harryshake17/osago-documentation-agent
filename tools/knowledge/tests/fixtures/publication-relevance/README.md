# Publication relevance regression fixture

Synthetic structured knowledge only; this fixture makes no claims about application behavior.

`inputs.json` contains 20 internal implementation research gaps and two gaps affecting
main-flow ordering and the business result. The reviewed `gaps.json` retains all 22 records,
including their original IDs and affected references. Its `publication_subset` contains only
the two material process gap IDs. `validation-report.json` preserves the claim inventory
and the conservative blocked publication gate.

The subset is a derived handoff for downstream filtering; classification is independent
of knowledge status, severity, confidence and gap lifecycle. Unassessed items require
explicit relevance review. No Composer rendering behavior is changed by this fixture.
