# INVALID_REFERENCE_TIME_IN_FIXTURE

classification: TEST_FIXTURE_BUG (not Falkor routing defect)

## Mechanism
Graphiti 0.29.3 `retrieve_episodes` → `WHERE e.valid_at <= $reference_time`.
`add_episode(..., reference_time=datetime.now())` stores that as episode `valid_at`.
Fixtures that stamp `now = datetime.now()` **before** writes then pass that same
`now` into retrieve can exclude just-written episodes.

## Proof (run_003)
- Control1: `reference_time < valid_at` → episode NOT returned (PASS)
- Control2: `query_time = datetime.now()` AFTER write → episode returned (PASS)
- No +1s cushion required in this run (`used_plus_one_second: false`)

## Preferred pattern
```python
await add_episode(...)
query_time = datetime.now(timezone.utc)  # AFTER writes
await retrieve_episodes(query_time, ...)
```
