# 📏 FM-17-pre — MEASUREMENT CHARTER

**Document type:** MEASUREMENT-DESIGN ONLY (no results)  
**Status:** `MEASUREMENT_CHARTER_FROZEN` (upon commit)  
**Date baseline:** 2026-09-11  
**Protocol commit:** `469fe64beee40973753b290e057226dabac59eae`  
**FM-16 execution anchor:** `62cfa45a80ec83794b701d88873ce136b7629354`  
**Branch:** `experiment/falkordblite-deterministic-memory`  
**Mode:** PRE-EXECUTION · ANTI-LEAKAGE · ANTI-DRIFT · NO ABLATION  
**Experiment class:** `TARGETED_MECHANISTIC_ABLATION` (features informed by FM-16 failures ≠ blind generalization)  
**Protocol repair:** v1.1 anti-leakage / annotation integrity (this revision)  

---

## 0. Primary discrimination question

> On the frozen FM-16 fixture, does **oracle-quality typed structural information** add useful relevance/qualification signal **beyond CE-only ranking**, and does **structural → CE residual composition** preserve more useful evidence than **structural qualification alone**?

This is a **bounded diagnostic** question.

### It is NOT

| Forbidden framing |
|-------------------|
| Architecture decision |
| Production design |
| Proof that structure can be extracted automatically |
| Proof of Honest Empty |
| Proof that graph memory is superior |
| Proof that a CrossEncoder is inadequate |

### Ceiling statement

```
ORACLE STRUCTURAL VALUE     ≠  AUTOMATIC EXTRACTION ACCURACY
ORACLE QUERY INTERPRETATION ≠  REAL QUERY UNDERSTANDING
ORACLE PASS                 ≠  DEPLOYABLE PIPELINE
```

The experiment measures the **combined ceiling** of:

```
PERFECT QUERY STRUCTURAL INTERPRETATION
+
PERFECT CANDIDATE/FACT STRUCTURAL REPRESENTATION
```

It does **not** isolate candidate-side structure alone.

```
ORACLE QUERY INTERPRETATION ≠ REAL QUERY UNDERSTANDING
ORACLE FACT STRUCTURE       ≠ REAL EXTRACTION
COMBINED ORACLE CEILING     ≠ DEPLOYABLE PIPELINE
ORACLE STRUCTURAL VALUE     ≠ AUTOMATIC EXTRACTION ACCURACY
```

A positive result authorizes only a **future** question such as:

> Can those fields be extracted reliably enough to preserve the gain?

It does **not** answer that question.

Primary positive label:

`ORACLE_QUERY_AND_FACT_STRUCTURAL_REPRESENTATION_HAS_MEASURABLE_VALUE`

---

## 1. Evidence universe

```
EVIDENCE_UNIVERSE_FM17_PRE =
  frozen facts / candidates / queries from FM-16 artifacts/memoryops/run_007
  + preregistered oracle annotation layer (when frozen+hashed)
```

Exact file list: [`FROZEN_RUN007_INPUTS.md`](FROZEN_RUN007_INPUTS.md).

### Preserved inequalities

```
NOT FOUND IN EVIDENCE UNIVERSE  ≠  FALSE IN THE REAL WORLD
NO MATCH                        ≠  FACT DOES NOT EXIST
STRUCTURALLY_FILTERED_EMPTY     ≠  KNOWLEDGE ABSENCE
RETRIEVAL FAILURE               ≠  HONEST EMPTY
```

The experiment evaluates **candidate qualification relative to the frozen fixture only**.  
No external world knowledge may change gold or candidate truth.

---

## 2. Six pre-execution answers

| # | Question | Charter section |
|---|----------|-----------------|
| 1 | What is the evidence universe? | §1 |
| 2 | What do ACCEPT / REJECT / UNRESOLVED mean? | §3 |
| 3 | What query classes are evaluated? | §4 |
| 4 | What candidate relevance roles exist? | §5 |
| 5 | What errors/losses are measured? | §8–§9 |
| 6 | What is / is not scientifically justified? | §0, §12, §14 |

---

