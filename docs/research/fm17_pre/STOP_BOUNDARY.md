# 🛑 STOP BOUNDARY — FM-17-pre

## CURRENT REVIEWED STATE

**Final reviewed implementation SHA:** `080e1959fe6a3d996f2690059fcdc687dd5c832e`  
**Independent integrity verdict:** `PASS_WITH_MINOR_FINDINGS`  
**Integrity/protocol verdict:** `GO_FOR_OFFLINE_ABLATION = YES`  
**Real annotation:** `NOT_EXECUTED`  
**Evaluation overlay:** `NOT_EXPOSED`  
**A0–A3:** `NOT_EXECUTED`  
**Runtime / product / architecture change:** `NO`  
**Merge:** `NO`

> `GO_FOR_OFFLINE_ABLATION = YES` means the integrity/protocol gate is sufficient for the bounded offline one-shot oracle ablation. It is **not** itself user authorization to execute annotation or ablation.

## AUTHORIZED NOW

- ✅ Maintain protocol / schema / guide documentation
- ✅ Preserve preregistered A0–A3 rules and metrics
- ✅ Preserve frozen `artifacts/memoryops/run_007` references
- ✅ Preserve the v1.3.1 external-root integrity procedure
- ✅ Record independent review results and documentation-only follow-up
- ❌ **DO NOT MERGE** to main / upstream Fractal

## NOT AUTHORIZED NOW

- ❌ Start real CAL/TEST annotation
- ❌ Expose the evaluation overlay
- ❌ Execute FM-17-pre A0/A1/A2/A3
- ❌ Produce ablation `result.json` / survivor receipts as completed run
- ❌ Rescore CE or embeddings outside the already frozen protocol
- ❌ Download / train a new model
- ❌ Run LLM recognition experiment
- ❌ Run graph / path experiment
- ❌ Run specialized SLM experiment
- ❌ Modify Graphiti runtime / search recipe
- ❌ Architecture promotion / product change
- ❌ Treat oracle success as implementation readiness
- ❌ Fabricate a second annotator
- ❌ Use gold/HN/CE/embedding/evaluation-overlay information to build A1/A2 STRUCTURAL fields

## FINAL INDEPENDENT INTEGRITY REVIEW

Exact reviewed SHA:

`080e1959fe6a3d996f2690059fcdc687dd5c832e`

Final independently reported checks:

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
VERDICT = PASS_WITH_MINOR_FINDINGS
GO_FOR_OFFLINE_ABLATION = YES
```

The warning concerns unrelated pytest `asyncio_mode` configuration and is not an enforcement blocker.

## External-root trust boundary

The package-local `frozen_root_commitment` is audit/consistency state only. It is **not** authority and must never be used as a fallback expected root.

A valid integrity GO requires:

```text
EXTERNAL_R0
=
PACKAGE_LOCAL_ROOT
=
ACTUAL_RECOMPUTED_ROOT
```

The external expected root must be recorded outside the package before evaluation-overlay exposure and supplied independently to validation.

Missing, malformed or wrong external `R0` → `FAIL / GO_ALLOWED=false`.

Full replacement of artifact + package hashes + manifest + receipt + package-local root with a new `R1` cannot self-authorize when the previously recorded external `R0` is held fixed.

## Required execution boundary if user later authorizes option C

```text
BLIND ANNOTATION
→ INDEPENDENT A/B SUBMISSION
→ ADJUDICATION
→ STRUCTURAL PACKAGE FINALIZED
→ HASHES COMPUTED
→ ROOT R0 COMPUTED
→ R0 RECORDED OUTSIDE PACKAGE
→ FREEZE
→ STOP
→ ONLY THEN EVALUATION OVERLAY
→ VALIDATE AGAINST PREVIOUSLY RECORDED --expected-frozen-root R0
→ A0–A3 ONLY IF INTEGRITY PASS
→ BOUNDED RESULT / INTERPRETATION
```

The validator cannot prove by itself when or by whom `R0` was historically recorded. That remains an accepted procedural limitation under this bounded experiment; it does not allow package self-authorization.

## User decision only

| Code | Decision |
|---|---|
| **A** | REQUEST NEW FIXES — only if a new material R1+R2+R3 bypass is demonstrated |
| **B** | DEFER / CANCEL |
| **C** | AUTHORIZE THE FROZEN OFFLINE ORACLE ANNOTATION + ABLATION |

**Current protocol eligibility:** C may now be considered.  
**Current execution authorization:** C has **not** been given merely by the independent review.

## Meta-gate / stop-recursion rule

A future enforcement finding blocks only if all three hold:

```text
R1 = concrete INPUT/STATE → BYPASS → INVALID CONSEQUENCE path
AND
R2 = realistically attainable
AND
R3 = material scientific consequence
```

If any is absent, classify the issue as `ACCEPTED_RESIDUAL_RISK` / `NICE_TO_HAVE`; do not reopen speculative hardening.

`ENFORCEMENT_COMPLEXITY_EXHAUSTED = YES` means no broad theoretical hardening is requested. It does **not** mean a future demonstrated material bypass must be ignored.

## Interpretation lock

```text
ORACLE STRUCTURE ≠ PREDICTED STRUCTURE
ORACLE FILTER PASS ≠ REAL STRUCTURED PIPELINE PASS
COMBINED QUERY+FACT ORACLE CEILING ≠ DEPLOYABLE PIPELINE
A3 COMPONENT RETENTION ≠ A1/A2 COMPONENT IDENTIFICATION
HIGH UNRESOLVED RATE ≠ STRUCTURAL SUCCESS
VALIDATOR PASS ≠ EXPERIMENT SUCCESS
GO_FOR_OFFLINE_ABLATION ≠ ABLATION EXECUTED
RESEARCH ≠ RUNTIME
LAB ≠ PRODUCT
```

## Accepted residual risks

- Validator cannot independently prove when/by whom external `R0` was recorded.
- External-root recording/transport is procedural rather than PKI/signature/timestamp authenticated.
- Unrelated pytest `asyncio_mode` warning remains non-enforcement noise.

## Current STOP

Until the user separately authorizes option C:

```text
STOP
NO REAL ANNOTATION
NO EVALUATION OVERLAY
NO A0–A3
NO ABLATION
NO MERGE
NO PRODUCT CHANGE
```
