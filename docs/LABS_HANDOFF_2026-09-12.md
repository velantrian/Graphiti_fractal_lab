# 🧠 Labs Handoff — 2026-09-12

**For an independent AI reviewer (Manus / ChatGPT / other).**  
This document is written by **Labs**, a Grok Bot desktop assistant used by Ruslan (Velantrim) for lab research. Labs is **not human**. Labs executed tests and edits on **Labs' own computer**, then committed the durable record to GitHub. **GitHub is the source of truth.** Local run scratch on Labs' computer is not the archive.

Do **not** treat this chat paraphrase as evidence. Verify SHAs and files on GitHub.

---

---

## IF YOU ARE A FRESH LABS INSTANCE, START HERE

1. Fetch `velantrian/Graphiti_fractal_lab` · checkout `experiment/falkordblite-deterministic-memory`.
2. Read **this file** (FM-16 / FM-17-pre durable archive).
3. Read the current route: [`docs/research/CROSS_PROJECT_RESEARCH_RESUME_2026-09-12.md`](research/CROSS_PROJECT_RESEARCH_RESUME_2026-09-12.md).
4. Read the required terminology / work-surface map: [`docs/research/VELANTRIM_WORK_SURFACE_MAP_2026-09-12.md`](research/VELANTRIM_WORK_SURFACE_MAP_2026-09-12.md). Use it to interpret `World Map / Working Board`, Anchor, History, Orientation Packet, FM, and project routing/ownership surfaces without conflation.
5. Verify live `HEAD` and referenced SHAs. Chat is **not** newer than GitHub.
6. Reconstruct DONE / CURRENT / HOLD / BLOCKED / UNKNOWN / NEXT.
7. Report to Ruslan **before work**: `RESTORED_STATE` · `CURRENT_PRIORITY` · `BLOCKED_TRACKS` · `NEXT_ACTION` · `EXECUTION_AUTHORIZED`.
8. If execution is not explicit: **do not run experiments.**

**Current priority is CONT-E0T, not FM-17-pre.** FM-17-pre is one separate read-side line. Do not launch it from a resume.

---

## CROSS-PROJECT RESEARCH STATE / RESUME

FM-17-pre is **only one** research line. Overall empirical priority has moved.

Canonical route (Program Route v0.1, first persisted on GitHub here):  
[`docs/research/CROSS_PROJECT_RESEARCH_RESUME_2026-09-12.md`](research/CROSS_PROJECT_RESEARCH_RESUME_2026-09-12.md)

Terminology / work-surface map (required reading for fresh Labs):  
[`docs/research/VELANTRIM_WORK_SURFACE_MAP_2026-09-12.md`](research/VELANTRIM_WORK_SURFACE_MAP_2026-09-12.md)

| Track | Status |
|-------|--------|
| **ORNT-E1-PILOT** | COMPLETED — exploratory packet vs raw; proxy Δ ≈ +26.5; not T2/architecture proof |
| **CONT-E0T** | **NEXT EMPIRICAL PRIORITY** · DESIGN / PRE-EXECUTION · not authorized |
| **CAP-E1** | HOLD · not executed · not cancelled · not dependent on T2 |
| **ORNT-E1-CONFIRM** | BLOCKED on recorded CONT-E0T verdict |
| **FM-17-pre** | SEPARATE · integrity GO only · annotation/A0–A3 NOT_EXECUTED |

**One next action:** complete CONT-E0T preregistration fields (primary surface, fixtures, queries, T1/T2 equivalence check, model, rubric, reviewers, complexity, ledger envelope, equivalence ≠ adequacy). Then final review. Then separate Ruslan GO/NO-GO. Only then execute.

This handoff task does **not** authorize CONT-E0T, CAP-E1, ORNT-E1-CONFIRM, or FM-17 execution.

The sections below remain the FM-16 / FM-17-pre archive. **Do not treat them as the current program route.**


## 0. Who produced this

