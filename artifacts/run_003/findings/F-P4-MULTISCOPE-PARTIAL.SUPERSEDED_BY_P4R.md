# F-P4-MULTISCOPE-PARTIAL — SUPERSEDED_BY_P4R

status: SUPERSEDED_BY_P4R
reason: INVALID_REFERENCE_TIME_IN_FIXTURE
historical_evidence: artifacts/run_002/ (preserved; do not delete)
corrected_evidence: artifacts/run_003/result.json phase P4R_D status PASS

## Why superseded
run_002 P4C called `retrieve_episodes(now, ...)` where `now` was captured **before**
`add_episode`. Graphiti 0.29.3 filters `e.valid_at <= reference_time`, and
`add_episode` sets `valid_at` from a later `datetime.now()`, so empty multi-group
retrieve was a **fixture timing bug**, not Falkor multi-scope routing failure.

P4R temporal Control1/Control2 + P4R-D with `query_time` AFTER writes both markers found.

## Still valid
- P4B multi-group **search** PASS (run_002) remains valid.
