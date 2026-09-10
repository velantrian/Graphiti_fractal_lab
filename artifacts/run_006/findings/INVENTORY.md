# P7 Write-Surface Inventory (graphiti-core==0.29.3 + FalkorDBLite)

Evidence-backed from installed package under `.venv/.../graphiti_core/`.
Fixture-scoped experimental classifications live in MATRIX.md / result.json.

| id | symbol | accepts invalid_at/expired_at | hypothesized risk | matrix |
|---|---|---|---|---|
| EntityEdge.save | `graphiti_core.edges.EntityEdge.save` | True | HIGH — SET e=$edge_data can overwrite newer invalid_at with None | P7-B, P7-C |
| FalkorEntityEdgeOperations.save | `graphiti_core.driver.falkordb.operations.entity_edge_ops.FalkorEntityEdgeOperations.save` | True | HIGH — same SET e=$edge_data | P7-E |
| FalkorEntityEdgeOperations.save_bulk | `graphiti_core.driver.falkordb.operations.entity_edge_ops.FalkorEntityEdgeOperations.save_bulk` | True | HIGH — bulk SET replaces relationship map | P7-F |
| EntityEdgeNamespace.save | `graphiti_core.namespaces.edges.EntityEdgeNamespace.save` | True | HIGH (delegates to ops); Falkor routing requires group-cloned driver | P7-E |
| EntityEdgeNamespace.save_bulk | `graphiti_core.namespaces.edges.EntityEdgeNamespace.save_bulk` | True | HIGH | P7-F |
| add_nodes_and_edges_bulk | `graphiti_core.utils.bulk_utils.add_nodes_and_edges_bulk` | True | HIGH when called with pre-built SNAPSHOT_PRE EntityEdge list | P7-D |
| Graphiti.add_episode | `graphiti_core.graphiti.Graphiti.add_episode` | indirect — LLM extract + resolve_extracted_edges then bulk persist | LOW for late-T1 stale narrative (P6-A SAFE_HIGH_LEVEL); does not accept raw SNAPSHOT_PRE bytes | P7-A |
| Graphiti.add_episode_bulk | `graphiti_core.graphiti.Graphiti.add_episode_bulk` | indirect — same resolve then bulk | LOW for late-T1 (expect preserve like add_episode) | P7-H |
| Graphiti.add_triplet | `graphiti_core.graphiti.Graphiti.add_triplet` | edge object accepted then resolve_extracted_edge before bulk write | MEDIUM — may rewrite same UUID after resolve; not a raw snapshot restore | P7-I |
| driver.execute_query + get_entity_edge_save_query | `FalkorDriver.execute_query + get_entity_edge_save_query(FALKORDB)` | True | HIGH — raw Cypher surface | P7-G |
| EpisodicEdge.save / CommunityEdge.save / HasEpisodeEdge / NextEpisodeEdge | `graphiti_core.edges.(EpisodicEdge|CommunityEdge|HasEpisodeEdge|NextEpisodeEdge).save` | False | N/A for EntityEdge temporal resurrection | P7-N/A |
| RelatesToNode_ (Kuzu) | `Kuzu RelatesToNode_ intermediate` | Kuzu-only modeling | NOT_RUN_ON_FALKOR | P7-N/A |
| remove_episode | `graphiti_core.graphiti.Graphiti.remove_episode` | False | N/A | P7-N/A |
| restore/import helpers | `(none found in graphiti_core 0.29.3)` | False | N/A — not present | P7-N/A |

## Source checks
```json
{
  "edges.EntityEdge.save": true,
  "edge_db_queries": true,
  "bulk_utils": true,
  "falkor_entity_edge_ops": true,
  "namespaces_edges": true,
  "graphiti.add_episode": true
}
```

## Falkor single-edge save Cypher (excerpt)
```cypher
MATCH (source:Entity {uuid: $edge_data.source_uuid})
                MATCH (target:Entity {uuid: $edge_data.target_uuid})
                MERGE (source)-[e:RELATES_TO {uuid: $edge_data.uuid}]->(target)
                SET e = $edge_data
                SET e.fact_embedding = vecf32($edge_data.fact_embedding)
                RETURN e.uuid AS uuid
```

## Falkor bulk-edge save Cypher (excerpt)
```cypher
UNWIND $entity_edges AS edge
                MATCH (source:Entity {uuid: edge.source_node_uuid})
                MATCH (target:Entity {uuid: edge.target_node_uuid})
                MERGE (source)-[r:RELATES_TO {uuid: edge.uuid}]->(target)
                SET r = edge
                SET r.fact_embedding = vecf32(edge.fact_embedding)
                WITH r, edge
                RETURN edge.uuid AS uuid
```

