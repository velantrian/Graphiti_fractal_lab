# P7 Write-Surface Matrix (fixture-scoped)

Classifications from pytest on Graphiti 0.29.3 + FalkorDBLite only.
RESTORED_BYTES ≠ RESTORED_CURRENT_APPLICABILITY.

| id | path | status | classification | invalid_at | expired_at | RESTORED_BYTES |
|---|---|---|---|---|---|---|
| P7-A | Graphiti.add_episode late reference_time=T1 | PASS | PRESERVES_INVALIDATION | PRESERVES_INVALIDATION | PRESERVES_EXPIRED_AT | False |
| P7-B | EntityEdge.save(SNAPSHOT_PRE) | PASS | CLEARS_NEWER_INVALIDATION | CLEARS_NEWER_INVALIDATION | CLEARS_EXPIRED_AT | True |
| P7-C | EntityEdge.save(SNAPSHOT_POST) | PASS | PRESERVES_INVALIDATION | PRESERVES_INVALIDATION | PRESERVES_EXPIRED_AT | False |
| P7-D | add_nodes_and_edges_bulk([SNAPSHOT_PRE]) | PASS | CLEARS_NEWER_INVALIDATION | CLEARS_NEWER_INVALIDATION | CLEARS_EXPIRED_AT | True |
| P7-E | EdgeNamespace(group_driver).entity.save(SNAPSHOT_PRE) | PASS | CLEARS_NEWER_INVALIDATION | CLEARS_NEWER_INVALIDATION | CLEARS_EXPIRED_AT | True |
| P7-F | EdgeNamespace(group_driver).entity.save_bulk([SNAPSHOT_PRE]) | PASS | CLEARS_NEWER_INVALIDATION | CLEARS_NEWER_INVALIDATION | CLEARS_EXPIRED_AT | True |
| P7-G | FalkorDriver.execute_query(get_entity_edge_save_query, edge_data=SNAPSHOT_PRE) | PASS | CLEARS_NEWER_INVALIDATION | CLEARS_NEWER_INVALIDATION | CLEARS_EXPIRED_AT | True |
| P7-H | Graphiti.add_episode_bulk([RawEpisode late T1]) | PASS | PRESERVES_INVALIDATION | PRESERVES_INVALIDATION | PRESERVES_EXPIRED_AT | False |
| P7-I | Graphiti.add_triplet(source, SNAPSHOT_PRE_edge, target) | PASS | PRESERVES_INVALIDATION | PRESERVES_INVALIDATION | PRESERVES_EXPIRED_AT | False |
| P7-N/A | P7-N/A | PASS | NOT_APPLICABLE | None | None | None |

## invalid_at vs expired_at

- Baseline T2 sets BOTH `invalid_at≈T2` and `expired_at≈utc_now()` on OLD
  (from `resolve_edge_contradictions`).
- Low-level SNAPSHOT_PRE writes typically clear BOTH (None in edge_data map).
- High-level add_episode / add_episode_bulk late-T1 expected to PRESERVE invalid_at.
- If classes diverge, overall is PARTIAL.

## Not started

- P8, fixes, Fractal MemoryOps / Crystal / SVL integration, Ladybug, real LLM,
  Graphiti upgrade, merge to main, upstream Graphiti_fractal edits.

