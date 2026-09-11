# 📊 Preregistered Metrics — FM-17-pre (v1.1)

**Primary verdict must NOT be a single aggregate accuracy.**  
**UNRESOLVED_RATE is a co-primary diagnostic.** No positive conclusion may rest on rejection metrics alone.

Report **separately** for query-class axes:

| Axis code | `query_class` values |
|-----------|----------------------|
| **A / Q-A** NARROW / DIRECT | `NARROW` |
| **B / Q-B** STATE / SCOPE / TEMPORAL | `STATE` |
| **C / Q-C** BROAD / EXPLORATORY | `BROAD` |
| **D / Q-D** NO-ANSWER | `NO_ANSWER` |
| **E / Q-E** COMPONENT / MULTI-HOP DIAGNOSTIC | `MULTIHOP` |

```
SUCCESS ON Q-A ≠ SUCCESS ON Q-C
SUCCESS ON Q-D ≠ SUCCESS ON Q-E
```

## Notation

- \(C_q\): frozen CE candidate set
- \(S_q^{(arm)}\): survivors
- \(G_q^{DIR}\) etc.: from **EVALUATION_OVERLAY** `gold_relevance_class` only (after structural freeze)
- Pair structural state: ACCEPT / REJECT / UNRESOLVED

---

## Co-primary joint report (required for any positive claim)

Any positive A1/A2 conclusion must jointly report:

1. rejection quality (`NONANSWER_REJECTION_RATE`, HN rejection)
2. `DIRECT_GOLD_RECALL`
3. `FALSE_EMPTY_RATE`
4. `UNRESOLVED_RATE`

```
HIGH UNRESOLVED RATE ≠ STRUCTURAL SUCCESS
LOW FALSE REJECTION CAUSED BY "KEEP EVERYTHING UNRESOLVED" ≠ USEFUL QUALIFICATION
```

### UNRESOLVED_RATE

Among pairs with a structural decision:

\[
\frac{|\{(q,f):\ \mathrm{state}(q,f)=\mathrm{UNRESOLVED}\}|}{|\{(q,f)\}|}
\]

Also report per query-class axis.

---

## Per query-class metrics

### DIRECT_GOLD_RECALL

\[
\frac{|\{f \in G_q^{DIR} : f \in S_q\}|}{|G_q^{DIR}|}
\]

Undefined if empty gold; macro-average over defined queries.

### NONANSWER_REJECTION_RATE / RELATED_REJECTION_RATE

Fraction of NONANSWER / RELATED overlay facts with \(f \notin S_q\).

### COMPONENT_RETENTION (A1/A2)

Same formula using \(G_q^{COMP}\) on **A1/A2** (no gold in the filter). This is the **non-tautological** component metric.

### A3_COMPONENT_RETENTION

Reported **separately** as `ORACLE_COMPONENT_IDENTITY_CEILING_DIAGNOSTIC` / integrity check.  
**Not** a primary success gate. A3 forcing KEEP on COMPONENT gold makes retention ≈ 1.0 **partly tautological**.

### NO_ANSWER_EMPTY_ACCURACY (axis D)

\(\mathbf{1}[S_q=\emptyset]\) on overlay-empty DIRECT+COMPONENT queries.  
Bounded claim only: `STRUCTURAL_ORACLE_IMPROVED_NO_ANSWER_DISCRIMINATION_ON_FROZEN_FIXTURE`.  
Not Honest Empty solved.

### FALSE_EMPTY_RATE / NONEMPTY_GOLD_MISS_RATE

As protocol v1.0.

---

## Per HN stratum (EVALUATION overlay only)

HN labels are **not** annotation inputs. After freeze, for each HN1–12:

| Metric | Definition |
|--------|------------|
| `rejection_rate` | HN-labeled pairs with fact ∉ survivors |
| `inversion_count_before` | HN CE > min DIRECT gold CE (A0) |
| `inversion_count_after` | same on survivors |

HN9: see filter-rules TQ11/TF23 `SEMANTIC_DESIGN_LIMITATION`.

---

## Global diagnostics

| Metric | Definition |
|--------|------------|
| `candidate_reduction_ratio` | \(1 - \sum|S_q|/\sum|C_q|\) |
| `ce_ranking_on_A2_survivors` | MRR / P@k / R@k for DIRECT gold within A2 using frozen CE |
| `DIRECT_GOLD_REMOVED_COUNT` | DIRECT overlay facts rejected by A1/A2 |
| `COMPONENT_REMOVED_COUNT` | COMPONENT overlay facts rejected by A1/A2 (A3 excluded from this primary count) |
| `UNRESOLVED_RATE` | co-primary (above) |

---

## Explicitly non-primary

- Single global accuracy / “overall intelligence”
- A3 component retention as A1/A2 success
- Re-calibrated neural threshold
- MemoryKeep composite
- Embedding-only arms