| Field | Value |
|-------|--------|
| Assistant name | **Labs** |
| Role | Lab / research executor for Velantrim Graphiti work |
| User | Ruslan |
| Language of collaboration | Russian (docs/protocol often English) |
| Product repo (DO NOT TOUCH) | `velantrian/Graphiti_fractal` |
| Lab repo (ONLY this) | `velantrian/Graphiti_fractal_lab` |
| Branch | `experiment/falkordblite-deterministic-memory` |
| Integrity implementation SHA | `080e1959fe6a3d996f2690059fcdc687dd5c832e` |
| Docs after independent review (pre-this-handoff) | `d668e511c751116b60456a8810316c97fb3cd5c1` |
| Date | 2026-09-12 |

Labs ran pytest / probes / git commit+push **on Labs' computer**. Canonical artifacts, protocol, validator, and receipts live in **GitHub**. If local checkout and GitHub diverge, **trust GitHub**.

---

## 1. What we worked on (arc)

Research question chain, **lab repo only**, no merge, no product-runtime promotion.

### 1.1 Graphiti + FalkorDBLite deterministic memory (P0–P7)

Prove WRITE → REMEMBER → REOPEN → RETRIEVE → UPDATE → CONTRADICT → RESTORE on Graphiti 0.29.3 + FalkorDBLite. Frozen. Artifacts under `artifacts/run_001` … `run_006` (P-track) plus MemoryOps later.

### 1.2 Fractal MemoryOps (FM-0 … FM-16)

Thin local executable MemoryOps prototype, then real-LLM / real-embedding / CE work:

| Phase | What | Execution SHA (approx) |
|-------|------|-------------------------|
| FM-0…10 | Prototype + temporal class + provenance | earlier on same branch |
| FM-11…12 | DeepSeek natural ingest / contradiction | run_003 |
| FM-13 | Search-path instrumentation | run_004 |
| FM-14 | Real embeddings differential | run_005 |
| FM-15 | BGE cross-encoder | run_006 |
| **FM-16** | CE held-out calibration | **`62cfa45`** · `artifacts/memoryops/run_007` |

**FM-16 frozen finding (do not rewrite):**  
`GENERALIZATION=GLOBAL_THRESHOLD_NOT_FEASIBLE`. Global CE / embedding θ not feasible. Under those rules `CE_VS_EMBEDDING=NO_MATERIAL_GAIN`. Scope PARTIAL (notable: HN9 TQ11/TF23 CE vs embedding rank-1 inversion). No runtime CE promotion.

### 1.3 FM-17-pre — structural oracle ablation **protocol + integrity gate only**

Offline ablation **designed**, **not executed**. Target: frozen FM-16 `run_007` fixture.

Question:

> On the frozen FM-16 fixture, does oracle-quality **query + fact** typed structure add useful qualification beyond CE-only ranking, and does structural→CE residual preserve more useful evidence than structure alone?

Class: `TARGETED_MECHANISTIC_ABLATION`.  
Positive claim name (protocol): `ORACLE_QUERY_AND_FACT_STRUCTURAL_REPRESENTATION_HAS_MEASURABLE_VALUE` — **not** implementation readiness.

Arms (science **unchanged**):

| Arm | Meaning |
|-----|---------|
| A0 | Frozen CE baseline |
| A1 | Structural oracle ACCEPT/REJECT/UNRESOLVED |
| A2 | Structural → CE residual (same survivors, CE order) |
| A3 | `ORACLE_COMPONENT_IDENTITY_CEILING_DIAGNOSTIC` (not primary success gate) |

Co-primary: `UNRESOLVED_RATE`. Validator is **integrity validator ≠ relevance judge**.

---

## 2. Where we arrived (current state)

**Integrity implementation SHA:** `080e1959fe6a3d996f2690059fcdc687dd5c832e`  
**Docs-after-review SHA (GitHub, before this handoff file):** `d668e511c751116b60456a8810316c97fb3cd5c1`  
**Status:** PROTOCOL + CHARTER + v1.3.1 EXTERNAL FREEZE ANCHOR + **independent integrity review recorded**.  
**Independent verdict (recorded on GitHub, not by Labs):** `PASS_WITH_MINOR_FINDINGS`.  
**Integrity/protocol:** `GO_FOR_OFFLINE_ABLATION = YES` — **integrity verdict only**.  
**REAL annotation / overlay / A0–A3:** `NOT_EXECUTED`.  
This GO does **not** itself start annotation or ablation. User option **C** is still required to execute.

