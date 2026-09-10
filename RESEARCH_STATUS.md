# 📊 RESEARCH_STATUS

> **Repo:** `velantrian/Graphiti_fractal_lab`  
> **Role:** 🔬 RESEARCH sandbox — full Fractal tree mirrored for experimentation; not production Fractal Memory  
> **Updated:** 2026-09-10  
> **Upstream authority:** `velantrian/Graphiti_fractal` remains separate. Lab evidence never authorizes upstream/runtime changes.  

🤖 **AI routing:** start with [`docs/ai/README.md`](docs/ai/README.md).  
🔎 **Current retrieval-relevance research:** [`docs/research/RETRIEVAL_RELEVANCE_TRACK.md`](docs/research/RETRIEVAL_RELEVANCE_TRACK.md).  
🧾 Exact experiment claims must be checked against `artifacts/memoryops/run_00X/`, tests, and the exact branch/commit.

---

## 🧠 Current research picture

Two distinct lab lanes exist and must not be conflated:

1. **Graph-backend smoke / adapter lane** — LadybugDB + SQLite smoke and backend capability probing.
2. **Retrieval-relevance experiment lane** — bounded Graphiti 0.29.3 / FalkorDBLite experiments with run-specific model/provider evidence.

```text
ONE REPOSITORY ≠ ONE EXPERIMENTAL CLAIM
LAB TEST ≠ UPSTREAM RUNTIME
RESEARCH RESULT ≠ PRODUCTION AUTHORIZATION
```

### 🔬 Retrieval-relevance track

| Experiment | Evidence | Result ceiling | Status |
|---|---|---|---|
| **FM-13** | `artifacts/memoryops/run_004/` | BM25 introduces broad candidates; RRF preserves measured noise; Cross-Encoder was not invoked. | ✅ COMPLETED |
| **FM-14** | `artifacts/memoryops/run_005/` | Real BGE embeddings improve semantic geometry, but active hybrid filtering remains insufficient; Zephyr false positives persist. | ✅ COMPLETED |
| **FM-15** | `artifacts/memoryops/run_006/` | Real local `BAAI/bge-reranker-v2-m3` provides useful pairwise query↔fact relevance signal on the frozen 4-fact fixture. No runtime threshold/gate authorized. | ✅ COMPLETED |
| **FM-16** | no `run_007/` yet | Held-out generalization + calibration remains the next scientific question, but the first protocol draft failed independent pre-scoring review and must be revised before preregistration/scoring. | 🟠 PLANNED / PROTOCOL_REVISION_REQUIRED / NOT_RUN |

Current bounded next action:

> Revise FM-16 protocol semantics and success criteria **before preregistration or scoring**. Do not run the superseded draft.

### 🔴 FM-16 independent protocol review — 2026-09-10

Independent review verdict: `REQUEST_CHANGES_BEFORE_SCORING`.

This is **not** an FM-16 model result. No FM-16 scorer was run, no `run_007/` exists, and no generalization claim is available.

Critical findings to incorporate into the hardened protocol:

1. **Retrieval relevance was partially conflated with support for a positive proposition.** A direct negative answer such as “X does not support Y” can still be highly relevant to the yes/no question “Does X support Y?”. HN7/HN10/HN12 examples and related gold rules must be corrected before scoring.
2. **`GENERALIZATION_STRONG` could pass while rejecting zero hard negatives on answerable queries.** Strong success therefore needs an explicit preregistered hard-negative rejection / returned-set quality gate in addition to recall safety and honest EMPTY.
3. **No feasible calibration threshold must produce `threshold = null` and thresholded test metrics = `NOT_APPLICABLE`; no fallback threshold may be invented.**
4. **Model identity must be verified from the actually loaded snapshot/weights/tokenizer/config/inference profile.** A cached revision string alone is not enough.
5. **Metric formulas, denominators, tie handling, threshold comparator, verdict table, and “systematic inversion” rules must be frozen before scoring.**
6. **TEST outputs/rankings must not be exposed before threshold freeze.** The safe order is preregistration → calibration scoring → threshold freeze → TEST scoring/reporting → anchor regression.
7. **Claim scope remains bounded.** `800 pairs` is a matrix size, not 800 independent observations; success would establish only performance on the defined synthetic held-out fixture.

Additional integrity note:

```text
RELEVANT_ANSWER
≠
SUPPORTS_POSITIVE_PROPOSITION
```

A negative, conditional, scoped, historical, attributed, or numeric statement may be relevant or irrelevant depending on the **information need of the query**. Gold labels must encode that need, not a preferred truth polarity.

---

## 🔍 FM-13 → FM-16 research chain

