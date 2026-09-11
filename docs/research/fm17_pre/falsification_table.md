# ⚖️ Falsification / Interpretation Table — FM-17-pre

## Operational thresholds (“materially”)

These are **preregistered** for this fixture protocol:

| Phrase | Operationalization |
|--------|--------------------|
| Material HN reduction | On HN9 diagnostic queries: `inversion_count_after = 0` for A1/A2 **or** HN9 `rejection_rate ≥ 0.90` on labeled HN9 pairs; **and** at least two of {HN2, HN1 incompatible-pred, unsupported/no-answer entity mismatch} show `rejection_rate` ↑ by ≥ 0.20 absolute vs A0 membership baseline |
| DIRECT gold preserved | Macro `DIRECT_GOLD_RECALL` on axis **A (NARROW)** ≥ A0 recall − **0.05** absolute |
| No-answer improves | Axis **D** `NO_ANSWER_EMPTY_ACCURACY` ↑ by ≥ **0.10** absolute vs A0 **or** reaches **1.0** |
| Broad not materially destroyed | Axis **C** macro recall over (`DIRECT`∪ broad FM-16 gold mapping) drop ≤ **0.10** absolute vs A0; larger drop = broad-axis failure **without** auto-failing axis A |
| Component retention | On `MULTIHOP_COMPONENT_RETENTION`: `COMPONENT_RETENTION = 1.0` under **A3**; under A1/A2 report value — regression vs keeping hop-1 is a protected failure for “structural success” claims |

---

## Outcome labels

### 1) `STRUCTURAL_INFORMATION_HAS_MEASURABLE_ORACLE_VALUE`
### (alias: `SUPPORTED_AS_USEFUL_SIGNAL`)

When **all** hold:

1. Material HN reduction (table above)
2. DIRECT gold preserved on axis A
3. No-answer improves on axis D
4. Broad not materially destroyed **or** broad failure is explicitly reported as axis-C-only (still require axes A/D/E gates)
5. Component retention does not regress on protected diagnostic under **A3** (`COMPONENT_RETENTION=1.0`)

**Means only:** if the system had correct structural information, it would materially help the tested relevance problem.

**Does NOT mean:** extraction works · query parsing works · production feasibility · runtime routing · graph implementation · architecture authorization · implementation readiness.

---

### 2) `STRUCTURAL_SIGNAL_NOT_SUFFICIENT`

When structure helps some strata **but**:

- residual no-answer / broad / semantic errors remain after correct structure; **or**
- broad still needs semantic qualification; **or**
- no-answer cannot be separated without harming gold on axis A; **or**
- component preservation **conflicts** with strict structural rejection (A1 hurts E while A3 is required to save components)

This is a **valid scientific outcome**, not a protocol failure.

---

### 3) `STRUCTURAL_SIGNAL_FALSIFIED_FOR_THIS_FIXTURE`

When **even under oracle-quality labels**:

- structural arms provide **no meaningful improvement** over A0 on preregistered HN/no-answer metrics; **or**
- materially harm protected DIRECT gold (axis A drop > 0.05) **or** forced component loss that A3 cannot justify without emptying the diagnostic

---

### 4) `H-E_STRUCTURAL_THEN_CE_RESIDUAL_SUPPORTED_AS_USEFUL_SIGNAL`

When:

- A2 improves over A1 on residual ranking / NONANSWER·RELATED rejection / CE MRR among survivors
- **without** worsening protected DIRECT recall, COMPONENT retention (A3 diagnostic), or no-answer empty behavior beyond preregistered tolerances

---

## Axis independence reminder

```
STRUCTURAL FILTER FAILURE ON BROAD
≠ STRUCTURAL FILTER FAILURE ON DIRECT

BROAD RECALL IMPROVEMENT
≠ DIRECT-ANSWER QUALIFICATION
```
