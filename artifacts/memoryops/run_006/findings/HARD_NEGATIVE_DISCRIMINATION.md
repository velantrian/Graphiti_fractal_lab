# HARD_NEGATIVE_DISCRIMINATION

- Q1_HARD_NEGATIVE_MARGIN: 0.9438925869762897
- Q2_HARD_NEGATIVE_MARGIN: 0.9837360717356205
- Q3_HARD_NEGATIVE_MARGIN: 0.03222320139502699

margin > 0 → CE separates gold from non-gold on this fixture.

```json
{
  "Q1": {
    "query_id": "Q1",
    "query_text": "Who works on Project Orion?",
    "gold_fact_ids": [
      "F1"
    ],
    "gold_scores": {
      "F1": 0.9741688370704651
    },
    "non_gold_scores": {
      "F2": 0.03027625009417534,
      "F3": 0.0073229726403951645,
      "F4": 2.0570820197463036e-05
    },
    "LOWEST_GOLD_SCORE": 0.9741688370704651,
    "BEST_NON_GOLD_SCORE": 0.03027625009417534,
    "HARD_NEGATIVE_MARGIN": 0.9438925869762897,
    "separates_perfectly_on_fixture": true
  },
  "Q2": {
    "query_id": "Q2",
    "query_text": "What language does Project Orion use?",
    "gold_fact_ids": [
      "F2"
    ],
    "gold_scores": {
      "F2": 0.9972037076950073
    },
    "non_gold_scores": {
      "F1": 0.0025138286873698235,
      "F3": 1.7932947230292484e-05,
      "F4": 0.013467635959386826
    },
    "LOWEST_GOLD_SCORE": 0.9972037076950073,
    "BEST_NON_GOLD_SCORE": 0.013467635959386826,
    "HARD_NEGATIVE_MARGIN": 0.9837360717356205,
    "separates_perfectly_on_fixture": true
  },
  "Q3": {
    "query_id": "Q3",
    "query_text": "What is related to Project Nova?",
    "gold_fact_ids": [
      "F3",
      "F4"
    ],
    "gold_scores": {
      "F3": 0.049960434436798096,
      "F4": 0.03224395960569382
    },
    "non_gold_scores": {
      "F1": 2.03070230782032e-05,
      "F2": 2.0758210666826926e-05
    },
    "LOWEST_GOLD_SCORE": 0.03224395960569382,
    "BEST_NON_GOLD_SCORE": 2.0758210666826926e-05,
    "HARD_NEGATIVE_MARGIN": 0.03222320139502699,
    "separates_perfectly_on_fixture": true
  }
}
```
