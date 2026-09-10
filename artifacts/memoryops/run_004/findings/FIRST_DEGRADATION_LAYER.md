# FIRST_DEGRADATION_LAYER

- **layer:** `BM25_CANDIDATE_GENERATION`
- **NEO4J_CAUSAL_EVIDENCE:** NO

For Q4 (`Who works on Project Zephyr?`) the cosine channel returned **0** candidates
(`sim_min_score=0.6` filtered all hash-embedding neighbors). All four final edges
**first entered via BM25 fulltext** (ranks 0..3), then RRF over a single non-empty
result set preserved that order into `Graphiti.search`.

There is no Zephyr entity/edge in the corpus; BM25 still matches lexical tokens
(`works`, `Project`, etc.) on unrelated WORKS_ON/USES facts. Cross-encoder is not
on the default `EDGE_HYBRID_SEARCH_RRF` path. FalkorDBLite only — not Neo4j.

```json
{
  "label": "FIRST_DEGRADATION_LAYER",
  "layer": "BM25_CANDIDATE_GENERATION",
  "Q4_bm25_count": 4,
  "Q4_cosine_count": 0,
  "Q4_ZEPHYR_FIRST_ENTRY": {
    "question": "WHERE DID EACH EDGE FIRST ENTER?",
    "edges": [
      {
        "final_rank": 0,
        "uuid": "091c8acc-cc5f-4f2d-89b2-a7333f778a49",
        "name": "WORKS_ON",
        "fact": "Alice works on Project Orion.",
        "first_channel": "bm25",
        "first_channel_rank": 0,
        "channels_present": [
          {
            "channel": "bm25",
            "rank": 0
          }
        ],
        "rrf": {
          "rank": 0,
          "uuid": "091c8acc-cc5f-4f2d-89b2-a7333f778a49",
          "rrf_score": 1.0,
          "first_entry": {
            "first_channel": "bm25",
            "first_channel_rank": 0,
            "fact": "Alice works on Project Orion.",
            "name": "WORKS_ON",
            "channels_present": [
              {
                "channel": "bm25",
                "rank": 0
              }
            ]
          }
        }
      },
      {
        "final_rank": 1,
        "uuid": "e2282d3f-879e-42b6-9e24-b1a7c9ea550e",
        "name": "WORKS_ON",
        "fact": "Bob works on Project Nova.",
        "first_channel": "bm25",
        "first_channel_rank": 1,
        "channels_present": [
          {
            "channel": "bm25",
            "rank": 1
          }
        ],
        "rrf": {
          "rank": 1,
          "uuid": "e2282d3f-879e-42b6-9e24-b1a7c9ea550e",
          "rrf_score": 0.5,
          "first_entry": {
            "first_channel": "bm25",
            "first_channel_rank": 1,
            "fact": "Bob works on Project Nova.",
            "name": "WORKS_ON",
            "channels_present": [
              {
                "channel": "bm25",
                "rank": 1
              }
            ]
          }
        }
      },
      {
        "final_rank": 2,
        "uuid": "e7608a9b-489d-4536-9135-77ecbdac8d26",
        "name": "USES",
        "fact": "Project Orion uses Python.",
        "first_channel": "bm25",
        "first_channel_rank": 2,
        "channels_present": [
          {
            "channel": "bm25",
            "rank": 2
          }
        ],
        "rrf": {
          "rank": 2,
          "uuid": "e7608a9b-489d-4536-9135-77ecbdac8d26",
          "rrf_score": 0.3333333333333333,
          "first_entry": {
            "first_channel": "bm25",
            "first_channel_rank": 2,
            "fact": "Project Orion uses Python.",
            "name": "USES",
            "channels_present": [
              {
                "channel": "bm25",
                "rank": 2
              }
            ]
          }
        }
      },
      {
        "final_rank": 3,
        "uuid": "cf7fbae4-7962-4109-8821-e95f5b20baa9",
        "name": "USES",
        "fact": "Project Nova uses Rust.",
        "first_channel": "bm25",
        "first_channel_rank": 3,
        "channels_present": [
          {
            "channel": "bm25",
            "rank": 3
          }
        ],
        "rrf": {
          "rank": 3,
          "uuid": "cf7fbae4-7962-4109-8821-e95f5b20baa9",
          "rrf_score": 0.25,
          "first_entry": {
            "first_channel": "bm25",
            "first_channel_rank": 3,
            "fact": "Project Nova uses Rust.",
            "name": "USES",
            "channels_present": [
              {
                "channel": "bm25",
                "rank": 3
              }
            ]
          }
        }
      }
    ]
  },
  "NEO4J_CAUSAL_EVIDENCE": "NO"
}
```
