# 🧭🔬 Graphiti Fractal Lab — Retrieval Relevance Reasoning Log

> **Role:** long-form research commentary / decision history  
> **Scope:** `velantrian/Graphiti_fractal_lab` · retrieval-relevance lane  
> **Date baseline:** 2026-09-10  
> **Authority:** explanatory only. Exact experiment claims remain subordinate to exact Git state, executable artifacts, score matrices, tests and receipts.  
> **Purpose:** preserve not only *what* FM-13 → FM-16 says, but *why the research moved from one question to the next*, which alternatives were considered, which interpretations were rejected, and what the current question actually means.

---

## 0. Why this commentary exists

A short status table is not enough for this research line.

If a future human or AI sees only:

```text
FM-13 = diagnosis
FM-14 = embeddings
FM-15 = Cross-Encoder
FM-16 = held-out threshold test
```

it is easy to misread the work as a normal sequence of model upgrades: “BM25 was weak, embeddings were better, Cross-Encoder was better, now tune a threshold.” That is **not** the actual research story.

The real question gradually changed as evidence accumulated. The project began by asking whether Graphiti-backed memory could persist and retrieve state correctly. Once persistence, scope isolation, temporal invalidation and provenance were demonstrated in bounded laboratory settings, the bottleneck moved to something subtler: retrieval could be technically successful while still returning information that did not answer the query.

That distinction matters because:

```text
SEARCH RETURNED SOMETHING
≠
SEARCH RETURNED SOMETHING RELEVANT
```

and:

```text
BEST AVAILABLE CANDIDATE
≠
GOOD ENOUGH CANDIDATE
```

The later FM experiments therefore were not attempts to prove that “Cross-Encoder is good.” They were attempts to isolate the missing capability, falsify competing explanations, and determine whether an existing scalar relevance signal can support an honest rejection boundary without damaging recall.

This log preserves that chain.

---

## 1. The earlier memory work changed the question

The laboratory had already accumulated evidence on storage and continuity before the relevance work became central.

The earlier bounded phases established, within their tested scope, that the lab could perform deterministic Graphiti/FalkorDBLite ingestion, close and reopen the store, preserve group isolation, and exercise temporal supersession. Later replay experiments also exposed an important distinction: low-level restored bytes do not automatically mean restored facts remain currently applicable.

That produced invariants such as:

```text
RESTORED_BYTES
≠
RESTORED_CURRENT_APPLICABILITY
```

and:

```text
OLD FACT STILL STORED
≠
OLD FACT STILL CURRENT
```

Those results were important because they removed one tempting explanation for later retrieval failures. When the Zephyr query returned unrelated facts, the immediate problem was not “maybe the database forgot what was stored” or “maybe persistence failed.” The lab already had evidence that persistence and retrieval plumbing could work.

So the research focus moved upward:

```text
Can we store/reopen/retrieve?
        ↓
yes, in bounded lab scope
        ↓
Can we distinguish current/history/provenance?
        ↓
yes, in bounded lab scope
        ↓
But does retrieval return only things that actually answer the query?
```

This is the point where FM-13 begins to matter.

---

## 2. The motivating failure: Project Zephyr

The simplest negative control became the most informative example.

The frozen small memory contained facts about Orion and Nova. The query:

```text
Who works on Project Zephyr?
```

had no relevant fact in the fixture.

An ideal relevance-aware retrieval stage should be allowed to say:

```text
[]
```

or an equivalent typed no-relevant-result outcome.

Instead, the active hybrid path returned unrelated memories from the fixture. This was scientifically useful because it showed a structural property of ranking systems:

```text
A ranker can always identify the "best" item among bad candidates.
That does not mean the best item is acceptable.
```

BM25, cosine similarity and reciprocal-rank fusion can order candidates relative to each other. Relative ranking alone does not guarantee an **absolute qualification boundary**.

The Zephyr case therefore became the negative control for the emerging research question:

> Can the system preserve broad recall while also rejecting all candidates when none of them actually answer the query?

This is the origin of the “honest EMPTY” idea. Honest EMPTY is not evidence that Zephyr does not exist in the world. It means only that **the tested candidate set contains no candidate that passes the relevance criterion**.

Hence:

```text
NO_RELEVANT_RESULT
≠
ENTITY_PROVEN_ABSENT
```

---

## 3. Why FM-13 came before changing the model

The first instinct could have been: “replace the embedding model” or “turn on a stronger reranker.” That would have been premature because the active path itself had not yet been instrumented.

