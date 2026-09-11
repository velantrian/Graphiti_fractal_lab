# 📊 Preregistered Metrics — FM-17-pre

**Primary verdict must NOT be a single aggregate accuracy.**

Report **separately** for query-class axes:

| Axis code | `query_class` values |
|-----------|----------------------|
| **A** NARROW / DIRECT | `NARROW` |
| **B** STRUCTURED + STATE / SCOPE | `STATE` |
| **C** BROAD / EXPLORATORY | `BROAD` |
| **D** NO-ANSWER | `NO_ANSWER` |
| **E** COMPONENT / MULTI-HOP DIAGNOSTIC | `MULTIHOP` (+ diagnostic_subset) |

Failure on axis C does **not** imply failure on axis A (and vice versa).

## Notation

- For query \(q\), let \(C_q\) be the candidate set from frozen CE scores.
- Let \(S_q^{(arm)}\) be survivors under arm ∈ {A0,A1,A2,A3}.
- Let \(G_q^{DIR}\) = facts with `gold_relevance_class=DIRECT` for \(q\).
- \(G_q^{COMP}\), \(G_q^{REL}\), \(G_q^{NON}\) analogously.
- FM-16 gold empty queries: \(G_q^{DIR}=G_q^{COMP}=\emptyset\).

---

## Per query-class metrics

### DIRECT_GOLD_RECALL

\[
\frac{|\{f \in G_q^{DIR} : f \in S_q\}|}{|G_q^{DIR}|}
\]

Undefined if \(|G_q^{DIR}|=0\); report n/a. Macro-average over queries in the axis with defined values.

### NONANSWER_REJECTION_RATE

\[
\frac{|\{f \in G_q^{NON} : f \notin S_q\}|}{|G_q^{NON}|}
\]

### RELATED_REJECTION_RATE

\[
\frac{|\{f \in G_q^{REL} : f \notin S_q\}|}{|G_q^{REL}|}
\]

### COMPONENT_RETENTION

\[
\frac{|\{f \in G_q^{COMP} : f \in S_q\}|}{|G_q^{COMP}|}
\]

**Required** on axis E / `MULTIHOP_COMPONENT_RETENTION` subset.  
Structural success is **invalid** if this regresses to improve DIRECT precision by deleting required components.

### NO_ANSWER_EMPTY_ACCURACY (axis D)

For `query_class=NO_ANSWER` with empty DIRECT+COMPONENT gold:

\[
\mathbf{1}[S_q = \emptyset]
\]

Macro-average. When empty due to structural rejects, set `STRUCTURALLY_FILTERED_EMPTY=true` on the receipt.

### FALSE_EMPTY_RATE

Among queries with nonempty \(G_q^{DIR}\) (and, on axis E, nonempty \(G_q^{COMP}\)):

\[
\mathbf{1}[S_q = \emptyset]
\]

### NONEMPTY_GOLD_MISS_RATE

Among queries with nonempty \(G_q^{DIR}\):

\[
\mathbf{1}[G_q^{DIR} \cap S_q = \emptyset]
\]

(Survivor nonempty or empty, but all DIRECT gold missing.)

---

## Per HN stratum (FM-16 labels)

For each HN1–HN12 on CAL and TEST splits separately:

| Metric | Definition |
|--------|------------|
| `rejection_rate` | fraction of HN-labeled pairs with fact ∉ survivors |
| `inversion_count_before` | count where HN CE score > min DIRECT gold CE on same query (A0) |
| `inversion_count_after` | same using survivors: HN still in \(S_q\) and ranked above a surviving DIRECT gold under arm order (A0/A2/A3-CE); for A1 use membership-only: HN kept while any DIRECT gold rejected |

---

## Global diagnostics

| Metric | Definition |
|--------|------------|
| `candidate_reduction_ratio` | \(1 - \frac{\sum_q |S_q|}{\sum_q |C_q|}\) |
| `ce_ranking_on_A2_survivors` | MRR / P@k / R@k for DIRECT gold within A2 survivor lists using frozen CE order |
| `n_direct_gold_removed` | count of DIRECT gold facts rejected by structure |
| `n_component_facts_removed` | count of COMPONENT facts rejected (must be 0 under A3 on diagnostic subset) |

---

## Explicitly non-primary

- Single global “accuracy”
- Re-calibrated neural threshold as success criterion
- MemoryKeep composite score
- Embedding-only arms (embeddings may be referenced diagnostically, not as primary arms)