```text
FM-13
Locate first measured degradation
→ BM25 broad candidates + RRF no semantic rejection

FM-14
Replace deterministic embeddings with real BGE embeddings
→ geometry improves
→ final hybrid filtering still insufficient

FM-15
Score every frozen query↔fact pair with real local BGE Cross-Encoder
→ useful pairwise relevance signal confirmed on fixture
→ threshold/generalization/runtime still NOT established

FM-16 v1 protocol
Independent pre-scoring review
→ REQUEST_CHANGES_BEFORE_SCORING
→ no scorer run
→ no run_007
→ draft is superseded for execution

FM-16 hardened protocol
NEXT
→ fix gold semantics
→ add explicit hard-negative rejection success gate
→ formalize infeasible-threshold/null branch and exact metric rules
→ pin actual loaded model profile
→ preregister before calibration/test scoring
```

Important FM-15 qualification:

- FM-14 embeddings were also mathematically separable on the tiny pair matrix;
- therefore `NEW_SEPARABILITY_VS_EMBEDDINGS = NOT_ESTABLISHED`;
- Cross-Encoder pairwise signal **is** established on the frozen fixture;
- broad-query Q3 had relatively low absolute CE scores, so arbitrary global thresholds are unsafe;
- no production `reranker_min_score` was selected.

For detailed reasoning and protocol-review findings, read [`docs/research/RETRIEVAL_RELEVANCE_TRACK.md`](docs/research/RETRIEVAL_RELEVANCE_TRACK.md).

---

## 🧩 Donor status for this track

Cross-project and external mechanisms are research references only:

- 🗿 **Titan** — selected/discarded + reason receipt shape; narrow negative-control/admission patterns.
- 💠 **Crystal** — hard-negative/no-recall-loss evaluation discipline and adversarial strata.
- 🧬 **Native Kernel** — relevance/similarity/rank must not become epistemic truth.
- 🦞 **OpenClaw** — candidate-window and ranking lessons; lexical fallback demonstrates recall-vs-honest-EMPTY tension.
- 🔬 **SVL** — fail-closed applicability/UNKNOWN test discipline.
- **EITI** — empty-capable selectors plus forced-fill/fallback as a negative example.
- 🕸 **Fractal experience applicability** — internal precedent for `retrieved ≠ applicable` and all-rejected results, but tool compatibility ≠ semantic query relevance.

```text
DONOR ≠ DEPENDENCY
DONOR PATTERN ≠ ADOPTED RUNTIME
SHARED GATE SHAPE ≠ SHARED AUTHORITY
```

---

## 🪞 Mirror honesty

| Path / lane | Meaning |
|---|---|
| `core/`, `api/`, `docker-compose.yml`, Fractal tests | Mirrored for safe experimentation. Presence does not mean Neo4j/Docker/secrets are available or that upstream Fractal is active here. |
| `src/fractal_lab/backends/`, Ladybug/SQLite tests | Lab-only graph-backend smoke/adapters. |
| `src/fractal_lab/memoryops/` / experiment code + `artifacts/memoryops/` | Separate bounded retrieval/memory experiment lane. Claims are run-specific. |
| `docs/research/RETRIEVAL_RELEVANCE_TRACK.md` | Human+AI explanation of the current relevance research chain; not executable proof. |
| `requirements.txt` | Mirrored Fractal stack dependency surface; dependency presence ≠ validated runtime parity. |

```text
Mirrored Fractal files ≠ Docker available ≠ Neo4j running ≠ Fractal ACTIVE in this environment
FalkorDBLite experiment evidence ≠ Neo4j parity
```

---

## ✅ Validated / observed in bounded lab scopes

### Graph-backend smoke lane

| Item | Evidence | Notes |
|---|---|---|
| ✅ LadybugDB on-disk create | `tests/test_ladybug_smoke.py` | Historical/current smoke lane; re-run on exact head before citing current pass count. |
| ✅ Ladybug node/rel Cypher write+read | same | Smoke only. |
| ✅ SQLite lab metadata table | `tests/test_sqlite_meta.py` | stdlib `sqlite3`. |
| ✅ Thin adapter interfaces | `src/fractal_lab/backends/` | Protocol + `ValidationStatus`. |
| ✅ Stubs declare NOT VALIDATED | backend stub tests | Kùzu / Postgres / DuckDB remain unvalidated. |

### Retrieval-relevance lane

| Item | Evidence | Scope ceiling |
|---|---|---|
| ✅ FM-13 path instrumentation | `run_004` | Frozen small fixture; not production path authorization. |
| ✅ Real BGE embedding differential | `run_005` | Real semantic geometry tested; not sufficient final filtering proof. |
| ✅ Real local BGE Cross-Encoder pairwise scoring | `run_006` | 20 frozen pairs; pairwise relevance signal only. |
| ✅ FM-15 integrity tests | `run_006/pytest.txt` | 14 passed in recorded run; green tests ≠ production authorization. |
| ✅ FM-16 protocol review | independent read-only audit | Protocol flaws found before scoring; this is methodology evidence, not scorer evidence. |