## 3. Structural decision states (ternary)

Structural decisions are **not** a numeric score. Emit exactly one of:

### ACCEPT

**Meaning:** The candidate satisfies every applicable preregistered structural constraint that is known/evaluable (no `MISMATCH`; and at least one applicable `MATCH`, **or** all features `NOT_APPLICABLE` with explicit “structure silent → treat as non-rejecting survivor” per mapping below).

**ACCEPT does NOT mean:** true · authoritative · best answer · semantically sufficient · current in the real world.

### REJECT

**Meaning:** At least one applicable preregistered structural constraint produces an **explicit** incompatibility (`MISMATCH`).

Examples: prod query vs test fact · polarity opposite · entity Alice vs Bob.

Only **explicit** incompatibility may produce `REJECT`.

### UNRESOLVED

**Meaning:** The structural layer lacks enough information to determine compatibility.

Examples: missing field · `UNKNOWN` annotation · ambiguous mapping · broad query with no single predicate · open-text semantic condition · incomplete temporal specification.

```
UNKNOWN    ≠  MISMATCH
MISSING    ≠  FALSE
UNRESOLVED ≠  REJECT
```

### Mapping to frozen protocol vocabulary (`KEEP` / `REJECT`)

Protocol files at `469fe64` use binary `KEEP`/`REJECT`. This charter **refines without rewriting** those files:

| Charter state | Protocol binary | Survivor for A1/A2? |
|---------------|-----------------|---------------------|
| `REJECT` | `REJECT` | **No** |
| `ACCEPT` | `KEEP` | **Yes** |
| `UNRESOLVED` | `KEEP` (protocol: UNKNOWN never rejects) | **Yes** |

**Operational refinement for measurement:**

```
IF any applicable feature == MISMATCH:
    state = REJECT
ELIF any applicable feature == MATCH:
    state = ACCEPT
ELSE:
    # only UNKNOWN and/or NOT_APPLICABLE
    state = UNRESOLVED
```

All-`NOT_APPLICABLE` → `UNRESOLVED` (structure silent), still a survivor (matches protocol “KEEP when silent”).

**A2 residual set** = candidates with state ∈ `{ACCEPT, UNRESOLVED}` (= protocol A1 KEEP set), then frozen CE order.

---

## 4. Query strata (separate reporting)

Reuse frozen protocol axis names; map to charter codes:

| Charter | Protocol `query_class` / axis | Name |
|---------|-------------------------------|------|
| **Q-A** | Axis A / `NARROW` | NARROW / DIRECT |
| **Q-B** | Axis B / `STATE` | STATE / SCOPE / TEMPORAL |
| **Q-C** | Axis C / `BROAD` | BROAD / EXPLORATORY |
| **Q-D** | Axis D / `NO_ANSWER` | NO-ANSWER |
| **Q-E** | Axis E / `MULTIHOP` | MULTI-HOP / COMPONENT DIAGNOSTIC |

```
SUCCESS ON Q-A  ≠  SUCCESS ON Q-C
SUCCESS ON Q-D  ≠  SUCCESS ON Q-E
```

Do **not** aggregate into one headline metric only.

---

## 5. Candidate relevance roles (evaluation-only)

| Role | Operational definition |
|------|------------------------|
| **DIRECT** | Can directly support the requested answer under the frozen query interpretation |
| **COMPONENT** | Does not directly answer the original query but is required or potentially required as part of a valid multi-hop chain |
| **RELATED** | Semantically/topically related but not needed to support the answer or a protected reasoning path |
| **NONANSWER** | Does not answer the information need and is not a protected component |

```
DIRECT ≠ COMPONENT ≠ RELATED ≠ NONANSWER
```

Stored as `gold_relevance_class` in the annotation schema — **EVALUATION-ONLY** (see §6).

---

## 6. Anti-leakage firewall (mandatory)

### Invariant

```
FILTER_DECISION_FIELDS  ∩  EVALUATION_GOLD_FIELDS  =  ∅
```

for arms **A1** and **A2**, with **no exceptions**.

### EVALUATION_GOLD_FIELDS (may NOT drive A1/A2)

