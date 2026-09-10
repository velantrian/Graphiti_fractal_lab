# H-CONFIG / SEARCH_CONFIG_HYPOTHESIS

Material retrieval behavior is explained by SearchConfig recipe EDGE_HYBRID_SEARCH_RRF: hybrid BM25+cosine, RRF fusion, sim_min_score=0.6, limit=num_results (10), no cross-encoder, no node/community scope, no Zephyr entity gate. MemoryOps passes group_ids and num_results through unchanged.

```json
{
  "label": "H-CONFIG",
  "finding": "Material retrieval behavior is explained by SearchConfig recipe EDGE_HYBRID_SEARCH_RRF: hybrid BM25+cosine, RRF fusion, sim_min_score=0.6, limit=num_results (10), no cross-encoder, no node/community scope, no Zephyr entity gate. MemoryOps passes group_ids and num_results through unchanged.",
  "search_config_ref": "artifacts/memoryops/run_004/search_config.json"
}
```
