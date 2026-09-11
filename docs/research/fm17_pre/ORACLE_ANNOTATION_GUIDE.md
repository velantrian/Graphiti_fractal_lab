# 🏷️ Oracle Annotation Guide — FM-17-pre (v1.1)

**Experiment class:** `TARGETED_MECHANISTIC_ABLATION`  
**Not:** general validation of structural relevance.

## Allowed inputs for A1/A2 STRUCTURAL fields

```
A1_A2_ANNOTATION_INPUTS ∩ EVALUATION_OUTCOME_INFORMATION = ∅
```

A1/A2 structural fields MAY be derived **only** from:

| Code | Source |
|------|--------|
| A | raw query text |
| B | raw fact/candidate text |
| C | a **pre-frozen** ontology/schema |
| D | a **pre-frozen** lexical/semantic rulebook |
| E | independently adjudicated annotation based **only** on A–D |

A1/A2 structural fields MUST NOT be derived from:

- FM-16 gold membership
- `gold_relevance_class`
- HN class / HN stratum labels
- CE score / CE rank
- embedding score / embedding rank
- candidate rank
- known model failure
- desired arm outcome
- TEST result
- whether the candidate is expected to be accepted/rejected

**RULE_DERIVED** means: deterministic application of **D** to **A/B**, never “this is HN9 therefore scope=test”.

HN labels and gold may appear **only** in `record_layer=EVALUATION_OVERLAY` **after** structural freeze.

## Record layers

| `record_layer` | Who sees it | May contain gold/HN? |
|----------------|-------------|----------------------|
| `STRUCTURAL` | annotator_A, annotator_B, adjudicator | **No** |
| `EVALUATION_OVERLAY` | evaluator after freeze | Yes |

## Field-level provenance

Every decision-relevant query/fact field is `{ "value", "provenance" }` (see schema).

`provenance` required keys:

- `source_type`: `RAW_QUERY_TEXT | RAW_FACT_TEXT | FIXED_RULE | HUMAN_ANNOTATION | ADJUDICATED`
- `source_span`: quote from raw text, or null
- `rule_id`: frozen rulebook id, or null
- `annotator_id`: pseudonymous (`annotator_A`, `annotator_B`, `adjudicator_1`)
- `blinding_status`: `BLINDED_TO_GOLD_AND_HN | NOT_BLINDED | UNKNOWN`
- `adjudication_status`: `NOT_REQUIRED | PENDING | AGREED | ADJUDICATED`

Annotator submissions with `blinding_status=NOT_BLINDED` or `UNKNOWN` are **invalid** for primary A1/A2.

## Blinded independent annotation

Preferred:

```
ANNOTATOR A  ──┐
               ├── disagreement log → adjudication → freeze
ANNOTATOR B  ──┘
```

- A must not see B’s decisions before submitting (and vice versa).
- Both blinded to gold, HN, relevance class, CE/embedding scores and ranks, desired structural-arm result.
- Then compare fields, log disagreements, adjudicate.

Record: total fields · agreements · disagreements · agreement rate · disagreement categories · adjudicated fields.

If genuine independent annotation **cannot** be performed:

```
INDEPENDENT_ANNOTATION_AVAILABLE = NO
```

**STOP before ablation.** Do **not** fabricate a second annotator.

## Sanitized annotator view

Annotators receive **only** objects matching `sanitized_annotation_input.schema.json`:

`query_id`, `fact_id`, `query_text`, `fact_text` (optional split tag without outcomes).

They must **not** inspect: CE score/rank, embedding score/rank, threshold result, per-pair run_007 success/failure, HN identity, gold identity.

This repair defines the package **format**. It does **not** authorize populating real CAL/TEST packages.

## Construction order

