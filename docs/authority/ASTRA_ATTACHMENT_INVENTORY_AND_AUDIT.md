# ASTRA ATTACHMENT INVENTORY AND AUDIT — 2026-10-05

## Target attachment set

### A. Mandatory authority / handoff documents
1. `00_ASTRA_HANDOFF_MANIFEST_FINAL.md` — **TO CREATE / FINALIZE**
2. `01_USABLE_CONTROL_COCKPIT_V1_PRODUCT_SCOPE_FREEZE_v1.0.md` — **RECOVERED / PASS**
3. `02_ARCHITECTURE_MONITORING_LAYER_AND_WORK_EXECUTION_BOUNDARY_FINAL.md` — **SOURCE RECOVERED; CLEAN CONSOLIDATION NEEDED**
4. `03_OPERATIONAL_WORKFLOW_AND_COLLABORATION_CONTRACT_FINAL.md` — **TO CREATE from approved freezes / Product Scope**
5. `04_ASTRA_AUTHORITY_AND_BOUNDARIES_FINAL.md` — **RECOVERED; minor final review needed**
6. `05_UI_VISUAL_GOVERNANCE_AND_SHARED_SHELL_FINAL.md` — **SOURCES RECOVERED; CONSOLIDATION NEEDED**
7. `06_VISUAL_FREEZE_MANIFEST_FINAL.md` — **RECOVERED / PASS subject to physical 8-image presence**
8. `07_A14_VISUAL_CONSISTENCY_AUDIT.md` — **RECOVERED / PASS**
9. `08_INTERACTION_CONTRACT_V1_FINAL.md` — **DRAFT RECOVERED; UPDATE REQUIRED**
10. `09_DATA_CONTRACT_V1_FINAL.md` — **DRAFT RECOVERED; A15 REQUIRED**
11. `10_ACCEPTANCE_AND_TEST_CONTRACT_V1_FINAL.md` — **DRAFT RECOVERED; FINAL REVIEW REQUIRED**
12. `11_PRE_ASTRA_READINESS_CHECKLIST_FINAL.md` — **CURRENT CHECKLIST RECOVERED; FINAL UPDATE REQUIRED**
13. `12_ASTRA_READ_ONLY_BOOTSTRAP_PROMPT_FINAL.md` — **DRAFT RECOVERED; FINAL UPDATE REQUIRED**

### B. Mandatory visual authority
14. `V01_Portfolio.png` — **RECOVERED / PASS**
15. `V02_Project_Overview.png` — **RECOVERED / PASS**
16. `V03_Master_Planner.png` — **RECOVERED / PASS**
17. `V04_Economic_Control.png` — **RECOVERED / PASS**
18. `V05_Technical_Control.png` — **RECOVERED / PASS**
19. `V06_Procurement_Control.png` — **RECOVERED / PASS**
20. `V07_Document_Control.png` — **RECOVERED / PASS**
21. `V08_Billing_Payment_Control.png` — **RECOVERED / PASS**

### C. Reference-only context
22. `REFERENCE_BROFIND_PROJECT_WORKFLOW_AS-IS_STUDY_v1.0.md` — **RECOVERED / REFERENCE ONLY; NOT PRODUCT AUTHORITY**

## V5 package audit

The previous `PRE_ASTRA_READINESS_PACK_V5_2026-10-05.zip` is incomplete and must not be used as the Astra handoff package.

Observed defects:
- only 3 of the 8 canonical visuals are physically included (Procurement, Document, Billing & Payment);
- Portfolio, Project Overview, Master, Economics and Technical visuals are missing;
- `00_READ_ME_FIRST.md` still lists blockers already resolved by A14;
- `04_INTERACTION_CONTRACT_V1_DRAFT.md` still describes Billing and Payment separately and a standalone Control section;
- `05_DATA_CONTRACT_MATRIX_DRAFT.md` is explicitly incomplete (A15 not closed);
- `06_ACCEPTANCE_GATES_AND_TESTS_DRAFT.md` is still draft;
- `07_ASTRA_BOOTSTRAP_PROMPT_DRAFT.md` is still draft and references authority documents not physically present in the pack;
- the old `UI_GOVERNANCE_VISUAL_LANGUAGE_V1.md` states Figma is visual authority, while the current A14 decision uses eight canonical frozen mockups + Shared UI Shell Contract. It must be reconciled before attachment;
- the package contains correction-history micro-contracts (A08/A09/etc.) that should be consolidated into final contracts rather than force Astra to reconstruct precedence.

## Exclusions from the final core Astra package

Do not attach as authority:
- `COCKPIT_CORE_PRINCIPLES_FREEZE_v1_DRAFT.md`;
- old scope/governance drafts;
- old UI semantic/UI freeze human-review files if they conflict with the 04/10 Product Scope Freeze and A14 decisions;
- old economic-first implementation plan as execution authority;
- rejected/experimental mockups;
- separate Payment mockup;
- document-centric Technical mockup;
- standalone Control mockup.

Historical implementation-plan material may be consulted later only as reference during baseline gap analysis.

## Readiness conclusion

**Attachment inventory: complete.**

**Final Astra package: NOT READY YET.**

Before final packaging:
1. close A15 Data Contract;
2. update/finalize Interaction Contract for combined Billing & Payment and no standalone Control;
3. finalize Acceptance/Test Contract;
4. reconcile UI Governance with A14 visual authority;
5. create clean Architecture + Operational/Collaboration consolidated contracts;
6. finalize checklist, handoff manifest and Astra bootstrap prompt;
7. run one final cross-document contradiction scan;
8. package exactly the 22 items listed above.
