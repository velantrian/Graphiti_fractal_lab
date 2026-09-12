# 🌎🧭 VELANTRIM — Work Surface Map / What Is What — 2026-09-12

**Purpose:** durable terminology and routing map for fresh AI instances.  
**Status:** documentation / navigation only. **Not architecture, not Canon, not runtime authorization, not a new organ.**

If this map conflicts with a project's primary source or a newer reviewed route, the primary/newer source wins and the conflict must be reported rather than silently reconciled.

---

## 1. Why this map exists

The same words were beginning to be used for different things: *world map*, *working board*, *current state*, *history*, *orientation packet*, *FM*, *anchor*, *Soul*, *Continuum*. This page fixes the working meanings so a fresh AI does not merge different research questions or assign them to the wrong project.

The map answers two questions:

1. **What object are we talking about?**
2. **Which research/project surface is responsible for studying or consuming it?**

It does **not** decide unresolved architecture.

---

## 2. World Map / Working Board / Current Project Model

### Preferred working meaning

**WORLD MAP / WORKING BOARD** is a user-facing shorthand for the **CURRENT PROJECT MODEL / CURRENT WORKING BOARD**:

> a bounded, current, project-scoped representation of what matters *now* relative to an accepted project anchor.

Typical contents may include:

- accepted current goal / anchor reference;
- active constraints;
- accepted decisions that still hold;
- blockers;
- unresolved questions / UNKNOWNs;
- current process position;
- current project facts needed for resume;
- provenance pointers;
- an `accepted_next_step` only if it was explicitly accepted with provenance.

### It is NOT

```text
WORKING BOARD ≠ FULL WORLD MODEL
WORKING BOARD ≠ HISTORY
WORKING BOARD ≠ CANON
WORKING BOARD ≠ ORIENTATION PACKET
WORKING BOARD ≠ RETRIEVAL RESULT
WORKING BOARD ≠ SOUL / IDENTITY
```

The phrase **World Model** is currently too strong if it implies causal dynamics, prediction, counterfactual simulation, environment modelling, or action-consequence simulation. Those capabilities are not established by the present CONT/ORNT/CAP work.

Therefore, when precision matters, prefer:

```text
CURRENT PROJECT MODEL
CURRENT WORKING BOARD
SCOPED CURRENT STATE
```

### Critical unresolved point

How the working board is produced is **not decided yet**:

```text
T1: maintained current state / working board

T2: same current state + genuine accepted transition history
    (possibly supporting reconstruction/projection)
```

`CONT-E0T` exists specifically to test whether T2 adds independent continuity value beyond a competent T1.

Do **not** write:

> "the World Map is the projection of the ledger"

as a settled fact before CONT-E0T evidence.

---

## 3. Project Anchor

**PROJECT ANCHOR** = human-accepted scoped project intent.

Working components:

```text
goal
constraints
owner / accountable human context
scope
accepted status
```

It tells the system what the project is trying to accomplish and therefore provides a basis for **goal-relative relevance**.

Important boundaries:

```text
PROJECT ANCHOR ≠ PROJECT SCOPE
PROJECT ANCHOR ≠ SOUL IDENTITY
PROJECT ANCHOR ≠ VISION JOURNAL
PROJECT ANCHOR ≠ SALIENCE SCORE
PROJECT ANCHOR ≠ MODEL-GUESSED GOAL
```

Goal recognition may someday propose a **candidate** anchor, but:

```text
RECOGNIZED GOAL ≠ ACCEPTED ANCHOR
```

Current experiments use explicit/human-authored anchors where applicable.

---

## 4. History / State Trajectory

**HISTORY** = recoverable past / trajectory of accepted changes.

Potential uses include:

- historical `THEN` / as-of reconstruction;
- supersession trace;
- decision/rationale trace where captured;
- reopen reasoning;
- audit / forensic inspection.

But:

```text
HISTORY VALUE ≠ CONTINUITY VALUE
CURRENT STATE ≠ STATE TRAJECTORY
REBUILDABILITY ≠ CONTINUITY BENEFIT
```

A competent current board may be sufficient for resume even when history remains useful for other queries. CONT-E0T is the test.

---

## 5. Orientation Packet