FM-13 asked a narrower question:

> Where does the measured degradation first appear, and which ranking components are actually being called?

This was important because the repository already constructed a Cross-Encoder object. A future reviewer could easily look at the code and assume that Cross-Encoder relevance was participating in search.

Instrumentation showed otherwise:

```text
CROSS_ENCODER CONSTRUCTED
≠
CROSS_ENCODER USED
```

The measured path was effectively broad lexical + semantic candidate generation followed by RRF. The Cross-Encoder call count was zero.

That finding prevented a false diagnosis. Without instrumentation one might have concluded:

> “Cross-Encoder cannot reject Zephyr.”

But the correct statement was:

> “The tested path did not call the Cross-Encoder at all.”

FM-13 also localized the first measured broadening to BM25 candidate generation, while the more important end-to-end weakness was that later fusion/selection did not remove irrelevant candidates. This nuance matters:

```text
BROAD CANDIDATE GENERATION
≠
BROKEN CANDIDATE GENERATION
```

High-recall candidate generation is often desirable. The problem is only exposed when the next layer has no meaningful reject option.

That is why the next experiment did not immediately activate a runtime gate. The next question became:

> Maybe the problem is only the artificial deterministic embedding geometry. What happens if the candidate space uses a real semantic embedding model?

That question became FM-14.

---

## 4. FM-14: real embeddings improved geometry but did not solve rejection

FM-14 changed one major variable: deterministic embeddings were replaced by real local BGE embeddings while keeping the experiment bounded.

The result was intentionally not reduced to “embeddings good/bad.”

The important observation was:

- top relevant facts improved in ordering;
- Q1–Q3 ranking quality at the top was strong on the tiny fixture;
- lower-ranked noise remained;
- the Zephyr no-answer query still returned unrelated facts;
- its cosine similarities were still above the active similarity floor.

So FM-14 weakened one hypothesis:

```text
"The whole problem is just fake/deterministic embeddings"
```

Real semantic geometry helped, but did not create an honest rejection boundary in the active tested path.

This changed the research question again.

Instead of asking:

> “Are real embeddings better?”

we now needed to ask:

> “Does a stronger query↔fact pairwise scorer contain enough signal to distinguish a direct answer from a near miss or no-answer candidate?”

An additional subtlety emerged later: the FM-14 pairwise cosine matrix itself happened to be mathematically separable on the tiny fixture. That means it would be incorrect to retell FM-14 as “embeddings had no separability.” They did have a fixture-specific interval; what failed was the active search/fusion/filtering configuration.

This distinction became crucial when interpreting FM-15:

```text
NEW SEPARABILITY FROM CE
≠
ESTABLISHED
```

because embeddings already showed some tiny-fixture separability.

---

## 5. Donor audits: search for an existing mechanism before inventing one

Before creating a new “relevance subsystem,” the research deliberately looked across the Velantrim ecosystem and selected external systems for reusable patterns.

The goal was not to import their architecture wholesale. The goal was to answer:

> Does something already exist that can express broad candidates → qualification → reject-all / typed no-signal?

Several donor patterns were identified:

### Graphiti itself

Graphiti 0.29.3 already contains dormant mechanisms such as Cross-Encoder reranking, `reranker_min_score`, MMR variants and combined search recipes. This strongly weakened the idea that the first response should be a brand-new relevance module.

### Titan

Titan has useful gate shapes: selected/discarded candidates, thresholding, reasons, and typed no-signal patterns. But Titan’s trust/risk/goal-fit logic is orchestration policy, not semantic memory relevance authority.

### Crystal

Crystal contributed stronger evaluation discipline: hard negatives, no-recall-loss thinking, abstention tests and adversarial strata. But Crystal’s Canon/evidence admission rules are not a replacement for query relevance scoring.

### Native Kernel

Native Kernel reinforced semantic boundaries:

```text
RELEVANCE ≠ TRUTH
SIMILARITY ≠ EPISTEMIC VALIDITY
```

### SVL

SVL provided useful fail-closed applicability patterns and explicit UNKNOWN-style outcomes, but applicability is a different dimension from text relevance.

### OpenClaw / EITI

These systems were useful partly as negative examples. Broad candidate windows before filtering can be a good pattern, while lexical fallback / forced top-k after a rejection gate can destroy honest EMPTY.

The donor audit therefore produced a design discipline, not an integration plan:

```text
DONOR_REFERENCE
≠
ADOPTED_RUNTIME
```

