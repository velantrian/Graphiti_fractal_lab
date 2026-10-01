# 🧪 LAB NOTICE — Graphiti_fractal_lab
> 🌐 🇬🇧 **English** · 🇷🇺 [Русский](./README.md)

> **This repository is a RESEARCH full copy of Fractal for experimentation.**
>
> - **Upstream (do not modify from lab tasks):** https://github.com/velantrian/Graphiti_fractal
> - **This lab:** https://github.com/velantrian/Graphiti_fractal_lab — safe place to try changes, backends, and docs edits.
> - **Honest runtime split:**
>   - 🐞 **Lab smoke path (no Docker):** `src/fractal_lab/` + LadybugDB/SQLite — see [`RESEARCH_STATUS.md`](RESEARCH_STATUS.md) and [`docs/ai/README.md`](docs/ai/README.md)
>   - 🗄️ **Full Fractal / Neo4j path:** mirrored tree below (`core/`, `docker-compose.yml`, …) still **requires Docker + secrets**; it is **not** claimed runnable in this lab environment without them
> - Previous lab-only landing preserved at [`docs/LAB_LANDING.md`](docs/LAB_LANDING.md)

---

# 🧠 FRACTAL MEMORY 🕸️

> **Graphiti-native local-first memory for AI agents.**
>
> Imagine an AI that does not merely keep the latest messages in its context window, but can **remember events over time, connect people and ideas, return to past experience, and preserve the provenance of memory** — without turning found, frequently repeated, or model-generated material into automatic truth.
>
> Fractal builds exactly this kind of bounded memory layer on top of **Graphiti + Neo4j**.

[🤖 **Special for AI / Agents**](docs/ai/README.md) · [🗺️ **Deep Human Overview**](SYSTEM_OVERVIEW.md) · [🧱 Technology Evolution](docs/TECHNOLOGY_EVOLUTION.md) · [🧠 AI Model Evolution](docs/AI_MODEL_EVOLUTION.md) · [🦞 OpenClaw Patterns](docs/OPENCLAW_ADOPTED_PATTERNS.md)

> 🤖 **AI coding agent / automated auditor:** do not infer current state from a polished human narrative. Start with [`docs/ai/README.md`](docs/ai/README.md), then check the exact live code, tests, and CI evidence.

---

## 👋 Fractal in 60 seconds

An ordinary chat often looks like this:

```text
💬 prompt → 🤖 model → 🗣️ answer
```

Fractal adds durable memory with explicit boundaries between the human and the model:

```text
👤 query
   ↓
🧭 recall policy
   ↓
🧩 scoped namespaces
   ↓
🕸️ Graphiti temporal memory
   ↓
🗄️ Neo4j
   ↓
📦 bounded remembered context
   ↓
🤖 model
   ↓
🗣️ answer
```

### In simple terms

Fractal is like a personal memory library where:

- 🕸️ **Graphiti** connects events, entities, and relationships over time;
- 🗄️ **Neo4j** stores the graph durably;
- 🧩 **namespaces** prevent different classes of memory from blending together unnoticed;
- 🔎 **recall** searches only within permitted areas;
- 🧾 **provenance** shows where derived artifacts came from;
- 🛡️ **trust rules** prevent frequency or import from automatically becoming authority;
- 🤖 **LLM** uses memory, but does not receive a hidden right to declare its output a durable fact.

### In engineering terms

Fractal is a single-owner local-first memory service on top of `graphiti_core==0.29.3` and Neo4j 5.26 LTS with canonical ingestion, namespace-scoped retrieval, chat persistence, provenance, L1–L3 views, and a bounded memory lifecycle.

It **does not build a second graph engine**: Graphiti remains the primary temporal/episodic memory semantics layer.

---

## 🧭 What to open first

