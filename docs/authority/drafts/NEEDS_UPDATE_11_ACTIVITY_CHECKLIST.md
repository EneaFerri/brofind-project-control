# 01 — PRE-ASTRA ACTIVITY CHECKLIST

This is the single go/no-go checklist. Astra coding does not start until all **GATE** rows are PASS.

| ID | Activity | Type | Current status | PASS condition |
|---|---|---|---|---|
| A01 | Product & Scope authority consolidated | GATE | **PASS** | One current V1 Product Freeze covers all V1 domains and boundaries. |
| A02 | Architecture / Work Execution Boundary consolidated | GATE | **PASS** | Monitoring-first, READ MANY / WRITE LITTLE, AI/human authority and execution boundaries are explicit. |
| A03 | Portfolio visual freeze | GATE | **PASS** | Canonical mockup identified; no competing version admitted. |
| A04 | Project Overview visual freeze | GATE | **PASS** | Canonical monitoring-first Overview recovered and validated: compact domain strip, main exposure, other Attention, compact next gate; AI drawer project-wide. |
| A05 | Master Planner visual freeze | GATE | **PASS** | Current corrected mockup retained; downstream dates are not auto-shifted; future readiness can be `DA VERIFICARE`; completion % explicitly means milestone count. |
| A06 | Economic Control visual freeze | GATE | **PASS** | Current approved mockup retained; AI only via common project drawer; mock numbers marked illustrative. |
| A07 | Technical Control visual freeze | GATE | **PASS** | Decision/technical-condition view is canonical; old document-centric technical mockup explicitly rejected. |
| A08 | Procurement visual freeze | GATE | **PASS** | Domain content validated: `Stadio`, `Prossima scadenza`, `Need Date`, `Supplier Promise`, `Current Forecast`, `Stato controllo`, `Impatto`; common-shell duplication handled by A13A. |
| A09 | Document Control visual freeze | GATE | **PASS** | Logical Document Item is primary; control states aligned; missing/late/critical remain derived conditions. |
| A10 | Billing & Payment Control visual freeze | GATE | **PASS** | One combined surface: contractual maturity → invoiced → payment due → collected, without becoming accounting/credit workflow. |
| A11 | Separate Payment screen | GATE | **REMOVED / N/A** | Merged into A10 Billing & Payment Control to avoid duplication. |
| A12 | Standalone Control screen | GATE | **REMOVED / N/A** | Cross-domain control remains functional chain; standalone page removed to avoid duplication. |
| A13 | Common project AI drawer contract | GATE | **PASS (semantic)** | One drawer across project screens; it can answer on the whole selected project, not just the current page; advisory only. |
| A13A | Shared UI shell consistency | GATE | **PASS** | Single project navigation; no sidebar duplication; one project-wide AI drawer; shared header and local-toolbar rules frozen. |
| A14 | Visual manifest finalized | GATE | **PASS** | Eight canonical surfaces + final shared-shell contract; rejected variants excluded; duplicate navigation/actions resolved by shared-shell authority. |
| A15 | Cross-domain data contract finalized | GATE | **PARTIAL** | Required fields, meanings, source, authority, freshness, derivation and confirmation rules completed per domain. |
| A16 | Mock values vs authoritative data rule | GATE | **PASS** | Mockup numbers are visual examples only; code may not seed them as source facts unless fixture/test data is explicitly selected. |
| A17 | Interaction contract finalized | GATE | **PASS DRAFT — human review needed** | Sorting, drilldown, drawers, source/history, correction paths and archive behavior are explicit. |
| A18 | Acceptance tests / QA contract finalized | GATE | **PASS DRAFT — human review needed** | Automated semantic tests + visual comparison + real Brofind pilot UAT defined. |
| A19 | Repository baseline bootstrap | GATE | **TODO IN ASTRA READ-ONLY BOOTSTRAP** | Repository, branch, HEAD, dirty state, stable baseline, current docs and test baseline reconciled before mutation. |
| A20 | Baseline → target gap analysis | GATE | **TODO IN ASTRA READ-ONLY BOOTSTRAP** | Reuse vs new model/API/UI work identified without code changes. |
| A21 | Updated staged implementation plan | GATE | **TODO AFTER A19/A20** | Vertical slices, dependencies, migrations, tests and human approval gates defined. |
| A22 | Human GO for implementation | GATE | **TODO** | the Product Owner explicitly authorizes coding after review of A19–A21. |

## Recommended sequence

**Now:** A15 → review A17/A18.

**Then Astra, read-only only:** A19 → A20 → A21.

**Then human gate:** A22.

**Only after A22:** implementation by vertical slices.
