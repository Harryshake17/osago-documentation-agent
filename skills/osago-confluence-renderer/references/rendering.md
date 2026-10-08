# Storage representation and publisher boundary

## Verified project integration

Current config: Confluence REST /rest/api, representation storage.
Installed renspec source: cli/lib/clients/confluence.js:
bodyValue reads bodyFile unchanged unless fromMarkdown; pageBody puts value into
body.storage with representation from config; create POST /content; update
PUT /content/{id} with current version+1. cli/lib/md2storage.js provides a small
general converter, but does not implement OSAGO privacy/lineage/material panels.
Neither publisher nor that general converter is modified.

On 2026-10-05 the configured instance login meta reported 8.9.0. An authenticated
POST /contentbody/convert/view (conversion only, no page mutation) returned
real H1/H2/H3/table/ul/code and visible info/warning/expand, no Unknown macro.
The renderer uses these capabilities. This is a representation proof, not proof
that this task published a page. PNG image resources use standard attachment
storage; successful display additionally needs the publisher to upload them.

Primary syntax references:
- https://confluence.atlassian.com/doc/confluence-storage-format-790796544.html
- https://confluence.atlassian.com/spaces/CONF53/pages/411108832/Confluence+Storage+Format+for+Macros

## Three independent layers

Content: immutable reviewed document plus bound manifest/review report.
Representation: AST Markdown parsing, approved hierarchy, XHTML, private lineage,
local diagram conversion/bundle. No source knowledge queries or page mutations.
Publication: existing renspec/Confluence connector, authentication, page lifecycle,
attachment uploads, versioning and post-publication body.view checks.

Renderer inputs may be JSON or YAML projections of existing schemas. If Composer
manifest describes draft, pair it with final's language-review report; validate
shared schemas, draft/final/manifest hash binding, claim inventory and gate.
Renderer does not overwrite manifest or produce a new knowledge manifest.

## Presentation metadata

Optional YAML:

    inline_identifiers: [ReadyForSign, RegisterPolicyContractNSIS]
    links:
      "https://wiki.example/pages/viewpage.action?pageId=123":
        url: "https://wiki.example/pages/viewpage.action?pageId=123"
        title: "Описание оформления полиса"
    diagrams:
      "link2-flow.mmd":
        source_file: link2-flow.mmd
        rendered_file: link2-flow.png
        caption: "Этапы оформления полиса"

Labels/captions are display metadata from already reviewed text; do not supply
new domain claims. Image paths resolve only within selected asset root.
Without rendered_file local mmdc may render selected source to PNG (no network).
Never send raw Mermaid to Confluence; unsupported raw inline Mermaid/HTML blocks
fail instead of becoming text or unverified macros.

Internal anchors and raw path links are recorded privately. Human-readable label
can remain unlinked when no public target exists; explicit metadata may provide
an approved public target. Do not invent URLs from paths or repositories.

## Native body and publication

Heading: <h1>/<h2>/<h3>, paragraph: <p>, table: <table>/<thead>/<tbody>,
list: <ul>/<ol>/<li>, inline symbol: <code>. BR source fields are paragraphs
under existing H3; no new rules, causal edits or order changes.
Warning/info/expand use ac:structured-macro + ac:rich-text-body.
Diagram: ac:image with human alt + ri:attachment filename, prepared PNG.

Publisher must use body_file as-is with content_format/representation=storage;
the REST fragment is {"body":{"storage":{"value":"<XHTML>","representation":"storage"}}}.
Never insert metadata, raw Markdown, or literal JSON wrapper into the body.
Verify eligible and unchanged gate, choose authorized destination/page identity,
ensure page exists, upload listed attachments, then write final body/version.
Preserve retry/idempotency/space guards of existing publisher. This skill does not
authorize publication, or override blocked upstream gate.

CLI check replays approved input rendering and compares body, metadata and assets,
rejecting stale/tampered bundles. Existing unrelated files are never purged.

## Link2 regression

fixtures/confluence-render/link2-reviewed.md is a small presentation regression
fixture: Link2 prose excerpts plus explicit synthetic rule/link/diagram/status
cases. It is not a newly reviewed production run and must not be published.
Tests use the shared documentation-manifest schema; no duplicate evidence/status
model. Verify actual parsed XML element hierarchy, table shape/cell order, lists,
code, separate warnings, private-ID/path exclusion, attachment resources,
hash/approval binding, gate preservation, determinism and CLI handoff.
Each attachment records both prepared PNG content_hash and selected source_hash;
check detects stale asset metadata without inspecting new system knowledge.
Literal code symbols remain visible even when a CodeComponent uses the same ID.
