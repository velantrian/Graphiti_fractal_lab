# RESEARCH_STATUS

**Repo:** Graphiti_fractal_lab  
**Date:** 2026-09-09  
**Role:** RESEARCH sandbox — not production Fractal Memory

## Validated in this lab

| Item | Evidence | Notes |
|---|---|---|
| LadybugDB on-disk create | `tests/test_ladybug_smoke.py` | `ladybug==0.20.3`, Python 3.13 |
| Ladybug node/rel Cypher write+read | same | CREATE NODE/REL TABLE + MATCH |
| SQLite lab metadata table | `tests/test_sqlite_meta.py` | stdlib `sqlite3` |
| Thin adapter interfaces | `src/fractal_lab/backends/` | Protocol + stubs |

## Explicitly NOT validated

| Item | Status |
|---|---|
| Graphiti / `graphiti_core` on Ladybug | **NOT VALIDATED** |
| Neo4j parity (temporal episodes, group_id, UUID, vectors, FTS, …) | **NOT CLAIMED** |
| Kùzu adapter | stub only — **NOT VALIDATED** (historical) |
| PostgreSQL adapter | stub only — **NOT VALIDATED** |
| DuckDB adapter | stub only — **NOT VALIDATED** |
| Migration / dual-write / rollback tooling | **NOT DESIGNED** |
| OpenAI / LLM / embeddings path | **out of scope** |
| Docker / Neo4j server | **intentionally absent** |

## Authority rule

```text
Upstream Graphiti_fractal + Neo4j = ACTIVE memory authority (elsewhere)
This lab's LadybugDB instance     = RESEARCH scratch only
Never treat lab graphs as Fractal durable memory
```

## Next research steps (optional)

1. Probe whether any Graphiti driver surface can target Ladybug
2. Map REQUIRED matrix rows to concrete Ladybug features
3. Keep stubs for Kùzu/Postgres/DuckDB until an owner explicitly schedules validation
