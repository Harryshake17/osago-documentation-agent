# Reader-first Link2 Composer regression

Inputs are read directly from the existing frozen synthetic fixture
`../../scenario/link2/inputs.json` and `../../scenario/link2/05-scenario.json`.
Those upstream files are unchanged. This is a contract regression, not a claim
about production Link2 behavior or complete negative-case coverage.

The validation sidecars preserve the original research gaps and add an explicitly
reviewed version applicability question (publication-relevant) and an internal
helper question with a filesystem locator (internal research). They make the
rendering boundary observable without rewriting source facts or Scenario steps.

`before.md` captures the previous Composer on these same inputs. `after.md` and
`documentation-manifest.json` capture the new section-centric output. One main
flow has five meaningful steps; the overview selects five principal mapped
components out of twelve technical nodes. All evidence, claims, original
artifacts and both kinds of gap remain in manifest provenance.

There is no .mmd link or name substituted for a diagram. Diagram publication
belongs to the separate Confluence Renderer and its presentation metadata.
