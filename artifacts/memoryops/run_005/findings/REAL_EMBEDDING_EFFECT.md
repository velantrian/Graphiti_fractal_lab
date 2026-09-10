# REAL_EMBEDDING_EFFECT

- embedder: `BAAI/bge-small-en-v1.5` via `fastembed+onnxruntime`
- dim: 384
- COSINE_CHANNEL_EFFECT: **COSINE_CHANNEL_EFFECT**
- FINAL_HYBRID: **FINAL_HYBRID_EFFECT**
- pipeline_note: EMBEDDING_IMPROVEMENT_CONFIRMED BUT SEARCH_PIPELINE_FILTERING_STILL_INSUFFICIENT

Real pretrained semantic vectors replace hash embeddings. Query×fact cosine geometry is meaningful (see similarity_matrix.json). Default search path still fuses BM25+cosine via RRF; CrossEncoder still N/A.

```json
{
  "label": "COSINE_CHANNEL_EFFECT",
  "Q1_cosine_count": 4,
  "Q4_cosine_count": 4,
  "Q4_run004_cosine_was": 0,
  "Q4_cosine_now_nonempty": true,
  "matrix_Q1_vs_N1": 0.8512866051764023,
  "matrix_Q4_vs_N1": 0.637605444232953,
  "above_sim_min_for_Q4_any_fact": true,
  "verdict": "COSINE_CHANNEL_EFFECT"
}
```
