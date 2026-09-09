# 📊 RESEARCH_STATUS

> **Repo:** `velantrian/Graphiti_fractal_lab`  
> **Role:** 🔬 RESEARCH sandbox — not production Fractal Memory  
> **Date:** 2026-09-09  
> **Last local verify:** `pytest -v` → **4 passed** · Python 3.13.5 · `ladybug==0.20.3`

🤖 For machine routing see [`docs/ai/README.md`](docs/ai/README.md).  
Re-run pytest on the exact head before citing pass counts elsewhere.

---

## 🧾 Status grammar

| Метка | Значение |
|---|---|
| ✅ **SMOKE / TESTED (lab)** | executable evidence in this repo |
| 🔬 **RESEARCH / STUB** | present as code or idea; not validated |
| ⚠️ **LIMITATION** | known bound |
| ❌ **NOT VALIDATED / NOT CLAIMED / NOT AUTHORIZED** | do not assert as capability |

```text
📄 file exists ≠ 🧪 tested ≠ 🔗 Fractal active ≠ 🚀 production/migration authorized
```

---

## ✅ Validated in this lab

| Item | Evidence | Notes |
|---|---|---|
| ✅ LadybugDB on-disk create | `tests/test_ladybug_smoke.py` | `ladybug==0.20.3`, Python 3.13 |
| ✅ Ladybug node/rel Cypher write+read | same | CREATE NODE/REL TABLE + MATCH |
| ✅ SQLite lab metadata table | `tests/test_sqlite_meta.py` | stdlib `sqlite3` |
| ✅ Thin adapter interfaces | `src/fractal_lab/backends/` | Protocol + `ValidationStatus` |
| ✅ Stubs declare NOT VALIDATED | `test_stubs_declare_not_validated` | Kùzu / Postgres / DuckDB |

**Pytest count (local verify):** 4 passed.

---

## ❌ Explicitly NOT validated

| Item | Status |
|---|---|
| Graphiti / `graphiti_core` on Ladybug | ❌ **NOT VALIDATED** |
| Neo4j parity (temporal episodes, group_id, UUID, vectors, FTS, …) | ❌ **NOT CLAIMED** |
| Kùzu adapter | 🔬 stub only — ❌ **NOT VALIDATED** |
| PostgreSQL adapter | 🔬 stub only — ❌ **NOT VALIDATED** |
| DuckDB adapter | 🔬 stub only — ❌ **NOT VALIDATED** |
| Migration / dual-write / rollback tooling | ❌ **NOT DESIGNED** |
| OpenAI / LLM / embeddings path | ❌ **OUT OF SCOPE** |
| Docker / Neo4j server | ❌ **INTENTIONALLY ABSENT** |
| Production / Fractal ACTIVE authority | ❌ **NOT THIS REPO** |

---

## 🛡️ Authority rule

```text
Upstream Graphiti_fractal + Neo4j = ✅ ACTIVE memory authority (elsewhere)
This lab's LadybugDB instance     = 🔬 RESEARCH scratch only
Never treat lab graphs as Fractal durable memory
```

---

## 🔬 Next research steps (optional)

1. Probe whether any Graphiti driver surface can target Ladybug.
2. Map REQUIRED matrix rows to concrete Ladybug features with evidence.
3. Keep stubs for Kùzu/Postgres/DuckDB until an owner explicitly schedules validation.
4. Do not convert this ledger into a migration authorization.
