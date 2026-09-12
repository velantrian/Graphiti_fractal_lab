# 🧭 Cross-Project Research Resume — 2026-09-12

**Canonical GitHub location for the current research program route.**  
**Labs entry point remains:** [`docs/LABS_HANDOFF_2026-09-12.md`](../LABS_HANDOFF_2026-09-12.md)  
**Required terminology / work-surface map:** [`VELANTRIM_WORK_SURFACE_MAP_2026-09-12.md`](VELANTRIM_WORK_SURFACE_MAP_2026-09-12.md)

This document persists Program Route v0.1 and the continuity/orientation state so a fresh Labs instance can resume **without this chat**. It is **not** evidence that any continuity architecture is correct. It does **not** authorize experiments.

If this file and chat disagree: **trust GitHub**, then investigate.

---

## IF YOU ARE A FRESH LABS INSTANCE, START HERE

1. Fetch `velantrian/Graphiti_fractal_lab`.
2. Checkout `experiment/falkordblite-deterministic-memory`.
3. Read [`docs/LABS_HANDOFF_2026-09-12.md`](../LABS_HANDOFF_2026-09-12.md) (FM-16 / FM-17-pre archive + this pointer).
4. Read **this file** (current cross-project route).
5. Read the required terminology / work-surface map: [`VELANTRIM_WORK_SURFACE_MAP_2026-09-12.md`](VELANTRIM_WORK_SURFACE_MAP_2026-09-12.md). Use it to interpret `World Map / Working Board`, Anchor, History, Orientation Packet, FM, and the project ownership/routing surfaces without conflation.
6. Verify live `HEAD` and referenced SHAs. Do not assume chat is newer than GitHub.
7. Reconstruct: DONE / CURRENT / HOLD / BLOCKED / UNKNOWN / NEXT.
8. Report to Ruslan **before any work**:

```text
RESTORED_STATE:
CURRENT_PRIORITY:
BLOCKED_TRACKS:
NEXT_ACTION:
EXECUTION_AUTHORIZED: YES/NO
```

9. If execution authorization is not explicit: **do not run experiments.**

GitHub = durable store. Labs' computer = execution environment only. Untracked local `data/` is not archive, Canon, or evidence.

---

## Program Route v0.1

This is the first durable GitHub persistence of the reviewed route. No second competing route.

```text
ORNT-E1-PILOT          COMPLETED
        |
        v
CONT-E0T               NEXT EMPIRICAL PRIORITY
                       DESIGN / PRE-EXECUTION
                       NOT AUTHORIZED TO RUN
        |
        +----------------------+----------------------+
        |                      |                      |
        v                      v                      v
  T1 sufficient          T2 adds bounded        INCONCLUSIVE
  (primary continuity    continuity value       repair protocol
   non-inferior +        (follow-up only,       no promotion
   cheaper/simpler)      no architecture
        |                 promotion)
        v
  rebase ORNT on
  maintained state;
  T2 may keep separate
  history/audit value


CAP-E1                 HOLD   (may reframe after CONT; not cancelled)
ORNT-E1-CONFIRM        BLOCKED until recorded CONT-E0T verdict
FM-17-pre              SEPARATE read-side line; STOPPED unless Ruslan C
```

**Meta-rule:** do not write another research-design document unless it removes a concrete CONT-E0T execution blocker **or** new evidence creates a new falsifiable question. Next knowledge should come from evidence, not another architecture discussion.

---

## Experiment statuses

| ID | Status | Role |
|----|--------|------|
| **ORNT-E1-PILOT** | COMPLETED | Exploratory applied test: explicit orientation packet vs raw RAG/history |
| **CONT-E0T** | DESIGN / PRE-EXECUTION | **Current main question** — history vs maintained current state |
| **CAP-E1** | HOLD · NOT EXECUTED | Capture of candidate transitions from raw interaction |
| **ORNT-E1-CONFIRM** | PREREGISTRATION DRAFT · BLOCKED | Confirmatory orientation; blocked on CONT verdict |
| **FM-17-pre** | SEPARATE · integrity ready · experiment NOT EXECUTED | Read-side qualification on frozen FM-16 fixture |

