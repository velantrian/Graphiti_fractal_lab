# 🧪 FM-17-pre — Structural Oracle Ablation (Protocol Index)

**Status:** PROTOCOL + CHARTER + v1.1 ANTI-LEAKAGE REPAIR FROZEN — **ABLATION NOT EXECUTED**  
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

## Arms

- **A0** CE baseline
- **A1** Structural oracle (ACCEPT/REJECT/UNRESOLVED)
- **A2** Structural → CE residual
- **A3** `ORACLE_COMPONENT_IDENTITY_CEILING_DIAGNOSTIC` (not a primary success gate)

## STOP

No annotation of CAL/TEST. No ablation. Next: **SEND REVISED PROTOCOL TO MANUS FOR RE-REVIEW**. Do not assume execution GO.
