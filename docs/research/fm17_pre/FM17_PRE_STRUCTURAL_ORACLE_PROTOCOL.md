# 🔬 FM-17-pre — STRUCTURAL ORACLE ABLATION PROTOCOL

**Document type:** PROTOCOL ONLY (no results)  
**Date baseline:** 2026-09-11  
**Lab repo:** `velantrian/Graphiti_fractal_lab`  
**Branch:** `experiment/falkordblite-deterministic-memory`  
**FM-16 anchor HEAD:** `62cfa45a80ec83794b701d88873ce136b7629354`  
**Mode:** OFFLINE · BOUNDED · EVIDENCE-FIRST · ANTI-DRIFT  
**Experiment class:** `TARGETED_MECHANISTIC_ABLATION`  
**Repair:** v1.1 anti-leakage / annotation integrity  

---

## 0. Header locks

### Scientific question

> On the frozen FM-16 fixture, does **oracle-quality query-and-fact typed structure** add useful qualification signal beyond CE-only ranking, and does structural→CE residual preserve more useful evidence than structure alone?

### Purpose

Measure the **upper bound** of usefulness of explicit structural information under **oracle-quality annotations**, **before** investing in:

- real extraction,
- graph traversal,
- LLM recognition,
- a fine-tuned memory-relevance model.

### Explicitly NOT asking (yet)

| Not asking | Why deferred |
|------------|--------------|
| Can Graphiti extract this structure? | Oracle ≠ predicted |
| Should production retrieval use structure? | No runtime authorization |
| Does MemoryKeep work? | Donor-only |
| Should we build a graph path scorer? | Out of scope features |

### Interpretation locks

```
ORACLE STRUCTURE          ≠  PREDICTED STRUCTURE
ORACLE QUERY INTERPRETATION ≠ REAL QUERY UNDERSTANDING
ORACLE FACT STRUCTURE     ≠  REAL EXTRACTION
COMBINED QUERY+FACT CEILING ≠ DEPLOYABLE PIPELINE
ORACLE FILTER PASS        ≠  REAL STRUCTURED PIPELINE PASS
ORACLE_QUERY_AND_FACT_STRUCTURAL_REPRESENTATION_HAS_MEASURABLE_VALUE
                          ≠  ARCHITECTURE / RUNTIME AUTHORIZATION
A3 COMPONENT RETENTION    ≠  A1/A2 COMPONENT IDENTIFICATION
```

A positive result means **only**:

> If **correct query structural interpretation and correct fact structural representation** were available, that **combined** information would materially help **this fixture’s known error classes**.

It does **not** establish extraction accuracy, query parsing accuracy, production feasibility, runtime routing, graph implementation, or architecture authorization.

### Authority

- ❌ No runtime Graphiti / MemoryOps change  
- ❌ No merge to main / upstream Fractal  
- ❌ No training / new model download as part of this protocol  
- ❌ No new architecture / product change  
- ✅ Offline ablation over **frozen** FM-16 `run_007` artifacts **only when later authorized**

---

## 1. Background (verified baseline — pointer)

FM-16 / `run_007` established (live artifacts):

- `GENERALIZATION = GLOBAL_THRESHOLD_NOT_FEASIBLE` (CE and embedding)
- both θ `null`
- `CE_VS_EMBEDDING = NO_MATERIAL_GAIN` under global-θ rules
- ranking-without-threshold still shows useful pairwise CE signal
- `scope_discrimination = PARTIAL` (HN9 inversions)
- broad gold score regime overlaps no-answer QUERY_MAX
- no runtime CE gate authorized

See `artifacts/memoryops/run_007/result.json` and `docs/research/fm17_pre/FROZEN_RUN007_INPUTS.md`.

---

## 2. Protected distinctions

### 2.1 Relevance classes

```
DIRECT_ANSWER
≠ MULTI_HOP_COMPONENT
≠ RELATED_CONTEXT
≠ NONANSWER
```

Report separately:

- `DIRECT_GOLD_RECALL`
- `COMPONENT_RETENTION` / `COMPONENT_RECALL`
- `RELATED_REJECTION`
- `NONANSWER_REJECTION`

**Do not collapse into one relevance label.**

### 2.2 Component-retention diagnostic (mandatory)

**Example:**

- Alice → works_on → Orion  
- Orion → uses → Python  

**Query:** *What language does Alice's project use?*

| Fact | `gold_relevance_class` |
|------|------------------------|
| Alice → works_on → Orion | **COMPONENT** (never ordinary NONANSWER) |
| Orion → uses → Python | **DIRECT** for decomposed second hop / final-answer evidence |

A structural filter is **not** considered successful if it improves direct-answer precision by deleting facts required for multi-hop.

Arm **A3** encodes the component-preserving override for this diagnostic subset.