**ORIENTATION PACKET** = a derived, query-oriented, disposable read artifact assembled for the model/user at a particular moment.

It may combine selected pieces of:

- current project state / working board;
- relevant history;
- accepted anchor;
- provenance / rationale references;
- explicit UNKNOWNs;
- query-role structure such as NOW / WHY / THEN / REOPEN.

It is not authoritative state.

```text
ORIENTATION PACKET ≠ SOURCE OF TRUTH
ORIENTATION PACKET ≠ CANON
ORIENTATION PACKET ≠ PERSISTENT MEMORY STORE
ORIENTATION PACKET ≠ STATE AUTHORITY
```

`ORNT-E1-PILOT` tested whether an oracle/prepared packet helps compared with raw RAG/history. It did **not** prove the storage representation or automatic capture mechanism.

---

## 6. Query roles

These are **read roles**, not separate stores:

```text
NOW      = current scoped state
THEN     = historical state as_of T
WHY      = transition / decision rationale in current ORNT work
REOPEN   = reconsideration / conditions for reopening
UNKNOWN  = unresolved / missing / not established
NEXT     = proposed next action unless explicitly accepted
```

Critical:

```text
THEN ≠ NEXT
QUERY ROLE ≠ STORAGE LOCATION
NEXT PROPOSAL ≠ ACCEPTED NEXT STEP
```

Do not place `next_allowed_step` inside THEN.

---

## 7. What "FM" means

**FM** here means **Fractal MemoryOps research sequence** inside `Graphiti_fractal_lab`.

It is an experiment/research numbering line, **not a list of architectural modules/organs**.

High-level arc:

```text
FM-0…10   MemoryOps prototype + temporal/provenance foundations
FM-11…12  real-LLM ingest / contradiction work
FM-13     retrieval-path instrumentation
FM-14     real embeddings differential
FM-15     cross-encoder work
FM-16     CE held-out calibration / threshold result
FM-17-pre structural-oracle qualification protocol + integrity gate
```

Current distinction:

- `FM-16` asks about ranking/calibration behaviour on the frozen fixture.
- `FM-17-pre` asks whether oracle-quality query+fact structure adds useful **query qualification** beyond CE-only ranking.
- FM-17 is **read-side qualification research**. It is not continuity, transition capture, or orientation-state storage.

```text
FM-17 ≠ CONT-E0T
FM-17 ≠ CAP-E1
FM-17 ≠ ORNT-E1
```

---

## 8. Main Velantrim work surfaces — routing map

This is a **working navigation map**, not a claim that every ownership relation is production-authorized.

| Surface | Working role | Must not be confused with |
|---|---|---|
| 💠 **Crystal** | evidence, provenance, epistemic admission, Canon boundary | project-goal valuation, query relevance, human authority |
| 🗿 **Titan** | orchestration / tools / runtime-hosting surface; may assemble contexts in future | semantic authority, Canon authority, proof of continuity |
| 🧬 **Native Kernel** | semantic obligations/invariants; bounded reference lab for claim→event→reduction→state→projection/receipt patterns | mandatory universal event sourcing, production continuity owner |
| 🌀 **Mentaury Soul** | identity, beliefs, character, self-model / governed self-change research | project working board, project status, project anchor storage |
| 🌎 **Continuum** | durable process continuity / minimum sufficient state / resume research | query qualification, identity, evidence admission |
| 🪁 **Mentaury-Kernel** | cross-domain composition surface | automatic owner of all project semantics |
| 🚀 **Cognitive OS** | model/tool/routing/evaluation policy profile | Canon, project state, identity |
| ⚗️ **CLOS** | cognitive research blueprint / research framing | runtime implementation or authorization |
| 🕸 **Graphiti Fractal / MemoryOps / FM** | retrieval, ranking, qualification and memory-lab experiments | continuity substrate, Canon, goal valuation |
| 🧭 **Atlas** | navigation / orientation to where to look; routing surface | evidence authority, state authority, full orientation engine |
| 🔬 **Research surfaces** | bounded experiments, audits, donor studies | production authorization |

If a future primary document establishes a different owner, update this map from the primary source. Do not infer ownership merely from project names.

---