- `gold_relevance_class`
- FM-16 `gold_relevant` / gold set membership when used as *relevance role*
- Any label derived solely to score DIRECT/COMPONENT/RELATED/NONANSWER metrics

### FILTER_DECISION_FIELDS (A1/A2 may use)

- `query.*` structural targets (entity, predicate, scope, polarity, condition, attribution, role, query_class)
- `fact.*` structural fields (same)
- Feature labels `MATCH|MISMATCH|UNKNOWN|NOT_APPLICABLE` from preregistered rules
- Frozen CE `RAW_SCORE` **only in A2** for ordering survivors (not for structural ACCEPT/REJECT/UNRESOLVED)

### Forbidden for A1/A2 (decisions AND annotation construction)

Must not use, inspect, or derive STRUCTURAL fields from:

`gold_relevance_class` · FM-16 gold membership · HN class/stratum · CE score/rank · embedding score/rank · candidate rank · known model failure · desired arm outcome · TEST result · expected ACCEPT/REJECT

```
A1_A2_ANNOTATION_INPUTS ∩ EVALUATION_OUTCOME_INFORMATION = ∅
```

Allowed STRUCTURAL inputs: raw query text · raw fact text · pre-frozen ontology/schema · pre-frozen lexical/semantic rulebook · adjudication of A–D only.

Gold / HN may be used **only after** STRUCTURAL freeze, in `EVALUATION_OVERLAY`, to compute metrics.

### A3 — `ORACLE_COMPONENT_IDENTITY_CEILING_DIAGNOSTIC`

Arm **A3** is the **sole** authorized exception that may consult COMPONENT gold labels.

| Constraint | Rule |
|------------|------|
| Name | `ORACLE_COMPONENT_IDENTITY_CEILING_DIAGNOSTIC` |
| Class | integrity / ceiling diagnostic — **not** a deployable pipeline |
| Report | **Separately** from A1/A2 |
| Influence | Must **not** change A1/A2 rules, thresholds, or field selection |
| Primary success | **NO** — A3 retention is **not** a gate for A1/A2 useful-signal |
| Claim ban | Must **not** claim a realistic system can identify components |

`A3_COMPONENT_RETENTION` = diagnostic / integrity check (partly tautological if KEEP is forced on COMPONENT gold).

```
A3 knows COMPONENT by oracle  ≠  A1/A2 can recognize COMPONENT
```

A3 roles only: (1) verify override works (2) show ceiling if perfect COMPONENT identity were known (3) expose whether that changes downstream candidate availability.

### v1.1 repair of prior FINDING

CONDITION “gold treats unconditional fact as DIRECT” **removed**. Unspecified query condition + conditional fact → `UNKNOWN`/`UNRESOLVED`.

---

## 7. Per-field MATCH / MISMATCH / UNKNOWN / NOT_APPLICABLE

Full tables remain in [`preregistered_filter_rules.md`](preregistered_filter_rules.md). Charter requires:

| Label | Behavior |
|-------|----------|
| `MATCH` | Does not reject |
| `MISMATCH` | May reject if rule preregistered |
| `UNKNOWN` | Must **not** reject solely because information is absent |
| `NOT_APPLICABLE` | Field excluded from decision for that pair/query class |

Minimum fields covered: entity · predicate · role/direction · scope · temporal state · polarity · condition · attribution.

---

## 8. Temporal semantics (bounded)

When available, distinguish fixture labels:

`CURRENT` · `HISTORICAL` · `TEST` · `PRODUCTION` · `DEFAULT` · `UNKNOWN`

(Protocol also uses `prod|test|default|historical|current|any|unknown` on scope/temporal fields.)

```
RECENT                  ≠  CURRENTLY_APPLICABLE
HISTORICAL              ≠  FALSE
CURRENT LABEL           ≠  CURRENT TRUTH OUTSIDE FIXTURE
TEMPORAL MISMATCH       ≠  LOW SEMANTIC RELEVANCE
```

If the fixture cannot represent a temporal distinction → **`UNRESOLVED`**, do not invent.