### 2.3 Query-class axes (mandatory separate reporting)

| Axis | Name | `query_class` |
|------|------|---------------|
| A | NARROW / DIRECT | `NARROW` |
| B | STRUCTURED + STATE / SCOPE | `STATE` |
| C | BROAD / EXPLORATORY | `BROAD` |
| D | NO-ANSWER | `NO_ANSWER` |
| E | COMPONENT / MULTI-HOP DIAGNOSTIC | `MULTIHOP` |

```
STRUCTURAL FILTER FAILURE ON BROAD
≠ STRUCTURAL FILTER FAILURE ON DIRECT

BROAD RECALL IMPROVEMENT
≠ DIRECT-ANSWER QUALIFICATION
```

---

## 3. Arms (minimal — no extras)

| Arm | Name | Definition |
|-----|------|------------|
| **A0** | CE BASELINE | Frozen CE ordering from `run_007`. **No new threshold.** |
| **A1** | STRUCTURAL ORACLE ONLY | Apply frozen oracle structural constraints. CE not used for keep/reject. |
| **A2** | STRUCTURAL → CE RESIDUAL | Same structural KEEP set as A1; order survivors by frozen CE `RAW_SCORE`. |
| **A3** | `ORACLE_COMPONENT_IDENTITY_CEILING_DIAGNOSTIC` | Gold-aware COMPONENT KEEP on diagnostic subset **only**; not a primary success gate. |

### Not in this experiment

LLM judge · fine-tuned SLM · graph path scorer · MemoryKeep α/β/γ/δ · new embedding model · query-conditioned neural threshold · hop count · edge centrality · PPR · graph distance · confidence · freshness weighting · provenance quality scoring.

---

## 4. Structural features in scope

1. entity  
2. predicate / relation  
3. role / direction  
4. scope  
5. temporal state  
6. polarity  
7. condition  
8. attribution  

Exact MATCH / MISMATCH / UNKNOWN / NOT_APPLICABLE tables:  
→ [`preregistered_filter_rules.md`](preregistered_filter_rules.md)

**UNKNOWN ≠ FALSE.** UNKNOWN must not be treated as MISMATCH.

---

## 5. Oracle annotations

- Schema: [`oracle_annotations.schema.json`](oracle_annotations.schema.json)
- Guide: [`ORACLE_ANNOTATION_GUIDE.md`](ORACLE_ANNOTATION_GUIDE.md)
- Template (NOT gold): [`oracle_annotations.template.jsonl`](oracle_annotations.template.jsonl)

STRUCTURAL annotations: raw query/fact + frozen ontology/rulebook only.  
**Forbidden inputs:** gold sets, `gold_relevance_class`, HN labels, CE/embedding scores/ranks.  
Field-level provenance required. Independent blinded annotators A/B + adjudication.  
If independent annotation unavailable → `INDEPENDENT_ANNOTATION_AVAILABLE=NO` and **STOP**.  
EVALUATION_OVERLAY (gold/HN) attaches only after STRUCTURAL freeze. See annotation guide v1.1.

---

## 6. No-answer semantics

Keep distinct:

```
NO_CANDIDATES
≠ NO_RELEVANT_MEMORY
≠ STRUCTURALLY_FILTERED_EMPTY
≠ RETRIEVAL_FAILURE
```

If `run_007` has candidates but oracle structure rejects all:

- `STRUCTURALLY_FILTERED_EMPTY = true`
- May support a **fixture-local** reading of `NO_RELEVANT_MEMORY` **only if** frozen gold for that query is empty
- **Must not** claim: “the system knows the fact does not exist”

---

## 7. Metrics

Full definitions: [`preregistered_metrics.md`](preregistered_metrics.md)

Minimum set:

**Per query class:** DIRECT_GOLD_RECALL · NONANSWER_REJECTION_RATE · RELATED_REJECTION_RATE · COMPONENT_RETENTION (A1/A2) · NO_ANSWER_EMPTY_ACCURACY · FALSE_EMPTY_RATE · NONEMPTY_GOLD_MISS_RATE · **UNRESOLVED_RATE (co-primary)**  

**Per HN stratum:** rejection rate · inversion count before/after filtering  

**Global:** candidate reduction ratio · CE ranking on A2 survivors · # DIRECT gold removed · # COMPONENT facts removed  

---

## 8. Falsification / interpretation

Full table: [`falsification_table.md`](falsification_table.md)

