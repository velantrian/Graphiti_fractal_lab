# 🧊 Frozen Inputs — FM-16 `run_007`

**Immutability:** Do not modify these files during FM-17-pre. Record `sha256` at ablation start.

**Anchor commit (FM-16 complete):** `62cfa45a80ec83794b701d88873ce136b7629354`

## Primary score tables (CE)

| Path | Role |
|------|------|
| `artifacts/memoryops/run_007/scores/ce_calibration.csv` | CAL CE pairs (immutable) |
| `artifacts/memoryops/run_007/scores/ce_test.csv` | TEST CE pairs (immutable) |
| `artifacts/memoryops/run_007/scores/fm15_anchor_recheck.csv` | FM-15 anchor recheck |

Known sha256 (authoring-time verify; re-hash at run):

- `ce_calibration.csv` → `bbfefda784818f795582066973749a6292e9704a7aec9e7faa0ed345aa3d9496`
- `ce_test.csv` → `022416304df33b525b00f2b9eed965ac986120ef49ee080c04dc2e36a514c6fd`
- `fm15_anchor_recheck.csv` → `d81d13ce6a7d87dfeb7d0734ac11134c4c8dd26381943c5c10942bca97cceb54`

## Embedding scores (reference only — not primary arms)

| Path |
|------|
| `artifacts/memoryops/run_007/scores/embedding_calibration.csv` |
| `artifacts/memoryops/run_007/scores/embedding_test.csv` |

## Corpus / gold / HN

| Path |
|------|
| `artifacts/memoryops/run_007/corpus/calibration_facts.json` |
| `artifacts/memoryops/run_007/corpus/calibration_queries.json` |
| `artifacts/memoryops/run_007/corpus/calibration_gold.json` |
| `artifacts/memoryops/run_007/corpus/test_facts.json` |
| `artifacts/memoryops/run_007/corpus/test_queries.json` |
| `artifacts/memoryops/run_007/corpus/test_gold.json` |
| `artifacts/memoryops/run_007/corpus/hard_negative_labels.json` |
| `artifacts/memoryops/run_007/corpus/adversarial_strata_manifest.json` |
| `artifacts/memoryops/run_007/corpus/fm15_anchor.json` |

Corpus hashes: see `artifacts/memoryops/run_007/hashes/frozen_corpus_sha256.json`.

## Evaluation / calibration receipts

| Path |
|------|
| `artifacts/memoryops/run_007/evaluation/ranking_without_threshold.json` |
| `artifacts/memoryops/run_007/evaluation/hard_negative_strata.json` |
| `artifacts/memoryops/run_007/evaluation/no_answer_strata.json` |
| `artifacts/memoryops/run_007/evaluation/adversarial_strata.json` |
| `artifacts/memoryops/run_007/evaluation/broad_query_results.json` |
| `artifacts/memoryops/run_007/evaluation/comparative_verdict.json` |
| `artifacts/memoryops/run_007/calibration/calibrated_thresholds.json` |
| `artifacts/memoryops/run_007/calibration/threshold_freeze_receipt.json` |
| `artifacts/memoryops/run_007/result.json` |
| `artifacts/memoryops/run_007/preregistration.json` |
| `artifacts/memoryops/run_007/findings/*.md` |
| `artifacts/memoryops/run_007/hashes/*` |

Note: FM-16 `THETA_CE` / `THETA_EMBEDDING` remain `null`. FM-17-pre **does not** introduce a new neural threshold as a success criterion.

## Multi-hop component diagnostic donors (text)

| Path | Role |
|------|------|
| `artifacts/memoryops/run_004/result.json` (`Q5_classification`) | Alice/Orion/Python co-retrieval evidence |
| `artifacts/memoryops/run_006/findings/Q5_CO_RETRIEVAL.md` | CE pairwise low on components |
| `artifacts/memoryops/run_006/result.json` | `q5_multi_hop_reasoning=NOT_PROVEN` |

## New artifacts (only when ablation authorized later)

| Path | When |
|------|------|
| `artifacts/memoryops/run_008/oracle_annotations.json` (name TBD) | After hash freeze, before arm compute |
| `artifacts/memoryops/run_008/ablation_result.json` | After arms — **NOT in this protocol commit** |

## Prohibited mutations

- No edits under `artifacts/memoryops/run_007/`
- No rescoring CE/embeddings
- No TEST-driven rule edits after freeze