Do **not** call all of these “E1”.

---

## ORNT-E1-PILOT (DONE)

**Identity:** exploratory applied test, explicit orientation packet vs raw RAG/history.

**Recorded run (from 2026-09-12 owner/review handoff; artifacts are NOT in this lab repo’s `artifacts/` as of this write):**

- 8 fixtures, 2 arms, 16 calls
- model: `gpt-5-mini`
- run errors: 0

**Measured diagnostic token-overlap proxy (recorded, not re-derived here):**

| | Raw | Packet | Δ |
|---|---:|---:|---:|
| Overall | ≈ 58.0 | ≈ 84.4 | ≈ +26.5 |

Approximate role split (recorded):

| Role | Raw | Packet |
|------|---:|---:|
| CURRENT / NOW | ≈ 0.704 | ≈ 0.943 |
| THEN | ≈ 0.381 | ≈ 0.745 |
| NEXT | ≈ 0.644 | ≈ 0.986 |
| UNKNOWN | ≈ 0.634 | 1.000 |
| WHY | ≈ 0.535 | ≈ 0.546 |

**Established:** packet helps the **tested** orientation task under an oracle/prepared representation. Evidence level: `POSITIVE_EXPLORATORY_APPLIED`.

**NOT established:** T2 > T1; transitions caused the gain; anchor independently caused the gain; transition history is necessary; automatic capture works; packet can be generated in runtime; deployability; architecture.

**Recorded threats (OPEN):** content advantage; selection/presentation advantage; token-overlap proxy bias; prompt asymmetry. Proxy-bias is an **OPEN THREAT**, not an established explanation.

**WHY:** little measured improvement. `WHY_CAUSE = UNKNOWN`. Do not create a rationale subsystem. In current ORNT, WHY = **transition / decision rationale** (not world causality, evidence validity, or retrospective narrative).

---

## CONT-E0T (NEXT / PRE-EXECUTION)

**Question:** Does genuine accepted transition history provide independent bounded continuity value beyond an equally informative maintained canonical current state?

| Arm | What |
|-----|------|
| **T1** | Versioned maintained current state (goals, constraints, blockers, accepted decisions, open questions, provenance refs, process position). **No** full accepted transition trajectory. |
| **T2** | **Same final-state information as T1** **plus** genuine accepted transition history (`from_state`, `to_state`, type, owner/authority, provenance, acceptance, supersession, ordering, timestamp). |

**Forbidden construction:** do not build T2 by serializing final state into fake SET events.

**Distinctions:**

```text
REPRESENTATION ADVANTAGE ≠ HISTORY ADVANTAGE ≠ CONTINUITY ADVANTAGE
EQUIVALENCE ≠ ADEQUACY
T1 ≈ T2  ≠  T1 is good enough in absolute terms
```

Primary continuity surface: correct current state, constraint preservation, blocker preservation, valid resume point, honest UNKNOWN.

If T2 is better only at “what was true before / what changed / what did we supersede?” → **HISTORY VALUE**, not automatically **CONTINUITY VALUE**.

**Outcomes:**

| Case | Record |
|------|--------|
| A — T1 sufficient | T1 non-inferior on primary continuity **and** cheaper/simpler → stop treating T2 as default continuity substrate. History may still have audit/forensic value. |
| B — T2 adds primary continuity | T2 improves ResumeAdequacy beyond preregistered threshold without unacceptable safety regression → follow-up only. No architecture promotion. |
| C — T2 helps only history | Record historical value. Do not call it a general continuity win. |
| D — inconclusive | Repair fixture/protocol. No architecture decision. |

**Executed:** NO. **Authorized:** NO.

### Still missing before CONT-E0T execution (preregistration, not redesign)

1. Primary confirmatory surface (final-state resume; historical queries separate)
2. Fixture set (count, IDs, content, hash/version; no post-hoc edits)
3. Queries per fixture (number, role, wording, current vs historical)
4. Operational T1/T2 final-state information **equivalence check**
5. Reader/model freeze (provider, version, temperature, seed, limits, prompts)
6. Semantic rubric frozen before outputs (resume adequacy vs historical metrics)
7. Reviewer procedure (roles, blindness, adjudication)
8. Complexity accounting **separately** (storage, annotation, replay, context). Do not invent a fake NetValue scalar unless weights are preregistered.
9. Ledger envelope (max transitions and/or max T2 token/byte budget)
10. Absolute adequacy boundary: T1 non-inferior to T2 ≠ T1 proven adequate