| Label | Short meaning |
|-------|----------------|
| `ORACLE_QUERY_AND_FACT_STRUCTURAL_REPRESENTATION_HAS_MEASURABLE_VALUE` | Combined query+fact oracle ceiling helps this fixture |
| `STRUCTURAL_THEN_CE_RESIDUAL_SHOWS_ADDITIONAL_VALUE_ON_FROZEN_FIXTURE` | A2 > A1 |
| `ORACLE_STRUCTURAL_REPRESENTATION_NOT_SUFFICIENT_ON_FIXTURE` | Residuals / UNRESOLVED dominate |
| `NO_MEASURABLE_GAIN_FROM_SPECIFIED_ORACLE_STRUCTURAL_REPRESENTATION` | Specified rules/representation: no gain vs A0 |
| `STRUCTURAL_GAIN_WITH_PROTECTED_RECALL_REGRESSION` | Mixed |

Do **not** require that structure “solve everything.”

---

## 9. Donor context (non-criteria)

| Source | Classification |
|--------|----------------|
| MemoryKeep | **SPECIFICATION / HYPOTHESIS DONOR** |
| Amadeus | **ANECDOTAL PRACTITIONER SIGNAL** |
| Reddit provenance+timestamp practitioner | **ANECDOTAL PRACTITIONER SIGNAL** |

They may motivate hypotheses. They **must not** define success criteria or expected numeric outcomes.

---

## 10. Procedure (when ablation later authorized)

1. Confirm `run_007` file hashes vs [`FROZEN_RUN007_INPUTS.md`](FROZEN_RUN007_INPUTS.md).  
2. Complete `oracle_annotations` → schema validate → **sha256 freeze receipt**.  
3. Compute A0–A3 offline only (no rescoring).  
4. Write receipts + metrics by axis A–E.  
5. Emit interpretation label(s) from falsification table.  
6. STOP — no runtime promotion.

**This commit stops before step 2–5 execution.**

---

## 11. Frozen inputs

See [`FROZEN_RUN007_INPUTS.md`](FROZEN_RUN007_INPUTS.md).

---

## 12. v1.1 semantic rule changelog (explicit)

1. **Annotation inputs:** RULE_DERIVED may not use HN labels or gold sets.  
2. **CONDITION:** unspecified query + conditional fact → `UNKNOWN`/`UNRESOLVED` (removed gold-DIRECT guidance).  
3. **PREDICATE × MULTIHOP:** N/A keyed off `query_class` from query text, not COMPONENT gold.  
4. **SCOPE × BROAD:** default `scope_target=any`; no gold/HN backsolve.  
5. **TQ11/TF23:** `SEMANTIC_DESIGN_LIMITATION`; HN9 rejection ≠ TF23 universally irrelevant.  
6. **A3:** renamed `ORACLE_COMPONENT_IDENTITY_CEILING_DIAGNOSTIC`; not a primary success gate.  
7. **UNRESOLVED_RATE:** co-primary; high unresolved ≠ success.  
8. **Claim:** combined query+fact ceiling name replaces unqualified oracle-value label.  
9. **Independence:** two blinded annotators + adjudication, or STOP (`INDEPENDENT_ANNOTATION_AVAILABLE=NO`).

## 13. STOP boundary

See [`STOP_BOUNDARY.md`](STOP_BOUNDARY.md).

Next user decision only: **A** fixes · **B** independent review · **C** authorize offline ablation · **D** cancel/defer.  
**Do not assume C.**

---

## 14. Self-review checklist

- [x] Oracle pass is **not** described as implementation readiness  
- [x] DIRECT and COMPONENT are separate  
- [x] Broad queries reported on a separate axis  
- [x] UNKNOWN is not treated as FALSE / MISMATCH  
- [x] No-answer states are separated  
- [x] Structural rules are exact (decision tables), not prose-only  
- [x] No new neural score is introduced  
- [x] Frozen `run_007` scores remain immutable  
- [x] No TEST-driven rule tuning is permitted  
- [x] MemoryKeep is donor-only  
- [x] No architecture promotion  
- [x] No runtime authorization  

---

## 15. Machine-readable stub

```json
{
  "protocol": "FM-17-pre_STRUCTURAL_ORACLE_ABLATION",
  "status": "PROTOCOL_FROZEN_NOT_EXECUTED",
  "fm16_anchor_head": "62cfa45a80ec83794b701d88873ce136b7629354",
  "arms": ["A0", "A1", "A2", "A3"],
  "positive_label": "ORACLE_QUERY_AND_FACT_STRUCTURAL_REPRESENTATION_HAS_MEASURABLE_VALUE",
  "experiment_class": "TARGETED_MECHANISTIC_ABLATION",
  "a3": "ORACLE_COMPONENT_IDENTITY_CEILING_DIAGNOSTIC",
  "a3_primary_success_gate": false,
  "implementation_readiness_authorized": false,
  "runtime_authorized": false,
  "merge_authorized": false,
  "ablation_authorized": false,
  "awaiting": ["A_FIXES", "B_INDEPENDENT_REVIEW", "C_AUTHORIZE_OFFLINE_ABLATION", "D_CANCEL_DEFER"]
}
```
