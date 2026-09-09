# 🧪 LABS HANDOFF — Graphiti / Fractal lab session

**Status:** RESEARCH BRIEF FOR EXTERNAL AUDIT (ChatGPT / human)  
**Date:** 2026-09-09 (Europe/Berlin evening; UTC ~20:18)  
**Author:** Labs (Grok Bot assistant for user Quitzon Trey / velantrian)  
**Audience:** ChatGPT auditor + owner — decide next adaptation steps  
**Language:** Russian body (owner preference) + machine-scannable facts

> 🤖 **For AI auditors:** This document is orientation + evidenced claims. Prefer live GitHub SHAs, pytest, and the smoke transcript below over narrative polish.  
> ❌ Do not treat this lab as production authorization for Fractal Memory.  
> 🔒 Upstream `velantrian/Graphiti_fractal` was **not** modified in this work.

---

## 1. 🎯 Goal of the session

Owner asked whether Labs can run “the system” for testing (Velantrim / memory stack), then focused on **`Graphiti_fractal`**, then created a **research fork** to experiment with lighter backends (LadybugDB / Kùzu / SQLite / PostgreSQL / …) **without changing the main repo**.

Later: landscape research + **live smoke** of Graphiti on FalkorDBLite. Owner now wants a **full handoff** before choosing next steps with ChatGPT.

---

## 2. 📌 Repositories (exact)