## 9. How the pieces fit — current working picture

```text
             👤 HUMAN / OWNER
        accepts protected intent/state changes
                    │
                    ▼
             🎯 PROJECT ANCHOR
        goal · constraints · scope · owner
                    │
                    ▼
      🌎 CURRENT PROJECT MODEL / WORKING BOARD
      what holds now relative to that anchor
                    │
          ┌─────────┴─────────┐
          │                   │
          ▼                   ▼
   🕰 HISTORY / TRAJECTORY   🔍 RETRIEVAL
   how we got here            candidate records
          │                   │
          │                   ▼
          │            🕸 QUALIFICATION
          │            what matters for query
          └─────────┬─────────┘
                    ▼
            📦 ORIENTATION PACKET
        NOW · WHY · THEN · REOPEN · UNKNOWN
                    │
                    ▼
                  🤖 LLM
           use / reason / propose NEXT
                    │
                    ▼
              👤 HUMAN ACCEPTANCE
          where protected acceptance is required
```

Orthogonal boundaries:

```text
💠 Crystal: evidence / Canon admission
🌀 Soul: identity / beliefs
🧭 Atlas: where-to-look / navigation
🗿 Titan: orchestration/runtime host
```

None of those orthogonal roles silently makes model output authoritative.

---

## 10. Current research questions mapped to the picture

| Experiment | Exact question in the map |
|---|---|
| `CONT-E0T` | Is the **working board/current state (T1)** enough for resume, or does **genuine accepted history (T2)** add independent continuity value? |
| `CAP-E1` | Can raw interaction produce reliable **candidate state-changing transitions** without granting them authority? |
| `ORNT-E1-PILOT` | Does an explicit prepared **orientation packet** help the reader model vs raw RAG/history? COMPLETED exploratory. |
| `ORNT-E1-CONFIRM` | After representation is decided/bounded, does structured packet presentation hold up under a confirmatory rubric? BLOCKED on CONT verdict. |
| `FM-17-pre` | Which retrieved records qualify for a specific query? Separate read-side line. |

Current priority:

```text
CONT-E0T preregistration completion
→ final review
→ Ruslan GO / NO-GO
→ only then execution
```

---

## 11. Non-conflation guards

```text
WORKING BOARD ≠ FULL WORLD MODEL
WORKING BOARD ≠ HISTORY
WORKING BOARD ≠ ORIENTATION PACKET
PROJECT ANCHOR ≠ PROJECT SCOPE
PROJECT ANCHOR ≠ SOUL IDENTITY
QUERY RELEVANCE ≠ GOAL RELEVANCE
QUERY ROLE ≠ STORAGE LOCATION
RETRIEVED ≠ RELEVANT
RELEVANT ≠ EVIDENCE
EVIDENCE ≠ AUTHORITY
CANDIDATE TRANSITION ≠ ACCEPTED TRANSITION
ORIENTATION PACKET ≠ SOURCE OF TRUTH
MODEL OUTPUT ≠ STATE AUTHORITY
MODEL OUTPUT ≠ CANON
HISTORY ADVANTAGE ≠ CONTINUITY ADVANTAGE
ORACLE VALUE ≠ CAPTURE ACCURACY ≠ DEPLOYABILITY
```

---

## 12. Fresh-AI interpretation rule

When a fresh AI reads "карта мира", "world map", or "рабочая доска" in this research branch, interpret it by default as:

> **CURRENT PROJECT MODEL / CURRENT WORKING BOARD** — a bounded current-state view relative to an accepted project anchor.

Do **not** infer a full causal World Model service, simulator, prediction engine, or mandatory ledger projection unless a newer primary document explicitly establishes it.

When the user asks "над чем мы сейчас работаем?", answer from the current Program Route, not from whichever project document was opened most recently.

---

## 13. Current status

```text
ORNT-E1-PILOT     DONE
CONT-E0T          NEXT / PRE-EXECUTION / NOT AUTHORIZED
CAP-E1            HOLD
ORNT-E1-CONFIRM   BLOCKED
FM-17-pre         SEPARATE / STOPPED
```

**One next action:** complete/freeze CONT-E0T preregistration fields. No experiment is authorized by this map.