---

## 9. Modality / condition semantics

Do **not** collapse into one predicate state:

`IS` · `WAS` · `WANTS` · `PLANS` · `MAY` · `MUST` · `ATTEMPTED` · `SUCCEEDED` · `FAILED`

```
attempted X   ≠  succeeded at X
desired X     ≠  actual X
conditional X ≠  unconditional X
```

If frozen annotations lack enough information → **`UNRESOLVED`**.

---

## 10. Arms (exact — no additions)

| Arm | Definition |
|-----|------------|
| **A0** | CE BASELINE — frozen CE ranking only |
| **A1** | STRUCTURAL ORACLE — ACCEPT/REJECT/UNRESOLVED per frozen rules; survivors = ACCEPT∪UNRESOLVED |
| **A2** | STRUCTURAL → CE RESIDUAL — same survivors as A1; frozen CE ranking among them |
| **A3** | COMPONENT-PRESERVING **ORACLE_DIAGNOSTIC** only |

**Do not add:** graph paths · LLM judge · SLM · new CE · query-conditioned model · new embedding · MemoryKeep score · confidence weighting · freshness weighting.

### Matched comparison

Hold constant: frozen queries · facts · candidate universe · CE scores · embedding artifacts · gold · strata · metrics · candidate budget.

Any A0/A1/A2 difference must be attributable to the **preregistered structural decision mechanism**, not new retrieval or new model scoring.

---

## 11. Primary losses / error types

| Error | Definition |
|-------|------------|
| `FALSE_ACCEPT` | Structurally incompatible NONANSWER/RELATED survives when applicable rule should `REJECT` |
| `FALSE_EXCLUSION_DIRECT` | A DIRECT gold candidate is removed |
| `FALSE_EXCLUSION_COMPONENT` | A protected COMPONENT is removed |
| `FALSE_EMPTY` | Gold answer evidence exists in the frozen evidence universe but the arm leaves no usable answer evidence |
| `UNSUPPORTED_NONEMPTY` | A no-answer query still exposes candidate(s) as answer-worthy |
| `UNRESOLVED_RATE` | Fraction of pairs where structure cannot make a decisive ACCEPT/REJECT (`state=UNRESOLVED`) |

**Do not** interpret `UNRESOLVED` as automatic failure **or** as success.

`UNRESOLVED_RATE` is **co-primary**. High unresolved rate ≠ structural success. Low false rejection from “keep everything UNRESOLVED” ≠ useful qualification. No positive conclusion from rejection metrics alone.

---

## 12. Metrics → scientific questions

Use [`preregistered_metrics.md`](preregistered_metrics.md). Charter mapping:

| Metric | Asks |
|--------|------|
| `DIRECT_GOLD_RECALL` | Did structure preserve direct evidence? |
| `COMPONENT_RETENTION` | Did protected multi-hop components survive? (A1/A2 without gold; A3 diagnostic separately) |
| `RELATED_REJECTION_RATE` | Are non-needed related facts removed? |
| `NONANSWER_REJECTION_RATE` | Are non-answers removed? |
| `NO_ANSWER_EMPTY_ACCURACY` | On Q-D, do survivors empty when gold empty? |
| `FALSE_EMPTY_RATE` | Empty survivors despite gold evidence? |
| `NONEMPTY_GOLD_MISS_RATE` | Survivors miss all DIRECT gold? |
| `UNRESOLVED_RATE` | How often is structure silent/insufficient? |
| `CANDIDATE_REDUCTION_RATIO` | How much does structure shrink the pool? |
| `HN_REJECTION_RATE_PER_STRATUM` | Per HN1–12, including HN9 scope |
| `DIRECT_GOLD_REMOVED_COUNT` | Count of harmed DIRECT gold |
| `COMPONENT_REMOVED_COUNT` | Count of harmed COMPONENTs |

**A2 additionally:** frozen CE ranking metrics (MRR/P@k/R@k) on the residual survivor set.

No single “overall intelligence” metric.

---

## 13. HN9 / scope diagnostic

