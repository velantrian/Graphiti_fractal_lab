# ZEPHYR_NO_RESULT

- Q4_MAX_SCORE: 0.007880358956754208
- POSITIVE_MIN_SCORE: 0.03224395960569382
- NO_RESULT_SEPARABILITY_MARGIN: 0.02436360064893961
- label: **SEPARABLE**

Positive margin ≠ authorized threshold. FIXTURE_ONLY / NOT_CALIBRATED.

```json
{
  "Q4_MAX_SCORE": 0.007880358956754208,
  "Q4_scores": {
    "F1": 0.007880358956754208,
    "F2": 2.956380194518715e-05,
    "F3": 0.005133460741490126,
    "F4": 1.866598177002743e-05
  },
  "POSITIVE_MIN_SCORE": 0.03224395960569382,
  "positive_gold_pairs": [
    {
      "query_id": "Q1",
      "fact_id": "F1",
      "score": 0.9741688370704651
    },
    {
      "query_id": "Q2",
      "fact_id": "F2",
      "score": 0.9972037076950073
    },
    {
      "query_id": "Q3",
      "fact_id": "F3",
      "score": 0.049960434436798096
    },
    {
      "query_id": "Q3",
      "fact_id": "F4",
      "score": 0.03224395960569382
    }
  ],
  "NO_RESULT_SEPARABILITY_MARGIN": 0.02436360064893961,
  "NO_RESULT_SEPARABILITY": "SEPARABLE",
  "observed_separation_interval": {
    "OBSERVED_SEPARATION_INTERVAL": "(0.007880358956754208, 0.03224395960569382]",
    "label": [
      "NOT_CALIBRATED",
      "NOT_AUTHORIZED",
      "FIXTURE_ONLY"
    ]
  },
  "THRESHOLD_SELECTED": false,
  "note": "Positive margin establishes SEPARABILITY_OBSERVED_ON_FM15_FIXTURE only."
}
```