The important conclusion at that stage was:

> First test the smallest missing mechanism using existing/local scorer capabilities. Do not create a new architectural organ before the evidence requires it.

That motivated FM-15.

---

## 6. FM-15: isolate the pairwise relevance signal

FM-15 intentionally did **not** activate the stock Graphiti Cross-Encoder search recipe.

Why? Because the stock recipe could change multiple things at once: candidate flow, truncation order, BFS/node effects and reranking. That would make it difficult to know which variable produced any improvement.

So FM-15 scored the frozen 20 query↔fact pairs directly with the local `BAAI/bge-reranker-v2-m3` model through the Graphiti BGE reranker client.

The primary question was deliberately narrow:

> Does a real local Cross-Encoder provide a useful pairwise query↔fact relevance signal on this tiny frozen fixture?

The answer was yes.

Examples:

```text
Q1: Who works on Project Orion?
F1 Alice works on Orion      ≈ 0.974169
next non-gold               ≈ 0.030276

Q2: What language does Orion use?
F2 Orion uses Python         ≈ 0.997204
next non-gold               ≈ 0.013468
```

The broad Nova query had much lower absolute relevant scores:

```text
Q3 relevant scores ≈ 0.049960 and 0.032244
```

The Zephyr no-answer candidates were lower:

```text
Q4 max ≈ 0.007880
```

This created a tiny-fixture separation interval for the **original FM-15 gold definition**.

But the correct conclusion was deliberately bounded:

```text
PAIRWISE_CE_SIGNAL = CONFIRMED_ON_FIXTURE
```

not:

```text
GLOBAL_THRESHOLD = SOLVED
```

not:

```text
CE > EMBEDDINGS IN GENERAL
```

and not:

```text
PRODUCTION_GATE_READY
```

The independent review also noted that comparing raw numeric margins between embedding cosine and CE sigmoid values is not methodologically sound because the score scales are different.

That is why the early “strongly improved” wording was downgraded. FM-15 proved a real pairwise signal, not general superiority.

---

## 7. Why FM-16 was proposed

FM-15 left the central practical question unresolved.

On four facts and a few queries, one can always observe a lucky gap. The real issue is whether an **absolute global threshold chosen without looking at the held-out test** can survive changes in entities, predicates, paraphrases, broad queries and adversarial near-misses.

So FM-16 was designed around a calibration/test split:

```text
CALIBRATION
→ choose threshold once
→ freeze/hash threshold

HELD-OUT TEST
→ apply it without retuning
```

The intended safeguards included:

- different entities in calibration and test;
- answerable and no-answer queries;
- hard-negative strata;
- CE versus embedding score families under the same calibration procedure;
- honest EMPTY;
- no forced refill;
- broad-query recall safety;
- explicit artifacts and receipts;
- no runtime activation.

At first glance this looked like the right next experiment.

Then independent pre-scoring review found that the protocol itself was not yet scientifically clean.

Stopping before scoring was therefore part of the research success, not a delay.

---

## 8. Astra review: the first FM-16 protocol had two fatal ambiguities

### 8.1 Relevance had been confused with positive entailment

The original adversarial design treated some negated candidates as hard negatives.

Example:

```text
Query: Does X support Y?
Fact:  X does NOT support Y.
```

For a yes/no information need, that fact is not irrelevant. It directly answers the question with polarity “NO.”

Therefore:

```text
RELEVANT ANSWER
≠
SUPPORTS POSITIVE PROPOSITION
```

This problem extends beyond negation.

A historical statement can be relevant or irrelevant depending on whether the query asks “currently” or asks for history. A conditional statement can answer a default-behavior question. A numeric statement on the opposite side of a threshold can still directly answer a yes/no threshold question.

The lesson was not “negation is always relevant.” The lesson was:

> Semantic phenomena such as polarity, time, scope, condition, attribution and numeric direction are **diagnostic dimensions**. They do not determine relevance by themselves. Relevance must be judged relative to the query’s information need.

### 8.2 The success criterion could reward an accept-all system

Astra constructed a counterexample where:

- every answerable query retained a gold item;
- every no-answer query produced EMPTY;
- no semantic inversion occurred;
- yet every answerable query retained all 40 candidates.

The old `GENERALIZATION_STRONG` rules could still pass this pathological system.

That exposed a missing requirement:

```text
HONEST EMPTY ON NO-ANSWER QUERIES
≠
GOOD FILTERING ON ANSWERABLE QUERIES
```

