# BM25_PERSISTENCE

- verdict: **BM25_NOISE_PERSISTS**
- Q4 BM25 count: 4

Q4 Zephyr absent: BM25 still returns corpus edges via lexical overlap on works/Project tokens — unchanged by real embeddings.

Changing only the embedder cannot remove BM25 candidate generation. FM-14 intentionally does not alter BM25 / RRF / limits.

```json
{
  "label": "BM25_NOISE_PERSISTS",
  "Q4_bm25_count": 4,
  "Q4_bm25_facts": [
    "Alice works on Project Orion.",
    "Bob works on Project Nova.",
    "Project Orion uses Python.",
    "Project Nova uses Rust."
  ],
  "verdict": "BM25_NOISE_PERSISTS",
  "detail": "Q4 Zephyr absent: BM25 still returns corpus edges via lexical overlap on works/Project tokens \u2014 unchanged by real embeddings."
}
```
