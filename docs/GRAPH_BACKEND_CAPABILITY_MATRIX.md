# Graph backend capability matrix (lab adaptation)

**Status:** RESEARCH / NO MIGRATION AUTHORIZED  
**Lab primary smoke path:** LadybugDB + SQLite  
**Upstream Fractal active backend:** Neo4j 5.26 LTS (in Graphiti_fractal — untouched)

Adapted in spirit from
`velantrian/Graphiti_fractal` → `docs/GRAPH_BACKEND_CAPABILITY_MATRIX.md`.
This lab copy exists so lightweight experiments cannot be mistaken for a storage
migration of Fractal Memory.

## Candidates (lab view)

| Backend | Role in this lab | Status |
|---|---|---|
| LadybugDB (`ladybug` pip) | primary on-disk graph smoke | **SMOKE-TESTED (lab only)** |
| SQLite | ops / lab metadata (not a graph authority) | **SMOKE-TESTED** |
| Neo4j | upstream Fractal durable graph | **ACTIVE upstream — not used here** |
| KùzuDB | historical embedded predecessor | **STUB / NOT VALIDATED** |
| PostgreSQL | relational metadata / optional | **STUB / NOT VALIDATED** |
| DuckDB | analytical / optional | **STUB / NOT VALIDATED** |

## Mandatory parity gate (unchanged intent)

A candidate must not replace Neo4j in Fractal until every REQUIRED capability has
evidence. **This lab does not satisfy that gate.**

| Capability | Requirement | Neo4j (upstream) | Ladybug lab |
|---|---|---|---|
| Graphiti driver compatibility | REQUIRED | current path | **NOT VALIDATED** |
| temporal episode semantics | REQUIRED | current path | **NOT VALIDATED** |
| `group_id` namespace isolation | REQUIRED | current path | **NOT VALIDATED** |
| exact UUID lookup/update | REQUIRED | current path | **NOT VALIDATED** |
| constraints / uniqueness | REQUIRED | current path | **NOT VALIDATED** |
| transactions / failure semantics | REQUIRED | current path | **NOT VALIDATED** |
| full-text/search primitives | REQUIRED | current path | **NOT VALIDATED** |
| vector/index primitives | REQUIRED | current path | **NOT VALIDATED** |
| community/query compatibility | REQUIRED | current path | **NOT VALIDATED** |
| backup/export | REQUIRED | supported | **NOT VALIDATED** |
| restore/import | REQUIRED | supported | **NOT VALIDATED** |
| migration tooling | REQUIRED | n/a current | **NOT DESIGNED** |
| rollback to Neo4j | REQUIRED | n/a current | **NOT DESIGNED** |
| ingest / retrieval / concurrency / durability benches | REQUIRED | baseline needed | **NOT RUN** |
| on-disk create + Cypher node/rel round-trip | lab smoke | n/a | **PASS (lab)** |
| SQLite metadata table | lab smoke | n/a | **PASS (lab)** |

## Migration invariant

```text
one active durable graph authority at a time
```

Forbidden without a separate owner migration decision (same as upstream):

- dual-write Neo4j + LadybugDB as memory authorities
- silent fallback between backends
- migration without counts + retrieval-equivalence evidence
- deleting Neo4j source before rollback evidence exists

## Lab evaluation sequence

1. ✅ Thin Ladybug + SQLite smoke outside Fractal runtime
2. Adapter stubs for optional backends (documented NOT VALIDATED)
3. ☐ Synthetic Graphiti compatibility probes (future)
4. ☐ Fixture export/import vs Neo4j (future, in/near upstream)
5. ☐ Explicit owner migration decision — **not this repo's job**

> Lightweight deployment is a benefit only if semantic compatibility and recovery remain intact.
