# 03 — VISUAL FREEZE MANIFEST — FINAL

**Status:** A14 PASS — APPROVED VISUAL AUTHORITY FOR ASTRA BOOTSTRAP.

Exactly one canonical visual is admitted for each V1 surface. Shared-shell differences still visible in older mockups are governed by `03A_SHARED_UI_SHELL_CONTRACT_V1.md` and do not reopen frozen domain content.

| Surface | Canonical file | Status | Notes |
|---|---|---|---|
| Portfolio | `PASS_01_Portfolio.png` | PASS | Global triage, domain sorting, principal exposure, archived filter. |
| Project Overview | `PASS_02_Project_Overview.png` | PASS | Monitoring-first: domain strip, principal exposure, other Attention, compact next gate. |
| Master Planner | `PASS_03_Master_Planner.png` | PASS | Target / Forecast / Actual distinct; readiness distinct; downstream dates are not auto-shifted. |
| Economic Control | `PASS_04_Economic_Control.png` | PASS | Budget / Actual / Committed / Forecast / Variance / Result semantics preserved. |
| Technical Control | `PASS_05_Technical_Control.png` | PASS | Primary object = technical decision/condition; evidence and alignment signals linked. |
| Procurement Control | `PASS_06_Procurement_Control.png` | PASS | Stage, next RFQ/Order deadline, Need Date, Supplier Promise, Current Forecast, Control State, Impact. |
| Document Control | `PASS_07_Document_Control.png` | PASS | Primary object = logical Document Item; canonical control states; missing/late derived. |
| Billing & Payment Control | `PASS_08_Billing_Payment_Control.png` | PASS | One chain: contractual maturity → invoiced → payment due → collected. |

## Explicitly rejected / non-authoritative visual concepts

- KPI/card-heavy Project Overview variants replacing the approved monitoring-first hierarchy.
- Document-centric Technical Control variants.
- EDMS-like Document Control variants using `Approved / In review / Late / Not started` as the base model.
- Separate Payment Control screen.
- Standalone Control dashboard.

## Shared shell precedence

`03A_SHARED_UI_SHELL_CONTRACT_V1.md` governs shared chrome:
- sidebar = global/app navigation;
- horizontal bar = project-domain navigation;
- one common project-wide AI drawer;
- no duplicated navigation or commands;
- page-specific actions remain local only where needed.

## Mock-data rule

All amounts, dates, suppliers, counts and percentages in mockups are visual/test examples unless explicitly mapped to authoritative source data. They may be fixtures, never silently production facts.