| If you… | Start here |
|---|---|
| 👤 are seeing the project for the first time | this README, then [`SYSTEM_OVERVIEW.md`](SYSTEM_OVERVIEW.md) |
| 🤖 AI coding agent / auditor | [`docs/ai/README.md`](docs/ai/README.md) |
| 🧑‍💻 want to understand the architecture deeply | [`SYSTEM_OVERVIEW.md`](SYSTEM_OVERVIEW.md) |
| 🧱 are comparing technologies | [`docs/TECHNOLOGY_EVOLUTION.md`](docs/TECHNOLOGY_EVOLUTION.md) |
| 🧠 are checking model/provider policy | [`docs/AI_MODEL_EVOLUTION.md`](docs/AI_MODEL_EVOLUTION.md) + `core/model_policy.py` |
| 🦞 are studying memory lifecycle ideas | [`docs/OPENCLAW_ADOPTED_PATTERNS.md`](docs/OPENCLAW_ADOPTED_PATTERNS.md) |
| 🧪 are checking what is actually proven | tests + GitHub Actions + exact-head PR evidence |

---

## 🧠 Mindmap

```text
                           🧠 FRACTAL
                               │
       ┌───────────────────────┼───────────────────────┐
       ▼                       ▼                       ▼
  🕸️ MEMORY GRAPH         🔎 RECALL               💬 CONTINUITY
       │                       │                       │
  events / relations      scoped search          persisted turns
       │                       │                       │
       ├──────────────┐        │             ┌────────┘
       ▼              ▼        ▼             ▼
  🧾 Provenance   🧩 Namespaces          🪜 L1 / L2 / L3
       │              │                        │
       └──────────────┴──────────┬─────────────┘
                                 ▼
                         🛡️ TRUST BOUNDARY
                                 │
                                 ▼
                       🔁 MEMORY LIFECYCLE
```

---

## 🗺️ Architecture at a glance

```text
┌──────────────────── 🌍 HUMAN / AGENT / TOOL ──────────────────────┐
│   🌐 Web UI · 🔌 HTTP · 🤖 MCP · ⌨️ CLI                           │
└───────────────────────────────┬────────────────────────────────────┘
                                ▼
                         🔐 local boundary
                                │
                                ▼
                           🧠 MemoryOps
                                │
               ┌────────────────┼────────────────┐
               ▼                ▼                ▼
        ✍️ canonical ingest   🔎 recall      💬 persistence
               │                │                │
               └────────────────┴────────┬───────┘
                                        ▼
                                   🕸️ Graphiti
                                        │
                                        ▼
                                🗄️ Neo4j 5.26 LTS
                                        │
                  ┌─────────────────────┼─────────────────────┐
                  ▼                     ▼                     ▼
             🧾 provenance         📊 telemetry          🪜 L1/L2/L3
```

### The main formula

```text
Graphiti remembers relationships through time.
Fractal bounds how that memory enters, is recalled, and is trusted.
Neo4j persists the graph.
The model uses memory — it does not become memory authority by default.
```

---

## 🌳 Project tree

```text
🧠 Fractal Memory
│
├── 🌐 Interfaces
│   ├── Web / HTTP
│   ├── MCP
│   └── CLI
│
├── 🕸️ Graph memory
│   ├── Graphiti
│   └── Neo4j
│
├── 🧩 Namespaces
│   ├── personal
│   ├── project
│   ├── knowledge
│   ├── experience
│   └── imports  ⚠️ isolated / untrusted
│
├── 🔎 Recall
│   └── off / auto / always
│
├── ✍️ Canonical ingest
│   └── knowledge/ingest.py
│
├── 🔁 Lifecycle
│   ├── promotion explainability
│   ├── consolidation preview
│   └── external import isolation
│
├── 🪜 Derived views
│   ├── L1 episodic
│   ├── L2 communities
│   └── L3 bounded synthesis
│
└── 🔬 Research / adjacent
    ├── GraphRAG / KAG / CAG
    ├── PostgreSQL / pgvector
    ├── alternative graph backends
    └── causal / GDS experiments
```

---

## 📊 What exists, what is bounded, what is being researched