**One next research action:** complete those CONT-E0T preregistration fields → final review → **separate Ruslan GO / NO-GO** → only then execute.

---

## CAP-E1 (HOLD)

**Question:** Can raw natural interaction be converted into **candidate** state-changing transitions accurately enough for later human acceptance?

```text
CANDIDATE TRANSITION ≠ ACCEPTED TRANSITION
CAPTURE CONFIDENCE ≠ AUTHORITY
PROVENANCE ≠ TRUTH
MODEL OUTPUT ≠ CANON
```

The model must not silently create accepted state.

**HOLD because CONT-E0T is priority — not cancelled, not dependent on T2 being true.**

If T1 wins, CAP may reframe from “capture for a persistent ledger” toward “detect state-changing signals so maintained current state can be updated safely.”

**Future hygiene (record only, do not execute):** independent dual human gold + IAA + adjudication; freeze span matching (exact / turn-level / overlap / semantic); separate `UnauthorizedAcceptanceEmissionRate` from `HumanFalseAcceptRate`.

---

## ORNT-E1-CONFIRM (BLOCKED)

**Blocker:** written CONT-E0T verdict.

**Purpose:** given an already preserved representation, does structured orientation presentation improve bounded orientation?

Conceptual stack (adjacent differences = marginal contribution in this stack, **not** independent causal effects):

- A0 = raw
- A1 = FORMAT + SELECTION
- A2 = + accepted transitions/provenance
- A3 = + human-authored frozen anchor

Must **not** silently assume T2. If CONT says T1 sufficient → rebase ORNT on T1/current-state (or explicit comparative design). If CONT unresolved → do not preserve T2 by inertia.

**Future hygiene (record only):** log per arm source IDs, retrieved/selected/total tokens, `oracle-assisted-selection=YES/NO`. Prompt symmetry: do not tell baseline “you do not receive X”. Held-out internal confirmation ≠ external generalization ≠ cross-model replication ≠ deployment evaluation.

---

## FM-17-pre (SEPARATE / STOPPED)

Read-side: which retrieved records qualify for a given query?  
**Not** continuity, capture, orientation proof, or accepted-history proof.

- Integrity SHA: `080e1959fe6a3d996f2690059fcdc687dd5c832e`
- Review: `PASS_WITH_MINOR_FINDINGS`
- Integrity/protocol: `GO_FOR_OFFLINE_ABLATION = YES`
- User execution: **NOT authorized**
- Annotation / overlay / A0–A3: **NOT_EXECUTED**

Do not launch FM-17 from this resume. Detail: [`../LABS_HANDOFF_2026-09-12.md`](../LABS_HANDOFF_2026-09-12.md) and [`fm17_pre/README.md`](fm17_pre/README.md).

FM-16 remains frozen at `62cfa45` / `artifacts/memoryops/run_007/`: `GENERALIZATION=GLOBAL_THRESHOLD_NOT_FEASIBLE`; under those rules `CE_VS_EMBEDDING=NO_MATERIAL_GAIN`. Do not reinterpret as “CE useless / embeddings solved retrieval / structure validated.”

---

## Conceptual model (accepted distinctions)

| Term | Is | Is not |
|------|----|--------|
| PROJECT ANCHOR | Human-accepted scoped project intent (goal, constraints, owner, scope, accepted status) | Soul identity, salience score, retrieved fact, model guess, BDI architecture |
| PROJECT SCOPE | Domain/boundary of work | The accepted intent inside that scope |
| CURRENT PROJECT STATE | What currently holds | Proven ledger-derived (T1 vs T2 projection is under test) |
| HISTORY | Recoverable past / trajectory | Automatic proof of continuity |
| ORIENTATION PACKET | Disposable, reconstructable, query-oriented read artifact | Source of truth / Canon / authority / persistent state |
| NEXT | Default = LLM proposal | Accepted next step without explicit human acceptance + provenance |
| THEN | Historical state as_of T | NEXT / `next_allowed_step` |

