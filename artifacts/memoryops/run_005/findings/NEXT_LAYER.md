# NEXT_LAYER

STOP after FM-14. No FM-15 / reranker / BM25 fix in this commit.

```json
{
  "do_not_do_in_FM14": [
    "reranker enable",
    "BM25 fix",
    "FM-15"
  ],
  "observed_bottleneck": "BM25_CANDIDATE_GENERATION + RRF fusion without existence gate",
  "suggested_next_layers_NOT_IMPLEMENTED": [
    "existence/entity gate for absent query entities",
    "BM25 field/analyzer tuning or query rewriting",
    "cross-encoder on EDGE_HYBRID_SEARCH_CROSS_ENCODER (FM-15?)",
    "sim_min_score / channel weight experiments"
  ],
  "NEO4J_CAUSAL_EVIDENCE": "NO"
}
```
