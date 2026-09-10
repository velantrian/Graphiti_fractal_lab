# UNEXPECTED_FINDINGS — FM-11/FM-12 REAL_LLM run_003

## F-FM11-DET-EMBED-BROAD-RETRIEVAL
With DETERMINISTIC_EMBEDDING, Q4 ("Who works on Project Zephyr?") returned 4 hits
(all stored edges) classified **IRRELEVANT** rather than **NO_RESULT**.
Deterministic embedder does not semantically exclude unrelated queries; ranking is
non-semantic. STRUCTURAL retrieval ≠ SEMANTIC relevance.

## F-FM11-Q5-MULTI-FACT-RELEVANT
Q5 ("Does Alice use Python?") judged RELEVANT because both Alice→Orion and
Orion→Python facts were retrieved together. No direct Alice→uses→Python edge
was required. SEMANTIC answerability via multi-fact adjacency — do not force
expected edge shapes.

## F-FM12-PROVIDER-CACHE-CROSS-RUN
Variance RUN_A cache_miss≈2026 / hit≈5248; RUN_B and RUN_C miss≈362 / hit≈6912.
Provider-automatic Context Caching warmed across A→B/C despite separate lab
clients/DBs (account-level). CACHE_HIT ≠ better semantic result; B/C latency
conditions are WARM vs A's colder start — do not compare as identical.

## F-FM11-USAGE-RECEIPT-SCOPE
`usage_receipt.json` / fingerprint aggregates track the shared module client
(~23 generate calls for FM-11 + FM-12A–D path). Variance RUN_A/B/C use separate
`RealLlmCallStats` instances recorded under `run_*/variance_run.json`.
Combined variance-only approx: hit=19072 miss=2750 prompt=21822 completion=3906
(calls=15). Do not treat fingerprint TOKEN_USAGE as whole-suite exclusive total.

## SUPERSESSION
`BLOCKED_NO_REAL_PROVIDER.md` retained as history; superseded by this REAL_LLM run.
