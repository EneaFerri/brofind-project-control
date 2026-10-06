# 05 — CROSS-DOMAIN DATA CONTRACT MATRIX — DRAFT

This matrix defines the minimum semantic fields Astra must preserve. Exact DB/API schemas are implementation decisions after baseline gap analysis.

| Domain | Minimum control fields | Typical source | Human confirmation / override |
|---|---|---|---|
| Project | project code, client, PM, scope profile, phase, configured sources | Galileo + opening/KOM | scope/phase corrections with history |
| Master Milestone | name, origin, owner, baseline date, target, forecast, actual, status, readiness, dependencies, sensitivity, evidence | contract/KOM/planner/project data | target change/sensitive completion as defined by governance |
| Procurement Item | logical item/lot, category, stage, RFQ-needed-by, order-needed-by, need date(s), supplier promise, current forecast, actual availability, freshness, linked milestones, monitoring owner | Galileo + offers/PO + supplier comms | ambiguous mapping, item override, sensitive implications |
| Technical Decision / Checkpoint | topic, state, confirming role, needed-by, impact links, source/evidence, decision outcome/history | KOM/specifications/mail/docs | confirmation/decision by competent role |
| Technical Alignment Signal | topic, evidence pattern, materiality, affected object, state, recurrence | configured communication/doc sources | transform/link/ignore and reason |
| Document Item | logical requirement, type, responsible role/party, needed-by, base state, latest evidence, adequacy context, linked milestone/object | Document List / Minimum Set / folder | non-deterministic adequacy and register evolution |
| Change Item | description, lifecycle, owner, impact matrix, economic classification, evidence, linked domain objects | human + docs/comms | official creation/outcome/closure |
| Economic VdA | baseline budget, current budget, actual, committed, ETC/forecast state, forecast value, variance, freshness, source, confidence | Galileo + structured Cockpit data | forecast/ETC and authorized budget changes |
| Economic Result | initial contract value, current recognized value, open extra/minus exposure, final cost forecast, expected result/margin | contract/Change + cost forecast | recognition of value changes |
| Billing Event | contractual trigger, expected maturity, evidence, maturity state, Galileo invoice state, tolerance, inconsistency | contract/KOM + Master/Documents + Galileo | ambiguous trigger/evidence |
| Payment | billed amount, collected amount, due/overdue state, project-progress comparator, data freshness | Galileo + project progress method | progress method / exceptional reconciliation |
| Attention | domain condition key, severity/state, explanation, compared values, source, as-of, confidence, owning context | deterministic control layer | ownership/acknowledgement; not semantic rewriting |
| Criticità | underlying condition, impact, owner, lifecycle, evidence, management objective/coverage | human or approved deterministic rule | explicit human governance except approved rule |
| Activity | owner, due date, expected result, status, linked cause, outcome, evidence | Cockpit collaboration state | explicit human assignment/closure |
| Outcome | structured result, author/confirming role, evidence, date | human / AI proposal confirmed by human | confirmation |
| Source Evidence | source type, locator/ref, source date, observed-at, freshness, confidence/verification, project association | all configured sources | ambiguous association/reconciliation |
| History Event | object, previous/new state/value, when, who, why, evidence, causal link | Cockpit | append-only according to domain rules |

## Unresolved items that must be explicitly closed before implementation of the affected slice
- Final numerical method for Payment project-progress comparator.
- Exact economic forecast methodology and double-counting protection.
- Category/default lead times and freshness thresholds.
- Exact Galileo integration mechanism.
- Exact Outlook/project-folder technical adapter.
- Final UI terminology for selected labels.
- Final sensitive-control authorization matrix.


## Billing & Payment presentation rule

Billing and Payment are shown in one V1 surface but remain distinct data semantics. Do not collapse billing-event maturity, invoice state, payment-due state and collection state into one generic status.
