# 🧠 FRACTAL LAB 🧪🕸️

> **RESEARCH sandbox рядом с Graphiti Fractal — не production memory.**
>
> Здесь мы проверяем, насколько лёгкие graph/metadata backends (прежде всего
> **LadybugDB + SQLite**) вообще живут вне Docker/Neo4j — без претензии заменить
> Graphiti или объявить migration.
>
> Upstream остаётся источником истины для Fractal Memory:
> [`velantrian/Graphiti_fractal`](https://github.com/velantrian/Graphiti_fractal).
> Этот репозиторий — **лаборатория**, не sibling runtime.

[🤖 **Special for AI / Agents**](docs/ai/README.md) ·
[🗺️ **Deep Human Overview**](SYSTEM_OVERVIEW.md) ·
[📊 Research Status](RESEARCH_STATUS.md) ·
[🗄️ Backend Matrix](docs/GRAPH_BACKEND_CAPABILITY_MATRIX.md)

> 🤖 **AI coding agent / automated auditor:** не выводи current state из красивого
> human narrative. Начни с [`docs/ai/README.md`](docs/ai/README.md), затем проверь
> exact live code, tests и этот lab ledger. **Не путай lab smoke с Fractal ACTIVE path.**

---

## 👋 Lab за 60 секунд

Обычный Fractal путь (upstream, **не этот repo**):

```text
👤 query → 🧭 recall → 🕸️ Graphiti → 🗄️ Neo4j → 📦 bounded context → 🤖 model
```

Этот lab делает другое — тонкий эксперимент **вне** Fractal runtime:

```text
🧪 lab smoke
   ↓
🐞 LadybugDB on-disk  ── Cypher node/rel round-trip
   ↓
🗃️ SQLite            ── lab ops / metadata only
   ↓
📄 stubs             ── Kùzu / Postgres / DuckDB (NOT VALIDATED)
```

### Простыми словами

Lab похож на верстак рядом с настоящей библиотекой памяти:

- 🐞 **LadybugDB** — лёгкий embedded graph для smoke (не Neo4j);
- 🗃️ **SQLite** — таблица метаданных прогонов (не graph authority);
- 📄 **stubs** — заготовки под другие backends, пока без evidence;
- 🕸️ **Graphiti + Neo4j** живут только в upstream Fractal и **сюда не перенесены**;
- 🔬 цель — честно узнать, что проходит smoke, а не объявить migration.

### Инженерным языком

`fractal-lab` — Python package (`src/fractal_lab`) с Protocol-адаптерами,
Ladybug smoke adapter, SQLite meta store и stub backends. Нет Docker, нет Neo4j,
нет OpenAI, нет `graphiti_core` runtime. **4 pytest smoke tests passed** на
Python 3.13 + `ladybug==0.20.3` (verify locally before citing elsewhere).

---

## 🧭 Что открыть первым

| Если вы… | Начните здесь |
|---|---|
| 👤 впервые видите lab | этот README, затем [`SYSTEM_OVERVIEW.md`](SYSTEM_OVERVIEW.md) |
| 🤖 AI coding agent / auditor | [`docs/ai/README.md`](docs/ai/README.md) → [`AGENTS.md`](AGENTS.md) |
| 🧑‍💻 хотите архитектуру глубже | [`SYSTEM_OVERVIEW.md`](SYSTEM_OVERVIEW.md) |
| 📊 проверяете, что реально доказано | [`RESEARCH_STATUS.md`](RESEARCH_STATUS.md) + `pytest` |
| 🗄️ сравниваете backends | [`docs/GRAPH_BACKEND_CAPABILITY_MATRIX.md`](docs/GRAPH_BACKEND_CAPABILITY_MATRIX.md) |
| 🧠 ищете production Fractal Memory | ➡️ [`Graphiti_fractal`](https://github.com/velantrian/Graphiti_fractal) |

---

## 🧠 Mindmap

```text
                        🧪 FRACTAL LAB
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
   🐞 Ladybug smoke      🗃️ SQLite meta        📄 Optional stubs
   on-disk Cypher        ops / runs ledger     Kùzu · Postgres · DuckDB
        │                     │                     │
        ▼                     ▼                     ▼
   ✅ SMOKE-TESTED       ✅ SMOKE-TESTED       🔬 STUB / NOT VALIDATED
        │                     │                     │
        └──────────┬──────────┴──────────┬──────────┘
                   ▼                     ▼
            🛡️ Authority rule      ❌ No Fractal parity
         lab ≠ durable memory     Neo4j / Graphiti out of scope
```

---

## 🗺️ Архитектура одним взглядом

```text
┌──────────────── 🌍 RESEARCHER / AI AGENT / CI ────────────────┐
│   ⌨️ pytest · 📄 docs · 🧪 smoke only                         │
└─────────────────────────────┬─────────────────────────────────┘
                              ▼
                    🧪 fractal_lab adapters
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
   🐞 LadybugAdapter    🗃️ SqliteLabMeta    📄 *Stub backends
   CREATE/MATCH smoke   record_run/list     raise / declare status
          │                   │                   │
          ▼                   ▼                   ▼
   💾 on-disk .lbdb      💾 .sqlite file     (no durable claim)
```

### Главная формула

```text
Upstream Fractal remembers with Graphiti + Neo4j.
This lab smokes lightweight backends outside that path.
Smoke ≠ parity. Stub ≠ validated. Lab graph ≠ Fractal memory.
```

---

## 🌳 Дерево проекта

```text
🧪 Graphiti_fractal_lab
│
├── 📦 src/fractal_lab/
│   └── backends/
│       ├── base.py              Protocol + ValidationStatus
│       ├── ladybug_adapter.py   ✅ primary runnable path
│       ├── sqlite_meta.py       ✅ lab ops/metadata
│       ├── kuzu_stub.py         🔬 NOT VALIDATED
│       ├── postgres_stub.py     🔬 NOT VALIDATED
│       └── duckdb_stub.py       🔬 NOT VALIDATED
│
├── 🧪 tests/
│   ├── test_ladybug_smoke.py
│   └── test_sqlite_meta.py
│
├── 📚 docs/
│   ├── ai/README.md             🤖 machine-first entry
│   └── GRAPH_BACKEND_CAPABILITY_MATRIX.md
│
├── 🗺️ SYSTEM_OVERVIEW.md
├── 📊 RESEARCH_STATUS.md
├── 🤖 AGENTS.md
└── 💾 data/                     scratch (gitkeep)
```

---

## 📊 Что есть, что ограничено, что исследуется

| Область | Сейчас | Смысл |
|---|---|---|
| 🐞 LadybugDB on-disk create | ✅ **SMOKE** | `ladybug==0.20.3`, pytest |
| 🐞 Cypher node/rel round-trip | ✅ **SMOKE** | CREATE NODE/REL + MATCH |
| 🗃️ SQLite lab metadata | ✅ **SMOKE** | stdlib `sqlite3` runs table |
| 🔌 Thin adapter Protocol | ✅ **IMPLEMENTED** | `GraphBackend` + status enum |
| 📄 Kùzu / Postgres / DuckDB | 🔬 **STUB** | declare `NOT VALIDATED` |
| 🕸️ Graphiti on Ladybug | ❌ **NOT VALIDATED** | no `graphiti_core` path here |
| 🗄️ Neo4j parity | ❌ **NOT CLAIMED** | temporal, group_id, vectors, … |
| 🔁 Migration / dual-write | ❌ **NOT AUTHORIZED** | lab ≠ migration decision |
| 🤖 OpenAI / embeddings | ❌ **OUT OF SCOPE** | intentionally absent |
| 🐳 Docker / Neo4j server | ❌ **ABSENT** | by design |
| 🚀 Production / Fractal ACTIVE | ❌ **NOT THIS REPO** | see upstream |

---

## 🧾 Визуальная грамматика статусов

| Метка | Значение |
|---|---|
| ✅ **smoke / tested (lab)** | локальный contract evidence в **этом** repo |
| 🟡 **bounded** | существует, но не authority path |
| 🔬 **research / stub** | изучается; код/док ≠ runtime adoption |
| ⚠️ **limitation** | известная граница |
| ❌ **not authorized / not claimed** | нельзя утверждать как Fractal capability |

```text
📄 file exists
   ≠ 🧪 contract proved
   ≠ 🎛️ feature enabled
   ≠ 🔗 active Fractal path
   ≠ 📡 runtime observed in production
   ≠ 🚀 migration / production authorized
```

> Lab ✅ SMOKE никогда не повышает статус backend до Fractal ✅ ACTIVE.

---

## 🚀 Быстрый старт (без Docker)

```bash
cd Graphiti_fractal_lab
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
pip install -e .
pytest -v
```

Ожидаемый smoke path:

1. создаёт on-disk LadybugDB;
2. пишет/читает несколько nodes + relationships через Cypher;
3. создаёт SQLite table для lab metadata;
4. assert round-trip; stubs объявляют `STUB_NOT_VALIDATED`.

---

## ⚠️ Честные ограничения

- 🧪 это **RESEARCH lab**, не drop-in для `Graphiti_fractal`;
- 🕸️ **нет** Graphiti / Neo4j parity и нет такого claim;
- 🐞 Ladybug здесь — adjacent experiment, не durable Fractal authority;
- 📄 Kùzu / Postgres / DuckDB — stubs only;
- 🔁 migration, dual-write, rollback tooling **не спроектированы**;
- 🤖 LLM / embeddings / OpenAI — out of scope;
- 🐳 Docker / Neo4j server намеренно отсутствуют;
- 🚀 green pytest ≠ production authorization ≠ Fractal migration GO.

---

## 🔗 Upstream relationship

| Repo | Role |
|---|---|
| [`velantrian/Graphiti_fractal`](https://github.com/velantrian/Graphiti_fractal) | ✅ ACTIVE Fractal Memory (Graphiti + Neo4j) |
| [`velantrian/Graphiti_fractal_lab`](https://github.com/velantrian/Graphiti_fractal_lab) | 🔬 RESEARCH sandbox (this repo) |

```text
Upstream Graphiti_fractal + Neo4j  = ACTIVE memory authority (elsewhere)
This lab's LadybugDB instance      = RESEARCH scratch only
Never treat lab graphs as Fractal durable memory
```

---

## 📚 Читать глубже

### 👤 Для человека

➡️ [`SYSTEM_OVERVIEW.md`](SYSTEM_OVERVIEW.md) — backends, proven vs not, authority boundaries.

### 🤖 Для AI / Agents / Auditors

➡️ [`docs/ai/README.md`](docs/ai/README.md) — machine-first reading order и invariants.  
➡️ [`AGENTS.md`](AGENTS.md) — короткий обязательный указатель.

### 📊 Evidence

- [`RESEARCH_STATUS.md`](RESEARCH_STATUS.md)
- [`docs/GRAPH_BACKEND_CAPABILITY_MATRIX.md`](docs/GRAPH_BACKEND_CAPABILITY_MATRIX.md)
- `tests/` + local `pytest`

---

## 🧭 Одна реальность — разные представления

```text
                       🧪 ONE LAB REALITY
                                │
          ┌─────────────────────┼─────────────────────┐
          │                     │                     │
          ▼                     ▼                     ▼
     👤 HUMAN VIEW         🤖 AI VIEW            📚 EVIDENCE
 README + OVERVIEW       docs/ai/README       pytest / status
          │                     │                     │
          └─────────────────────┼─────────────────────┘
                                ▼
                       ⚙️ LIVE LAB CODE
```

**Human docs объясняют. AI docs маршрутизируют. Evidence доказывает. Live code определяет текущую реализацию.**

---

## License

MIT (lab scaffolding). Upstream Fractal остаётся отдельно licensed/owned.
