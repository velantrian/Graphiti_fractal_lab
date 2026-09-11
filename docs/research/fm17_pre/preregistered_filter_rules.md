# 📐 Preregistered Filter Rules — FM-17-pre

**Status:** FROZEN for protocol review  
**UNKNOWN ≠ FALSE** — never treat `UNKNOWN` as `MISMATCH`.

## Feature decision vocabulary

For each applicable feature comparison, emit exactly one of:

| Label | Meaning |
|-------|---------|
| `MATCH` | Explicit compatibility |
| `MISMATCH` | Explicit incompatibility |
| `UNKNOWN` | Insufficient annotation to decide |
| `NOT_APPLICABLE` | Feature not used for this query_class / query target |

---

## 1. ENTITY

**Inputs:** `query.entity_targets[]`, `fact.entities[]` (canonical strings).

| Condition | Label |
|-----------|-------|
| `query.entity_targets` empty **and** `query_class ∈ {BROAD}` with scope-only intent documented | `NOT_APPLICABLE` |
| `query.entity_targets` empty otherwise | `UNKNOWN` |
| Non-empty intersection between targets and fact entities (exact canonical match) | `MATCH` |
| Targets non-empty, fact entities non-empty, **empty intersection**, and at least one fact entity is an explicit *different* entity of the same type as a target | `MISMATCH` |
| Targets non-empty but fact entities empty | `UNKNOWN` |

Near-name collisions (e.g. Nimbus vs NimbusX) are **MISMATCH** if both are annotated as distinct canonical IDs.

---

## 2. PREDICATE / RELATION

**Inputs:** `query.predicate_target`, `fact.predicate`.  
**Allowed equivalents:** only those listed in `predicate_equivalence.json` **if** that file is frozen with the annotations; until then, equivalence set = exact string match only.

| Condition | Label |
|-----------|-------|
| `query_class ∈ {BROAD}` and `predicate_target is null` | `NOT_APPLICABLE` |
| `query_class = MULTIHOP` and evaluating a `COMPONENT` fact | `NOT_APPLICABLE` for predicate mismatch against the *final* predicate (component predicates may differ) |
| `predicate_target` null and not covered above | `NOT_APPLICABLE` |
| `fact.predicate` null | `UNKNOWN` |
| Exact match or preregistered equivalent | `MATCH` |
| Both non-null and not equivalent **and** listed in preregistered *incompatible pairs* (e.g. `founded` vs `owned`) | `MISMATCH` |
| Both non-null, not equivalent, not in incompatible list | `UNKNOWN` (do **not** invent soft mismatch) |

---

## 3. ROLE / DIRECTION

**Inputs:** `query.role_target`, `fact.role` (`subject` / `object`).

| Condition | Label |
|-----------|-------|
| Either side null / missing | `UNKNOWN` |
| `query_class ∈ {BROAD}` and role_target null | `NOT_APPLICABLE` |
| Subject and object both specified on query and both match fact role fields | `MATCH` |
| Both sides fully specified and subject/object swapped or conflicting | `MISMATCH` |
| Partially specified | `UNKNOWN` |

---

## 4. SCOPE

**Inputs:** `query.scope_target`, `fact.scope`.

| Condition | Label |
|-----------|-------|
| `query.scope_target = any` | `NOT_APPLICABLE` |
| `query_class = BROAD` **and** protocol marks exploratory as scope-agnostic for that query (`scope_target=any`) | `NOT_APPLICABLE` |
| `query.scope_target = unknown` or `fact.scope = unknown` | `UNKNOWN` |
| Equal scopes (`prod`/`prod`, `test`/`test`, `default`/`default`, `current`/`current`) | `MATCH` |
| `prod` or `current` query vs `test` fact | `MISMATCH` |
| `current` query vs `historical` fact | `MISMATCH` |
| `default` query vs `test` fact when query is production-oriented STATE | `MISMATCH` |
| Other unequal pairs not listed | `UNKNOWN` |

**HN9 diagnostic:** production-oriented query + `fact.scope=test` → `MISMATCH`.

---

## 5. TEMPORAL STATE

**Inputs:** `query.scope_target` ∈ `{historical,current}` and/or dedicated temporal intent; `fact.temporal_state`.