### Integrity version ladder (verify on GitHub)

| Version | SHA | Closed |
|---------|-----|--------|
| Protocol | `469fe64` | A0–A3 protocol docs |
| Charter | `8aebf70` | claim bounds, anti-leakage prose |
| v1.1 | `bcad493` | no gold/HN for A1/A2 construction; dual blinded annotation; A3 diagnostic; UNRESOLVED co-primary |
| v1.2 | `914ea5c` | fail-closed schema; T1–T18 / P1–P4; 26 tests |
| v1.3 | `f091ba2` | empty/incomplete package; A/B-derived disagreement; real SHA-256; T19–T26 / P5–P6; 36 tests |
| **v1.3.1** | **`080e195`** | **external `expected_frozen_root` required; package cannot replace its own root (T27); T28–T29 / P7; 40 tests** |

Manus independently found (then Labs closed):

1. v1.2: empty `{}` → PASS; hashes not recomputed.
2. v1.3: full package + local root replacement → PASS (package self-authoritative).
3. v1.3.1 closed: `actual_root == package_local_root == EXTERNAL_EXPECTED_ROOT`; missing external → FAIL.
4. Post-`080e195` **docs-only** commits (`8b31072` … `d668e51`) record the independent integrity review. Labs did **not** author those four commits; they appeared on the remote while this handoff was being written.

Pytest at integrity SHA `080e195`:  
`python3 -m pytest tests/lab/test_fm17_pre_schema_enforcement.py -v` → **40 passed** (1 unrelated asyncio warning).

---

## 3. Where everything lives on GitHub

Repo: https://github.com/velantrian/Graphiti_fractal_lab  
Branch: `experiment/falkordblite-deterministic-memory`  
Tip: https://github.com/velantrian/Graphiti_fractal_lab/tree/experiment/falkordblite-deterministic-memory

### 3.1 FM-17-pre (start here)

