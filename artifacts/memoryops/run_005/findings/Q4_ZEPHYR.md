# Q4_ZEPHYR

- REAL_EMBEDDINGS_SUFFICIENT_FOR_Q4: **REAL_EMBEDDINGS_NOT_SUFFICIENT_FOR_Q4**
- final retrieved: ['Project Orion uses Python.', 'Alice works on Project Orion.', 'Bob works on Project Nova.', 'Project Nova uses Rust.']
- bm25: ['Alice works on Project Orion.', 'Bob works on Project Nova.', 'Project Orion uses Python.', 'Project Nova uses Rust.']
- cosine: ['Project Orion uses Python.', 'Bob works on Project Nova.', 'Project Nova uses Rust.', 'Alice works on Project Orion.']
- matrix Q4 vs facts: {'Alice works on Project Orion.': 0.637605444232953, 'Project Orion uses Python.': 0.6630608780228715, 'Bob works on Project Nova.': 0.6606814752666372, 'Project Nova uses Rust.': 0.6534129907444763}

Zephyr is absent from the corpus. Ideal final list is empty. If BM25 still supplies edges, RRF will surface false positives unless cosine-only filtering or a later gate removes them (out of FM-14 scope).

```json
{
  "label": "REAL_EMBEDDINGS_SUFFICIENT_FOR_Q4",
  "Q4_final_empty": false,
  "Q4_bm25_still_feeds_rrf": true,
  "Q4_cosine_count": 4,
  "verdict": "REAL_EMBEDDINGS_NOT_SUFFICIENT_FOR_Q4"
}
```
