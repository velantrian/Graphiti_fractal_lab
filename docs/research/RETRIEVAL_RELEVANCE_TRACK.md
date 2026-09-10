# 🔬 Graphiti Fractal Lab — Retrieval Relevance Research Track

> **Status:** CURRENT RESEARCH TRACK  
> **Scope:** `velantrian/Graphiti_fractal_lab` · branch `experiment/falkordblite-deterministic-memory`  
> **Updated:** 2026-09-10  
> **Evidence authority:** exact Git state + executable artifacts under `artifacts/memoryops/run_00X/`  
> **Runtime authority:** NONE — this document does not activate or authorize Fractal runtime changes.

## 🤖 AI / human short rule

Read this file to understand **why the experiments exist and what they established**. For a factual experiment claim, open the linked `result.json`, score matrix, pytest receipt, model fingerprint, and exact commit. Narrative summary is navigation, not proof.

```text
RESEARCH SUMMARY ≠ EXECUTABLE EVIDENCE
LAB RESULT ≠ PRODUCTION AUTHORIZATION
RETRIEVAL ≠ RELEVANCE ≠ EVIDENCE ≠ TRUTH
NO_RELEVANT_RESULT ≠ ENTITY_PROVEN_ABSENT
```

## 🎯 Research question

The active Fractal/Graphiti retrieval family can generate broad candidates, but a nonblank query can still surface comparatively high-ranked facts that do not actually answer the query. The research track therefore asks:

```text
broad candidates
      ↓
query ↔ candidate relevance discrimination
      ↓
retain / reject
      ↓
possibly honest EMPTY
```

This is a **query-time relevance** problem. It is not a storage, provenance, Canon, belief, permission, or temporal-authority problem.

## 📍 Current frontier

| Stage | Question | Evidence-bound result | Status |
|---|---|---|---|
| FM-13 | Where does measured retrieval noise first enter? | BM25 introduces broad candidates; RRF preserves them; CE was not invoked. | ✅ COMPLETED |
| FM-14 | Are real semantic embeddings alone sufficient? | Real BGE geometry improves, but final hybrid filtering remains insufficient; Zephyr still returns four false positives. | ✅ COMPLETED |
| FM-15 | Does a real pairwise Cross-Encoder provide a useful query↔fact signal? | Yes on the frozen 4-fact fixture. Strong pairwise discrimination observed; no threshold/runtime gate authorized. | ✅ COMPLETED |
| FM-16 v1 protocol | Does the signal generalize under held-out calibration + adversarial negatives? | Independent pre-scoring audit found methodological defects in gold semantics and success criteria. No scorer was run. | 🔴 REQUEST_CHANGES_BEFORE_SCORING / SUPERSEDED |
| FM-16 hardened protocol | Direct-answer ranking + global-threshold feasibility, with corrected labels and separate multi-hop diagnostics. | Not yet preregistered/executed. | ⏳ NEXT / NOT_RUN |

**Current next action:** finalize the hardened FM-16 protocol before preregistration or scoring. Do not run the superseded protocol text.

---

## FM-13 — Search-path diagnosis

**Evidence:** `artifacts/memoryops/run_004/`

Observed on the frozen Q1–Q5 fixture:

- effective path was Graphiti edge hybrid BM25 + cosine → RRF;
- `cross_encoder_calls_total = 0`;
- Q4 `Who works on Project Zephyr?` had no gold-relevant facts but returned all four stored facts;
- MemoryOps was pass-through for the measured edge ordering/facts;
- artifact classification: `FIRST_DEGRADATION_LAYER = BM25_CANDIDATE_GENERATION`.

Interpretation ceiling:

> Broad BM25 candidate generation is not itself a defect; the observed failure is that later fusion/selection did not reject query-irrelevant candidates on this fixture.

The artifact labels Q5 as `MULTI_HOP`; this research ledger uses the stricter interpretation **CO_RETRIEVAL_ONLY / MULTI_HOP_REASONING_NOT_PROVEN**.

---

## FM-14 — Real embedding differential

**Evidence:** `artifacts/memoryops/run_005/`

One experimental variable changed from deterministic embeddings to a real local semantic embedder (`BAAI/bge-small-en-v1.5`). Extraction control passed.

Result:

- Q1–Q3 macro `Precision@1 = 1.0`, `Recall@3 = 1.0`, `MRR = 1.0`;
- lower-rank noise remained (`Precision@3 = 0.4444`, `Precision@4 = 0.3333`);
- Q4 Zephyr still returned four unrelated facts;
- artifact conclusion: `EMBEDDING_IMPROVEMENT_CONFIRMED BUT SEARCH_PIPELINE_FILTERING_STILL_INSUFFICIENT`;
- `NEO4J_CAUSAL_EVIDENCE = NO`.

