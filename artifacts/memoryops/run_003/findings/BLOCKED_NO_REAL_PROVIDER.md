# BLOCKED_NO_REAL_PROVIDER

Checked process environment and box-secrets.json.

- LLM-related env vars: ABSENT/EMPTY
- box-secrets: only GH_TOKEN / GITHUB_TOKEN / GITHUB_PERSONAL_ACCESS_TOKEN
- openai package installed (3.11.0) but unusable without key
- anthropic package: not installed
- DeterministicTemporalLLMClient was NOT used as a stand-in

FM-11/FM-12 matrix: NOT_RUN except FM-11A=BLOCKED.


---
SUPERSEDED_BY: FM-11/FM-12 REAL_LLM DeepSeek run (same run_003).
Prior BLOCKED_NO_REAL_PROVIDER kept as history.
