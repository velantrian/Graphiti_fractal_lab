# H-EMBED / EMBEDDING_HYPOTHESIS

Query vectors are DETERMINISTIC_EMBEDDING (hash→L2), dim=1024. Cosine channel uses sim_min_score=0.6; surviving candidates are real channel hits, not Neo4j artifacts. Deterministic embeddings lack semantic geometry — cosine neighbors are hash-space accidents filtered only by min_score.

```json
{
  "label": "H-EMBED",
  "finding": "Query vectors are DETERMINISTIC_EMBEDDING (hash\u2192L2), dim=1024. Cosine channel uses sim_min_score=0.6; surviving candidates are real channel hits, not Neo4j artifacts. Deterministic embeddings lack semantic geometry \u2014 cosine neighbors are hash-space accidents filtered only by min_score.",
  "embedding_label": "DETERMINISTIC_EMBEDDING",
  "examples": {
    "Q1": {
      "label": "DETERMINISTIC_EMBEDDING",
      "dim": 1024,
      "sha256_hex": "ce45a99a01f9ce34ea05c96eaaf27b4fe34a55e01f5b1ba96bda53d96a304b9d",
      "embedding_dim_constant": 1024,
      "l2_norm": 1.0,
      "head8": [
        0.04093738781969971,
        -0.007688747966136497,
        -0.04550907579956466,
        0.048418331786751444,
        0.0459246837977342,
        0.04800272378858189,
        0.03304083585447845,
        0.039690563825191094
      ],
      "input_text": "Who works on Project Orion?",
      "input_text_sha256": "e26d12f4eef3cfdf91fae342981a5f5ee07003bfb42b4ccab64b47338734961b"
    },
    "Q4": {
      "label": "DETERMINISTIC_EMBEDDING",
      "dim": 1024,
      "sha256_hex": "b17301ba4c581af759eba754f3930e28d1f6a3cda1bc82bb7ca714f79af52b04",
      "embedding_dim_constant": 1024,
      "l2_norm": 1.0,
      "head8": [
        0.0014616983515939417,
        -0.03320143398620537,
        -0.008561376059335974,
        -0.02109021907299838,
        -0.047818417502144835,
        -0.03779534309121491,
        -0.051577070406243555,
        -0.012320028963434693
      ],
      "input_text": "Who works on Project Zephyr?",
      "input_text_sha256": "83306b4d0d2504625fa6d1244ab9685f2f77ad957c23113bf2d3e7a86efd4eb3"
    },
    "Q5": {
      "label": "DETERMINISTIC_EMBEDDING",
      "dim": 1024,
      "sha256_hex": "c76ad6bc8bab05c7ae4eb6318945fa6960bcc2df050031d2a9af5d1b8c528570",
      "embedding_dim_constant": 1024,
      "l2_norm": 1.0,
      "head8": [
        -0.027696007606531077,
        -0.0354251260083537,
        -0.04959517641169518,
        -0.04143666254310464,
        0.020396284671476375,
        0.04143666254310464,
        0.010090793469046207,
        -0.00021469773338396108
      ],
      "input_text": "Does Alice use Python?",
      "input_text_sha256": "3f2d0c1fafe0977fae87d8b2e4b61d92dd20e54578cf098a742e945e8f038cac"
    }
  }
}
```