```text
REAL EMBEDDINGS IMPROVED GEOMETRY
≠
REAL EMBEDDINGS SOLVED FINAL RELEVANCE FILTERING
```

The full FM-14 pairwise cosine matrix happened to be separable for the tiny fixture, so later CE work must not claim that embeddings had zero separability.

---

## FM-15 — Real Cross-Encoder separability

**Evidence:** `artifacts/memoryops/run_006/`

Recorded scorer:

```text
model: BAAI/bge-reranker-v2-m3
revision: 953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e
weight_sha256: d9e3e081faff1eefb84019509b2f5558fd74c1a05a2c7db22f74174fcedb5286
Graphiti client: BGERerankerClient
pair_count: 20
runtime search CE: OFF
threshold tuning: NONE
```

Observed CE matrix highlights:

| Query | Gold / relevant behavior | Hard-negative / no-answer behavior |
|---|---|---|
| Q1 `Who works on Project Orion?` | F1 `0.974169` | best non-gold `0.030276` |
| Q2 `What language does Project Orion use?` | F2 `0.997204` | best non-gold `0.013468` |
| Q3 `What is related to Project Nova?` | F3 `0.049960`, F4 `0.032244` | best non-gold ≈ `0.000021` |
| Q4 `Who works on Project Zephyr?` | gold = ∅ | max candidate `0.007880` |
| Q5 `Does Alice use Python?` | all pairs `gold_relevant=false` in FM-15 | F1 `0.023136`, F2 `0.005334` |

FM-15 established a **useful pairwise query↔fact relevance signal on this frozen fixture under its original gold definition**. It did not establish generalization or a production threshold.

Important non-claims:

- FM-14 embeddings were also mathematically separable on this tiny pair matrix;
- cosine and CE sigmoid scores are different scales;
- `NEW_SEPARABILITY_VS_EMBEDDINGS = NOT_ESTABLISHED`;
- `PAIRWISE_CE_SIGNAL = CONFIRMED_ON_FIXTURE`;
- Q5 was explicitly not direct-support gold in FM-15; co-retrieval did not prove multi-hop reasoning.

### Q5 boundary discovered during later review

Claude Opus identified a conditional counterexample that matters for **future task definition**.

If a later protocol reclassifies Q5's intermediate F2 `Project Orion uses Python` as required primary relevance gold, then:

```text
Q5 F2 required component score = 0.005334
Q4 Zephyr best false score     = 0.007880
```

To preserve Q5 F2, `θ <= 0.005334` would be required. To reject Q4's best false candidate, `θ > 0.007880` would be required. No single θ can satisfy both.

This does **not** retroactively falsify FM-15 because FM-15 explicitly labels Q5 pairs non-gold. It does establish that a changed task definition can destroy the toy threshold interval.

New mandatory distinction:

```text
DIRECT ANSWER
≠
MULTI-HOP / ANSWER-SUPPORT COMPONENT
≠
RELATED CONTEXT
```

---

## 🔴 FM-16 v1 — Independent protocol audit before scoring

**Status:** `REQUEST_CHANGES_BEFORE_SCORING / SUPERSEDED_FOR_EXECUTION`.

The independent audit was read-only. It verified the then-live branch had advanced only by documentation commits, `run_006` artifacts remained intact, `run_007` did not exist, and FM-16 had not run.

### Critical finding 1 — relevance ≠ positive support

The superseded protocol incorrectly allowed examples where a direct negative answer was labelled as a hard negative merely because it negated a proposition.

Example:

```text
Q: Does X support Y?
F1: X supports Y.          → relevant answer: YES
F2: X does not support Y. → relevant answer: NO
```

Both can be relevant to the information need. A query↔fact relevance scorer should not be punished for recognizing a direct negative answer.

New invariant:

```text
RELEVANT_ANSWER
≠
SUPPORTS_POSITIVE_PROPOSITION
```

The same issue affects conditional and numeric yes/no examples. Gold relevance must be defined by the information need, not preferred polarity.

### Critical finding 2 — `GENERALIZATION_STRONG` could pass with zero useful filtering

The old success criteria allowed a counterexample where:

- all answerable queries retain gold;
- all no-answer queries become EMPTY;
- no semantic inversion occurs;
- yet every answerable query still returns all 40 candidates;
- hard-negative rejection = 0%.

Therefore `GENERALIZATION_STRONG` must include an explicit preregistered **hard-negative rejection / returned-set quality** requirement, not only recall and no-answer EMPTY.