Query roles: **NOW** (current scoped state) · **THEN** (as_of T) · **WHY** (transition/decision rationale in current ORNT) · **REOPEN** · **UNKNOWN** · **NEXT** (proposal).  
**THEN ≠ NEXT.** Do not put `next_allowed_step` inside THEN.

Keep **QUERY RELEVANCE** and **GOAL RELEVANCE** as separate axes.

---

## Invariants

```text
SOURCE ≠ AUTHORITY ≠ CONFIDENCE ≠ ACCESS
DISCOVERY ≠ RANKING ≠ QUALIFICATION ≠ EVIDENCE ≠ AUTHORITY
STORED ≠ CURRENT
LATEST ≠ CURRENT
SUPERSEDED ≠ FALSE
RETRIEVED ≠ RELEVANT
RELEVANT ≠ EVIDENCE
PROPOSAL ≠ DECISION
OBSERVATION ≠ ACCEPTED TRANSITION
CANDIDATE TRANSITION ≠ ACCEPTED TRANSITION
SUMMARY ≠ PROMOTION
MODEL OUTPUT ≠ CANON
MODEL OUTPUT ≠ STATE AUTHORITY
UNKNOWN ≠ FALSE
UNKNOWN ≠ MISMATCH
UNRESOLVED ≠ REJECT
REFERENCE LABORATORY ≠ UNIVERSAL ARCHITECTURE
REBUILDABLE PROJECTION ≠ MANDATORY EVENT SOURCING
ORIENTATION ≠ CANON
ATTENTION ≠ STATE
ROUTING ≠ AUTHORITY
REPRESENTATION ADVANTAGE ≠ HISTORY ADVANTAGE
HISTORY ADVANTAGE ≠ CONTINUITY ADVANTAGE
EQUIVALENCE ≠ ADEQUACY
CURRENT STATE ≠ STATE TRAJECTORY
REBUILDABILITY ≠ CONTINUITY BENEFIT
ORACLE VALUE ≠ DEPLOYABILITY
ORACLE VALUE ≠ TRANSITION-CAPTURE_ACCURACY
ORACLE VALUE ≠ PROOF THAT TRANSITION HISTORY IS NECESSARY
CAPTURE CONFIDENCE ≠ AUTHORITY
PROJECT ANCHOR ≠ PROJECT SCOPE
ORIENTATION PACKET ≠ SOURCE OF TRUTH
HELD-OUT INTERNAL CONFIRMATION ≠ EXTERNAL GENERALIZATION
```

---

## Multi-model review (not a vote)

| Reviewer | Role | Useful residue |
|----------|------|----------------|
| Manus | Organize Program Route | Route as above; listed remaining CONT prereg fields |
| Grok | Sequencing / stale-state / drift | CONT_FIRST; stop opening new tracks. Correction: CONT is NEXT/PRE-EXECUTION, not already ACTIVE execution |
| DeepSeek | Causal identifiability | CONT-E0T identifiable; minor hygiene only (adequacy wording, ledger envelope, later ORNT logging, prompt symmetry, CAP IAA/spans) |
| Qwen | Semantic non-conflation | WHY is dangerous if vague; keep WHY = transition/decision rationale; no large WHY taxonomy in runtime |
| Perplexity | External methodology | No external blocker. Analogy ≠ import: no BDI architecture, no required event sourcing, no default full factorial, no new salience/approval-fatigue/goal-recognition runtime |
| ChatGPT | (in the cycle) | Do not treat as a vote |

---

## What not to add / not to run

**Do not create:** World Model, Orientation Engine, Anchor Manager, Transition Capture organ, Human Oversight organ, Meta-controller, BDI subsystem, goal-recognition runtime, salience engine, multi-scope / approval-fatigue / company-of-agents benchmarks, new E2/E3, Family C, new FM phase from this file, CORRUPTION_REBUILD as primary CONT task, expanded CAP ontology without evidence.

**Do not run unless separately authorized:** CONT-E0T · CAP-E1 · ORNT-E1-CONFIRM · FM-17 A0–A3.