FM-16 live anchor: `TQ11` × `TF23` (test-scope fact ranked above production/default golds under CE and embedding).

Charter handling:

- Report HN9 rejection / inversion before vs after structure on Q-B and Q-C as applicable.
- Do **not** silently assume the broad query has only one valid semantic reading.
- Default BROAD `scope_target=any` unless query text explicitly names a scope.
- HN9 rejection under one interpretation ≠ proof TF23 is universally irrelevant (`SEMANTIC_DESIGN_LIMITATION`).

---

## 14. Multi-hop safety

Conceptual diagnostic:

```
Alice → works_on → Orion     = COMPONENT
Orion → uses → Python        = DIRECT (decomposed final-hop evidence)
Query: "What language does Alice's project use?"
```

A local relevance filter is **not** safe merely because the first fact is not DIRECT.

Measure whether at least one valid **evidence chain** can survive (component retention).

```
CO-RETRIEVAL           ≠  MULTI-HOP REASONING
COMPONENT RETENTION    ≠  MULTI-HOP SUCCESS
```

FM-17-pre may measure **component retention only**.  
Do **not** claim multi-hop reasoning is established.

---

## 15. Honest Empty claim boundary

**Prohibited claim:** `HONEST_EMPTY = SOLVED`

**Allowed bounded claim if supported:**

`STRUCTURAL_ORACLE_IMPROVED_NO_ANSWER_DISCRIMINATION_ON_FROZEN_FIXTURE`

**Prohibited:** “THE SYSTEM KNOWS WHEN MEMORY HAS NO ANSWER”

```
STRUCTURAL_EMPTY  ≠  SEMANTIC HONEST EMPTY  ≠  WORLD-KNOWLEDGE ABSENCE
```

---

## 16. Test isolation / no test-driven tuning

### Conceptual order

1. Protocol frozen  
2. Measurement charter frozen  
3. Ontology/schema frozen  
4. Semantic/lexical rulebook frozen  
5. Annotators receive **only** sanitized raw query/fact (`sanitized_annotation_input.schema.json`)  
6. Independent blinded annotation (A then B; no peeking)  
7. Disagreement report  
8. Adjudication  
9. Freeze STRUCTURAL package + SHA256 + receipt (`gold_access=false`, `hn_access=false`, `ce_score_access=false`, `embedding_score_access=false`)  
10. Only then attach EVALUATION_OVERLAY  
11. One A0/A1/A2/A3 execution (if later authorized)  
12. Results lock  
13. Interpretation  

If `INDEPENDENT_ANNOTATION_AVAILABLE = NO`: **STOP before ablation**. Do not fake a second annotator.

### Honesty about FM-16 history

FM-16 **already inspected TEST** scores/metrics historically (`run_007` held-out evaluation exists in-repo).  
Therefore this charter does **not** claim cryptographically perfect blindness to TEST content.

Instead define:

```
NO_NEW_TEST_DRIVEN_ADAPTATION_AFTER_FM17_PRE_FREEZE
```

After this charter + protocol freeze, **forbidden** TEST-driven:

field selection · predicate equivalence additions · scope rule edits · threshold edits · query reclassification · metric changes · annotation reinterpretation

---

## 17. Annotation integrity

Each frozen annotation package must record:

| Field | Requirement |
|-------|-------------|
| Generator | who/what produced each record |
| `annotation_source` | `HUMAN_GOLD` \| `RULE_DERIVED` |
| `annotation_version` | monotonic string/int |
| `schema_version` | matches `oracle_annotations.schema.json` |
| `sha256` | of frozen annotation file |
| `created_at_utc` / `frozen_at_utc` | timestamps |
| Amendment policy | see below |

### Amendments after freeze

Require: new version · explicit reason · changed-field log · invalidation/restart if scoring/ablation already began.  
**No silent corrections.**

LLM drafts are non-gold unless independently reviewed and upgraded (see annotation guide).

---

## 18. Permitted result vocabulary

