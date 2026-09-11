# ✅🔐 FM-17-pre v1.3.1 — Final Integrity Review

**Date:** 2026-09-11  
**Repository:** `velantrian/Graphiti_fractal_lab`  
**Branch:** `experiment/falkordblite-deterministic-memory`  
**Reviewed SHA:** `080e1959fe6a3d996f2690059fcdc687dd5c832e`  
**Parent:** `f091ba26a5a5eb555cef7ed13cc38ec33671e566`  
**Independent review verdict:** `PASS_WITH_MINOR_FINDINGS`  
**Integrity/protocol GO:** `GO_FOR_OFFLINE_ABLATION = YES`  
**Real annotation:** `NOT_EXECUTED`  
**A0–A3:** `NOT_EXECUTED`  
**Merge/runtime/product/architecture change:** `NO`

> This document is a research-status / integrity-closure record. It does **not** constitute execution authorization and does not establish the structural hypothesis.

## 1. Why FM-17-pre exists

FM-16 / `run_007` established a bounded mixed-task result: the BGE CrossEncoder carried a stronger ranking signal than the embedding baseline, while neither score family supported one feasible global raw threshold under the frozen qualification constraints. That result separated **ranking** from **qualification**.

FM-16 did not establish Honest Empty, structural sufficiency, real query understanding, fact extraction accuracy, or multi-hop reasoning.

FM-17-pre therefore asks a new bounded mechanistic question:

> If query structural interpretation and fact structural representation were oracle-correct, would this combined typed information add measurable qualification value beyond CE-only ranking, and would STRUCTURE → CE RESIDUAL preserve more useful evidence than STRUCTURE ALONE?

Planned arms remain unexecuted:

- **A0** — frozen CE baseline;
- **A1** — structural oracle qualification: `ACCEPT / REJECT / UNRESOLVED`;
- **A2** — structural qualification → CE residual ranking;
- **A3** — `ORACLE_COMPONENT_IDENTITY_CEILING_DIAGNOSTIC`, not a primary success gate.

Protected distinctions:

```text
DIRECT_ANSWER ≠ MULTI_HOP_COMPONENT ≠ RELATED_CONTEXT ≠ NONANSWER
UNKNOWN ≠ MISMATCH
UNRESOLVED ≠ REJECT
ORACLE QUERY INTERPRETATION ≠ REAL QUERY UNDERSTANDING
ORACLE FACT STRUCTURE ≠ REAL EXTRACTION
ORACLE VALUE ≠ DEPLOYABILITY
VALIDATOR PASS ≠ EXPERIMENT SUCCESS
```

## 2. Integrity-hardening lineage

### Initial protocol freeze

`469fe64beee40973753b290e057226dabac59eae`

Created the bounded Structural Oracle Ablation protocol and kept A3 diagnostic-only.

### Measurement Charter

`8aebf70eeed29e75f7fa794d4671ed280f0e06f4`

Made the evidence universe, query strata, candidate roles, loss/metric boundaries, Honest-Empty limitations and multi-hop limitations explicit.

### v1.1 — scientific / anti-leakage repair

`bcad4931f9bebefb67397fb29c210868c5e5f1a0`

Key repairs included:

- prohibited HN/gold-derived structural annotation;
- made the combined query+fact oracle claim explicit;
- isolated A3 as diagnostic-only;
- kept condition semantics gold-independent;
- bounded broad-query scope handling;
- retained `UNRESOLVED_RATE` as a safety/co-primary diagnostic;
- formalized blinded independent A/B annotation plus adjudication.

### v1.2 — fail-closed schema gate

`914ea5c7baa67c2fe5ffbd562b4465f12a7a39e9`

Hardened field provenance, blinding, forbidden access, sanitized input, annotator independence, adjudication and amendment invalidation.

Independent review then found two material fail-open classes:

1. empty/incomplete package could receive `PASS / GO_ALLOWED=true`;
2. hash fields existed without effective content-hash recomputation/verification.

This established:

```text
VALIDATING EVERYTHING PRESENT ≠ VALIDATING THAT EVERYTHING REQUIRED IS PRESENT
HASH FIELD PRESENT ≠ HASH VERIFIED
```

### v1.3 — completeness + real content integrity

`f091ba26a5a5eb555cef7ed13cc38ec33671e566`

Added:

- fail-closed package completeness;
- expected record coverage;
- A/B-derived disagreement set rather than trusting self-reported `disagreement_count`;
- actual SHA-256 recomputation from file bytes / canonical JSON;
- declared-vs-actual hash comparison;
- local manifest/root consistency;
- adversarial T19–T26 and positive P5/P6 paths.

This closed empty/incomplete package, coverage, false-zero-disagreement, wrong-hash, post-freeze-tamper and local-manifest-replacement cases.

Independent adversarial review then found one remaining material root-of-trust path: artifact + hashes + manifest + receipt + package-local root could all be replaced consistently and still pass because the expected root was supplied by the same package.

That established:

```text
INTERNAL HASH CONSISTENCY ≠ PRE-OVERLAY FREEZE AUTHENTICITY
NON-CIRCULAR ROOT ≠ EXTERNALLY HELD ROOT OF TRUST
```

