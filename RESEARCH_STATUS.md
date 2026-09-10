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
| **FM-16** | planned `artifacts/memoryops/run_007/` | Held-out generalization + calibration + adversarial hard negatives; no result exists yet. | ⏳ PLANNED / NOT_RUN |

Current bounded next question:

> Does the FM-15 Cross-Encoder signal generalize to entity-disjoint held-out data and adversarial near-misses, and can one threshold selected only on calibration data preserve recall while enabling honest EMPTY?

**Do not skip directly to runtime integration.**

---

## 🔍 FM-13 → FM-15 research chain

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

FM-16
PLANNED
→ larger entity-disjoint calibration/test corpus
→ adversarial semantic hard negatives
→ CE vs embedding baseline
→ calibration-only global-threshold feasibility
```

Important FM-15 qualification:

- FM-14 embeddings were also mathematically separable on the tiny pair matrix;
- therefore `NEW_SEPARABILITY_VS_EMBEDDINGS = NOT_ESTABLISHED`;
- Cross-Encoder pairwise signal **is** established on the frozen fixture;
- broad-query Q3 had relatively low absolute CE scores, so arbitrary global thresholds are unsafe;
- no production `reranker_min_score` was selected.

For detailed reasoning and donor map, read [`docs/research/RETRIEVAL_RELEVANCE_TRACK.md`](docs/research/RETRIEVAL_RELEVANCE_TRACK.md).

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

---

## ❌ Explicitly NOT established

| Claim | Status |
|---|---|
| Neo4j parity for FalkorDBLite memory experiments | ❌ NOT ESTABLISHED |
| Production/general Fractal relevance gate | ❌ NOT IMPLEMENTED / NOT AUTHORIZED |
| Global calibrated CE threshold | ❌ NOT ESTABLISHED |
| `NO_RELEVANT_MEMORY` runtime semantics | ❌ NOT IMPLEMENTED |
| CE generalization beyond small fixture | ⏳ FM-16 NOT_RUN |
| Cross-Encoder superiority over embeddings in general | ❌ NOT ESTABLISHED |
| Cross-Encoder score as evidence/truth/Canon | ❌ FORBIDDEN CONFLATION |
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

1. Run **FM-16 held-out generalization/calibration** when execution resources are available.
2. Stop for independent review after FM-16.
3. Only if evidence supports it, separately design an end-to-end candidate-union → CE qualification → honest EMPTY experiment.
4. Do not activate CE in runtime or set production threshold from FM-15 alone.

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
pairwise_ce_signal: CONFIRMED_ON_FM15_FIXTURE
new_separability_vs_embeddings: NOT_ESTABLISHED
global_threshold: NOT_ESTABLISHED
runtime_relevance_gate: NOT_IMPLEMENTED
no_relevant_memory_runtime: NOT_IMPLEMENTED
new_relevance_module_justified: false
architecture_change: false
upstream_runtime_changed_by_research: false
current_next_action: FM16_HELD_OUT_GENERALIZATION_AND_CALIBRATION
```
