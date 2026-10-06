# 08 — A14 VISUAL CONSISTENCY AUDIT

**Result: PASS**

A14 reviewed the eight canonical V1 surfaces together, not individually.

## Canonical surfaces reviewed

1. Portfolio
2. Project Overview
3. Master Planner
4. Economic Control
5. Technical Control
6. Procurement Control
7. Document Control
8. Billing & Payment Control

## Cross-screen findings

### PASS — domain composition
Each canonical surface has a distinct purpose and does not need another redesign.

- Portfolio = global triage.
- Overview = project-level synthesis/exposure.
- Master = milestone/date/readiness control.
- Economics = cost/result control.
- Technical = technical decisions/conditions.
- Procurement = supply timing/control.
- Documents = logical document availability/adequacy.
- Billing & Payment = contractual maturity → invoice → due → collected.

### RESOLVED — duplicated navigation
Several mockups still visually contain both sidebar domain links and horizontal project tabs.

Resolution: `03A_SHARED_UI_SHELL_CONTRACT_V1.md` is higher authority for shared chrome:
- sidebar = app/global only;
- horizontal bar = project-domain navigation only.

No domain mockup regeneration is required.

### RESOLVED — Billing / Payment duplication
Older mockups show separate Billing and Payment navigation.

Final rule:
- one `Billing & Payment` project screen;
- Billing and Payment remain distinct control semantics;
- separate Billing and Payment semaphores may remain in Portfolio/Overview;
- either signal opens the same combined screen, focused to the relevant section.

### RESOLVED — standalone Control
`Control` is removed as a standalone navigation destination.

The functional chain remains:
`Domain → Attention → optional Criticità → optional Attività → Outcome → re-evaluate`.

### RESOLVED — AI duplication
One common project-wide AI drawer is used everywhere.

Domain-specific AI cards are not part of V1.

### RESOLVED — AI authority examples
Generated mockups contain a few example prompts that would imply operational recommendations, e.g. supplier alternatives or actions to reduce risk.

Those prompts are **non-authoritative and must not be implemented**.

Allowed AI behavior is explanatory/assistive:
- show causes;
- compare sources;
- identify missing/conflicting information;
- summarize state;
- explain risk;
- propose extracted information for human confirmation.

AI must not choose suppliers, engineering solutions or operational actions.

### RESOLVED — action duplication
Shared actions belong in the shared shell; local actions remain local.

`Apri in nuova scheda` is removed from the V1 product shell.

`Export` may remain page-local.

### RESOLVED — naming
Use one project-nav vocabulary:
`Overview · Master · Technical · Procurement · Documents · Economics · Billing & Payment · Criticità · Attività · Conversazioni · Storico`.

Generated typos are corrected in implementation without reopening the visual freeze.

### RESOLVED — mock data inconsistencies
Mockups contain illustrative values and may not be mutually coherent across screens (PM names, dates, invoices, amounts, etc.).

They are **visual fixtures, not source facts**.

Implementation must use one coherent project fixture/data set across all screens and must never import mockup values as production data.

## A14 decision

**VISUAL FREEZE MANIFEST: PASS**

The visual freeze consists of:
1. the eight canonical domain-content mockups;
2. `03A_SHARED_UI_SHELL_CONTRACT_V1.md` for shared chrome;
3. the semantic/product/data contracts.

No further image regeneration is required before Astra bootstrap unless a later MODEL GAP is discovered.
