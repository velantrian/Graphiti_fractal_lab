# F-P4-LAST-WRITE-AFFINITY

phase: P4D
test: write_order_reversal
status: FAIL

```json
{
  "marker_a": "A_ONLY_6e94524a6ff7453792e4d0186ac791e1",
  "marker_b": "B_ONLY_6e94524a6ff7453792e4d0186ac791e1",
  "group_a": "p4d_A_6e94524a6f",
  "group_b": "p4d_B_6e94524a6f",
  "rows": [
    {
      "sequence": "A_then_B_read_A",
      "driver_database_after_writes": "p4d_B_6e94524a6f",
      "search": {
        "requested_group": "p4d_A_6e94524a6f",
        "driver_database_before": "p4d_B_6e94524a6f",
        "driver_database_after": "p4d_B_6e94524a6f",
        "result_count": 6,
        "expected_marker_found": true,
        "foreign_marker_found": false
      },
      "retrieve_episodes": {
        "requested_group": "p4d_A_6e94524a6f",
        "driver_database_before": "p4d_B_6e94524a6f",
        "driver_database_after": "p4d_B_6e94524a6f",
        "result_count": 0,
        "expected_marker_found": false,
        "foreign_marker_found": false
      }
    },
    {
      "sequence": "B_then_A_read_B",
      "driver_database_after_writes": "p4d_A_6e94524a6f",
      "search": {
        "requested_group": "p4d_B_6e94524a6f",
        "driver_database_before": "p4d_A_6e94524a6f",
        "driver_database_after": "p4d_A_6e94524a6f",
        "result_count": 6,
        "expected_marker_found": true,
        "foreign_marker_found": false
      },
      "retrieve_episodes": {
        "requested_group": "p4d_B_6e94524a6f",
        "driver_database_before": "p4d_A_6e94524a6f",
        "driver_database_after": "p4d_A_6e94524a6f",
        "result_count": 0,
        "expected_marker_found": false,
        "foreign_marker_found": false
      }
    }
  ],
  "affinity_failures": [
    {
      "sequence": "A_then_B_read_A",
      "surface": "retrieve_episodes",
      "driver_after_writes": "p4d_B_6e94524a6f",
      "requested_group": "p4d_A_6e94524a6f"
    },
    {
      "sequence": "B_then_A_read_B",
      "surface": "retrieve_episodes",
      "driver_after_writes": "p4d_A_6e94524a6f",
      "requested_group": "p4d_B_6e94524a6f"
    }
  ],
  "leaks": []
}
```