Also distinguish:

```text
ALL_NON_GOLD_REJECTION
≠
HARD_NEGATIVE_REJECTION
```

### Additional mandatory hardening

Before scoring, the revised protocol must also define:

1. **No feasible calibration threshold:** `threshold = null`; thresholded test metrics = `NOT_APPLICABLE`; no fallback threshold.
2. **Threshold-free held-out analysis:** after `threshold=null` is frozen/hashed, raw TEST ranking metrics may still be computed; null only disables thresholded metrics.
3. **Model identity:** verify the actually loaded CE/embedding snapshot/weights/tokenizer/config/inference profile, not only a cached revision string.
4. **Exact metric definitions:** denominators, tie handling, threshold comparator, candidate threshold set, selected-set precision, and verdict precedence.
5. **Exact verdict table:** labels such as `BETTER`, `MIXED`, `GENERALIZATION_PARTIAL`, `FAILED`, and systematic inversion must be defined before scoring.
6. **Leakage-safe ordering:** preregistration → model fingerprint verification → calibration scoring → threshold freeze/null freeze → test scoring/reporting → anchor regression.
7. **Claim ceiling:** 800 query×fact pairs are matrix entries, not 800 independent statistical observations.
8. **Scorer failure semantics:** timeout/NaN/missing score ≠ successful EMPTY.
9. **Numeric hard-negative floor:** the need for a floor is accepted; any concrete value such as `0.85` remains unadopted until justified and preregistered.

---

## 🧠 Post-review synthesis: Perplexity + Gemini + Claude Opus

### Perplexity

Primarily confirmed the direction: the problem is candidate qualification / honest EMPTY, not a need to invent a new architectural organ. It reinforced preregistration, hard-negative rejection, no-forced-refill, and donor-boundary discipline.

### Gemini

Helped structure evaluation labels/metrics, especially separating primary relevance from polarity/temporal/scope diagnostics. Useful direction, but two suggestions are **not adopted as fixed rules**:

- a concrete hard-negative rejection floor of `0.85` has no current evidence-based justification;
- negation/numeric/temporal classes cannot be marked universally relevant or irrelevant without considering the query information need.

### Claude Opus

Added the most important new task-boundary insight:

- FM-15 remains valid under its original Q5 non-gold definition;
- if multi-hop answer-support components are promoted into the same primary threshold gold, the FM-15 score matrix already provides a counterexample to one global threshold;
- broad associative queries may occupy a different score regime from narrow factoid queries;
- larger negative candidate sets make global-threshold fragility a plausible **pre-experiment hypothesis**, not an established result.

---

## 🧪 FM-16 hardened protocol — current required shape

FM-16 should now isolate two primary hypotheses:

```text
H1 — DIRECT RANKING
Can the frozen score family rank direct answers above hard negatives on unseen data?

H2 — GLOBAL ABSOLUTE GATE
Can one calibration-derived global threshold separate direct answers from non-answers while preserving recall and honest EMPTY?
```

A third hypothesis is explicitly separate:

```text
H3 — COMPONENT RETRIEVAL
Can retrieval retain facts that are not direct answers by themselves but are needed for multi-hop/compositional answering?
```

Current rule:

> FM-16 tests H1 + H2. Q5-like multi-hop components remain separate diagnostics / future experiment and do not silently enter primary threshold gold.

The primary FM-16 evaluation gold should be **direct-answer relevance**, not training target and not positive entailment.

Suggested diagnostic dimensions may include:

- answer polarity;
- temporal fit;
- scope fit;
- condition fit;
- attribution fit;
- numeric/relation fit;
- broad-vs-narrow query class;
- multi-hop component marker.

These diagnostics do not automatically determine primary relevance.

### Broad-query challenge

Q3 `What is related to Project Nova?` demonstrates that broad associative relevance may have much lower absolute scores than narrow factoid relevance.

```text
NARROW FACTOID RELEVANCE
≠
BROAD ASSOCIATIVE RELEVANCE
```

Broad queries should remain an explicit challenge stratum with explicit gold semantics because they can falsify the single-global-threshold hypothesis.

### Threshold feasibility

`GLOBAL_THRESHOLD_NOT_FEASIBLE` is a valid outcome and a plausible pre-experiment prediction, but it is **not established before FM-16**.

If calibration finds no feasible threshold:

```text
threshold = null
thresholded TEST metrics = NOT_APPLICABLE
```

After that null decision is frozen/hashed, threshold-free held-out ranking/generalization evaluation may still proceed.

---

## 🧩 Donor map — research context only

