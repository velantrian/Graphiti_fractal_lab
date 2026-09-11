# 🧪 FM-17-pre — Structural Oracle Ablation (Protocol Index)

**Status:** PROTOCOL + CHARTER + v1.3.1 EXTERNAL FREEZE ANCHOR GATE FROZEN — **INTEGRITY REVIEW PASSED · ABLATION NOT EXECUTED**  
**Experiment class:** `TARGETED_MECHANISTIC_ABLATION`  
**Date baseline:** 2026-09-11  
**FM-16 execution anchor:** `62cfa45a80ec83794b701d88873ce136b7629354`  
**Final reviewed integrity SHA:** `080e1959fe6a3d996f2690059fcdc687dd5c832e`  
**Final independent integrity verdict:** `PASS_WITH_MINOR_FINDINGS`  
**Integrity/protocol GO:** `GO_FOR_OFFLINE_ABLATION = YES`  
**Real annotation / overlay / A0–A3:** `NOT_EXECUTED`  
**Branch:** `experiment/falkordblite-deterministic-memory`

> `GO_FOR_OFFLINE_ABLATION = YES` is an integrity/protocol verdict only. It does **not** itself authorize or execute real annotation, evaluation-overlay exposure, A0–A3, merge, runtime/product change, model execution, or architecture promotion.

## Purpose (one line)

Measure the **combined ceiling** of perfect **query** structural interpretation **plus** perfect **fact** structural representation on the frozen FM-16 fixture — before extraction, graph, LLM, or SLM investment.

## Primary discrimination question

> On the frozen FM-16 fixture, does oracle-quality query-and-fact typed structure add useful qualification signal beyond CE-only ranking, and does structural→CE residual preserve more useful evidence than structure alone?

**Not asking (yet):** Can Graphiti extract it? Real query understanding? Production? MemoryKeep? Path scorer? Honest Empty solved?

## Current scientific state

```text
FM17_PRE_INTEGRITY_GATE = READY
FM17_PRE_FINAL_REVIEW = PASS_WITH_MINOR_FINDINGS
GO_FOR_OFFLINE_ABLATION = YES  [INTEGRITY / PROTOCOL VERDICT ONLY]

REAL_ANNOTATION = NOT_EXECUTED
EVALUATION_OVERLAY_EXPOSED = NO
A0_A1_A2_A3 = NOT_EXECUTED
STRUCTURAL_VALUE = NOT_ESTABLISHED
QUERY_UNDERSTANDING = NOT_ESTABLISHED
EXTRACTION_ACCURACY = NOT_ESTABLISHED
HONEST_EMPTY = NOT_ESTABLISHED
MULTI_HOP = NOT_PROVEN
RUNTIME_CHANGE = NO
PRODUCT_CHANGE = NO
ARCHITECTURE_PROMOTION = NO
MERGE = NO
```

## Reading order

1. [FM17_PRE_MEASUREMENT_CHARTER.md](FM17_PRE_MEASUREMENT_CHARTER.md) — claims / anti-leakage
2. [FM17_PRE_STRUCTURAL_ORACLE_PROTOCOL.md](FM17_PRE_STRUCTURAL_ORACLE_PROTOCOL.md) — master protocol
3. [ORACLE_ANNOTATION_GUIDE.md](ORACLE_ANNOTATION_GUIDE.md) — blinded A/B annotation
4. [oracle_annotations.schema.json](oracle_annotations.schema.json) — field-level provenance
5. [sanitized_annotation_input.schema.json](sanitized_annotation_input.schema.json) — annotator view format
6. [annotation_receipt.schema.json](annotation_receipt.schema.json) — freeze receipt
7. [preregistered_filter_rules.md](preregistered_filter_rules.md)
8. [preregistered_metrics.md](preregistered_metrics.md) — includes co-primary `UNRESOLVED_RATE`
9. [falsification_table.md](falsification_table.md)
10. [oracle_annotations.template.jsonl](oracle_annotations.template.jsonl) — EXAMPLE_NOT_GOLD
11. [FROZEN_RUN007_INPUTS.md](FROZEN_RUN007_INPUTS.md)
12. [STOP_BOUNDARY.md](STOP_BOUNDARY.md)
13. [validate_fm17_pre_package.py](validate_fm17_pre_package.py) — integrity validator (**≠ relevance judge**)
14. [pre_ablation_validation_receipt.schema.json](pre_ablation_validation_receipt.schema.json)
15. [EXTERNAL_FREEZE_ANCHOR.md](EXTERNAL_FREEZE_ANCHOR.md) — mandatory external pre-overlay `R0`
16. [FM17_PRE_V1_3_1_FINAL_INTEGRITY_REVIEW_2026-09-11.md](FM17_PRE_V1_3_1_FINAL_INTEGRITY_REVIEW_2026-09-11.md) — final independent integrity closure