So strong success must include an explicit hard-negative rejection / returned-set quality gate.

A general non-gold rejection number is also insufficient if easy unrelated negatives dominate the denominator. The protocol must distinguish hard negatives from easy negatives.

Astra additionally required a clean infeasible-threshold branch, exact metric definitions before scoring, stronger model identity verification, leakage-safe ordering and explicit treatment of score failures.

---

## 9. Perplexity: confirmed the direction and the need to keep the experiment bounded

Perplexity largely reinforced Astra’s critique.

Its most useful contribution was not a new architecture idea, but confirmation that the research should remain focused on the existing missing obligation:

```text
broad candidates
→ relevance qualification
→ reject / retain
→ possible honest EMPTY
```

It also emphasized that a failure of a single global threshold would not automatically justify a new architectural subsystem. The correct next step is still to test the bounded hypothesis first.

This mattered because there was a temptation to jump from “RRF keeps noise” directly to “build a new relevance organ.” The combined donor evidence and Perplexity review argue against that jump.

---

## 10. Gemini: useful decomposition, but some suggested constants were too early

Gemini improved the proposed annotation structure by separating a primary relevance label from diagnostics such as polarity, temporal fit and scope fit.

That direction is retained.

However, two ideas were deliberately **not** accepted as fixed truth.

First, Gemini proposed a concrete hard-negative rejection floor such as `0.85`. The need for a floor is supported by Astra’s counterexample; the specific number is not yet justified.

Therefore:

```text
HARD_NEGATIVE_REJECTION_FLOOR
= TO_BE_PREREGISTERED WITH RATIONALE
```

Second, semantic classes such as negation or numeric contrast cannot be assigned universal relevance labels. A negated fact may directly answer one query and be irrelevant to another.

This reinforced a more general rule:

```text
DIAGNOSTIC PHENOMENON
≠
PRIMARY RELEVANCE LABEL
```

---

## 11. Claude Opus: Q5 exposed a deeper task-definition problem

Claude’s most important contribution was to revisit Q5:

```text
Does Alice use Python?
```

The small fixture contains:

```text
F1: Alice works on Orion
F2: Orion uses Python
```

Together these facts can support a multi-step inference. FM-15, however, explicitly did **not** label Q5 as direct-support gold. Its recorded status was essentially:

```text
DIRECT SUPPORT = false
CO-RETRIEVAL = yes
MULTI-HOP REASONING = not proven
```

Claude noticed that if a future FM-16 protocol silently changed the definition of relevance and promoted the second-hop component into primary gold, the tiny threshold gap already disappears.

The critical scores are:

```text
Q5 F2 Orion uses Python      = 0.005334
Q4 best Zephyr false         = 0.007880
```

If F2 must survive the threshold:

```text
θ <= 0.005334
```

If the best Zephyr false candidate must be rejected:

```text
θ > 0.007880
```

Both cannot be true.

This does **not** invalidate FM-15 under its original labels. It reveals that two different retrieval tasks had begun to blur together.

The mandatory distinction is now:

```text
DIRECT ANSWER
≠
MULTI-HOP / ANSWER-SUPPORT COMPONENT
≠
RELATED CONTEXT
```

This is arguably the most important conceptual refinement after Astra’s review.

A direct-answer relevance scorer asks:

> Does this candidate itself answer the information need?

A component-retrieval system asks:

> Is this candidate useful because, together with another fact, it enables an answer?

A related-context retriever asks something broader again:

> Is this fact associated with the subject even if it does not directly answer or complete a required inference?

Those are not interchangeable gold definitions.

---

## 12. Broad queries created another boundary

Q3 was intentionally broad:

```text
What is related to Project Nova?
```

The relevant CE scores were much lower than the narrow Q1/Q2 factoid scores.

That observation does not prove that broad queries cannot use a global threshold. But it shows why the hypothesis is nontrivial.

A narrow factoid query like:

```text
Who works on Nova?
```

has a much tighter information need than:

```text
What is related to Nova?
```

Therefore the research now explicitly distinguishes:

```text
NARROW FACTOID RELEVANCE
≠
BROAD ASSOCIATIVE RELEVANCE
```

The current decision is **not** to remove broad queries just because they make thresholding harder. They are scientifically valuable because they may falsify the idea that one scalar global threshold works across query classes.

But their gold semantics must be frozen explicitly before scoring. Otherwise “related” can expand after seeing scores, which would create evaluation leakage.

