# 04 — INTERACTION CONTRACT V1 — DRAFT

## Global navigation
- Portfolio is the global triage entry point.
- Selecting a project opens its Project Overview.
- The sidebar is app-level and must not duplicate project-domain navigation.
- Project domain screens use one stable project header and one horizontal project navigation bar.
- Project navigation labels/order are identical on all project screens.
- Support surfaces (sources/evidence, history, settings, parties/roles) are on demand and do not compete with primary control navigation.

## Portfolio
- Default ordering is **global control priority before pagination**.
- Clicking a domain header sorts the whole portfolio by severity in that domain, before pagination.
- Clicking a project/domain state drills into that project/domain and preserves context.
- Archived projects are excluded from the operational portfolio by default, remain searchable/filterable and can be reactivated.

## Project Overview
Approved structure:
1. project context;
2. compact clickable domain strip;
3. main exposure;
4. other relevant Attention;
5. compact next significant gate;
6. support/AI on demand.

The Overview does not become a KPI dashboard or duplicate domain detail.

## Master Planner
- Shows selected control milestones/gates, not a detailed planning replacement.
- Target, Forecast and Actual remain distinct.
- Readiness remains distinct from date/status.
- Upstream delay can mark downstream **DA VERIFICARE / possible impact**, not silently move dates.
- User can correct a wrongly linked blocker/dependency with reason/history.

## Procurement
- Header/list must make visible what needs RFQ and by when, what needs an order and by when, and what already threatens project dates.
- `Need Date`, `Supplier Promise`, `Current Forecast`, `Actual Availability` are different meanings.
- Cockpit may create/control a Procurement Item; it does not emit RFQs or POs.

## Technical
- Primary object is a technical decision/condition, not a document.
- Evidence can be mail, KOM, P&ID, specification, report, etc.
- Alignment signal may propose a checkpoint/decision link; it is not automatically a Criticità or Activity.

## Documents
- Primary object is the required logical Document Item.
- Physical files/revisions are evidence/detail.
- Base states: `ATTESO / DISPONIBILE / DA AGGIORNARE / DA VERIFICARE / N/A`.
- Missing/late/critical is derived from relevance, phase/date and adequacy, not a universal workflow state.

## Economics
- Budget, Actual/consuntivo, Committed/impegnato, Forecast and recognized contract value are semantically distinct.
- Change exposure can influence forecast before recognized contract value.
- Drilldown must show the cause of a variance, not only the number.

## Billing
- Controls contractual billing-event maturity against Galileo billing state.
- Does not act as an invoice-management system.

## Payment
- Simple numerical control of real progress vs billed vs collected.
- No collection/credit workflow.

## Control
- Attention / Criticità / Activity / Change / Outcome remain distinct.
- Every operational item links back to the underlying domain cause.
- Activity closure triggers re-evaluation; it does not automatically clear the condition.

## AI drawer
- Common project-wide drawer, closed by default.
- Can answer cross-domain questions and cite/show sources.
- AI proposals must be visibly distinguishable from confirmed facts.