```json
[
  {
    "id": "P7-A",
    "path": "Graphiti.add_episode late reference_time=T1",
    "status": "PASS",
    "classification": "PRESERVES_INVALIDATION",
    "invalid_at_class": "PRESERVES_INVALIDATION",
    "expired_at_class": "PRESERVES_EXPIRED_AT",
    "RESTORED_BYTES": false,
    "RESTORED_CURRENT_APPLICABILITY": false
  },
  {
    "id": "P7-B",
    "path": "EntityEdge.save(SNAPSHOT_PRE)",
    "status": "PASS",
    "classification": "CLEARS_NEWER_INVALIDATION",
    "invalid_at_class": "CLEARS_NEWER_INVALIDATION",
    "expired_at_class": "CLEARS_EXPIRED_AT",
    "RESTORED_BYTES": true,
    "RESTORED_CURRENT_APPLICABILITY": true
  },
  {
    "id": "P7-C",
    "path": "EntityEdge.save(SNAPSHOT_POST)",
    "status": "PASS",
    "classification": "PRESERVES_INVALIDATION",
    "invalid_at_class": "PRESERVES_INVALIDATION",
    "expired_at_class": "PRESERVES_EXPIRED_AT",
    "RESTORED_BYTES": false,
    "RESTORED_CURRENT_APPLICABILITY": false
  },
  {
    "id": "P7-D",
    "path": "add_nodes_and_edges_bulk([SNAPSHOT_PRE])",
    "status": "PASS",
    "classification": "CLEARS_NEWER_INVALIDATION",
    "invalid_at_class": "CLEARS_NEWER_INVALIDATION",
    "expired_at_class": "CLEARS_EXPIRED_AT",
    "RESTORED_BYTES": true,
    "RESTORED_CURRENT_APPLICABILITY": true
  },
  {
    "id": "P7-E",
    "path": "EdgeNamespace(group_driver).entity.save(SNAPSHOT_PRE)",
    "status": "PASS",
    "classification": "CLEARS_NEWER_INVALIDATION",
    "invalid_at_class": "CLEARS_NEWER_INVALIDATION",
    "expired_at_class": "CLEARS_EXPIRED_AT",
    "RESTORED_BYTES": true,
    "RESTORED_CURRENT_APPLICABILITY": true
  },
  {
    "id": "P7-F",
    "path": "EdgeNamespace(group_driver).entity.save_bulk([SNAPSHOT_PRE])",
    "status": "PASS",
    "classification": "CLEARS_NEWER_INVALIDATION",
    "invalid_at_class": "CLEARS_NEWER_INVALIDATION",
    "expired_at_class": "CLEARS_EXPIRED_AT",
    "RESTORED_BYTES": true,
    "RESTORED_CURRENT_APPLICABILITY": true
  },
  {
    "id": "P7-G",
    "path": "FalkorDriver.execute_query(get_entity_edge_save_query, edge_data=SNAPSHOT_PRE)",
    "status": "PASS",
    "classification": "CLEARS_NEWER_INVALIDATION",
    "invalid_at_class": "CLEARS_NEWER_INVALIDATION",
    "expired_at_class": "CLEARS_EXPIRED_AT",
    "RESTORED_BYTES": true,
    "RESTORED_CURRENT_APPLICABILITY": true
  },
  {
    "id": "P7-H",
    "path": "Graphiti.add_episode_bulk([RawEpisode late T1])",
    "status": "PASS",
    "classification": "PRESERVES_INVALIDATION",
    "invalid_at_class": "PRESERVES_INVALIDATION",
    "expired_at_class": "PRESERVES_EXPIRED_AT",
    "RESTORED_BYTES": false,
    "RESTORED_CURRENT_APPLICABILITY": false
  },
  {
    "id": "P7-I",
    "path": "Graphiti.add_triplet(source, SNAPSHOT_PRE_edge, target)",
    "status": "PASS",
    "classification": "PRESERVES_INVALIDATION",
    "invalid_at_class": "PRESERVES_INVALIDATION",
    "expired_at_class": "PRESERVES_EXPIRED_AT",
    "RESTORED_BYTES": false,
    "RESTORED_CURRENT_APPLICABILITY": false
  },
  {
    "id": "P7-N/A",
    "path": "P7-N/A",
    "status": "PASS",
    "classification": "NOT_APPLICABLE",
    "invalid_at_class": null,
    "expired_at_class": null,
    "RESTORED_BYTES": null,
    "RESTORED_CURRENT_APPLICABILITY": null
  }
]
```
