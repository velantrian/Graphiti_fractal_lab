# 🏷️ Oracle Annotation Guide — FM-17-pre

## Goal

Produce an **auditable** `oracle_annotations.json` / `.jsonl` covering every evaluated `(query_id, fact_id)` pair used by the offline ablation (at minimum: all pairs appearing in frozen `run_007` CE score tables that participate in metrics, plus the **MULTIHOP_COMPONENT_RETENTION** diagnostic pairs).

## Sources

| `annotation_source` | Meaning | Allowed as gold for ablation? |
|---------------------|---------|--------------------------------|
| `HUMAN_GOLD` | Human-authored structural + relevance labels | ✅ Yes |
| `RULE_DERIVED` | Deterministic rules from explicit lexical markers / FM-16 HN labels / gold sets | ✅ Yes **if** rule text is cited in `annotation_notes` and reviewed |

### LLM labels

- ❌ LLM-generated labels are **not** gold by default.
- If present for convenience, mark `annotation_source` as a non-gold channel (do **not** use `HUMAN_GOLD`), put `LLM_DRAFT_NOT_GOLD` in `annotation_notes`, and **exclude** from primary ablation until independently reviewed and upgraded to `HUMAN_GOLD` or replaced by `RULE_DERIVED`.

## Required fields

See `oracle_annotations.schema.json`.

Minimum:

- `query_id`, `fact_id`
- `query.*` structural targets + `query_class`
- `fact.*` structural fields
- `gold_relevance_class` ∈ `{DIRECT, COMPONENT, RELATED, NONANSWER}`
- `annotation_source`, `annotation_notes`

## Relevance classes (protected)

```
DIRECT_ANSWER ≠ MULTI_HOP_COMPONENT ≠ RELATED_CONTEXT ≠ NONANSWER
```

| Class | Meaning |
|-------|---------|
| `DIRECT` | Fact answers the query (or the decomposed final-hop evidence when `query_class=MULTIHOP`) without requiring another hop |
| `COMPONENT` | Fact is necessary for a multi-hop answer but is not itself the final answer |
| `RELATED` | Topically related but not required for the answer |
| `NONANSWER` | Should not survive as an answer-supporting memory for this query |

### Mandatory example (diagnostic)

Query: *What language does Alice's project use?*

- `Alice → works_on → Orion` → **COMPONENT** (never ordinary NONANSWER)
- `Orion → uses → Python` → **DIRECT** for decomposed second hop / final-answer evidence
- `Nova → uses → Rust` → **RELATED** (or NONANSWER if protocol marks stricter; template uses RELATED)

## Query classes (separate axes)

| `query_class` | Axis |
|---------------|------|
| `NARROW` | Narrow / direct factoid |
| `STATE` | Structured + state / scope-sensitive |
| `BROAD` | Broad / exploratory |
| `NO_ANSWER` | Gold empty / unsupported / nonexistent |
| `MULTIHOP` | Component retention diagnostic |

Map FM-16 `query_subtype` / `query_class` into these axes in notes when deriving from run_007.

## Freeze rule

1. Complete annotations.
2. Validate against schema.
3. Compute `sha256` of the annotation file.
4. Record hash in ablation receipt **before** any arm computation.
5. **No TEST-driven retuning** of filter rules after seeing held-out metrics.

## Template

`oracle_annotations.template.jsonl` contains **EXAMPLE_NOT_GOLD** rows only.