| Repo | Role | SHA (main tip at handoff) | Notes |
|---|---|---|---|
| [`velantrian/Graphiti_fractal`](https://github.com/velantrian/Graphiti_fractal) | **Upstream / canon** Fractal Memory (Graphiti + Neo4j) | `2437244` | **Untouched** this session |
| [`velantrian/Graphiti_fractal_lab`](https://github.com/velantrian/Graphiti_fractal_lab) | **RESEARCH lab** — full mirror + lab adapters | `930279b` | Experiment freely |

Lab was created public as `Graphiti_fractal_lab` (owner-chosen name). Contents now include:

- Full mirrored Fractal tree (code, docs, docker-compose, tests, …)
- Lab-only layer: `src/fractal_lab/` (Ladybug + SQLite + stubs), smoke tests, Velantrim-style docs, `docs/LAB_LANDING.md`, LAB NOTICE on README
- Upstream AI router preserved as `docs/ai/UPSTREAM_FRACTAL_README.md` where applicable

---

## 3. 🖥️ What Labs environment actually is

Labs = Grok Bot assistant with a **shared Linux “box” computer** (not the user’s personal PC unless registered machines are used).

| Capability | Observed fact |
|---|---|
| OS / Python | Linux, **Python 3.13.5** |
| GitHub | Authenticated as **`velantrian`** via `gh` / `GH_TOKEN` |
| Docker | **`docker: command not found`** — Neo4j via `docker compose` **not available** |
| Node | Present (v20.x observed earlier) |
| OpenAI | **`OPENAI_API_KEY` not set** in this environment at smoke time |
| Desktop / browser | Available via box desktop (not required for this handoff) |
| Cloud coding agent | Launch blocked: Cursor usage exhausted / on-demand needed — work done via shell + `gh` instead |
| Can create/push GitHub repos under velantrian | **Yes** (lab repo created + pushes succeeded) |
| Must not change upstream without owner ask | Observed: Fractal main not pushed |

### What Labs can do well here

- Clone / mirror / edit **`Graphiti_fractal_lab`**
- `pip` install embedded DBs and Python libs
- Run pytest / smoke scripts
- Read upstream via `gh api` without mutating it
- Write docs in Velantrim human+AI style

### What Labs cannot do *right now* (blockers)

- Run **documented Fractal quickstart** (`docker compose` + Neo4j 5.26.29 + app `:8000`) — no Docker
- Run **default Graphiti()** needing OpenAI — no API key in env
- Claim **production** or **Graphiti↔Ladybug official driver** (does not exist upstream)
- Use Cursor CloudAgent until usage/on-demand restored (workaround: local/shell)

---

## 4. 🧵 Chronology (decisions)

1. Owner: can Labs run “my system”? → clarified multi-organ Velantrim; System OS `GITHUB_NOT_CREATED`; Native Kernel `runtime FROZEN`; Titan production not authorized; E2E not validated (from other bots’ memory/transcripts).
2. Focus → **`Graphiti_fractal`**: assembled product; quickstart = Docker + Neo4j + secrets.
3. Owner: Ladybug/Kuzu/SQLite/Postgres easier than Neo4j? → Yes for install; **not** validated as Fractal ACTIVE replacements (upstream matrix: Ladybug EVALUATE ONLY).
4. Owner: create **second research repo**, don’t touch main → created **`Graphiti_fractal_lab`**.
5. Velantrim-style docs rewritten for lab.
6. Owner: mirror **all** Fractal code+docs into lab → done (`930279b`), lab adapters preserved.
7. Landscape research: Kùzu archived; Ladybug active successor; Graphiti multi-backend; FalkorDBLite candidate for no-Docker Graphiti.
8. Live smoke Graphiti + FalkorDBLite → connect/indices/query **OK** with stubs; episode not run (no OpenAI).
9. **Now:** handoff for ChatGPT audit; Labs waits for owner direction.

---

## 5. 🗄️ Database / Graphiti landscape (evidence)

### Kùzu

- GitHub [`kuzudb/kuzu`](https://github.com/kuzudb/kuzu): **`archived: true`**, last push **2025-10-10**
- Community narrative: team acqui-hired (Apple); do not rely on unmaintained tree for security/fixes
- Upstream Graphiti README: **Kuzu driver deprecated**

### LadybugDB

- GitHub [`LadybugDB/ladybug`](https://github.com/LadybugDB/ladybug): **not archived**, ~**1724★**, active pushes (incl. 2026-09-09)
- Install: `pip install ladybug`
- Positioning: embedded columnar graph / “DuckDB for graphs”; Cypher; successor path from Kùzu
- Landscape takes: [gdotv Kùzu legacy article](https://gdotv.com/blog/kuzu-legacy-embedded-graph-database-landscape/), [Ladybug blog](https://blog.ladybugdb.com/post/ladybug-flying-solo/), [ladybugdb.com](https://ladybugdb.com/)
- **No official Graphiti driver for Ladybug** found
- Labs: **Ladybug smoke already green** in lab (`4 passed` earlier; package import still OK at handoff)

### SQLite / PostgreSQL / DuckDB

| Store | Labs fit | Fractal-lab role |
|---|---|---|
| SQLite | Built into Python | Ops/metadata — **smoke OK**; not graph authority |
| PostgreSQL | Installable via apt (server; no Docker required) | ADJACENT relational — stub only so far |
| DuckDB | `pip` available | Analytics adjacent — stub only |

Upstream Fractal `TECHNOLOGY_EVOLUTION`: SQLite **DEFERRED**, Postgres/pgvector **ADJACENT**, Neo4j **ACTIVE**.

### Neo4j (Fractal ACTIVE path)

- Fractal `docker-compose.yml`: `neo4j:5.26.29-community` + app
- Needs `.env`: `NEO4J_PASSWORD`, `OPENAI_API_KEY`, `FRACTAL_API_TOKEN`, …
- Labs: **blocked** (no Docker)

### Graphiti (`graphiti-core`)

- Fractal pins **`graphiti_core==0.29.3`**
- Fractal `core/graphiti_client.py`: constructs `Graphiti(uri, user, password)` — **Neo4j hardcode** + OpenAI LLM/embedder; requires `NEO4J_URI/USER/PASSWORD`
- Upstream drivers ([docs](https://getzep-graphiti.mintlify.app/guides/graph-drivers), [getzep/graphiti](https://github.com/getzep/graphiti)): Neo4j, FalkorDB, Neptune, Kùzu (deprecated)
- **FalkorDBLite**: embedded FalkorDB via `pip` / `graphiti-core[falkordblite]`; Python ≥3.12; examples pass `AsyncFalkorDB` into `FalkorDriver`

---

## 6. 🔬 Live smoke results (Labs, 2026-09-09)

Environment: `/workspace/Graphiti_fractal_lab` venv, Python 3.13.5.

| Step | Result |
|---|---|
| `pip install graphiti-core[falkordblite]==0.29.3` | OK (also needed `httpx` etc.) |
| Default `Graphiti(graph_driver=…)` with no OpenAI | **FAIL** — `OpenAIError: Missing credentials` |
| `Graphiti(graph_driver=FalkorDriver(AsyncFalkorDB(...)), llm_client=Stub, embedder=Stub, cross_encoder=Stub)` | **CONNECT OK** |
| `await build_indices_and_constraints()` | **INDICES OK** |
| `await driver.execute_query(...)` | **OK** |
| `add_episode` with real model | **NOT RUN** — no `OPENAI_API_KEY` |
| Process shutdown | `RuntimeWarning` redislite shutdown (non-fatal for smoke) |

**Interpretation (honest):**

- ❌ Fractal-as-shipped (Neo4j Docker path) — **not runnable on Labs now**
- ✅ Graphiti library + **FalkorDBLite** — **storage/driver path works** on Labs without Docker
- 🟡 Full “smart” Graphiti episodes — **needs LLM/embedder credentials** (or a deliberate stub-only research mode)
- ✅ Ladybug path — independent of Graphiti; good for embedded graph experiments / future adapter research

---

## 7. 🧱 What already exists in the lab

- Mirror of Fractal product code + docs + compose
- `src/fractal_lab/backends/`: Ladybug adapter, SQLite meta, stubs (kuzu/postgres/duckdb)
- Tests: `tests/test_ladybug_smoke.py`, `tests/test_sqlite_meta.py`
- Docs: README LAB NOTICE, `SYSTEM_OVERVIEW.md`, `RESEARCH_STATUS.md`, `docs/ai/README.md`, `AGENTS.md`, capability matrix
- **Not yet:** `FRACTAL_GRAPH_BACKEND=falkordblite` wired into `core/graphiti_client.py`; no OpenAI episode proof; no Ladybug↔Graphiti driver

---

## 8. 🧭 Options for ChatGPT / owner to choose

### A — Wire FalkorDBLite into lab Fractal client
- Change lab-only `graphiti_client` (or factory) to select Neo4j vs FalkorDBLite via env
- Keep upstream Fractal untouched
- Still need OpenAI (or stubs) for episode path

### B — Prove Graphiti episode on Labs
- Provide `OPENAI_API_KEY` via secure secret mechanism
- Run `add_episode` + search smoke on FalkorDBLite
- Highest evidence for “Graphiti works in sandbox”

### C — Deepen Ladybug-native lab memory (no Graphiti)
- Evolve Fractal *boundaries* (namespaces, provenance ideas) on Ladybug+SQLite
- Accept: not Graphiti semantics until a real driver exists

### D — Install Docker on Labs box → Neo4j path
- Closest to upstream quickstart
- Heavier; still needs secrets

### E — Pause code; only doc/governance
- Update RESEARCH_STATUS / matrix with this handoff; wait

**Labs recommendation (non-binding):** Prefer **B then A** if the goal is “real Graphiti in sandbox”; prefer **C** if the goal is “lightest always-on lab without API keys”; **D** only if parity with upstream compose matters more than embedded simplicity.

---

## 9. ⚠️ Non-claims / invariants

```text
file exists ≠ smoke tested ≠ Graphiti-compatible ≠ Fractal ACTIVE ≠ production authorized
research lab ≠ upstream authority
Ladybug ≠ official Graphiti backend
FalkorDBLite smoke ≠ full Fractal app validated
CI green upstream ≠ lab runtime
Kùzu archived ≠ use for new work
```

Upstream Fractal migration matrix still says: one durable graph authority at a time; Ladybug experiment = EVALUATE ONLY; no silent dual-write.

---

## 10. 📎 Links

- Lab: https://github.com/velantrian/Graphiti_fractal_lab  
- Upstream: https://github.com/velantrian/Graphiti_fractal  
- Ladybug: https://github.com/LadybugDB/ladybug  
- Graphiti: https://github.com/getzep/graphiti  
- Drivers: https://getzep-graphiti.mintlify.app/guides/graph-drivers  
- FalkorDBLite: https://pypi.org/project/falkordblite/ · https://docs.falkordb.com/operations/falkordblite/falkordblite-py  

---

## 11. ✅ Ask to ChatGPT

Please audit this handoff and advise the owner:

1. Which option (A–E) best fits a **Labs sandbox** that must stay experimental and must not corrupt upstream Fractal?
2. Any risk in treating FalkorDBLite as interim Graphiti backend for lab (semantics/parity gaps vs Neo4j)?
3. Should Ladybug remain parallel research only until a Graphiti driver exists?
4. Minimum evidence bar before calling lab “Graphiti-runnable” (indices-only vs episode+search)?

Owner will return to Labs with a concrete decision.

---

*End of handoff. Generated for copy/paste into ChatGPT.*
