# F-P4-READ-SURFACE-DIVERGENCE — SUPERSEDED_BY_P4R

status: SUPERSEDED_BY_P4R
reason: INVALID_REFERENCE_TIME_IN_FIXTURE
note: run_002 did not emit a dedicated F-P4-READ-SURFACE-DIVERGENCE.md file;
the search-hit / retrieve-miss pattern in P4D rows is the divergence symptom.

corrected_evidence: artifacts/run_003/result.json P4R_B and P4R_C — search and
retrieve agree (both find expected marker) when query_time is AFTER writes.

## Why superseded
retrieve_episodes is temporally filtered; search is not. Early reference_time made
retrieve empty while search succeeded — appearing as surface divergence / affinity.