| Area | Now | Meaning |
|---|---|---|
| 🕸️ Graphiti memory | ✅ **ACTIVE** | primary temporal graph memory engine |
| 🗄️ Neo4j 5.26 LTS | ✅ **ACTIVE** | durable graph persistence |
| 🧩 Namespace isolation | ✅ **ACTIVE** | scoped memory boundaries |
| 🔎 Adaptive recall | ✅ **ACTIVE** | `off / auto / always` |
| 💬 Chat persistence | ✅ **ACTIVE** | persisted turns + bounded summaries |
| 🧾 Provenance | ✅ **ACTIVE** | exact lineage for new derived artifacts |
| 🔐 Unique ingest claim | ✅ **TESTED** | concurrent duplicate admission fail-closed at app boundary |
| 🔁 Promotion | 🟡 **EXPLAIN / GATED** | eligibility exists; automatic durable writer is absent |
| 🧪 Consolidation | 🟡 **DRY_RUN** | preview only |
| 📥 External imports | 🟡 **ISOLATED** | explicit apply; remain untrusted |
| 🪜 L1 / L2 / L3 | ✅ / 🟡 | views/synthesis, not a new Canon |
| 🕸️ GraphRAG / KAG / CAG | 🔬 **RESEARCH** | not active parallel pipelines |
| 🗃️ PostgreSQL / pgvector | 🔬 **ADJACENT** | not the current memory authority |
| 🐞 Alternative graph backend | 🔬 **RESEARCH** | migration is not activated |
| 🧮 Causal / GDS write-back | ❌ **NOT AUTHORIZED** | research ≠ runtime |
| 🚀 Production authorization | ❌ **NOT CLAIMED** | CI green ≠ production authorization |

---

## 🧾 Visual status grammar

| Label | Meaning |
|---|---|
| ✅ **active / tested** | belongs to the current engineering path and is confirmed by corresponding contract evidence |
| 🟡 **bounded / gated** | exists, but is limited by a preview/config/authority boundary |
| 🔬 **research / adjacent** | under study; the presence of code or documentation does not mean runtime adoption |
| 🚧 **open PR** | is not `main` yet |
| ⚠️ **limitation** | known boundary |
| ❌ **not authorized / unavailable** | cannot be asserted as an active capability |

```text
📄 file exists
   ≠ 🧪 contract proved
   ≠ 🎛️ feature enabled
   ≠ 🔗 active path
   ≠ 📡 runtime observed
   ≠ 🚀 production authorized
```

---

## 🆚 How Fractal differs in architectural emphasis

> This is **not a “who is better” ranking**. The approaches solve different problems and can be used together.

| Approach | 🎯 Main task | 🕸️ Temporal graph | 🧾 Provenance | 🛡️ Trust isolation | 🔁 Promotion lifecycle |
|---|---|---:|---:|---:|---:|
| 📦 Vector RAG | retrieve relevant context | ❌ | 🟡 varies | 🟡 varies | ❌ usually outside scope |
| 🧠 Agent memory / Letta-style | continuity + managed memory | 🟡 varies | 🟡 varies | 🟡 varies | ✅/🟡 |
| 🕸️ Graph memory | relation-aware memory | ✅/🟡 | ✅/🟡 | 🟡 varies | 🟡 varies |
| 🕸️ Graphiti | temporal knowledge-graph primitives | 🎯 core | 🎯 core | implementation-level | graph semantics |
| 🧠 **Fractal** | bounded local AI memory **on Graphiti** | ✅ | ✅ explicit | 🎯 core | 🎯 explain / preview / gated |

**Fractal does not replace Graphiti.** It uses Graphiti as the primary memory engine and adds application-level boundaries: namespaces, canonical ingestion, trust isolation, lifecycle gates, product surfaces, and validation contracts.

Detailed explanation and comparison limitations → [`SYSTEM_OVERVIEW.md`](SYSTEM_OVERVIEW.md).

---

