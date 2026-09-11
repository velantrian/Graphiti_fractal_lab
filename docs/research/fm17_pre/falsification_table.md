# ⚖️ Falsification / Interpretation Table — FM-17-pre (v1.1)

**Experiment class:** `TARGETED_MECHANISTIC_ABLATION`  
Asks: can explicit **oracle query+fact** structure address **known** FM-16 error classes on this fixture?  
Does **not** establish general-world structural sufficiency.

```
FEATURES INFORMED BY PRIOR FAILURE ANALYSIS ≠ BLIND GENERALIZATION
```

## Operational thresholds (“materially”)

| Phrase | Operationalization |
|--------|--------------------|
| Material HN reduction | Evaluation-overlay HN strata: at least two of {HN2, incompatible-pred HN1, unsupported/no-answer entity mismatch} show `rejection_rate` ↑ ≥ 0.20 absolute vs A0; HN9 reported **separately** with `SEMANTIC_DESIGN_LIMITATION` note (not a universal TF23-irrelevance proof) |
| DIRECT gold preserved | Macro `DIRECT_GOLD_RECALL` on **Q-A** ≥ A0 − **0.05** |
| No-answer improves | Q-D `NO_ANSWER_EMPTY_ACCURACY` ↑ ≥ **0.10** vs A0 **or** reaches 1.0 |
| Broad not materially destroyed | Q-C recall drop ≤ **0.10** vs A0; larger drop = Q-C failure only |
| UNRESOLVED not “success by silence” | `UNRESOLVED_RATE` jointly reported; a high unresolved rate **blocks** a positive useful-qualification claim even if rejection looks good |
| A1/A2 component retention | Report `COMPONENT_RETENTION` on A1/A2 **without** A3 override; regression vs A0 is mixed/negative evidence |
| A3 retention | **Not a success gate.** Integrity check only |

A3 `COMPONENT_RETENTION=1.0` MUST NOT be used as evidence of structural component identification.

---

## Permitted outcome labels

### 1) `ORACLE_QUERY_AND_FACT_STRUCTURAL_REPRESENTATION_HAS_MEASURABLE_VALUE`

When **all** hold on **A1/A2** (not A3):

1. Material HN reduction (table) **and** rejection quality reported
2. DIRECT gold preserved on Q-A
3. No-answer improves on Q-D **or** explicitly not claimed
4. Broad not materially destroyed **or** Q-C-only failure stated
5. `UNRESOLVED_RATE` jointly reported and not functioning as “keep everything”
6. A1/A2 `COMPONENT_RETENTION` does not collapse hop-1 on Q-E (A3 not used here)

**Means only:** combined ceiling of perfect query interpretation **plus** perfect fact representation would materially help **this fixture’s known error classes**.

**Does NOT mean:** extraction · query understanding · production · architecture · Honest Empty · general structural sufficiency.

---

### 2) `STRUCTURAL_THEN_CE_RESIDUAL_SHOWS_ADDITIONAL_VALUE_ON_FROZEN_FIXTURE`

A2 improves over A1 on residual ranking / NONANSWER·RELATED rejection / CE MRR among survivors **without** worsening protected DIRECT recall, A1/A2 component retention, empty behavior, or hiding errors in UNRESOLVED.

---

### 3) `ORACLE_STRUCTURAL_REPRESENTATION_NOT_SUFFICIENT_ON_FIXTURE`

Helps some strata; residuals remain; or UNRESOLVED dominates; or broad still needs semantic qualification; or no-answer vs gold tradeoff.

Valid scientific outcome.

---

### 4) `NO_MEASURABLE_GAIN_FROM_SPECIFIED_ORACLE_STRUCTURAL_REPRESENTATION`

Even under oracle query+fact labels + specified rules, no meaningful improvement vs A0 **or** harms DIRECT gold > 0.05.

**Strongest allowed negative:** the **specified** oracle query-and-fact representation and filter rules did not provide sufficient measurable gain on the frozen fixture.

**Do not conclude:** `STRUCTURE IS USELESS`. Residual explanations remain: ontology too coarse · fields incomplete · broad queries not decidable · rules too strict · fixture lacks structure · semantic interpretation dominates · component information missing · useful only on some strata.

---

### 5) `STRUCTURAL_GAIN_WITH_PROTECTED_RECALL_REGRESSION`

Mixed: some HN/no-answer gain with DIRECT or A1/A2 COMPONENT loss.

### 6) `STRUCTURAL_ORACLE_IMPROVED_NO_ANSWER_DISCRIMINATION_ON_FROZEN_FIXTURE`

Fixture-relative empty result only. **Not** `HONEST_EMPTY_SOLVED`.

---

## Forbidden vocabulary

`SOLVED` · `GENERALIZED` · `UNDERSTANDS` · `PRODUCTION_READY` · `ARCHITECTURE_VALIDATED` · `STRUCTURE_IS_SUFFICIENT` · `STRUCTURE_IS_USELESS` · `HONEST_EMPTY_SOLVED` · `MULTI_HOP_SOLVED` · `CE_OBSOLETE` · `STRUCTURAL_INFORMATION_HAS_MEASURABLE_ORACLE_VALUE` as an **unqualified** primary (superseded by the query+fact combined name)

---

## Axis independence

```
STRUCTURAL FILTER FAILURE ON BROAD ≠ STRUCTURAL FILTER FAILURE ON DIRECT
BROAD RECALL IMPROVEMENT ≠ DIRECT-ANSWER QUALIFICATION
```