---

## Fresh-instance self-test (must be answerable from GitHub alone)

| # | Question | Answer in this file |
|---|----------|---------------------|
| 1 | Completed? | ORNT-E1-PILOT DONE; FM-16 frozen; FM-17-pre integrity ready, experiment not executed |
| 2 | Current priority? | CONT-E0T preregistration completion → final review → owner GO/NO-GO |
| 3 | Must not run yet? | CONT-E0T until separate authorization; CAP-E1; ORNT-E1-CONFIRM; FM-17 A0–A3 |
| 4 | Why CONT-E0T? | Test whether genuine accepted history adds independent continuity value beyond equally informative maintained current state |
| 5 | What ORNT-E1-PILOT established? | Exploratory packet advantage on tested fixtures. Not T2/capture/architecture proof |
| 6 | If T1 wins? | Prefer simpler maintained-state continuity substrate; keep separately demonstrated history value |
| 7 | If T2 only improves THEN/history? | Record historical value; not a general continuity win |
| 8 | WHY unresolved? | Weak pilot Δ; cause UNKNOWN; no rationale subsystem |
| 9 | One next action? | Finish/freeze CONT-E0T preregistration fields — not run multiple experiments |

---

## Machine-readable snapshot

```json
{
  "resume_type": "cross_project_research_state",
  "date": "2026-09-12",
  "canonical_lab_repository": "velantrian/Graphiti_fractal_lab",
  "branch": "experiment/falkordblite-deterministic-memory",
  "labs_handoff": "docs/LABS_HANDOFF_2026-09-12.md",
  "cross_project_resume": "docs/research/CROSS_PROJECT_RESEARCH_RESUME_2026-09-12.md",
  "work_surface_map": "docs/research/VELANTRIM_WORK_SURFACE_MAP_2026-09-12.md",
  "program_route_persisted_here": true,
  "ornt_e1_pilot": {
    "status": "COMPLETED",
    "evidence_level": "POSITIVE_EXPLORATORY_APPLIED",
    "artifacts_in_this_repo": false,
    "source_of_numbers": "2026-09-12 owner/review handoff recording",
    "fixtures": 8,
    "calls": 16,
    "model": "gpt-5-mini",
    "proxy_raw": 58.0,
    "proxy_packet": 84.4,
    "proxy_delta": 26.5,
    "strong_signal": ["NOW", "THEN", "NEXT", "UNKNOWN"],
    "weak_or_unresolved": ["WHY"],
    "why_cause": "UNKNOWN",
    "proves_t2_over_t1": false,
    "proves_transition_history_required": false,
    "proves_capture": false,
    "proves_deployability": false
  },
  "cont_e0t": {
    "status": "DESIGN_PRE_EXECUTION",
    "program_priority": "NEXT_EMPIRICAL_PRIORITY",
    "executed": false,
    "authorized": false,
    "question": "Does genuine accepted transition history add independent bounded continuity value beyond an equally informative maintained current state?"
  },
  "cap_e1": {
    "status": "HOLD",
    "executed": false,
    "semantically_depends_on_t2": false
  },
  "ornt_e1_confirm": {
    "status": "BLOCKED",
    "executed": false,
    "blocker": "recorded CONT-E0T verdict"
  },
  "fm17_pre": {
    "status": "SEPARATE_READ_SIDE_TRACK",
    "integrity_implementation_sha": "080e1959fe6a3d996f2690059fcdc687dd5c832e",
    "integrity_go": true,
    "user_execution_authorized": false,
    "ablation_executed": false
  },
  "fm16": {
    "execution_sha": "62cfa45a80ec83794b701d88873ce136b7629354",
    "artifacts": "artifacts/memoryops/run_007",
    "generalization": "GLOBAL_THRESHOLD_NOT_FEASIBLE",
    "ce_vs_embedding_under_frozen_rules": "NO_MATERIAL_GAIN"
  },
  "current_next_action": "complete CONT-E0T preregistration fields",
  "architecture_change_authorized": false,
  "new_organ_authorized": false,
  "product_repo_change_authorized": false,
  "experiment_executed_by_this_docs_update": false
}
```
