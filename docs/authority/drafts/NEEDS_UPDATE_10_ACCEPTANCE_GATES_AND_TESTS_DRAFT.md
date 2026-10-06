# 06 — ACCEPTANCE GATES AND TEST CONTRACT — DRAFT

A screen or slice is not complete merely because it renders.

## Gate 1 — Authority compliance
PASS when:
- implementation cites the exact semantic and visual authority used;
- no rejected/experimental mockup is treated as canonical;
- no UI behavior introduces new domain/workflow semantics.

## Gate 2 — Data semantics
PASS when:
- Target/Baseline, Observed/Actual, Forecast and Variance are not conflated;
- source/as-of/freshness/confidence are available where required;
- missing data is never rendered as healthy;
- mock values are not production facts.

## Gate 3 — Domain rules
Examples:
- Master upstream delay does not silently shift downstream dates.
- Procurement Promise ≠ Forecast ≠ Need Date.
- Activity close does not resolve Criticità automatically.
- Document missing/critical condition derives from relevance/date.
- AI proposal does not become confirmed fact without the required rule/human confirmation.

## Gate 4 — Automated tests
At minimum:
- domain unit tests for derived states and transitions;
- API/projection tests;
- role/authorization tests for writes;
- import/reconciliation regression tests;
- stable deduplication for deterministic Attention;
- history preservation tests;
- regression of existing stable-baseline behaviors.

## Gate 5 — Visual verification
For each canonical screen:
- structure and section order match the frozen mockup;
- data states match the semantic contract;
- no unauthorized extra cards/sections/actions;
- desktop target is readable;
- AI drawer does not permanently consume screen width when closed;
- missing/partial/unavailable states render correctly.

## Gate 6 — Real Brofind pilot
Use a small set of real projects covering:
- healthy project;
- early economic variance;
- contractual milestone risk;
- procurement item before PO and after PO;
- stale supplier forecast;
- technical decision awaiting client;
- missing/insufficient document relevant to a gate;
- matured billing event not aligned in Galileo;
- collection lag vs project progress;
- Change Item with economic exposure;
- Activity completed but underlying condition persists.

PASS requires user validation that the cockpit reveals useful control information earlier or more reliably than the current process without forcing duplicate data entry.