---

## ❌ Explicitly NOT established

| Claim | Status |
|---|---|
| Neo4j parity for FalkorDBLite memory experiments | ❌ NOT ESTABLISHED |
| Production/general Fractal relevance gate | ❌ NOT IMPLEMENTED / NOT AUTHORIZED |
| Global calibrated CE threshold | ❌ NOT ESTABLISHED |
| `NO_RELEVANT_MEMORY` runtime semantics | ❌ NOT IMPLEMENTED |
| CE generalization beyond small fixture | ⏳ FM-16 NOT_RUN; protocol revision required first |
| Cross-Encoder superiority over embeddings in general | ❌ NOT ESTABLISHED |
| Cross-Encoder score as evidence/truth/Canon | ❌ FORBIDDEN CONFLATION |
| FM-16 v1 success criteria as scientifically sufficient | ❌ SUPERSEDED / REQUEST_CHANGES_BEFORE_SCORING |
| MMR/BFS/Titan/OpenClaw/Soul/Crystal donor adoption into runtime | ❌ NOT ADOPTED |
| Kùzu/Postgres/DuckDB backend parity | ❌ NOT VALIDATED |
| Migration / dual-write / rollback authorization | ❌ NOT AUTHORIZED |

---

## 🛡️ Core research invariants

```text
RESEARCH ≠ RUNTIME
FILE EXISTS ≠ TESTED
TESTED ≠ ACTIVE
ACTIVE ≠ PRODUCTION AUTHORIZED
RETRIEVED ≠ RELEVANT
RELEVANT ≠ SUPPORTS_POSITIVE_PROPOSITION
RELEVANCE ≠ EVIDENCE
RELEVANCE ≠ TRUTH
EVIDENCE ≠ BELIEF
BELIEF ≠ TRUTH
MODEL/JUDGE SCORE ≠ AUTHORITY
NO_RELEVANT_RESULT ≠ ENTITY ABSENT
NOT RETRIEVED ≠ ABSENT
UNKNOWN ≠ FALSE
TEMPORAL APPLICABILITY ≠ SEMANTIC RELEVANCE
RESTORED BYTES ≠ RESTORED CURRENT APPLICABILITY
```

Upstream `Graphiti_fractal` remains the separate implementation authority. This lab must never silently promote experiment output into upstream behavior.

---

## 🤖 Evidence reading order

For retrieval-relevance claims:

```text
exact branch / exact commit
  > run-specific artifacts + pytest receipts
  > experiment code
  > RESEARCH_STATUS.md
  > docs/research/RETRIEVAL_RELEVANCE_TRACK.md
  > donor / external summaries
```

For graph-backend smoke claims, use the relevant backend tests and capability matrix instead.

---

## 🔬 Next research steps

### Retrieval relevance — current bounded priority

1. Produce a **hardened FM-16 protocol revision** before preregistration or scoring.
2. Correct retrieval-relevance gold semantics, especially yes/no negation, conditions, and numeric comparisons.
3. Add explicit preregistered hard-negative rejection / returned-set quality criteria for `GENERALIZATION_STRONG`.
4. Define infeasible calibration as `threshold = null` with thresholded TEST metrics `NOT_APPLICABLE`.
5. Freeze exact metrics, denominators, ties, comparator, verdict table, model snapshot/profile, and sequencing.
6. Only then execute FM-16; stop afterward for independent review.
7. Do not activate CE in runtime or set production threshold from FM-15 or from the superseded FM-16 draft.

### Backend lane — separate priority family

- Continue Ladybug/Kùzu/Postgres/DuckDB capability work only when separately scheduled.
- Do not treat backend experiments as the next action for the retrieval-relevance track.

---

## 🤖 Machine-readable snapshot

```yaml
repo: velantrian/Graphiti_fractal_lab
scope: research_sandbox
retrieval_relevance_track: IN_PROGRESS
fm13: COMPLETED
fm14: COMPLETED
fm15: COMPLETED
fm16: PLANNED_NOT_RUN
fm16_protocol_v1: REQUEST_CHANGES_BEFORE_SCORING_SUPERSEDED
fm16_preregistration: NOT_CREATED
fm16_run_007: NOT_CREATED
pairwise_ce_signal: CONFIRMED_ON_FM15_FIXTURE
new_separability_vs_embeddings: NOT_ESTABLISHED
global_threshold: NOT_ESTABLISHED
runtime_relevance_gate: NOT_IMPLEMENTED
no_relevant_memory_runtime: NOT_IMPLEMENTED
new_relevance_module_justified: false
architecture_change: false
upstream_runtime_changed_by_research: false
current_next_action: REVISE_FM16_PROTOCOL_BEFORE_PREREGISTRATION_AND_SCORING
```
