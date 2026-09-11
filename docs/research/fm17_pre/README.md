# 🧪 FM-17-pre — Structural Oracle Ablation (Protocol Index)

**Status:** PROTOCOL + MEASUREMENT CHARTER FROZEN — **ABLATION NOT EXECUTED**  
**Date baseline:** 2026-09-11  
**Protocol commit:** `469fe64beee40973753b290e057226dabac59eae`  
**FM-16 execution anchor:** `62cfa45a80ec83794b701d88873ce136b7629354`  
**Branch:** `experiment/falkordblite-deterministic-memory`

## Purpose (one line)

Measure the **upper bound** of usefulness of **explicit structural information** under **oracle-quality annotations**, before investing in extraction, graph traversal, LLM recognition, or a fine-tuned memory-relevance model.

## Primary discrimination question

> On the frozen FM-16 fixture, does oracle-quality typed structural information add useful relevance/qualification signal beyond CE-only ranking, and does structural→CE residual composition preserve more useful evidence than structural qualification alone?

**Not asking (yet):** Can Graphiti extract it? Should production use it? Does MemoryKeep work? Should we build a path scorer? Is Honest Empty solved?

## Reading order

1. [FM17_PRE_MEASUREMENT_CHARTER.md](FM17_PRE_MEASUREMENT_CHARTER.md) — **what may be measured / claimed**
2. [FM17_PRE_STRUCTURAL_ORACLE_PROTOCOL.md](FM17_PRE_STRUCTURAL_ORACLE_PROTOCOL.md) — master protocol
3. [preregistered_filter_rules.md](preregistered_filter_rules.md) — MATCH/MISMATCH/UNKNOWN/N/A
4. [preregistered_metrics.md](preregistered_metrics.md) — metrics
5. [falsification_table.md](falsification_table.md) — outcome labels
6. [oracle_annotations.schema.json](oracle_annotations.schema.json) + [ORACLE_ANNOTATION_GUIDE.md](ORACLE_ANNOTATION_GUIDE.md)
7. [oracle_annotations.template.jsonl](oracle_annotations.template.jsonl) — examples only (NOT gold)
8. [FROZEN_RUN007_INPUTS.md](FROZEN_RUN007_INPUTS.md)
9. [STOP_BOUNDARY.md](STOP_BOUNDARY.md)

## Documents

| File | Role |
|------|------|
| [FM17_PRE_MEASUREMENT_CHARTER.md](FM17_PRE_MEASUREMENT_CHARTER.md) | Measurement charter (claims / anti-leakage) |
| [FM17_PRE_STRUCTURAL_ORACLE_PROTOCOL.md](FM17_PRE_STRUCTURAL_ORACLE_PROTOCOL.md) | Master protocol |
| [oracle_annotations.schema.json](oracle_annotations.schema.json) | Annotation JSON Schema |
| [oracle_annotations.template.jsonl](oracle_annotations.template.jsonl) | Example template rows (NOT gold) |
| [ORACLE_ANNOTATION_GUIDE.md](ORACLE_ANNOTATION_GUIDE.md) | How to annotate |
| [preregistered_filter_rules.md](preregistered_filter_rules.md) | Exact MATCH/MISMATCH/UNKNOWN/N/A rules |
| [preregistered_metrics.md](preregistered_metrics.md) | Metric definitions |
| [falsification_table.md](falsification_table.md) | Outcome → interpretation |
| [FROZEN_RUN007_INPUTS.md](FROZEN_RUN007_INPUTS.md) | Immutable run_007 inputs |
| [STOP_BOUNDARY.md](STOP_BOUNDARY.md) | Authorization / stop |

## Arms (offline only)

- **A0** CE baseline (frozen scores)
- **A1** Structural oracle only
- **A2** Structural → CE residual
- **A3** Component-preserving **ORACLE_DIAGNOSTIC** (segregated; not deployable evidence)

## STOP

No ablation results in this commit. Await user decision: **A** fixes · **B** independent review · **C** authorize offline ablation · **D** defer.
