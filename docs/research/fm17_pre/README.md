# 🧪 FM-17-pre — Structural Oracle Ablation (Protocol Index)

**Status:** PROTOCOL + CHARTER + v1.3.1 EXTERNAL FREEZE ANCHOR GATE FROZEN — **ABLATION NOT EXECUTED**  
**Experiment class:** `TARGETED_MECHANISTIC_ABLATION`  
**Date baseline:** 2026-09-11  
**FM-16 execution anchor:** `62cfa45a80ec83794b701d88873ce136b7629354`  
**Branch:** `experiment/falkordblite-deterministic-memory`

## Purpose (one line)

Measure the **combined ceiling** of perfect **query** structural interpretation **plus** perfect **fact** structural representation on the frozen FM-16 fixture — before extraction, graph, LLM, or SLM investment.

## Primary discrimination question

> On the frozen FM-16 fixture, does oracle-quality query-and-fact typed structure add useful qualification signal beyond CE-only ranking, and does structural→CE residual preserve more useful evidence than structure alone?

**Not asking (yet):** Can Graphiti extract it? Real query understanding? Production? MemoryKeep? Path scorer? Honest Empty solved?

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
14. [annotation_receipt.schema.json](annotation_receipt.schema.json) / [pre_ablation_validation_receipt.schema.json](pre_ablation_validation_receipt.schema.json)


## Arms

- **A0** CE baseline
- **A1** Structural oracle (ACCEPT/REJECT/UNRESOLVED)
- **A2** Structural → CE residual
- **A3** `ORACLE_COMPONENT_IDENTITY_CEILING_DIAGNOSTIC` (not a primary success gate)

## STOP

No annotation of CAL/TEST. No ablation. Next: **SEND REVISED PROTOCOL TO MANUS FOR RE-REVIEW**. Do not assume execution GO.

## Enforcement invariants (v1.3.1)

```
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

v1.3: empty/incomplete package → FAIL; real SHA-256 vs local root.
v1.3.1: `expected_frozen_root` is **mandatory and EXTERNAL** (`--expected-frozen-root`); package-local root is never authoritative. FULL_PACKAGE_PLUS_ROOT_REPLACEMENT → FAIL (T27).
