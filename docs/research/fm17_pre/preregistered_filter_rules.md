# 📐 Preregistered Filter Rules — FM-17-pre (v1.1)

**Status:** FROZEN for protocol re-review  
**Experiment class:** `TARGETED_MECHANISTIC_ABLATION`  
**UNKNOWN ≠ FALSE** · **UNRESOLVED ≠ REJECT** · **UNRESOLVED ≠ SUCCESS**

A1/A2 decisions use **STRUCTURAL** fields only (raw text + frozen rulebook).  
They must not read gold, HN, CE, embeddings, or `gold_relevance_class`.

## Feature decision vocabulary

| Label | Meaning |
|-------|---------|
| `MATCH` | Explicit compatibility — does not reject |
| `MISMATCH` | Explicit incompatibility — may reject |
| `UNKNOWN` | Insufficient annotation — must **not** reject solely because information is absent |
| `NOT_APPLICABLE` | Field excluded for this pair/query class |

Charter ternary (see measurement charter):

```
IF any applicable feature == MISMATCH:   state = REJECT
ELIF any applicable feature == MATCH:    state = ACCEPT
ELSE:                                    state = UNRESOLVED   # UNKNOWN and/or NOT_APPLICABLE only
```

Survivors for A1/A2 = `{ACCEPT, UNRESOLVED}`.

```
HIGH UNRESOLVED RATE ≠ STRUCTURAL SUCCESS
```

---

## 1. ENTITY

**Inputs:** `query.entity_targets.value[]`, `fact.entities.value[]`.

| Condition | Label |
|-----------|-------|
| `query.entity_targets` empty **and** `query_class ∈ {BROAD}` | `NOT_APPLICABLE` |
| `query.entity_targets` empty otherwise | `UNKNOWN` |
| Non-empty intersection (exact canonical match) | `MATCH` |
| Targets non-empty, fact entities non-empty, empty intersection, at least one fact entity is an explicit *different* entity of the same type | `MISMATCH` |
| Targets non-empty but fact entities empty | `UNKNOWN` |

Near-name collisions (Nimbus vs NimbusX) are `MISMATCH` if both are distinct canonical IDs in the **pre-frozen ontology**, not because an HN5 label exists.

---

## 2. PREDICATE / RELATION

**Inputs:** `query.predicate_target.value`, `fact.predicate.value`.  
Equivalence / incompatibility lists: only from **pre-frozen rulebook** (`predicate_equivalence` / `predicate_incompatible`). Until frozen, exact string match only.

| Condition | Label |
|-----------|-------|
| `query_class ∈ {BROAD}` and `predicate_target` is null | `NOT_APPLICABLE` |
| `query_class = MULTIHOP` (assigned from **query text**, e.g. possessive “X’s project”) | `NOT_APPLICABLE` |
| `predicate_target` null and not covered above | `NOT_APPLICABLE` |
| `fact.predicate` null | `UNKNOWN` |
| Exact match or preregistered equivalent | `MATCH` |
| Both non-null, not equivalent, **and** listed in frozen incompatible pairs (e.g. `founded` vs `owned`) | `MISMATCH` |
| Both non-null, not equivalent, not in incompatible list | `UNKNOWN` |

**Changed rule (v1.1):** MULTIHOP predicate N/A is keyed off **query_class from query text**, **not** off `gold_relevance_class=COMPONENT`.

---

## 3. ROLE / DIRECTION

| Condition | Label |
|-----------|-------|
| Either side null / missing | `UNKNOWN` |
| `query_class ∈ {BROAD}` and role_target null | `NOT_APPLICABLE` |
| Subject and object both specified and both match | `MATCH` |
| Both sides fully specified and swapped/conflicting | `MISMATCH` |
| Partially specified | `UNKNOWN` |

---

## 4. SCOPE

**Inputs:** `query.scope_target.value`, `fact.scope.value`.

**BROAD default (v1.1):** If query text does not **explicitly** name production / test / current / historical / default, annotators MUST set `scope_target = any`. Do **not** backsolve a narrower target from gold or HN9.

| Condition | Label |
|-----------|-------|
| `query.scope_target = any` | `NOT_APPLICABLE` |
| `query_class = BROAD` with `scope_target = any` | `NOT_APPLICABLE` |
| `query.scope_target = unknown` or `fact.scope = unknown` | `UNKNOWN` |
| Equal scopes (`prod`/`prod`, `test`/`test`, `default`/`default`, `current`/`current`) | `MATCH` |
| `prod` or `current` query vs `test` fact (**only** when query text explicitly licenses prod/current) | `MISMATCH` |
| `current` query vs `historical` fact (explicit current intent in query text) | `MISMATCH` |
| `default` query vs `test` fact when `query_class = STATE` **and** query text is production-oriented | `MISMATCH` |
| Other unequal pairs not listed | `UNKNOWN` |

### TQ11 / TF23-type case (`SEMANTIC_DESIGN_LIMITATION`)

Query example: *What components are associated with Project Titan?*  
Fact example: *Project Titan uses H2 in tests.*

Under the **default BROAD** interpretation (`scope_target=any`), SCOPE is `NOT_APPLICABLE`. The test-scope fact may be legitimate related/contextual evidence.