## Full inventory records
```json
[
  {
    "id": "EntityEdge.save",
    "symbol": "graphiti_core.edges.EntityEdge.save",
    "path": "edges.py:335",
    "signature": "async def save(self, driver: GraphDriver)",
    "accepts_temporal_fields": true,
    "fields": [
      "invalid_at",
      "expired_at",
      "valid_at",
      "reference_time"
    ],
    "persist_mechanism": "get_entity_edge_save_query(FALKORDB): MERGE ... SET e = $edge_data",
    "hypothesized_risk": "HIGH \u2014 SET e=$edge_data can overwrite newer invalid_at with None",
    "matrix_rows": [
      "P7-B",
      "P7-C"
    ]
  },
  {
    "id": "FalkorEntityEdgeOperations.save",
    "symbol": "graphiti_core.driver.falkordb.operations.entity_edge_ops.FalkorEntityEdgeOperations.save",
    "path": "driver/falkordb/operations/entity_edge_ops.py:36",
    "signature": "async def save(self, executor, edge, tx=None)",
    "accepts_temporal_fields": true,
    "fields": [
      "invalid_at",
      "expired_at",
      "valid_at"
    ],
    "note": "Omits reference_time from edge_data (unlike EntityEdge.save)",
    "persist_mechanism": "Same get_entity_edge_save_query(FALKORDB)",
    "hypothesized_risk": "HIGH \u2014 same SET e=$edge_data",
    "matrix_rows": [
      "P7-E"
    ]
  },
  {
    "id": "FalkorEntityEdgeOperations.save_bulk",
    "symbol": "graphiti_core.driver.falkordb.operations.entity_edge_ops.FalkorEntityEdgeOperations.save_bulk",
    "path": "driver/falkordb/operations/entity_edge_ops.py:66",
    "signature": "async def save_bulk(self, executor, edges, tx=None, batch_size=100)",
    "accepts_temporal_fields": true,
    "fields": [
      "invalid_at",
      "expired_at",
      "valid_at"
    ],
    "persist_mechanism": "get_entity_edge_save_bulk_query(FALKORDB): UNWIND ... SET r = edge",
    "hypothesized_risk": "HIGH \u2014 bulk SET replaces relationship map",
    "matrix_rows": [
      "P7-F"
    ]
  },
  {
    "id": "EntityEdgeNamespace.save",
    "symbol": "graphiti_core.namespaces.edges.EntityEdgeNamespace.save",
    "path": "namespaces/edges.py:47",
    "signature": "async def save(self, edge: EntityEdge, tx=None) -> EntityEdge",
    "accepts_temporal_fields": true,
    "persist_mechanism": "generate_embedding + FalkorEntityEdgeOperations.save",
    "hypothesized_risk": "HIGH (delegates to ops); Falkor routing requires group-cloned driver",
    "matrix_rows": [
      "P7-E"
    ]
  },
  {
    "id": "EntityEdgeNamespace.save_bulk",
    "symbol": "graphiti_core.namespaces.edges.EntityEdgeNamespace.save_bulk",
    "path": "namespaces/edges.py:56",
    "signature": "async def save_bulk(self, edges, tx=None, batch_size=100)",
    "accepts_temporal_fields": true,
    "persist_mechanism": "FalkorEntityEdgeOperations.save_bulk",
    "hypothesized_risk": "HIGH",
    "matrix_rows": [
      "P7-F"
    ]
  },
  {
    "id": "add_nodes_and_edges_bulk",
    "symbol": "graphiti_core.utils.bulk_utils.add_nodes_and_edges_bulk",
    "path": "utils/bulk_utils.py:128",
    "signature": "async def add_nodes_and_edges_bulk(driver, episodic_nodes, episodic_edges, entity_nodes, entity_edges, embedder)",
    "accepts_temporal_fields": true,
    "fields": [
      "invalid_at",
      "expired_at",
      "valid_at",
      "reference_time"
    ],
    "persist_mechanism": "get_entity_edge_save_bulk_query \u2192 SET r = edge",
    "hypothesized_risk": "HIGH when called with pre-built SNAPSHOT_PRE EntityEdge list",
    "matrix_rows": [
      "P7-D"
    ]
  },
  {
    "id": "Graphiti.add_episode",
    "symbol": "graphiti_core.graphiti.Graphiti.add_episode",
    "path": "graphiti.py:980",
    "signature": "async def add_episode(... reference_time, group_id, ...)",
    "accepts_temporal_fields": "indirect \u2014 LLM extract + resolve_extracted_edges then bulk persist",
    "persist_mechanism": "_process_episode_data \u2192 add_nodes_and_edges_bulk(resolved+invalidated)",
    "hypothesized_risk": "LOW for late-T1 stale narrative (P6-A SAFE_HIGH_LEVEL); does not accept raw SNAPSHOT_PRE bytes",
    "matrix_rows": [
      "P7-A"
    ]
  },
  {
    "id": "Graphiti.add_episode_bulk",
    "symbol": "graphiti_core.graphiti.Graphiti.add_episode_bulk",
    "path": "graphiti.py:1230",
    "signature": "async def add_episode_bulk(bulk_episodes: list[RawEpisode], group_id=...)",
    "accepts_temporal_fields": "indirect \u2014 same resolve then bulk",
    "persist_mechanism": "add_nodes_and_edges_bulk(resolved+invalidated)",
    "hypothesized_risk": "LOW for late-T1 (expect preserve like add_episode)",
    "matrix_rows": [
      "P7-H"
    ]
  },
  {
    "id": "Graphiti.add_triplet",
    "symbol": "graphiti_core.graphiti.Graphiti.add_triplet",
    "path": "graphiti.py:1645",
    "signature": "async def add_triplet(source_node, edge: EntityEdge, target_node)",
    "accepts_temporal_fields": "edge object accepted then resolve_extracted_edge before bulk write",
    "persist_mechanism": "resolve_extracted_edge \u2192 add_nodes_and_edges_bulk",
    "hypothesized_risk": "MEDIUM \u2014 may rewrite same UUID after resolve; not a raw snapshot restore",
    "matrix_rows": [
      "P7-I"
    ]
  },
  {
    "id": "driver.execute_query + get_entity_edge_save_query",
    "symbol": "FalkorDriver.execute_query + get_entity_edge_save_query(FALKORDB)",
    "path": "driver/falkordb_driver.py:238 + models/edges/edge_db_queries.py:63",
    "signature": "async def execute_query(cypher_query_, **kwargs)",
    "accepts_temporal_fields": true,
    "persist_mechanism": "MERGE RELATES_TO SET e=$edge_data (same Cypher as EntityEdge.save)",
    "hypothesized_risk": "HIGH \u2014 raw Cypher surface",
    "matrix_rows": [
      "P7-G"
    ]
  },
  {
    "id": "EpisodicEdge.save / CommunityEdge.save / HasEpisodeEdge / NextEpisodeEdge",
    "symbol": "graphiti_core.edges.(EpisodicEdge|CommunityEdge|HasEpisodeEdge|NextEpisodeEdge).save",
    "path": "edges.py (non-EntityEdge)",
    "accepts_temporal_fields": false,
    "persist_mechanism": "MENTIONS / HAS_MEMBER / HAS_EPISODE / NEXT_EPISODE \u2014 no invalid_at/expired_at",
    "hypothesized_risk": "N/A for EntityEdge temporal resurrection",
    "matrix_rows": [
      "P7-N/A"
    ]
  },
  {
    "id": "RelatesToNode_ (Kuzu)",
    "symbol": "Kuzu RelatesToNode_ intermediate",
    "path": "models/edges/edge_db_queries.py KUZU branch; driver/kuzu/*",
    "accepts_temporal_fields": "Kuzu-only modeling",
    "persist_mechanism": "Not used on FalkorDBLite (direct RELATES_TO relationship)",
    "hypothesized_risk": "NOT_RUN_ON_FALKOR",
    "matrix_rows": [
      "P7-N/A"
    ]
  },
  {
    "id": "remove_episode",
    "symbol": "graphiti_core.graphiti.Graphiti.remove_episode",
    "path": "graphiti.py:1765",
    "accepts_temporal_fields": false,
    "persist_mechanism": "DELETE edges/nodes created by episode \u2014 no snapshot restore",
    "hypothesized_risk": "N/A",
    "matrix_rows": [
      "P7-N/A"
    ]
  },
  {
    "id": "restore/import helpers",
    "symbol": "(none found in graphiti_core 0.29.3)",
    "path": "migrations/ empty; no restore/import EntityEdge APIs located",
    "accepts_temporal_fields": false,
    "hypothesized_risk": "N/A \u2014 not present",
    "matrix_rows": [
      "P7-N/A"
    ]
  }
]
```