---

## 13. The global-threshold hypothesis is now separated from ranking quality

A major conceptual improvement is that FM-16 should no longer collapse two questions into one.

### H1 — Direct ranking

```text
Can the scorer rank direct answers above hard negatives on unseen data?
```

### H2 — Global absolute gate

```text
Can one threshold selected only on calibration data separate direct answers from non-answers across the held-out fixture while preserving recall and allowing honest EMPTY?
```

These hypotheses can have different outcomes.

For example:

```text
H1 = PASS
H2 = FAIL
```

would mean the Cross-Encoder is useful as a reranker but not stable enough to act as a single absolute gate.

That is a valuable result, not a failed experiment.

It would point toward later hypotheses such as query-conditioned margins, relation-aware features, uncertainty bands or multiple signals — but only **after** the simple global-threshold hypothesis is actually tested.

---

## 14. H3 is now explicitly separate: multi-hop component retention

The Q5 discussion created a third hypothesis:

### H3 — Component retrieval

```text
Can retrieval preserve facts that are not direct answers by themselves but are necessary components of a multi-hop/compositional answer?
```

The current decision is:

```text
FM-16 tests H1 + H2.
H3 remains separate.
```

This prevents the experiment from changing target halfway through.

A future H3 experiment may require different evaluation logic, because a useful component can have low direct query↔fact relevance while still being necessary after an intermediate entity is discovered.

That may eventually motivate staged retrieval, graph traversal, query decomposition or structured relation matching. But none of those are currently authorized by FM-15.

---

## 15. Why `threshold = null` is important

The hardened protocol must allow the possibility that no single calibration threshold satisfies the preregistered recall and rejection constraints.

If so:

```text
threshold = null
```

This is a scientific result.

The experiment must not “pick the closest threshold” or loosen constraints after seeing the failure. That would convert preregistration into post-hoc tuning.

Thresholded held-out metrics should then be:

```text
NOT_APPLICABLE
```

However, once the null decision is frozen and hashed, threshold-free held-out ranking analysis can still be useful.

This distinction lets the experiment report something like:

```text
PAIRWISE RANKING GENERALIZES
BUT
ONE GLOBAL ABSOLUTE GATE IS NOT FEASIBLE
```

without inventing a fallback threshold.

---

## 16. Why the larger negative set matters, but is not proof in advance

Claude also pointed out a statistical intuition: as the number and diversity of negative candidates grows, the maximum negative score has more opportunities to become large.

The tiny FM-15 interval is therefore fragile. Moving from four candidates to hundreds of query×negative comparisons can expose a high-scoring near miss even if average discrimination remains strong.

This is a useful preregistered prediction:

```text
GLOBAL THRESHOLD FRAGILITY
= PLAUSIBLE HYPOTHESIS
```

but it is not yet evidence that FM-16 must fail.

The held-out distributions still need to be measured. The correct protocol should therefore retain full score distributions, hard-negative strata and per-query margins rather than reducing everything to one `min positive / max negative` number.

---

## 17. Model identity and reproducibility

FM-15 used a local reranker with model revision and weight hash recorded. The hardened FM-16 should strengthen this by verifying the actually loaded snapshot, tokenizer/config and inference profile, not merely trusting a cached revision string.

Historical DeepSeek extraction is a separate reproducibility concern because a remote provider can change behavior under the same model name.

For FM-16, however, the planned design avoids rerunning extraction. It uses a frozen deterministic textual corpus. Therefore:

```text
REMOTE DEEPSEEK IDENTITY
= HISTORICAL PROVENANCE CONCERN
```

not:

```text
FM-16 BLOCKER
```

The active FM-16 identity controls should focus on the actual CE and embedding snapshots and inference environment.

---

## 18. What the research is *not* allowed to conclude yet

Even a successful hardened FM-16 would remain a bounded synthetic held-out result.

It would not establish:

- production readiness;
- universal multilingual relevance calibration;
- correctness on arbitrary real-user memory distributions;
- temporal truth;
- belief validity;
- Canon admission;
- permission;
- multi-hop reasoning;
- Neo4j parity;
- end-to-end Fractal runtime benefit;
- latency/cost acceptability at production scale.

The candidate score remains a query-relevance signal, not an epistemic authority.

```text
RELEVANCE SCORE
≠
TRUTH
≠
EVIDENCE
≠
BELIEF
≠
CANON
≠
PERMISSION
```

---

## 19. Current scientific map