## Arms

- **A0** CE baseline
- **A1** Structural oracle (`ACCEPT / REJECT / UNRESOLVED`)
- **A2** Structural → CE residual
- **A3** `ORACLE_COMPONENT_IDENTITY_CEILING_DIAGNOSTIC` (not a primary success gate)

## Integrity-hardening lineage

```text
469fe64  initial protocol freeze
→ 8aebf70  Measurement Charter
→ bcad493  v1.1 anti-leakage / combined-oracle / A3 / broad / unresolved repair
→ 914ea5c  v1.2 fail-closed schema gate
→ f091ba2  v1.3 package completeness + A/B-derived disagreement + actual SHA-256
→ 080e195  v1.3.1 mandatory external pre-overlay expected root
→ independent Manus meta-gate: PASS_WITH_MINOR_FINDINGS
```

Key lessons from the hardening chain:

```text
VALIDATING EVERYTHING PRESENT ≠ VALIDATING THAT EVERYTHING REQUIRED IS PRESENT
HASH FIELD PRESENT ≠ HASH VERIFIED
INTERNAL HASH CONSISTENCY ≠ PRE-OVERLAY FREEZE AUTHENTICITY
NON-CIRCULAR ROOT ≠ EXTERNALLY HELD ROOT OF TRUST
PASSING TEST SUITE ≠ THREAT MODEL COMPLETE
```

## Final external-root integrity boundary

v1.3.1 requires the expected root from outside the package:

```text
EXTERNAL_R0
=
PACKAGE_LOCAL_ROOT
=
ACTUAL_RECOMPUTED_ROOT
```

The package-local `frozen_root_commitment` is audit/consistency state only. It is never an authority fallback.

The final independent review at exact SHA `080e1959fe6a3d996f2690059fcdc687dd5c832e` established:

```text
EXTERNAL_ROOT_REQUIRED = YES
PACKAGE_SELF_AUTHORIZATION = CLOSED
FULL_PACKAGE_PLUS_ROOT_REPLACEMENT = REJECTED
T27 = PASS
T28 = PASS
T29 = PASS
P7 = PASS
FULL_TEST_SUITE = 40 passed, 1 warning
PRE_OVERLAY_EXTERNAL_ANCHOR_PROCEDURE = SUFFICIENT
NEW_R1_R2_R3_MATERIAL_BYPASSES = []
ENFORCEMENT_COMPLEXITY_EXHAUSTED = YES
```

The warning is the unrelated pytest `asyncio_mode` configuration warning.

## Required two-phase freeze order for any later authorized execution

```text
BLIND ANNOTATION
→ ADJUDICATION
→ STRUCTURAL PACKAGE FINALIZED
→ HASH ROOT R0 COMPUTED
→ R0 RECORDED OUTSIDE PACKAGE
→ FREEZE
→ ONLY THEN EVALUATION OVERLAY
→ validator receives the previously recorded external R0
→ A0–A3 only after integrity PASS
```

## Accepted residual risks

- Validator cannot independently prove when or by whom external `R0` was recorded.
- External-root recording/transport is procedural rather than authenticated by PKI/signature/timestamp infrastructure.
- Unrelated pytest `asyncio_mode` warning remains non-enforcement noise.

The final independent review did not classify these as new material `R1 + R2 + R3` bypasses for this bounded offline one-shot protocol.

## Enforcement invariants

```text
POLICY_PASS ≠ SCHEMA_PASS
SCHEMA_PASS ≠ SCIENTIFIC_VALIDITY
VALIDATOR_PASS ≠ EXPERIMENT_SUCCESS
BLINDED ≠ CORRECT
PROVENANCE ≠ TRUTH
HASH_MATCH ≠ SEMANTIC_CORRECTNESS
TARGETED_MECHANISTIC_ABLATION ≠ GENERALIZATION
ORACLE VALUE ≠ DEPLOYABILITY
INVALID INPUT → FAIL CLOSED → STOP
```

Adversarial tests: `tests/lab/test_fm17_pre_schema_enforcement.py` (T1–T29 fail-closed, P1–P7 pass).

## STOP / next action boundary

The integrity-hardening/review phase is closed.

The next scientific action, **only if separately and explicitly authorized by the user**, is the one-shot:

```text
blinded A/B annotation
→ adjudication
→ external R0 freeze
→ post-freeze evaluation overlay
→ integrity validation against held R0
→ A0/A1/A2/A3 offline ablation
→ bounded interpretation
```

Until that separate authorization:

```text
STOP
NO REAL ANNOTATION
NO EVALUATION OVERLAY
NO A0–A3
NO ABLATION
NO MERGE
NO PRODUCT CHANGE
```
