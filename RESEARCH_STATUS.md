# 📊 RESEARCH_STATUS

> **Repo:** `velantrian/Graphiti_fractal_lab`  
> **Role:** 🔬 RESEARCH sandbox — full Fractal tree mirrored for experimentation; not production Fractal Memory  
> **Date:** 2026-11-05  
> **Mirror:** Entire tracked tree from `velantrian/Graphiti_fractal` copied into this lab so experiments can edit freely. Upstream must **never** be modified from lab tasks.  
> **Last local verify (lab smoke only):** `make PYTHON=python test-lab` / `pytest tests/test_ladybug_smoke.py tests/test_sqlite_meta.py -v` → **8 passed** · Python 3.12.3 · `ladybug==0.20.3`  
> **CI wire:** always-on `make test-lab` in `.github/workflows/ci.yml` after `test-contracts` (does **not** authorize Fractal migration).

🤖 For machine routing see [`docs/ai/README.md`](docs/ai/README.md).  
Re-run pytest on the exact head before citing pass counts elsewhere.

## 2026-10-29 — Draft lab parameter-binding experiment

The proposed branch delegates value parameters to Ladybug 0.20.3 rather than
interpolating text or rejecting parameterized queries. Local lab subset:
**9 passed** (four existing smoke tests and five parameter/reopen controls),
Python 3.12.14. See [scope and reproduction](docs/LAB_PARAMETER_BINDING.md).
This is no Graphiti/Neo4j parity, migration or production claim. The historical
four-test checkpoint below remains preserved; resolve the Draft PR for proposal state.

## 🔬 Issue-linked research

- For issue #3, see the [Engram post-ranking qualification source audit](docs/ENGRAM_POST_RANK_QUALIFICATION.md). It records a future bounded-evaluation candidate only; protocol readiness does not authorize an ablation or other experiment.

## 🪞 Mirror honesty

| Path | Meaning |
|---|---|
| `core/`, `api/`, `docker-compose.yml`, Fractal `tests/`, … | Mirrored for experimentation — **Neo4j/Docker/secrets still required** to run full stack; **not claimed runnable here without them** |
| `src/fractal_lab/`, `tests/test_ladybug_smoke.py`, `tests/test_sqlite_meta.py` | Lab-only Ladybug/SQLite smoke path (no Docker) |
| `docs/LAB_LANDING.md` | Previous lab-only README landing (pre-mirror) |
| `docs/ai/UPSTREAM_FRACTAL_README.md` | Upstream Fractal machine router (preserved beside lab router) |
| `requirements.txt` | Fractal stack deps (Graphiti/Neo4j/…); need Docker/secrets for real use |
| `requirements-lab.txt` + `pyproject.toml` | Lab Ladybug smoke deps |
| `constraints-ci.txt` | Reviewed pins including `ladybug==0.20.3` for lab smoke |

```text
Mirrored Fractal files ≠ Docker available ≠ Neo4j running ≠ Fractal ACTIVE in this environment
```

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

`ValidationStatus.SMOKE_TESTED` on an adapter is a **path-level** ledger claim (backed by lab tests), not proof that a cold `info()` call exercised storage.

---

## ✅ Validated in this lab

| Item | Evidence | Notes |
|---|---|---|
| ✅ LadybugDB on-disk create | `tests/test_ladybug_smoke.py` | `ladybug==0.20.3` |
| ✅ Ladybug node/rel Cypher write+read | same | CREATE NODE/REL TABLE + MATCH |
| ✅ Ladybug reopen in-process read | `test_ladybug_reopen_reads_prior_smoke_rows` | not crash/restart durability |
| ✅ SQLite lab metadata table | `tests/test_sqlite_meta.py` | stdlib `sqlite3` + reopen |
| ✅ Thin adapter interfaces | `src/fractal_lab/backends/` | Protocol + `ValidationStatus` |
| ✅ Stubs declare NOT VALIDATED and refuse connect/execute | `test_stubs_declare_not_validated_and_refuse_connect` | Kùzu / Postgres / DuckDB |
| ✅ Lab smoke wired into always-on CI | `.github/workflows/ci.yml` → `make test-lab` | still lab-only |

**Pytest count (local verify):** 8 passed (`test-lab`).

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
| OpenAI / LLM / embeddings path | ❌ **OUT OF SCOPE for lab smoke** (mirrored modules may exist) |
| Docker / Neo4j server in this lab box | ❌ **NOT CLAIMED runnable without Docker+secrets** |
| Production / Fractal ACTIVE authority | ❌ **NOT THIS REPO** |
| Crash/restart durability / parameterized Cypher | ❌ **NOT VALIDATED** |

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