The research line can now be summarized without losing the reasoning chain:

```text
PERSISTENCE / TEMPORAL / PROVENANCE WORK
        ↓
retrieval plumbing works in bounded lab scopes
        ↓
ZEHPYR NEGATIVE CONTROL
search returns something even when nothing answers the query
        ↓
FM-13
instrument the active path
→ BM25 broadens candidates
→ RRF preserves noise
→ CE object existed but was not called
        ↓
FM-14
replace deterministic embeddings with real BGE
→ ranking geometry improves
→ honest EMPTY still absent
        ↓
DONOR AUDITS
Graphiti already has dormant CE/min-score machinery
Titan/Crystal/SVL/etc. offer gate/eval patterns
→ no justification yet for a new relevance organ
        ↓
FM-15
score frozen query↔fact pairs directly with real local CE
→ useful pairwise signal confirmed on tiny fixture
→ CE superiority/global threshold/generalization not established
        ↓
FM-16 v1 DESIGN
held-out calibration + adversarial negatives
        ↓
ASTRA PRE-SCORING REVIEW
→ relevance ≠ positive entailment
→ strong criterion allowed accept-all pathology
→ stop before scoring
        ↓
PERPLEXITY
confirms bounded relevance/EMPTY direction
        ↓
GEMINI
useful label/metric decomposition
but arbitrary 0.85 not adopted
        ↓
CLAUDE OPUS
Q5 exposes task-definition conflict
→ direct answer ≠ multi-hop component ≠ related context
→ broad queries may occupy different score regime
        ↓
FM-16 HARDENED — NEXT
H1 direct ranking + H2 global gate
H3 multi-hop component retrieval remains separate
```

---

## 20. Current next action and stop boundary

The next action is **not** to run the old FM-16 draft.

The next action is to finalize a hardened preregistration-ready FM-16 protocol with:

1. primary evaluation gold = direct-answer relevance;
2. explicit distinction between direct answer, multi-hop component and related context;
3. broad-query gold frozen before scoring;
4. qualifier diagnostics for polarity/temporal/scope/condition/attribution/numeric relation;
5. explicit hard-negative rejection / returned-set quality criteria;
6. justified preregistered numeric floors rather than arbitrary constants;
7. exact metric formulas, denominators, ties and comparator;
8. exact verdict precedence;
9. strict model identity verification;
10. calibration-only threshold selection;
11. `threshold = null` if infeasible;
12. threshold-free held-out ranking analysis still permitted after null is frozen;
13. no forced refill;
14. no runtime activation;
15. no architecture promotion.

After FM-16 executes, stop for independent review before proposing any runtime gate.

```text
HARDEN PROTOCOL
→ PREREGISTER
→ CALIBRATE
→ FREEZE THRESHOLD / NULL
→ HELD-OUT TEST
→ INDEPENDENT REVIEW
→ ONLY THEN DISCUSS NEXT LAYER
```

---

## 21. Final commentary for future reviewers

The central lesson of this research line is not “Cross-Encoder wins.”

The lesson is that a retrieval system needs more than an ordering function if it is expected to return nothing when nothing is good enough. But the moment we introduce a reject boundary, the definition of “good enough” becomes the scientific problem.

A direct negative answer may be highly relevant. A historically true statement may be irrelevant to a “current” query. A multi-hop component may be necessary for an answer while scoring poorly against the original query. A broad associative query may legitimately accept many candidates that a narrow factoid query should reject.

Therefore the research cannot be reduced to “find a threshold.”

The real progression is:

```text
WHAT DOES THE QUERY NEED?
        ↓
WHAT KIND OF CANDIDATE COUNTS AS AN ANSWER?
        ↓
CAN A SCORER ORDER THOSE CANDIDATES?
        ↓
CAN ONE ABSOLUTE THRESHOLD GENERALIZE?
        ↓
IF NOT, WHAT SPECIFIC FAILURE MODE REMAINS?
```

Only after those questions are separated can the project decide whether the existing Graphiti machinery is sufficient, whether a query-conditioned gate is needed, or whether structured graph-aware retrieval should be tested.

Until then:

```text
NO NEW RELEVANCE MODULE
NO RUNTIME ACTIVATION
NO PRODUCTION THRESHOLD
NO ARCHITECTURAL PROMOTION
```

The current frontier is methodological: define FM-16 cleanly enough that whatever result it produces — strong, partial, null-threshold, ranking-only, or failure — will actually mean something.