| Condition | Label |
|-----------|-------|
| Query has no temporal intent | `NOT_APPLICABLE` |
| Fact `temporal_state` null/unknown | `UNKNOWN` |
| `current` intent + `current` fact | `MATCH` |
| `current` intent + `historical` fact | `MISMATCH` |
| `historical` intent + `historical` fact | `MATCH` |
| Otherwise | `UNKNOWN` |

---

## 6. POLARITY

**Inputs:** `query.polarity_target`, `fact.polarity`.

| Condition | Label |
|-----------|-------|
| Query polarity null (non-polar question) | `NOT_APPLICABLE` |
| Fact polarity null | `UNKNOWN` |
| Equal polarity | `MATCH` |
| Affirmative vs negated (or inverse) | `MISMATCH` |

---

## 7. CONDITION

**Inputs:** `query.condition_target`, `fact.condition`.

| Condition | Label |
|-----------|-------|
| Query has no condition intent (`condition_target` null) **and** fact.condition null | `NOT_APPLICABLE` |
| Query has no condition intent **but** fact has a restricting condition (e.g. `CACHE_MODE=true`) while gold treats unconditional fact as DIRECT | treat fact as conditional-extra → for STATE/NARROW unconditional queries: `MISMATCH` if preregistered; else `UNKNOWN` |
| Query requires condition C and fact.condition equals C | `MATCH` |
| Query requires C and fact.condition is incompatible | `MISMATCH` |
| Otherwise | `UNKNOWN` |

---

## 8. ATTRIBUTION

**Inputs:** `query.attribution_target`, `fact.attribution`.

| Condition | Label |
|-----------|-------|
| Query attribution null | `NOT_APPLICABLE` |
| Fact attribution null | `UNKNOWN` |
| Equal attribution identity | `MATCH` |
| Explicit different speaker/source than required confirmer | `MISMATCH` |

---

## Combination → KEEP / REJECT

### Applicable features

A feature is **applicable** iff its label is `MATCH` or `MISMATCH` or `UNKNOWN` (i.e. not `NOT_APPLICABLE`).  
`NOT_APPLICABLE` is ignored in the combination.

### Deterministic rule (A1 / A2 base)

```
IF any applicable feature label == MISMATCH:
    decision = REJECT
ELSE:
    decision = KEEP
```

Notes:

- `UNKNOWN` never causes `REJECT`.
- All-`NOT_APPLICABLE` (no applicable features) → `KEEP` (structure silent; residual ranking may still apply in A2).
- This is an **oracle upper-bound** filter, not a claim about extractability.

### A3 override (component-preserving diagnostic)

On pairs with `diagnostic_subset = MULTIHOP_COMPONENT_RETENTION` **and** `gold_relevance_class = COMPONENT`:

```
decision = KEEP
```

even if base rule would `REJECT` (log `A3_COMPONENT_OVERRIDE=true`).

### Survivor sets

| Arm | Survivor definition |
|-----|---------------------|
| **A0** | All candidates present in frozen CE score table for the query (no structural filter). Order = descending frozen `RAW_SCORE` (CE). **No new threshold.** |
| **A1** | Candidates with structural `KEEP`. Order = unspecified / stable by `fact_id` (filtering arm; CE not used for keep/reject). |
| **A2** | Same KEEP set as A1. Order = descending frozen CE `RAW_SCORE` among survivors. |
| **A3** | KEEP set under A3 override rules. Optional A3-CE = CE order among A3 survivors. |

### Empty outcomes

| Situation | Flag |
|-----------|------|
| Score table has zero rows for query | `NO_CANDIDATES` |
| Score table nonempty, all `REJECT` | `STRUCTURALLY_FILTERED_EMPTY = true` |
| Gold empty and `STRUCTURALLY_FILTERED_EMPTY` | may interpret as supporting `NO_RELEVANT_MEMORY` **for this fixture only** |
| Never claim | “system knows the fact does not exist” |
| Infrastructure missing scores | `RETRIEVAL_FAILURE` (should not occur on frozen run_007) |

`STRUCTURALLY_FILTERED_EMPTY ≠ RETRIEVAL_FAILURE ≠ NO_CANDIDATES`.
