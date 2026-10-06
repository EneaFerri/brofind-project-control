# 02 — ASTRA AUTHORITY AND BOUNDARIES

## Product identity

Brofind Project Control / Cockpit is a **Project Monitoring, Control and Coordination Layer** over Brofind's existing systems and processes.

Canonical monitoring chain:

`BASELINE / TARGET → OBSERVED → FORECAST → VARIANCE → ATTENTION → optional CRITICITÀ → optional ACTIVITY → OUTCOME → re-evaluate reality`

## Non-negotiable boundaries

- External authoritative systems remain authoritative.
- Cockpit is not ERP, procurement execution, engineering software, detailed Gantt/CPM, full EDMS, accounting, CRM or Service Management.
- UI cannot introduce workflow/domain semantics.
- Normal project progress is not an Activity.
- Attention is not Criticità.
- Criticità is not Activity.
- Closing Activity does not automatically resolve Criticità.
- Conversation is not Outcome.
- Change Item is distinct from Criticità.
- AI is assistive, not decision authority.
- Missing / stale / uncertain data must be visible and must never be silently represented as healthy.
- History/provenance must be preserved.
- Automation-first / no duplicate entry: when a configured source reliably provides a fact, the user should not have to re-enter it.

## AI boundary

The common AI drawer may:
- search and summarize project information;
- explain why a status/Attention is shown;
- compare sources;
- identify missing or conflicting information;
- propose links/checkpoints/outcomes/forecast inputs;
- prepare drafts and summaries.

It may not:
- choose suppliers;
- select engineering solutions;
- authorize cost;
- change contractual obligations;
- resolve ambiguous conflicting facts by authority;
- close technical decisions autonomously;
- create definitive workflow actions unless an explicitly approved deterministic rule authorizes it.

## Source boundary

Configured project sources can include:
- Galileo project data;
- project document folder;
- project Outlook/communication container;
- planner source;
- explicit uploaded/linked sources.

Ambiguous project association requires confirmation.

## Implementation authority rule

Astra must distinguish:
- **semantic authority**: product/architecture/workflow documents;
- **visual authority**: one canonical mockup per frozen surface;
- **implementation detail**: reversible unless constrained by the above.

If a visual cannot be implemented because data/architecture is insufficient, Astra must report an **IMPLEMENTATION GAP** rather than redesign the page.

## Mockup AI prompt rule

Generated AI prompt examples in mockups are non-authoritative.

Do not implement prompts or behaviors that ask AI to choose suppliers, propose engineering solutions, select operational alternatives, authorize cost or recommend a course of action.

Replace such examples with explanatory/source-based questions consistent with the AI boundary.