| Code | Use when |
|------|----------|
| `ORACLE_QUERY_AND_FACT_STRUCTURAL_REPRESENTATION_HAS_MEASURABLE_VALUE` | Positive combined query+fact oracle ceiling on this fixture |
| `STRUCTURAL_THEN_CE_RESIDUAL_SHOWS_ADDITIONAL_VALUE_ON_FROZEN_FIXTURE` | A2 adds value over A1 |
| `ORACLE_STRUCTURAL_REPRESENTATION_NOT_SUFFICIENT_ON_FIXTURE` | Insufficient alone |
| `NO_MEASURABLE_GAIN_FROM_SPECIFIED_ORACLE_STRUCTURAL_REPRESENTATION` | Negative vs A0 for **specified** representation/rules |
| `STRUCTURAL_GAIN_WITH_PROTECTED_RECALL_REGRESSION` | Mixed |
| `STRUCTURAL_ORACLE_IMPROVED_NO_ANSWER_DISCRIMINATION_ON_FROZEN_FIXTURE` | Bounded empty-set improvement only |

### Forbidden

`SOLVED` · `GENERALIZED` · `UNDERSTANDS` · `PRODUCTION_READY` · `ARCHITECTURE_VALIDATED` · `STRUCTURE_IS_SUFFICIENT` · `STRUCTURE_IS_USELESS` · `HONEST_EMPTY_SOLVED` · `MULTI_HOP_SOLVED` · `CE_OBSOLETE`

Unqualified `STRUCTURAL_INFORMATION_HAS_MEASURABLE_ORACLE_VALUE` is **superseded** (did not state query+fact combined ceiling).

Negative strongest claim: the specified oracle query-and-fact structural representation and filter rules did not provide sufficient measurable gain on the frozen fixture. **Not** “structure is useless.”

## 19. External Manus audit status

```
EXTERNAL RESEARCH INPUT  ≠  LOCAL EXECUTION EVIDENCE
```

Primary recommendation (input only): structural + residual composition vs single-model scoring.  
Strongest caution: formal structural predicates decide deterministically only **after** correct language/schema/entity/temporal grounding.

```
STRUCTURAL EXECUTION  ≠  QUERY UNDERSTANDING
```

Do not import literature claims as FM-17 results.

---

## 20. Donor / anecdote (non-criteria)

MemoryKeep = SPECIFICATION / HYPOTHESIS DONOR  
Amadeus / Reddit provenance practitioner = ANECDOTAL  

Not success criteria.

---

## 21. Self-audit checklist

- [x] `gold_relevance_class` cannot influence A1/A2  
- [x] HN / gold sets cannot construct A1/A2 STRUCTURAL fields  
- [x] Field-level provenance + blinding + independent adjudication required  
- [x] A3 `ORACLE_COMPONENT_IDENTITY_CEILING_DIAGNOSTIC` not a primary success gate  
- [x] UNKNOWN ≠ MISMATCH  
- [x] UNRESOLVED ≠ REJECT  
- [x] DIRECT ≠ COMPONENT  
- [x] Broad queries separately reported  
- [x] No-answer claim bounded  
- [x] Temporal semantics explicit  
- [x] Modality/condition semantics explicit  
- [x] Evidence universe frozen  
- [x] TEST-driven adaptation prohibited after freeze  
- [x] No new neural scoring introduced  
- [x] Oracle pass ≠ extraction pass  
- [x] No architecture/runtime authorization  
- [x] No experiment execution in this document  

---

## 22. STOP

This charter does **not** authorize ablation.

Next user decision only:

| Code | Decision |
|------|----------|
| **A** | REQUEST FIXES |
| **B** | SEND CHARTER + PROTOCOL FOR INDEPENDENT REVIEW |
| **C** | AUTHORIZE OFFLINE FM-17-PRE ABLATION |
| **D** | DEFER |

**Do not assume C.**

```json
{
  "document": "FM17_PRE_MEASUREMENT_CHARTER",
  "measurement_charter_frozen": true,
  "ablation_authorized": false,
  "ablation_executed": false,
  "protocol_commit": "469fe64beee40973753b290e057226dabac59eae",
  "fm16_anchor": "62cfa45a80ec83794b701d88873ce136b7629354"
}
```
