# 03A — SHARED UI SHELL CONTRACT V1

**Status:** FINAL — APPROVED BY A14 CROSS-SCREEN CONSISTENCY REVIEW.

This contract governs the chrome shared by all screens. It overrides inconsistent navigation/header chrome still visible in individual mockups without reopening their frozen domain-content composition.

## 1. Global sidebar

The sidebar is **app-level only**.

V1 global entries:
- `Portfolio`
- support/settings access as needed

The sidebar must **not** repeat project-domain destinations.

`Control` is not a standalone V1 screen and must not appear in global or project navigation.

## 2. Project navigation

When a project is selected, one horizontal project navigation bar is the single navigation surface for:

`Overview · Master · Technical · Procurement · Documents · Economics · Billing & Payment · Criticità · Attività · Conversazioni · Storico`

Rules:
- exact same labels and order on every project screen;
- page title may be more descriptive (`Master Planner`, `Technical Control`, etc.);
- no separate `Billing` and `Payment` tabs;
- Billing and Payment signals remain semantically distinct but open the same `Billing & Payment` surface, optionally focused to the relevant section.

## 3. Shared project header

Every project screen uses the same project identity/header structure:
- project code;
- client / project name;
- plant/project short description;
- project state;
- client;
- offer/reference;
- PM;
- contract/start date;
- current expected delivery/key project date where configured.

Mockup values are fixtures only and are not authoritative project facts.

## 4. Shared actions

### AI
- exactly one common `AI` button in the shared shell;
- drawer closed by default;
- drawer opens on the right;
- scope = entire selected project;
- current page is only a contextual hint;
- no permanent domain-specific AI card/panel.

### Open in new tab
`Apri in nuova scheda` is **not part of the V1 frozen shell**. Browser-native behavior is sufficient. Do not add it as a recurring product action unless later explicitly approved.

## 5. Local page toolbar

Allowed only for page-specific behavior:
- search;
- filters;
- view mode;
- export when meaningful;
- creation of a Cockpit-owned control object.

Approved examples:
- `Aggiungi Procurement Item`
- `Aggiungi documento richiesto`
- `Nuova decisione`

Forbidden examples:
- `Emetti RFQ`
- `Crea ordine`
- `Emetti fattura`

The Cockpit monitors/co-ordinates; it does not execute those external processes.

## 6. Support functions

`Project Settings`, `Parties & Roles`, sources/evidence and similar support functions are secondary support access, not primary project-domain navigation.

They may be exposed through a project/support menu or contextual drawer.

## 7. Duplication rule

A command/navigation action has one primary home.

If a function would appear both in shared shell and page content, keep it in the shared shell and remove the duplicate from the page.

## 8. Copy normalization

Canonical navigation labels:
- `Overview`
- `Master`
- `Technical`
- `Procurement`
- `Documents`
- `Economics`
- `Billing & Payment`
- `Criticità`
- `Attività`
- `Conversazioni`
- `Storico`

Correct obvious generated-text typos such as `Ecoments` → `Economics` during implementation. Such corrections do not reopen the visual freeze.

## 9. Mockup precedence

Frozen mockups remain authoritative for **domain content composition**.

Where an older mockup chrome conflicts with this contract, **this contract prevails**.
