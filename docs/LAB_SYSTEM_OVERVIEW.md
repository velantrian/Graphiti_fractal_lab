# 🗺️ Fractal Lab — Human System Overview

> **Назначение:** человеко-ориентированная карта **Graphiti_fractal_lab**.
>
> Этот документ объясняет **зачем существует лаборатория, как устроены adapters,
> что реально smoke-доказано, и чем lab принципиально не является** относительно
> upstream Fractal Memory.
>
> 🤖 AI coding agents и автоматические аудиторы должны начинать не отсюда, а с
> [`docs/ai/README.md`](docs/ai/README.md).

[🏠 README](README.md) · [🤖 Special for AI](docs/ai/README.md) · [📊 Research Status](RESEARCH_STATUS.md) · [🗄️ Backend Matrix](docs/GRAPH_BACKEND_CAPABILITY_MATRIX.md)

---

## 👋 L0 — что такое Fractal Lab за 30 секунд

**Graphiti_fractal_lab** — отдельный RESEARCH sandbox рядом с
[`Graphiti_fractal`](https://github.com/velantrian/Graphiti_fractal).

Он не запускает Graphiti, не поднимает Neo4j и не является memory service.
Он проверяет тонкий слой адаптеров: **LadybugDB** (on-disk graph smoke) +
**SQLite** (lab metadata) + явные **stubs** для других backends.

```text
🧪 researcher / CI
        │
        ▼
  fractal_lab adapters
        │
   ┌────┼────────────┐
   ▼    ▼            ▼
 🐞LB  🗃️SQLite   📄stubs
   │    │            │
   ▼    ▼            ▼
 smoke  meta     NOT VALIDATED
```

Главная идея:

> **Лёгкий backend можно изучать честно — только если не путать smoke с parity
> и lab scratch с durable Fractal authority.**

---

## 🧠 Mindmap — какие задачи решает lab

```text
                         🧪 FRACTAL LAB
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
   🐞 Embedded graph      🗃️ Ops metadata      🔬 Candidate stubs
   Ladybug smoke           SQLite runs          Kùzu / PG / DuckDB
        │                      │                      │
        ▼                      ▼                      ▼
   Cypher round-trip      record_run ledger     status declarations
        │                      │                      │
        └──────────┬───────────┴──────────┬───────────┘
                   ▼                      ▼
            🛡️ Authority fence      📊 Honest matrix
         lab ≠ Fractal memory    NOT VALIDATED rows stay red
```

---

## 🏗️ Архитектура одним взглядом

```text
┌──────────────────── 🌍 HUMAN / AGENT / CI ────────────────────────┐
│  ⌨️ pytest · 📄 docs · no HTTP product surface                    │
└───────────────────────────────┬────────────────────────────────────┘
                                ▼
                      📦 fractal_lab package
                                │
              ┌─────────────────┼──────────────────┐
              ▼                 ▼                  ▼
      🐞 LadybugAdapter   🗃️ SqliteLabMeta   📄 Graph stubs
      connect/smoke_*     ensure_schema      info() → STUB
              │                 │                  │
              ▼                 ▼                  ▼
         💾 .lbdb            💾 .sqlite         (no claim)
```

### Ключевая граница

```text
🧪 lab smoke proposes evidence about thin adapters
🕸️ upstream Fractal keeps Graphiti + Neo4j authority
📄 stubs declare absence of validation

smoke ≠ Graphiti parity
ladybug lab ≠ durable Fractal memory
sqlite meta ≠ graph authority
research ≠ runtime
green pytest ≠ migration GO
```

---

## 🌳 Дерево системы

```text
🧪 Graphiti_fractal_lab
│
├── 🔌 Backend Protocol
│   ├── ValidationStatus (smoke_tested | stub_not_validated | not_claimed)
│   └── GraphBackend (info / connect / close / execute)
│
├── ✅ Runnable smoke
│   ├── LadybugAdapter — on-disk create + Cypher NODE/REL round-trip
│   └── SqliteLabMeta — lab_runs table
│
├── 🔬 Stubs only
│   ├── KuzuStub
│   ├── PostgresStub
│   └── DuckDBStub
│
├── 🧪 Tests
│   ├── test_ladybug_smoke.py (info, write/read, stub statuses)
│   └── test_sqlite_meta.py (schema + round-trip)
│
└── 📚 Docs
    ├── README / SYSTEM_OVERVIEW (human)
    ├── docs/ai/README + AGENTS (AI)
    └── RESEARCH_STATUS + capability matrix (evidence grammar)
```

---

## 🐞 Backends — proven vs not

| Backend | Role in lab | Evidence | Fractal role |
|---|---|---|---|
| 🐞 LadybugDB `0.20.3` | primary on-disk graph smoke | ✅ pytest smoke | 🔬 upstream: ADJACENT / evaluate only |
| 🗃️ SQLite | ops / lab metadata | ✅ pytest smoke | n/a (not a graph authority) |
| 🗄️ Neo4j | **not used here** | — | ✅ ACTIVE in upstream Fractal |
| 🕸️ Graphiti / `graphiti_core` | **not used here** | ❌ NOT VALIDATED | ✅ ACTIVE upstream |
| 📄 Kùzu | stub | 🔬 NOT VALIDATED | historical / adjacent upstream |
| 📄 PostgreSQL | stub | 🔬 NOT VALIDATED | adjacent research |
| 📄 DuckDB | stub | 🔬 NOT VALIDATED | analytical optional |

Подробная таблица REQUIRED parity gates →
[`docs/GRAPH_BACKEND_CAPABILITY_MATRIX.md`](docs/GRAPH_BACKEND_CAPABILITY_MATRIX.md).

---

## ✅ Что доказано в lab (перепроверяйте pytest)

На момент локальной проверки в этой среде:

- **4 passed** (`pytest -v`);
- Python **3.13.5**;
- `ladybug==0.20.3`;
- Ladybug: create DB, CREATE NODE/REL TABLE, MATCH round-trip (`Ada`→`Bob`);
- SQLite: schema + `record_run` / `list_runs`;
- stubs: `info().status == STUB_NOT_VALIDATED`.

Это **lab smoke evidence**, не Fractal acceptance suite.

---

## ❌ Что явно не доказано и не заявлено

- Graphiti driver compatibility на Ladybug;
- temporal episodes, `group_id`, UUID constraints, FTS, vectors, communities;
- backup/restore, concurrency, crash durability benches;
- migration tooling / dual-write / rollback to Neo4j;
- OpenAI / embeddings / Docker Neo4j;
- production authorization.

---

## 🛡️ Authority fence

```text
one active durable graph authority at a time   ← upstream Fractal rule

Upstream Graphiti_fractal + Neo4j  = ACTIVE memory authority (elsewhere)
This lab's LadybugDB instance      = RESEARCH scratch only
```

Forbidden without a separate owner migration decision (same spirit as upstream):

- dual-write Neo4j + Ladybug as memory authorities;
- silent fallback between backends;
- deleting Neo4j source before rollback evidence;
- documenting lab smoke as Fractal ACTIVE.

---

## 🔁 Опциональные следующие research steps

1. Probe whether any Graphiti driver surface can target Ladybug (**separate evidence**).
2. Map REQUIRED matrix rows to concrete Ladybug features with tests.
3. Keep Kùzu/Postgres/DuckDB stubs until an owner schedules validation.
4. Never auto-promote RESEARCH → Fractal runtime via docs-only change.

---

## 🧭 Связь с Velantrim siblings

| Sibling | Relationship |
|---|---|
| 🧠 Graphiti_fractal | upstream concepts; ACTIVE Graphiti+Neo4j path |
| 🧪 Graphiti_fractal_lab | this RESEARCH sandbox |
| 🔱 Titan / 💠 Soul / Crystal | documentation grammar inspiration (AI entry, status honesty) |

Lab заимствует **стиль документации**, не runtime architecture этих систем.

---

## ⚠️ Честные ограничения

См. также README. Кратко: нет parity, нет migration GO, нет product HTTP surface,
нет Docker Neo4j, stubs не валидированы, lab graph не является Fractal memory.