1. freeze protocol  
2. freeze measurement charter  
3. freeze ontology/schema  
4. freeze semantic/lexical rulebook  
5. provide annotators **only** sanitized raw query/fact material  
6. independent annotation  
7. disagreement report  
8. adjudication  
9. freeze final **STRUCTURAL** annotation package  
10. compute SHA256  
11. sign/log `annotation_receipt` (`gold_access=false`, `hn_access=false`, `ce_score_access=false`, `embedding_score_access=false`)  
12. **only then** expose evaluation labels (`EVALUATION_OVERLAY`) to evaluator  
13. execute A0/A1/A2/A3 (when later authorized)  
14. lock results  
15. interpretation  

Historical limit: FM-16 TEST was already seen. Use `NO_NEW_TEST_DRIVEN_ADAPTATION_AFTER_FM17_PRE_FREEZE`. Do not claim pristine hidden-test blindness.

## Combined oracle ceiling

The experiment annotates **both** query structure **and** fact structure.

It measures the combined ceiling of:

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
```

Primary positive claim (if later earned):

`ORACLE_QUERY_AND_FACT_STRUCTURAL_REPRESENTATION_HAS_MEASURABLE_VALUE`

## Relevance classes (evaluation overlay only)

```
DIRECT ≠ COMPONENT ≠ RELATED ≠ NONANSWER
```

Mandatory **diagnostic** example (evaluation overlay, not annotator input):

Query: *What language does Alice's project use?*

- Alice → works_on → Orion → **COMPONENT**
- Orion → uses → Python → **DIRECT** (decomposed final hop)
- Nova → uses → Rust → **RELATED**

A3 may use COMPONENT identity as `ORACLE_COMPONENT_IDENTITY_CEILING_DIAGNOSTIC` only.

## Query classes

Derived from **query text + frozen rulebook**, not from gold emptiness.

| `query_class` | Axis | Rule sketch |
|---------------|------|-------------|
| `NARROW` | Q-A | Single-factoid / who-what-where with one predicate |
| `STATE` | Q-B | Explicit scope/temporal/state language in the query |
| `BROAD` | Q-C | Exploratory / “associated with” / “tell me about” |
| `NO_ANSWER` | Q-D | **Not assigned by annotators from gold.** Structural annotators do not label “this should be empty.” Query class NO_ANSWER, if used structurally, must come from query text (e.g. asking an unsupported relation type **named in the query**) or remain unset; empty-gold is evaluation overlay. |
| `MULTIHOP` | Q-E | Query text requires an intermediate entity (e.g. possessive “Alice’s project”) |

For **BROAD**: default `scope_target = any` unless the query text **explicitly** names prod/test/current/historical.

## Freeze / amendment

See `annotation_receipt.schema.json`. Any post-freeze amendment → new version, field log, reason; invalidate prior ablation if computation had started. No silent corrections.

## LLM

LLM drafts are **not** gold. If used as convenience, they are non-gold and excluded until independently reviewed under A–D.

## Template

`oracle_annotations.template.jsonl` — **EXAMPLE_NOT_GOLD** only.

## v1.2 free-text policy

STRUCTURAL records MUST NOT contain unbounded `annotation_notes`.

Optional structured `annotation_comment` only:

- `reason_code` ∈ `{LEXICAL_AMBIGUITY, MULTIPLE_PLAUSIBLE_PARSE, MISSING_EXPLICIT_SCOPE, SOURCE_SPAN_DISAGREEMENT, OTHER_NON_OUTCOME_REASON}`
- optional `comment` ≤ 280 chars

`annotation_comment` is **not** consumed by A1/A2 filter decisions.

Evaluation commentary lives in `EVALUATION_OVERLAY.evaluation_notes` after STRUCTURAL freeze.

Do not treat keyword regex (`gold`, `HN9`) as scientific protection.

## v1.2 fail-closed blinding

For `record_layer=STRUCTURAL`, every decision-relevant `blinding_status` MUST be `BLINDED_TO_GOLD_AND_HN`.

`NOT_BLINDED` and `UNKNOWN` → **schema-invalid**.

Sanitized annotator input MUST NOT include CAL/TEST split identity.
