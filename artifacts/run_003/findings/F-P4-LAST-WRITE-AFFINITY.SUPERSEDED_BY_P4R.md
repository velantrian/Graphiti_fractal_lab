# F-P4-LAST-WRITE-AFFINITY — SUPERSEDED_BY_P4R

status: SUPERSEDED_BY_P4R
reason: INVALID_REFERENCE_TIME_IN_FIXTURE
historical_evidence: artifacts/run_002/ (preserved; do not delete)
corrected_evidence: artifacts/run_003/result.json phases P4R_B, P4R_C status PASS

## Why superseded
run_002 P4A/P4D retrieve_episodes misses (including A→B→read A and B→A→read B)
used an early `reference_time`. With late `query_time`, P4R-B and P4R-C PASS for
both search and retrieve.

## Receipt wins over prose
run_002 `result.json` P4D `B_then_A_read_B.retrieve_episodes.expected_marker_found`
was **false** and listed under `affinity_failures`. Any prose claiming that cell PASS
is incorrect; the receipt is authoritative. The miss is explained by
INVALID_REFERENCE_TIME_IN_FIXTURE, not proven last-write retrieve affinity.

## Still OBSERVED (not superseded)
`driver._database` still mutates to the last-written `group_id` after `add_episode`
(see P4R-B/C evidence `driver_database_after_writes` / `last_write_group_observed`).
That mutation is real; it did **not** cause empty retrieve once reference_time was fixed
because `@handle_multiple_group_ids` clones a call-scoped driver for the requested group.