## 🛡️ Five boundaries that matter more than the number of features

```text
🔎 retrieval  ≠ evidence
🕸️ graph      ≠ truth
📥 imported   ≠ trusted
🔁 frequency  ≠ authority
🤖 model text ≠ durable fact
```

And two more engineering boundaries:

```text
🔬 research ≠ runtime
✅ green CI ≠ production authorization
```

---

## 🧩 Memory namespaces

| Namespace | Purpose | Normal recall |
|---|---|---:|
| 👤 `personal` | local owner/dialogue memory | ✅ |
| 🛠️ `project` | projects and technical decisions | ✅ |
| 📚 `knowledge` | documents and general knowledge | ✅ |
| 🧪 `experience` | task execution experience | ✅ |
| 📥 `imports` | explicitly applied external memory | ❌ isolated |

For multiple namespaces, Fractal performs **separate bounded Graphiti searches**, then combines the results at the application layer. A hidden global unscoped query is not the canonical path.

---

## 🔁 Memory lifecycle

### 🧭 Adaptive recall

```text
query
  ↓
recall policy
  ├── off     → no memory recall
  ├── auto    → skip only clearly trivial turns
  └── always  → bounded recall
```

### ⚖️ Promotion gate

Deterministic scoring can explain eligibility and blockers, but **does not perform an automatic durable promotion write**.

`untrusted` and `system` origins do not become eligible merely because of high recall frequency.

### 🧪 Consolidation

```bash
python main.py memory-consolidate-preview candidates.json
```

Always preview: `DRY_RUN / writes_performed=false`.

### 📥 External imports

```bash
# Preview — no write
python main.py memory-import ./memory.md --source-type openclaw

# Explicit write into isolated imports namespace
python main.py memory-import ./export.jsonl --source-type claude --apply
```

An applied import remains `untrusted` and does not receive normal chat recall authority.

---

## 🪜 L1 / L2 / L3

```text
🧠 L1 — recent episodic memory
          ↓
🕸️ L2 — Graphiti communities
          ↓
🧩 L3 — bounded synthesis with provenance
```

L3 is a derived representation, not a parallel source of truth.

---

## 🤖 AI model policy

Current defaults are centralized in `core/model_policy.py`.

| Workload | Default |
|---|---|
| 💬 Interactive chat | `gpt-5.6-terra` |
| 🕸️ Graphiti extraction / reasoning | `gpt-5.6-terra` |
| 🧩 Summary synthesis | `gpt-5.6-luna` |
| ⚙️ Graphiti small prompts | `gpt-5.6-luna` |
| 🧭 Frontier opt-in | `gpt-5.6-sol` via env |
| 🔢 Embeddings | `text-embedding-3-small` |

The first-class provider path is currently OpenAI. The history and roles of other model families are described separately in [`docs/AI_MODEL_EVOLUTION.md`](docs/AI_MODEL_EVOLUTION.md); mentioning a model there **does not mean active runtime support**.

The embedding model does not change automatically with the chat model, because that changes vector-index identity and requires a separate reindex/migration decision.

---

## 🧱 Technology roles

| Technology | Role | Status |
|---|---|---|
| 🕸️ Graphiti | temporal/episodic graph memory | ✅ ACTIVE |
| 🗄️ Neo4j | durable graph backend | ✅ ACTIVE |
| 🗃️ PostgreSQL / pgvector | relational/vector alternatives | 🔬 ADJACENT |
| 🕸️ GraphRAG / KAG / CAG | retrieval/reasoning references | 🔬 RESEARCH |
| ⚡ KV / prefix cache | inference compute reuse | ⚙️ INFERENCE LAYER |
| 🦞 OpenClaw patterns | selected memory lifecycle ideas | 🟡 BOUNDED ADOPTION |

Evidence-backed details → [`docs/TECHNOLOGY_EVOLUTION.md`](docs/TECHNOLOGY_EVOLUTION.md).

---

## 🚀 Quickstart

