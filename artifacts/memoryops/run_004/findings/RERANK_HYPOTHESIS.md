# H-RERANK / RERANK_HYPOTHESIS

- cross_encoder_verdict: **N/A**

DeterministicCrossEncoder is constructed on LabGraphitiStack but Graphiti.search selects EDGE_HYBRID_SEARCH_RRF whose edge reranker is reciprocal_rank_fusion — cross_encoder.rank is NOT invoked. RERANK_IMPROVES/NEUTRAL/DEGRADES for cross-encoder = N/A (NOT_OBSERVED). The effective ranker is RRF fusion over BM25+cosine lists.

```json
{
  "label": "H-RERANK",
  "cross_encoder_verdict": "N/A",
  "cross_encoder_calls_total": 0,
  "finding": "DeterministicCrossEncoder is constructed on LabGraphitiStack but Graphiti.search selects EDGE_HYBRID_SEARCH_RRF whose edge reranker is reciprocal_rank_fusion \u2014 cross_encoder.rank is NOT invoked. RERANK_IMPROVES/NEUTRAL/DEGRADES for cross-encoder = N/A (NOT_OBSERVED). The effective ranker is RRF fusion over BM25+cosine lists."
}
```