### v1.3.1 — external pre-overlay root

`080e1959fe6a3d996f2690059fcdc687dd5c832e`

v1.3.1 requires an externally supplied expected root:

```text
validate_package(package, expected_frozen_root=R0)
--expected-frozen-root <sha256>
```

The package-local `frozen_root_commitment.root_sha256` remains audit/consistency state. It is not authority and is not used as a fallback.

Effective integrity condition:

```text
EXTERNAL_R0
=
PACKAGE_LOCAL_ROOT
=
ACTUAL_RECOMPUTED_ROOT
```

Missing/malformed/wrong external `R0` fails. A fully replaced package with a new local root `R1` fails when the previously recorded external `R0` is held fixed.

## 3. Final independent meta-gate review

Independent review was performed read-only against exact SHA:

`080e1959fe6a3d996f2690059fcdc687dd5c832e`

Verified cases:

| Case | Meaning | Result |
|---|---|---|
| T27 | Full artifact + hashes + manifest + receipt + local-root replacement against held external `R0` | PASS as rejection test |
| T28 | Missing external expected root | PASS as rejection test |
| T29 | Wrong external expected root | PASS as rejection test |
| P7 | Valid package + correct external `R0` | PASS / `GO_ALLOWED=true` |

Independent full enforcement suite result:

```text
40 passed, 1 warning
```

The warning concerns unrelated pytest `asyncio_mode` configuration and was not classified as an enforcement blocker.

Final independent fields:

```text
VERDICT = PASS_WITH_MINOR_FINDINGS
GO_FOR_OFFLINE_ABLATION = YES
EXTERNAL_ROOT_REQUIRED = YES
PACKAGE_SELF_AUTHORIZATION = CLOSED
FULL_PACKAGE_PLUS_ROOT_REPLACEMENT = REJECTED
PRE_OVERLAY_EXTERNAL_ANCHOR_PROCEDURE = SUFFICIENT
NEW_R1_R2_R3_MATERIAL_BYPASSES = []
ENFORCEMENT_COMPLEXITY_EXHAUSTED = YES
```

`GO_FOR_OFFLINE_ABLATION = YES` is an integrity/protocol verdict only. It does not itself execute or authorize real annotation, evaluation-overlay exposure, A0–A3, runtime changes, model training/download, merge or architecture promotion.

## 4. Two-phase freeze boundary

Any later execution, if separately authorized, must preserve this order:

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

The validator cannot independently prove when or by whom a human recorded `R0`; that remains a procedural limitation rather than a package self-authorization path under this bounded offline one-shot protocol.

## 5. Accepted residual risks

- The validator cannot independently prove the historical time or identity of the actor who recorded external `R0`.
- External-root recording/transport is procedural rather than authenticated by PKI, signatures or an external timestamp authority.
- The unrelated pytest `asyncio_mode` warning remains non-enforcement noise.

The final independent review did not identify a new material `R1 + R2 + R3` bypass from these limitations.

## 6. Methodology findings

```text
POLICY_PASS ≠ SCHEMA_PASS
SCHEMA_PASS ≠ SCIENTIFIC_VALIDITY
VALIDATOR_PASS ≠ EXPERIMENT_SUCCESS
HASH_FIELD_PRESENT ≠ HASH_VERIFIED
INTERNAL_HASH_CONSISTENCY ≠ PRE_OVERLAY_FREEZE_AUTHENTICITY
PASSING_TEST_SUITE ≠ THREAT_MODEL_COMPLETE
TESTED PROPERTIES ≠ ALL RELEVANT FAILURE MODES
```

Passing tests establish the properties they actually exercise; they do not prove completeness of the threat model. Independent adversarial review was useful because it found realistic material paths outside earlier test coverage.

The stop-recursion meta-gate is risk-based:

```text
BLOCK only if:
R1 = concrete INPUT/STATE → BYPASS → INVALID CONSEQUENCE path
AND
R2 = realistically attainable
AND
R3 = material scientific consequence
```

If any of R1/R2/R3 is absent, classify the issue as `ACCEPTED_RESIDUAL_RISK` / `NICE_TO_HAVE` rather than reopen speculative hardening.

## 7. Current scientific state

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

The research boundary has therefore changed from:

> Can the planned experiment itself be trusted enough to run?

To:

> Does the frozen oracle structural mechanism add measurable qualification value beyond the CE-only baseline on the bounded fixture?

That scientific question remains unanswered because the real annotation and ablation have not yet been executed.

## 8. Next action boundary

The next action is **not** another broad integrity redesign.

If the user later separately and explicitly authorizes execution, reopen the frozen FM-17-pre protocol, annotation guide, `STOP_BOUNDARY.md`, external-root procedure and this closure record; then perform the one-shot blinded annotation → external-R0 freeze → post-freeze overlay → A0/A1/A2/A3 offline ablation exactly as frozen.

Until that authorization:

```text
STOP
NO REAL ANNOTATION
NO EVALUATION OVERLAY
NO A0–A3
NO ABLATION
NO MERGE
NO PRODUCT CHANGE
```