```
HN9_REJECTION under one chosen (narrower) interpretation
≠ UNIVERSAL PROOF THAT TF23 IS IRRELEVANT
```

A later evaluation overlay may tag `diagnostic_subset=HN9_SCOPE` **without** changing A1/A2 STRUCTURAL fields.

---

## 5. TEMPORAL STATE

| Condition | Label |
|-----------|-------|
| Query has no temporal intent (`temporal_target` any/null) | `NOT_APPLICABLE` |
| Fact `temporal_state` null/unknown | `UNKNOWN` |
| `current` intent + `current` fact | `MATCH` |
| `current` intent + `historical` fact | `MISMATCH` |
| `historical` intent + `historical` fact | `MATCH` |
| Otherwise | `UNKNOWN` |

Do not invent missing temporal knowledge. If the fixture cannot represent the distinction → UNRESOLVED.

```
RECENT ≠ CURRENTLY_APPLICABLE
HISTORICAL ≠ FALSE
TEMPORAL MISMATCH ≠ LOW SEMANTIC RELEVANCE
```

---

## 6. POLARITY

| Condition | Label |
|-----------|-------|
| Query polarity null | `NOT_APPLICABLE` |
| Fact polarity null | `UNKNOWN` |
| Equal polarity | `MATCH` |
| Affirmative vs negated (or inverse) | `MISMATCH` |

---

## 7. CONDITION

**Inputs:** `query.condition_target.value`, `fact.condition.value`.

**Changed rule (v1.1):** no consultation of gold / DIRECT membership.

Operational example:

- Query: *Is caching enabled?* → `condition_target = UNSPECIFIED`
- Fact: *Caching is enabled only when CACHE_MODE=true.* → `condition = CONDITIONAL:…`

| Condition | Label |
|-----------|-------|
| Query condition null/UNSPECIFIED **and** fact condition null | `NOT_APPLICABLE` |
| Query condition null/UNSPECIFIED **and** fact is CONDITIONAL | `UNKNOWN` → pair state contributes to **UNRESOLVED** (must not REJECT solely on this) |
| Query requires condition C and fact.condition equals C | `MATCH` |
| Query requires C and fact.condition is incompatible | `MISMATCH` |
| Otherwise | `UNKNOWN` |

```
attempted X ≠ succeeded at X
desired X   ≠ actual X
conditional X ≠ unconditional X
```

If frozen annotations lack enough information → UNRESOLVED.

---

## 8. ATTRIBUTION

| Condition | Label |
|-----------|-------|
| Query attribution null | `NOT_APPLICABLE` |
| Fact attribution null | `UNKNOWN` |
| Equal attribution identity | `MATCH` |
| Explicit different speaker/source than required confirmer | `MISMATCH` |

---

## Combination → ACCEPT / REJECT / UNRESOLVED

Applicable features: labels `MATCH` | `MISMATCH` | `UNKNOWN` (`NOT_APPLICABLE` ignored).

```
IF any applicable feature == MISMATCH:
    state = REJECT
ELIF any applicable feature == MATCH:
    state = ACCEPT
ELSE:
    state = UNRESOLVED
```

- `UNKNOWN` never causes `REJECT`.
- All-`NOT_APPLICABLE` → `UNRESOLVED` (structure silent) and still a survivor.
- This is a **combined query+fact oracle ceiling**, not extractability.

### A3 — `ORACLE_COMPONENT_IDENTITY_CEILING_DIAGNOSTIC` only

On evaluation-overlay pairs with `diagnostic_subset = MULTIHOP_COMPONENT_RETENTION` **and** `gold_relevance_class = COMPONENT`:

```
decision = KEEP   # integrity / ceiling check
log A3_COMPONENT_OVERRIDE=true
```

A3 **must not** influence A1/A2 rules.  
`A3_COMPONENT_RETENTION` = diagnostic / integrity check, **not** independent evidence that A1/A2 recognize components.

```
A3 knows COMPONENT by oracle  ≠  A1/A2 can recognize COMPONENT
```

### Survivor sets

| Arm | Survivors |
|-----|-----------|
| **A0** | All frozen CE candidates; order = descending `RAW_SCORE`; no new θ |
| **A1** | `state ∈ {ACCEPT, UNRESOLVED}`; order stable by `fact_id` |
| **A2** | Same set as A1; order = frozen CE among survivors |
| **A3** | A1/A2 set plus COMPONENT override on diagnostic subset — **ORACLE_DIAGNOSTIC**, not primary success |

### Empty outcomes

| Situation | Flag |
|-----------|------|
| Score table has zero rows | `NO_CANDIDATES` |
| Nonempty table, all `REJECT` | `STRUCTURALLY_FILTERED_EMPTY = true` |
| Gold empty and structurally filtered empty | fixture-local `NO_RELEVANT_MEMORY` reading **only** |
| Never claim | “system knows the fact does not exist” |
| Missing scores | `RETRIEVAL_FAILURE` |

`STRUCTURALLY_FILTERED_EMPTY ≠ RETRIEVAL_FAILURE ≠ NO_CANDIDATES ≠ HONEST EMPTY`.