Directory: [`docs/research/fm17_pre/`](https://github.com/velantrian/Graphiti_fractal_lab/tree/experiment/falkordblite-deterministic-memory/docs/research/fm17_pre)

| File | Role |
|------|------|
| `README.md` | Index + current status |
| `STOP_BOUNDARY.md` | What is / is not authorized; current reviewed GO |
| `FM17_PRE_V1_3_1_FINAL_INTEGRITY_REVIEW_2026-09-11.md` | Independent integrity closure (docs-only after `080e195`) |
| `EXTERNAL_FREEZE_ANCHOR.md` | v1.3.1 two-phase freeze procedure |
| `FM17_PRE_MEASUREMENT_CHARTER.md` | Claims / ACCEPT/REJECT/UNRESOLVED |
| `FM17_PRE_STRUCTURAL_ORACLE_PROTOCOL.md` | Master protocol |
| `ORACLE_ANNOTATION_GUIDE.md` | Blinded A/B |
| `oracle_annotations.schema.json` | Field provenance |
| `sanitized_annotation_input.schema.json` | Annotator view (no CAL/TEST/gold/HN) |
| `annotation_receipt.schema.json` | Freeze receipt |
| `pre_ablation_validation_receipt.schema.json` | Pre-ablation receipt schema |
| `preregistered_filter_rules.md` | A1/A2 rules |
| `preregistered_metrics.md` | Metrics + UNRESOLVED_RATE |
| `falsification_table.md` | Falsifiers |
| `oracle_annotations.template.jsonl` | EXAMPLE_NOT_GOLD only |
| `FROZEN_RUN007_INPUTS.md` | Pointers/hashes into run_007 |
| `validate_fm17_pre_package.py` | Integrity validator v1.3.1 |

Tests: [`tests/lab/test_fm17_pre_schema_enforcement.py`](https://github.com/velantrian/Graphiti_fractal_lab/blob/experiment/falkordblite-deterministic-memory/tests/lab/test_fm17_pre_schema_enforcement.py)

### 3.2 FM-16 frozen execution

- Commit: `62cfa45a80ec83794b701d88873ce136b7629354`
- Artifacts: [`artifacts/memoryops/run_007/`](https://github.com/velantrian/Graphiti_fractal_lab/tree/experiment/falkordblite-deterministic-memory/artifacts/memoryops/run_007)
- Typical subdirs: `corpus/`, `scores/`, `calibration/`, `evaluation/`, `hashes/`, `findings/`, `result.json`, `preregistration.json`

### 3.3 Earlier lab / MemoryOps

- Prior Labs capability handoff: [`docs/LABS_HANDOFF_2026-09-09.md`](https://github.com/velantrian/Graphiti_fractal_lab/blob/experiment/falkordblite-deterministic-memory/docs/LABS_HANDOFF_2026-09-09.md)
- This handoff: `docs/LABS_HANDOFF_2026-09-12.md`
- Branch status board: [`RESEARCH_STATUS.md`](https://github.com/velantrian/Graphiti_fractal_lab/blob/experiment/falkordblite-deterministic-memory/RESEARCH_STATUS.md)
- Integrity review write-up: [`docs/research/fm17_pre/FM17_PRE_V1_3_1_FINAL_INTEGRITY_REVIEW_2026-09-11.md`](https://github.com/velantrian/Graphiti_fractal_lab/blob/experiment/falkordblite-deterministic-memory/docs/research/fm17_pre/FM17_PRE_V1_3_1_FINAL_INTEGRITY_REVIEW_2026-09-11.md)
- MemoryOps runs: `artifacts/memoryops/run_001` … `run_007`
- P-track Graphiti/Falkor receipts: `artifacts/run_001` … `run_006` (if present on branch)

### 3.4 Forbidden sibling

https://github.com/velantrian/Graphiti_fractal — **product**. Labs did not modify it. Reviewer must not treat lab commits as product changes.

---

## 4. What Labs did on Labs' computer vs GitHub

| Surface | What |
|---------|------|
| Labs' computer | Checkout, pytest, direct `validate_package` probes, edit validator/tests/docs, `git commit` + `git push` |
| GitHub (canonical) | Branch history, SHAs, protocol, schemas, validator, tests, FM-16 artifacts |
| Not a source of truth | Chat summaries, Labs' local untracked `data/` scratch dirs |

Untracked local scratch that must **not** be treated as experiment evidence: `data/falkor_e2e/`, `data/memoryops_fm*` (local DB leftovers).

---

## 5. Open questions / remaining decisions (user + reviewer)

These are **not** invitations to invent science.

1. **Integrity re-review of `080e195` is already recorded on GitHub** as `PASS_WITH_MINOR_FINDINGS` / `GO_FOR_OFFLINE_ABLATION=YES` (integrity only). A new reviewer should still verify files, not trust this chat.

2. **Execution is still stopped.** Integrity GO ≠ user authorization to annotate or run A0–A3. Ruslan must explicitly choose **C** to execute.

3. **If user authorizes C:** blinded dual annotation of real CAL/TEST, freeze R0 **outside** the package, then overlay, then A0–A3 once. Not started.

4. **REC-1** (retrospective class-conditioned threshold diagnostic) is a **separate** track. Not part of FM-17-pre. Do not run or redesign from it.

5. **Residual (accepted, not speculative-hardened):**
   - Validator cannot prove *when* a human first saw evaluation overlay (procedural).
   - A caller who *knowingly* supplies a **new** R1 as `--expected-frozen-root` is a new external authorization, not package self-auth. Ops must record R0 before overlay.
   - No PKI / git-object fetch by design (`EXTERNAL_ROOT`).
   - `ENFORCEMENT_COMPLEXITY_EXHAUSTED = YES` — no speculative v1.4 unless a new R1+R2+R3 path is demonstrated.

6. **Do not:**
   - annotate CAL/TEST
   - execute A0–A3
   - merge
   - touch product repo
   - change science (classes, metrics, Honest Empty, multi-hop, A3 role)
   - add LLM judge / new embeddings / graph scorer

User decision codes after review: **A** fix · **B** send for review · **C** authorize ablation · **D** cancel/defer.

---

## 6. Machine-readable snapshot

```json
{
  "author": "Labs",
  "author_kind": "Grok Bot desktop assistant, not human",
  "user": "Ruslan",
  "handoff_date": "2026-09-12",
  "repository": "velantrian/Graphiti_fractal_lab",
  "product_repository": "velantrian/Graphiti_fractal",
  "product_repo_changed": false,
  "branch": "experiment/falkordblite-deterministic-memory",
  "integrity_implementation_sha": "080e1959fe6a3d996f2690059fcdc687dd5c832e",
  "docs_after_review_sha_before_this_handoff": "d668e511c751116b60456a8810316c97fb3cd5c1",
  "fm16_execution_sha": "62cfa45a80ec83794b701d88873ce136b7629354",
  "fm16_artifacts": "artifacts/memoryops/run_007",
  "fm17_pre_dir": "docs/research/fm17_pre",
  "validator": "docs/research/fm17_pre/validate_fm17_pre_package.py",
  "validator_version": "fm17-pre-validator-v1.3.1",
  "enforcement_tests": "tests/lab/test_fm17_pre_schema_enforcement.py",
  "pytest_at_head": "40 passed",
  "scientific_protocol_changed_in_integrity_patches": false,
  "real_annotation_created": false,
  "ablation_executed": false,
  "model_executed_for_fm17": false,
  "merge": false,
  "independent_integrity_verdict_recorded_on_github": "PASS_WITH_MINOR_FINDINGS",
  "go_for_offline_ablation_integrity_verdict": "YES",
  "go_for_offline_ablation_user_execution_authorized": false,
  "real_annotation_overlay_a0a3": "NOT_EXECUTED",
  "canonical_store": "GitHub",
  "labs_computer_role": "execute tests and push; not the archive"
}
```

---

## 7. Suggested reviewer start

1. `git fetch` + verify integrity code SHA `080e195` still parents the branch; do not confuse later **docs-only** commits with a science/runtime change.
2. Read `docs/research/fm17_pre/README.md` then `STOP_BOUNDARY.md` then `EXTERNAL_FREEZE_ANCHOR.md`.
3. Read `validate_fm17_pre_package.py` — confirm `expected_frozen_root` is never defaulted from the package.
4. Run `pytest tests/lab/test_fm17_pre_schema_enforcement.py`.
5. Replay T27: mutate artifact + recompute local root to R1; pass external R0 → FAIL.
6. Do **not** authorize ablation from this handoff alone.

---

## CROSS-PROJECT machine-readable pointer

```json
{
  "resume_type": "cross_project_research_state",
  "date": "2026-09-12",
  "canonical_lab_repository": "velantrian/Graphiti_fractal_lab",
  "branch": "experiment/falkordblite-deterministic-memory",
  "labs_handoff": "docs/LABS_HANDOFF_2026-09-12.md",
  "cross_project_resume": "docs/research/CROSS_PROJECT_RESEARCH_RESUME_2026-09-12.md",
  "work_surface_map": "docs/research/VELANTRIM_WORK_SURFACE_MAP_2026-09-12.md",
  "ornt_e1_pilot": {"status": "COMPLETED", "proves_t2_over_t1": false},
  "cont_e0t": {"status": "DESIGN_PRE_EXECUTION", "program_priority": "NEXT_EMPIRICAL_PRIORITY", "executed": false, "authorized": false},
  "cap_e1": {"status": "HOLD", "executed": false, "semantically_depends_on_t2": false},
  "ornt_e1_confirm": {"status": "BLOCKED", "blocker": "recorded CONT-E0T verdict"},
  "fm17_pre": {"status": "SEPARATE_READ_SIDE_TRACK", "integrity_go": true, "user_execution_authorized": false, "ablation_executed": false},
  "current_next_action": "complete CONT-E0T preregistration fields",
  "architecture_change_authorized": false,
  "product_repo_change_authorized": false
}
```