```bash
cp .env.example .env
# Заполните NEO4J_PASSWORD, OPENAI_API_KEY, FRACTAL_API_TOKEN.

docker compose build
docker compose up -d
```

Locally:

- 🌐 Web/API — `http://127.0.0.1:8000`
- 🕸️ Neo4j Browser — `http://127.0.0.1:7474`
- 🔌 Bolt — `127.0.0.1:7687`

Minimal configuration:

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=<strong-password>
OPENAI_API_KEY=<key>
FRACTAL_API_TOKEN=<long-random-token>
FRACTAL_USER_ID=<local-owner>
FRACTAL_MEMORY_RECALL=auto
```

Destructive operations are disabled by default:

```env
FRACTAL_ALLOW_HARD_DELETE=0
FRACTAL_ALLOW_CLEAR_ALL=0
```

---

## 🛠️ Main CLI commands

```bash
python main.py setup
python main.py seed
python main.py quality
python main.py context "Graphiti" --size full
python main.py benchmark
python main.py memory-status
python main.py memory-status --deep
python main.py memory-import ./memory.md --source-type openclaw
python main.py memory-promote-explain --help
python main.py memory-consolidate-preview candidates.json
python main.py l1 --query "Fractal Memory" --hours 24
python main.py l2 "Graphiti"
python main.py l3-build "Graphiti"
```

MCP stdio server:

```bash
python -m mcp_server
```

---

## 🧪 How the system is tested

```text
⚙️ always-on Python contracts
           ↓
🕸️ live provider-free Neo4j integration
           ↓
🤖 provider-backed E2E
   requires real OPENAI_API_KEY
           ↓
🗄️ legacy provenance preview
   requires real legacy credentials
   DRY_RUN only
```

An external test that was skipped because a secret was missing **does not count as PASS**.

---

## ⚠️ Honest limitations

- 🏠 the system is intentionally local/single-owner, not a multi-user SaaS;
- 📥 applied imports remain isolated/untrusted;
- 🔁 the automatic durable promotion writer is not activated;
- 🧪 consolidation remains preview-first;
- 🤖 the first-class provider path is currently OpenAI;
- 🔬 GraphRAG/KAG/CAG/PostgreSQL/pgvector/alternative graph backends are not hidden active dependencies;
- 🧮 causal/GDS research has no runtime write authority;
- 🚀 production authorization does not follow from a single green CI.

---

## 📚 Read deeper

### 👤 For humans

➡️ **[`SYSTEM_OVERVIEW.md`](SYSTEM_OVERVIEW.md)** — a detailed architectural tour: flows, boundaries, lifecycle, comparisons, validation semantics, and research map.

### 🤖 For AI / Agents / Auditors

➡️ **[`docs/ai/README.md`](docs/ai/README.md)** — machine-first reading order, authority rules, invariants, and forbidden inferences.

### 🧱 For technical research

- [`docs/TECHNOLOGY_EVOLUTION.md`](docs/TECHNOLOGY_EVOLUTION.md) — technology decisions;
- [`docs/AI_MODEL_EVOLUTION.md`](docs/AI_MODEL_EVOLUTION.md) — model/provider evolution;
- [`docs/OPENCLAW_ADOPTED_PATTERNS.md`](docs/OPENCLAW_ADOPTED_PATTERNS.md) — adopted memory patterns.

---

## 🧭 One reality — different views

```text
                       🧠 ONE PROJECT REALITY
                                │
          ┌─────────────────────┼─────────────────────┐
          │                     │                     │
          ▼                     ▼                     ▼
     👤 HUMAN VIEW         🤖 AI VIEW            📚 EVIDENCE
 README + OVERVIEW       docs/ai/README       tests / CI / PR
          │                     │                     │
          └─────────────────────┼─────────────────────┘
                                ▼
                       ⚙️ LIVE CODE / STATE
```

**Human docs explain. AI docs route. Evidence proves. Live code defines the current implementation.**