| Donor | Useful lesson | Boundary |
|---|---|---|
| 🗿 Titan | `selected/discarded + reason`, thresholded attention shape, typed no-signal precedent | Titan trust/confidence/risk/epistemic policy must not become Fractal relevance authority. |
| 💠 Crystal | preregistered hard-negative/no-recall-loss evaluation discipline; adversarial strata | Canon/evidence admission is not query relevance. |
| 🧬 Native Kernel | relevance/similarity/rank must not independently establish epistemic validity; UNKNOWN ≠ FALSE | invariant donor only. |
| 🦞 OpenClaw | broad candidate window, separate ranking signals, index identity; threshold-vs-recall tension | lexical fallback after failed strict score can defeat honest EMPTY; do not copy thresholds. |
| 🔬 SVL | applicability/UNKNOWN/fail-closed validation pattern | temporal applicability ≠ semantic query relevance. |
| EITI | empty-capable selectors and forced-top-k/fallback as a negative example | never refill rejected candidates merely to guarantee output count. |
| 🕸 Fractal experience applicability | `retrieved ≠ applicable`, per-candidate receipt, all-rejected output inside Fractal | tool/environment compatibility ≠ general semantic relevance. |

```text
DONOR_REFERENCE ≠ ADOPTED_RUNTIME
SIMILAR GATE SHAPE ≠ SHARED OWNER
```

## 🛡️ Research invariants

```text
RESEARCH ≠ RUNTIME
TESTED ≠ PRODUCTION AUTHORIZED
RETRIEVED ≠ RELEVANT
RELEVANT ≠ SUPPORTS_POSITIVE_PROPOSITION
DIRECT ANSWER ≠ MULTI-HOP COMPONENT ≠ RELATED CONTEXT
NARROW FACTOID RELEVANCE ≠ BROAD ASSOCIATIVE RELEVANCE
RELEVANCE ≠ EVIDENCE
RELEVANCE ≠ TRUTH
EVIDENCE ≠ BELIEF
BELIEF ≠ TRUTH
MODEL/JUDGE SCORE ≠ AUTHORITY
NO_RELEVANT_RESULT ≠ FACT FALSE
NO_RELEVANT_RESULT ≠ ENTITY ABSENT
NOT RETRIEVED ≠ ABSENT
TEMPORAL APPLICABILITY ≠ SEMANTIC RELEVANCE
SCORER_FAILURE ≠ HONEST_EMPTY
GOLD LABEL ≠ TRAINING TARGET
```

## 📚 Evidence routing

```text
exact branch / exact commit
  > run-specific executable artifacts + pytest receipts
  > lab experiment code
  > RESEARCH_STATUS.md
  > this explanatory track
  > external/cross-project donor summaries
```

## 🤖 Machine-readable current summary

```yaml
track: retrieval_relevance
scope: Graphiti_fractal_lab
status: IN_PROGRESS
upstream_runtime_changed: false
architecture_change: false
new_relevance_module_justified: false
fm13:
  status: COMPLETED
fm14:
  status: COMPLETED
fm15:
  status: COMPLETED
  pairwise_ce_signal: CONFIRMED_ON_FIXTURE
  new_separability_vs_embeddings: NOT_ESTABLISHED
  q5_primary_gold: false
  q5_co_retrieval: YES
  q5_multi_hop_reasoning: NOT_PROVEN
fm16:
  status: PLANNED_NOT_RUN
  protocol_v1: REQUEST_CHANGES_BEFORE_SCORING_SUPERSEDED
  preregistration: NOT_CREATED
  run_007: NOT_CREATED
  scorer_run: false
  primary_target: DIRECT_ANSWER_RELEVANCE
  h1_direct_ranking: TO_TEST
  h2_global_absolute_gate: TO_TEST
  h3_multi_hop_component_retrieval: SEPARATE_HYPOTHESIS
  hard_negative_rejection_floor: TO_BE_PREREGISTERED
  threshold_null_branch: REQUIRED
  threshold_free_test_after_null_freeze: ALLOWED
  generalization: INCONCLUSIVE
  next: FINALIZE_HARDENED_PROTOCOL_BEFORE_PREREGISTRATION_AND_SCORING
runtime_gate: NOT_IMPLEMENTED
global_threshold: NOT_ESTABLISHED
```

## ⛔ Stop boundary

Do not execute the superseded FM-16 v1 protocol. Until a hardened preregistered version exists and is independently reviewable, do not run scoring, choose a runtime threshold, activate Cross-Encoder in Fractal search, implement `NO_RELEVANT_MEMORY`, or create a new relevance subsystem.
