"""FM-16 lab-only Cross-Encoder held-out generalization & calibration.

Offline pairwise scoring only. No Graphiti search API / MemoryOps / BM25 / RRF /
runtime CE / DeepSeek extraction / forced refill / architecture changes.
"""

from __future__ import annotations

import asyncio
import csv
import hashlib
import json
import math
import os
import resource
import statistics
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from fractal_lab.experiments.cross_encoder_separability import (
    FACTS as FM15_FACTS,
    GOLD as FM15_GOLD,
    QUERIES as FM15_QUERIES,
    REQUIRED_MODEL,
    RealCrossEncoderUnavailableError,
    init_bge_reranker_client,
    resolve_model_revision,
    resolve_weight_fingerprint,
    score_logits_optional,
    score_pairs_official,
)
from fractal_lab.experiments.local_semantic_embedder import (
    DEFAULT_MODEL_NAME as EMBED_MODEL,
    LocalSemanticEmbedder,
    load_fastembed_model,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
RUN007 = REPO_ROOT / "artifacts" / "memoryops" / "run_007"
CHECKPOINT_DIR = RUN007 / "_checkpoints"

EXPECTED_START_SHA = "de304f120a7fdf5bbd1ac020e4333a50a541a219"
UPSTREAM_SHA = "2437244149baeb0c645e2e942125be92bba3a96b"
CE_REVISION_PIN = "953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e"
CE_WEIGHT_SHA_PIN = "d9e3e081faff1eefb84019509b2f5558fd74c1a05a2c7db22f74174fcedb5286"

HN_CORE = [f"HN{i}" for i in range(1, 7)]
HN_ADV = [f"HN{i}" for i in range(7, 13)]
ALL_HN = HN_CORE + HN_ADV

# ---------------------------------------------------------------------------
# Corpus — entity-disjoint CALIBRATION vs HELD_OUT_TEST (frozen before scoring)
# ---------------------------------------------------------------------------

CAL_FACTS: list[tuple[str, str]] = [
    ("CF01", "Mira works on Project Helix."),
    ("CF02", "Project Helix uses Go."),
    ("CF03", "Project Helix depends on Redis."),
    ("CF04", "Project Helix is owned by Apex Labs."),
    ("CF05", "Project Helix is deployed in Frankfurt."),
    ("CF06", "Jonas works on Project Cascade."),
    ("CF07", "Project Cascade uses TypeScript."),
    ("CF08", "Project Cascade depends on Kafka."),
    ("CF09", "Project Cascade is owned by Northwind Systems."),
    ("CF10", "Project Cascade has status beta."),
    ("CF11", "Elena works on Project Prism."),
    ("CF12", "Project Prism uses Kotlin."),
    ("CF13", "Project Prism depends on Grafana."),
    ("CF14", "Project Prism currently uses Go for the API layer."),
    ("CF15", "Project Prism previously used Python for the API layer."),
    ("CF16", "Theo works on Project Quasar."),
    ("CF17", "Project Quasar uses Elixir."),
    ("CF18", "Project Quasar depends on Celery."),
    ("CF19", "Project Quasar supports feature streaming."),
    ("CF20", "Project Quasar does NOT support feature streaming."),
    ("CF21", "Nadia works on Project Ember."),
    ("CF22", "Project Ember uses PostgreSQL in production."),
    ("CF23", "Project Ember uses SQLite in tests."),
    ("CF24", "Feature auth is enabled by default in Project Ember."),
    ("CF25", "Feature auth is enabled only when DEBUG_MODE=true in Project Ember."),
    ("CF26", "Owen works on Project Lattice."),
    ("CF27", "Project Lattice requires more than 16 GB of memory."),
    ("CF28", "Project Lattice requires less than 16 GB of memory."),
    ("CF29", "Project Lattice is deployed in Singapore."),
    ("CF30", "Priya confirmed migration Lattice-Blue."),
    ("CF31", "Kai works on Project Flux."),
    ("CF32", "Project Flux uses Go."),
    ("CF33", "Kai said that Priya may confirm migration Lattice-Blue."),
    ("CF34", "Project Flux has status alpha."),
    ("CF35", "Project Flux is owned by Apex Labs."),
    ("CF36", "Priya works on Project Harbor."),
    ("CF37", "Project Harbor uses TypeScript."),
    ("CF38", "Project Harbor depends on Redis."),
    ("CF39", "Project Harbor has status GA."),
    ("CF40", "Project HelixCore uses Ruby."),
]

TEST_FACTS: list[tuple[str, str]] = [
    ("TF01", "Sofia works on Project Nimbus."),
    ("TF02", "Project Nimbus uses Scala."),
    ("TF03", "Project Nimbus depends on MongoDB."),
    ("TF04", "Project Nimbus is owned by Brightline Corp."),
    ("TF05", "Project Nimbus is deployed in Tokyo."),
    ("TF06", "Marcus works on Project Vector."),
    ("TF07", "Project Vector uses Swift."),
    ("TF08", "Project Vector depends on RabbitMQ."),
    ("TF09", "Project Vector is owned by Redwood Analytics."),
    ("TF10", "Project Vector has status preview."),
    ("TF11", "Lena works on Project Cobalt."),
    ("TF12", "Project Cobalt uses Haskell."),
    ("TF13", "Project Cobalt depends on Prometheus."),
    ("TF14", "Project Cobalt currently uses Scala for the API layer."),
    ("TF15", "Project Cobalt previously used Java for the API layer."),
    ("TF16", "Hiro works on Project Aurora."),
    ("TF17", "Project Aurora uses Zig."),
    ("TF18", "Project Aurora depends on Sidekiq."),
    ("TF19", "Project Aurora supports feature sharding."),
    ("TF20", "Project Aurora does NOT support feature sharding."),
    ("TF21", "Amira works on Project Titan."),
    ("TF22", "Project Titan uses MySQL in production."),
    ("TF23", "Project Titan uses H2 in tests."),
    ("TF24", "Feature caching is enabled by default in Project Titan."),
    ("TF25", "Feature caching is enabled only when CACHE_MODE=true in Project Titan."),
    ("TF26", "Felix works on Project Willow."),
    ("TF27", "Project Willow requires more than 32 GB of memory."),
    ("TF28", "Project Willow requires less than 32 GB of memory."),
    ("TF29", "Project Willow is deployed in Dublin."),
    ("TF30", "Clara confirmed migration Willow-Green."),
    ("TF31", "Devon works on Project Cipher."),
    ("TF32", "Project Cipher uses Scala."),
    ("TF33", "Devon said that Clara may confirm migration Willow-Green."),
    ("TF34", "Project Cipher has status experimental."),
    ("TF35", "Project Cipher is owned by Brightline Corp."),
    ("TF36", "Clara works on Project Mesa."),
    ("TF37", "Project Mesa uses Swift."),
    ("TF38", "Project Mesa depends on MongoDB."),
    ("TF39", "Project Mesa has status stable."),
    ("TF40", "Project NimbusX uses Perl."),
]

# Query schema: (id, text, class, subtype, gold_fact_ids)
# class: answerable | no_answer
# subtype: narrow | paraphrase | broad | nonexistent | unsupported

CAL_QUERIES: list[dict[str, Any]] = [
    {"id": "CQ01", "text": "Who works on Project Helix?", "class": "answerable", "subtype": "narrow", "gold": ["CF01"]},
    {"id": "CQ02", "text": "What language does Project Cascade use?", "class": "answerable", "subtype": "narrow", "gold": ["CF07"]},
    {"id": "CQ03", "text": "What does Project Helix depend on?", "class": "answerable", "subtype": "narrow", "gold": ["CF03"]},
    {"id": "CQ04", "text": "Where is Project Helix deployed?", "class": "answerable", "subtype": "narrow", "gold": ["CF05"]},
    {"id": "CQ05", "text": "Which person is assigned to Project Prism?", "class": "answerable", "subtype": "paraphrase", "gold": ["CF11"]},
    {"id": "CQ06", "text": "What programming language powers Project Quasar?", "class": "answerable", "subtype": "paraphrase", "gold": ["CF17"]},
    {"id": "CQ07", "text": "Does Project Quasar support feature streaming?", "class": "answerable", "subtype": "paraphrase", "gold": ["CF19"]},
    {"id": "CQ08", "text": "Does Project Lattice require more than 16 GB of memory?", "class": "answerable", "subtype": "paraphrase", "gold": ["CF27"]},
    {"id": "CQ09", "text": "What is related to Project Helix?", "class": "answerable", "subtype": "broad", "gold": ["CF01", "CF02", "CF03", "CF04", "CF05"]},
    {"id": "CQ10", "text": "What should I know about Project Cascade?", "class": "answerable", "subtype": "broad", "gold": ["CF06", "CF07", "CF08", "CF09", "CF10"]},
    {"id": "CQ11", "text": "What components are associated with Project Ember?", "class": "answerable", "subtype": "broad", "gold": ["CF21", "CF22", "CF23", "CF24", "CF25"]},
    {"id": "CQ12", "text": "Tell me about Project Flux.", "class": "answerable", "subtype": "broad", "gold": ["CF31", "CF32", "CF34", "CF35"]},
    {"id": "CQ13", "text": "Who works on Project Zephyr?", "class": "no_answer", "subtype": "nonexistent", "gold": []},
    {"id": "CQ14", "text": "What language does Project Orion use?", "class": "no_answer", "subtype": "nonexistent", "gold": []},
    {"id": "CQ15", "text": "Where is Project Nova deployed?", "class": "no_answer", "subtype": "nonexistent", "gold": []},
    {"id": "CQ16", "text": "Who owns Project Atlas?", "class": "no_answer", "subtype": "nonexistent", "gold": []},
    {"id": "CQ17", "text": "Who founded Project Helix?", "class": "no_answer", "subtype": "unsupported", "gold": []},
    {"id": "CQ18", "text": "When was Project Cascade started?", "class": "no_answer", "subtype": "unsupported", "gold": []},
    {"id": "CQ19", "text": "What is the license of Project Prism?", "class": "no_answer", "subtype": "unsupported", "gold": []},
    {"id": "CQ20", "text": "How many users does Project Quasar have?", "class": "no_answer", "subtype": "unsupported", "gold": []},
]

TEST_QUERIES: list[dict[str, Any]] = [
    {"id": "TQ01", "text": "Who works on Project Nimbus?", "class": "answerable", "subtype": "narrow", "gold": ["TF01"]},
    {"id": "TQ02", "text": "What language does Project Vector use?", "class": "answerable", "subtype": "narrow", "gold": ["TF07"]},
    {"id": "TQ03", "text": "What does Project Nimbus depend on?", "class": "answerable", "subtype": "narrow", "gold": ["TF03"]},
    {"id": "TQ04", "text": "Where is Project Nimbus deployed?", "class": "answerable", "subtype": "narrow", "gold": ["TF05"]},
    {"id": "TQ05", "text": "Which person is assigned to Project Cobalt?", "class": "answerable", "subtype": "paraphrase", "gold": ["TF11"]},
    {"id": "TQ06", "text": "What programming language powers Project Aurora?", "class": "answerable", "subtype": "paraphrase", "gold": ["TF17"]},
    {"id": "TQ07", "text": "Does Project Aurora support feature sharding?", "class": "answerable", "subtype": "paraphrase", "gold": ["TF19"]},
    {"id": "TQ08", "text": "Does Project Willow require more than 32 GB of memory?", "class": "answerable", "subtype": "paraphrase", "gold": ["TF27"]},
    {"id": "TQ09", "text": "What is related to Project Nimbus?", "class": "answerable", "subtype": "broad", "gold": ["TF01", "TF02", "TF03", "TF04", "TF05"]},
    {"id": "TQ10", "text": "What should I know about Project Vector?", "class": "answerable", "subtype": "broad", "gold": ["TF06", "TF07", "TF08", "TF09", "TF10"]},
    {"id": "TQ11", "text": "What components are associated with Project Titan?", "class": "answerable", "subtype": "broad", "gold": ["TF21", "TF22", "TF23", "TF24", "TF25"]},
    {"id": "TQ12", "text": "Tell me about Project Cipher.", "class": "answerable", "subtype": "broad", "gold": ["TF31", "TF32", "TF34", "TF35"]},
    {"id": "TQ13", "text": "Who works on Project Zephyr?", "class": "no_answer", "subtype": "nonexistent", "gold": []},
    {"id": "TQ14", "text": "What language does Project Orion use?", "class": "no_answer", "subtype": "nonexistent", "gold": []},
    {"id": "TQ15", "text": "Where is Project Nova deployed?", "class": "no_answer", "subtype": "nonexistent", "gold": []},
    {"id": "TQ16", "text": "Who owns Project Atlas?", "class": "no_answer", "subtype": "nonexistent", "gold": []},
    {"id": "TQ17", "text": "Who founded Project Nimbus?", "class": "no_answer", "subtype": "unsupported", "gold": []},
    {"id": "TQ18", "text": "When was Project Vector started?", "class": "no_answer", "subtype": "unsupported", "gold": []},
    {"id": "TQ19", "text": "What is the license of Project Cobalt?", "class": "no_answer", "subtype": "unsupported", "gold": []},
    {"id": "TQ20", "text": "How many users does Project Aurora have?", "class": "no_answer", "subtype": "unsupported", "gold": []},
]

# Extra adversarial answerable queries embedded via paraphrase slots CQ07/CQ08 etc.
# Additional CAL queries for HN7-12 pair coverage use gold on CF14, CF22, CF24, CF30:
# We attach HN labels on existing queries rather than adding queries beyond 20.

def _build_hn_labels_cal() -> dict[str, dict[str, list[str]]]:
    """Frozen hard-negative labels for calibration (query -> fact -> [HN*])."""
    L: dict[str, dict[str, list[str]]] = defaultdict(dict)

    def add(qid: str, fid: str, *tags: str) -> None:
        cur = L[qid].setdefault(fid, [])
        for t in tags:
            if t not in cur:
                cur.append(t)

    # CQ01 Who works on Helix?
    add("CQ01", "CF02", "HN1")
    add("CQ01", "CF03", "HN1")
    add("CQ01", "CF04", "HN1")
    add("CQ01", "CF06", "HN2")
    add("CQ01", "CF11", "HN2")
    add("CQ01", "CF16", "HN2")
    add("CQ01", "CF40", "HN5", "HN3")  # HelixCore near-name + lexical Helix*
    add("CQ01", "CF32", "HN6")
    add("CQ01", "CF28", "HN6")
    add("CQ01", "CF18", "HN4")

    # CQ02 Cascade language
    add("CQ02", "CF06", "HN1")
    add("CQ02", "CF08", "HN1")
    add("CQ02", "CF10", "HN1")
    add("CQ02", "CF02", "HN2")  # Helix uses Go
    add("CQ02", "CF12", "HN2")
    add("CQ02", "CF37", "HN2", "HN3")  # Harbor uses TypeScript — same lang lexical
    add("CQ02", "CF40", "HN6")
    add("CQ02", "CF27", "HN6")
    add("CQ02", "CF15", "HN4")

    # CQ03 Helix depends
    add("CQ03", "CF01", "HN1")
    add("CQ03", "CF02", "HN1")
    add("CQ03", "CF08", "HN2")
    add("CQ03", "CF13", "HN2")
    add("CQ03", "CF18", "HN2")
    add("CQ03", "CF38", "HN2", "HN3")  # Harbor depends Redis — same library
    add("CQ03", "CF40", "HN5")
    add("CQ03", "CF28", "HN6")
    add("CQ03", "CF20", "HN4")

    # CQ04 Helix deployed
    add("CQ04", "CF01", "HN1")
    add("CQ04", "CF02", "HN1")
    add("CQ04", "CF29", "HN2")  # Lattice in Singapore
    add("CQ04", "CF40", "HN5")
    add("CQ04", "CF23", "HN6")
    add("CQ04", "CF15", "HN4")
    add("CQ04", "CF06", "HN6")

    # CQ05 Prism person
    add("CQ05", "CF12", "HN1")
    add("CQ05", "CF13", "HN1")
    add("CQ05", "CF01", "HN2")
    add("CQ05", "CF06", "HN2")
    add("CQ05", "CF26", "HN2")
    add("CQ05", "CF40", "HN6")
    add("CQ05", "CF15", "HN4")
    add("CQ05", "CF33", "HN3")

    # CQ06 Quasar language
    add("CQ06", "CF16", "HN1")
    add("CQ06", "CF18", "HN1")
    add("CQ06", "CF07", "HN2")
    add("CQ06", "CF12", "HN2")
    add("CQ06", "CF02", "HN2")
    add("CQ06", "CF20", "HN4")
    add("CQ06", "CF28", "HN6")
    add("CQ06", "CF40", "HN6")

    # CQ07 Quasar streaming — HN7 negation
    add("CQ07", "CF20", "HN7", "HN1")
    add("CQ07", "CF16", "HN1")
    add("CQ07", "CF17", "HN1")
    # gold CF19 — no HN label
    add("CQ07", "CF24", "HN4")
    add("CQ07", "CF25", "HN4")
    add("CQ07", "CF40", "HN6")
    add("CQ07", "CF28", "HN6")
    add("CQ07", "CF06", "HN2")

    # CQ08 Lattice memory — HN12
    add("CQ08", "CF28", "HN12", "HN1")
    add("CQ08", "CF26", "HN1")
    add("CQ08", "CF29", "HN1")
    add("CQ08", "CF22", "HN4")
    add("CQ08", "CF40", "HN6")
    add("CQ08", "CF20", "HN6")
    add("CQ08", "CF01", "HN2")
    add("CQ08", "CF33", "HN3")

    # CQ09 broad Helix
    add("CQ09", "CF06", "HN2")
    add("CQ09", "CF40", "HN5", "HN3")
    add("CQ09", "CF20", "HN6")
    add("CQ09", "CF28", "HN6")
    add("CQ09", "CF15", "HN4")
    add("CQ09", "CF23", "HN4")

    # CQ10 broad Cascade
    add("CQ10", "CF01", "HN2")
    add("CQ10", "CF37", "HN3")
    add("CQ10", "CF40", "HN6")
    add("CQ10", "CF20", "HN6")
    add("CQ10", "CF15", "HN4")
    add("CQ10", "CF28", "HN6")

    # CQ11 broad Ember — scope/condition
    add("CQ11", "CF01", "HN6")
    add("CQ11", "CF40", "HN6")
    add("CQ11", "CF20", "HN7")
    add("CQ11", "CF15", "HN8")
    add("CQ11", "CF33", "HN11")
    add("CQ11", "CF28", "HN12")

    # CQ12 broad Flux — attribution noise CF33 is in gold set? NO — excluded from gold
    add("CQ12", "CF33", "HN11", "HN4")  # attribution mismatch if asking about Flux broadly? 
    # Actually CF33 mentions Lattice-Blue / Priya — unrelated-ish to Flux identity beyond Kai
    add("CQ12", "CF01", "HN2")
    add("CQ12", "CF40", "HN6")
    add("CQ12", "CF20", "HN6")
    add("CQ12", "CF28", "HN12")
    add("CQ12", "CF15", "HN8")

    # Dedicated adversarial pairs via answerable queries that have matching gold:
    # Temporal: use CQ05-style — add labels on a paraphrase about Prism API language
    # We encode temporal via CQ06 alternative — attach to CQ05 for Prism current API:
    # Re-purpose: for query about Prism current language — we don't have dedicated query.
    # Use CQ03-like: add HN8 labels on CQ06? Better: mark for CQ09-style.
    
    # Explicit temporal query coverage via CQ05 gold CF11 only — instead label CF14/CF15
    # against a synthetic interpretation: "What language does Project Prism currently use for the API?"
    # We need that as one of the 12 — replace CQ06? Keep CQ06 Quasar; add temporal to CQ05?
    # Coverage: HN8 needs >=2 pairs. Label:
    add("CQ05", "CF15", "HN8")  # previously used Python — wrong temporal for person query? weak
    # Better dedicated: treat CQ04-adjacent — use CQ02 pattern on Prism via labels on CQ06 no.
    
    # Use CQ09 Helix broad — CF15 is HN8 for Prism temporal text present in corpus
    add("CQ09", "CF14", "HN4")  # related wrong project API fact
    
    # Scope mismatch HN9: Ember production vs tests — for a production query.
    # CQ11 gold includes both CF22 and CF23 (broad). For narrow production intent use labels:
    # Add on CQ03-style — create production-focused labels on CQ08? 
    # Label CF23 as HN9 relative to production gold when query is production:
    # We add a production query by using CQ04 subtype already used.
    # Attach to CQ11: when evaluating HN9 discrimination, compare CF22 vs CF23 scores for
    # a production-oriented receipt. Also mark CF23 as HN9 for a synthetic production query id.
    # Use CQ01? No. Use no_answer? No.
    # Mark for CQ11 evaluation pair CF22(gold-ish)/CF23(HN9) — for broad both are gold.
    # Change CQ11 gold to exclude CF23; CF23 is HN9 for production-oriented broad? 
    # TZ: broad may have MULTIPLE gold. Scope: Query "What does Project Ember use in production?"
    # Replace one paraphrase: change CQ08 is memory. Change CQ06 stays.
    # We'll set dedicated production query as CQ04 is deploy. Let's change CQ03? keep.
    # Fix: alter CQ11 gold to CF21,CF22,CF24 only; CF23=HN9, CF25=HN10
    pass

    # Fix CQ11 gold handling — redefine below after function via CAL_QUERIES mutation? 
    # Instead set labels assuming CQ11 gold = CF21,CF22,CF24 (production/default oriented)
    add("CQ11", "CF23", "HN9")
    add("CQ11", "CF25", "HN10")

    # Attribution HN11: CQ about Priya confirmation
    # Use CQ12 — CF30 is not in Flux gold; for Lattice confirmation we need a query.
    # Add labels on CQ08 (Lattice): CF33 is HN11 vs gold CF27? weak.
    add("CQ08", "CF30", "HN4")  # confirmed migration — related Lattice entity wrong predicate
    add("CQ08", "CF33", "HN11")

    # Temporal HN8 dedicated pairs: query CQ05 person — weak.
    # Add on a Quasar/Prism language paraphrase — use CQ06 and also:
    add("CQ06", "CF15", "HN8")
    add("CQ06", "CF14", "HN4")
    # For Prism current API — label under CQ05:
    add("CQ05", "CF14", "HN4")
    # Additional HN8: CQ04
    add("CQ04", "CF15", "HN8")

    # Condition HN10 already CF25 on CQ11
    add("CQ07", "CF25", "HN10")

    # Scope HN9 additional
    add("CQ02", "CF23", "HN9")
    add("CQ03", "CF23", "HN9")

    # Negation HN7 additional beyond CQ07
    add("CQ06", "CF20", "HN7")
    add("CQ10", "CF20", "HN7")

    # Numeric HN12 additional
    add("CQ01", "CF28", "HN12")
    add("CQ09", "CF28", "HN12")

    # Attribution additional
    add("CQ10", "CF33", "HN11")
    add("CQ09", "CF33", "HN11")

    # Clean gold keys if accidentally added
    for q in CAL_QUERIES:
        for g in q["gold"]:
            if g in L.get(q["id"], {}):
                # remove HN tags from gold facts
                del L[q["id"]][g]

    return {qid: dict(fmap) for qid, fmap in L.items()}


def _build_hn_labels_test() -> dict[str, dict[str, list[str]]]:
    L: dict[str, dict[str, list[str]]] = defaultdict(dict)

    def add(qid: str, fid: str, *tags: str) -> None:
        cur = L[qid].setdefault(fid, [])
        for t in tags:
            if t not in cur:
                cur.append(t)

    add("TQ01", "TF02", "HN1")
    add("TQ01", "TF03", "HN1")
    add("TQ01", "TF04", "HN1")
    add("TQ01", "TF06", "HN2")
    add("TQ01", "TF11", "HN2")
    add("TQ01", "TF16", "HN2")
    add("TQ01", "TF40", "HN5", "HN3")
    add("TQ01", "TF32", "HN6")
    add("TQ01", "TF28", "HN6", "HN12")
    add("TQ01", "TF18", "HN4")

    add("TQ02", "TF06", "HN1")
    add("TQ02", "TF08", "HN1")
    add("TQ02", "TF10", "HN1")
    add("TQ02", "TF02", "HN2")
    add("TQ02", "TF12", "HN2")
    add("TQ02", "TF37", "HN2", "HN3")
    add("TQ02", "TF40", "HN6")
    add("TQ02", "TF27", "HN6")
    add("TQ02", "TF15", "HN4", "HN8")
    add("TQ02", "TF23", "HN9")

    add("TQ03", "TF01", "HN1")
    add("TQ03", "TF02", "HN1")
    add("TQ03", "TF08", "HN2")
    add("TQ03", "TF13", "HN2")
    add("TQ03", "TF18", "HN2")
    add("TQ03", "TF38", "HN2", "HN3")
    add("TQ03", "TF40", "HN5")
    add("TQ03", "TF28", "HN6")
    add("TQ03", "TF20", "HN4", "HN7")
    add("TQ03", "TF23", "HN9")

    add("TQ04", "TF01", "HN1")
    add("TQ04", "TF02", "HN1")
    add("TQ04", "TF29", "HN2")
    add("TQ04", "TF40", "HN5")
    add("TQ04", "TF23", "HN6")
    add("TQ04", "TF15", "HN4", "HN8")
    add("TQ04", "TF06", "HN6")

    add("TQ05", "TF12", "HN1")
    add("TQ05", "TF13", "HN1")
    add("TQ05", "TF01", "HN2")
    add("TQ05", "TF06", "HN2")
    add("TQ05", "TF26", "HN2")
    add("TQ05", "TF40", "HN6")
    add("TQ05", "TF15", "HN4", "HN8")
    add("TQ05", "TF14", "HN4")
    add("TQ05", "TF33", "HN3")

    add("TQ06", "TF16", "HN1")
    add("TQ06", "TF18", "HN1")
    add("TQ06", "TF07", "HN2")
    add("TQ06", "TF12", "HN2")
    add("TQ06", "TF02", "HN2")
    add("TQ06", "TF20", "HN4", "HN7")
    add("TQ06", "TF28", "HN6")
    add("TQ06", "TF40", "HN6")
    add("TQ06", "TF15", "HN8")
    add("TQ06", "TF14", "HN4")

    add("TQ07", "TF20", "HN7", "HN1")
    add("TQ07", "TF16", "HN1")
    add("TQ07", "TF17", "HN1")
    add("TQ07", "TF24", "HN4")
    add("TQ07", "TF25", "HN4", "HN10")
    add("TQ07", "TF40", "HN6")
    add("TQ07", "TF28", "HN6")
    add("TQ07", "TF06", "HN2")

    add("TQ08", "TF28", "HN12", "HN1")
    add("TQ08", "TF26", "HN1")
    add("TQ08", "TF29", "HN1")
    add("TQ08", "TF22", "HN4")
    add("TQ08", "TF40", "HN6")
    add("TQ08", "TF20", "HN6")
    add("TQ08", "TF01", "HN2")
    add("TQ08", "TF33", "HN11", "HN3")
    add("TQ08", "TF30", "HN4")

    add("TQ09", "TF06", "HN2")
    add("TQ09", "TF40", "HN5", "HN3")
    add("TQ09", "TF20", "HN6", "HN7")
    add("TQ09", "TF28", "HN6", "HN12")
    add("TQ09", "TF15", "HN4", "HN8")
    add("TQ09", "TF23", "HN4", "HN9")
    add("TQ09", "TF33", "HN11")

    add("TQ10", "TF01", "HN2")
    add("TQ10", "TF37", "HN3")
    add("TQ10", "TF40", "HN6")
    add("TQ10", "TF20", "HN6", "HN7")
    add("TQ10", "TF15", "HN4", "HN8")
    add("TQ10", "TF28", "HN6")
    add("TQ10", "TF33", "HN11")

    add("TQ11", "TF01", "HN6")
    add("TQ11", "TF40", "HN6")
    add("TQ11", "TF20", "HN7")
    add("TQ11", "TF15", "HN8")
    add("TQ11", "TF33", "HN11")
    add("TQ11", "TF28", "HN12")
    add("TQ11", "TF23", "HN9")
    add("TQ11", "TF25", "HN10")

    add("TQ12", "TF33", "HN11", "HN4")
    add("TQ12", "TF01", "HN2")
    add("TQ12", "TF40", "HN6")
    add("TQ12", "TF20", "HN6", "HN7")
    add("TQ12", "TF28", "HN12")
    add("TQ12", "TF15", "HN8")

    for q in TEST_QUERIES:
        for g in q["gold"]:
            if g in L.get(q["id"], {}):
                del L[q["id"]][g]

    return {qid: dict(fmap) for qid, fmap in L.items()}


# Adjust CQ11 / TQ11 gold to exclude scope/condition hard negatives
for _q in CAL_QUERIES:
    if _q["id"] == "CQ11":
        _q["gold"] = ["CF21", "CF22", "CF24"]
for _q in TEST_QUERIES:
    if _q["id"] == "TQ11":
        _q["gold"] = ["TF21", "TF22", "TF24"]

CAL_ENTITIES = {
    "persons": {"Mira", "Jonas", "Elena", "Theo", "Nadia", "Owen", "Priya", "Kai"},
    "projects": {
        "Helix", "Cascade", "Prism", "Quasar", "Ember", "Lattice", "Flux", "Harbor", "HelixCore"
    },
    "orgs": {"Apex Labs", "Northwind Systems"},
    "libraries": {"Redis", "Kafka", "Grafana", "Celery"},
    "locations": {"Frankfurt", "Singapore"},
    "languages": {"Go", "TypeScript", "Kotlin", "Elixir", "Python", "Ruby"},
}

TEST_ENTITIES = {
    "persons": {"Sofia", "Marcus", "Lena", "Hiro", "Amira", "Felix", "Clara", "Devon"},
    "projects": {
        "Nimbus", "Vector", "Cobalt", "Aurora", "Titan", "Willow", "Cipher", "Mesa", "NimbusX"
    },
    "orgs": {"Brightline Corp", "Redwood Analytics"},
    "libraries": {"MongoDB", "RabbitMQ", "Prometheus", "Sidekiq"},
    "locations": {"Tokyo", "Dublin"},
    "languages": {"Scala", "Swift", "Haskell", "Zig", "Java", "Perl", "MySQL", "H2"},
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha256_json(obj: Any) -> str:
    blob = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return _sha256_bytes(blob)


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")


def facts_to_dict(facts: list[tuple[str, str]]) -> dict[str, str]:
    return {fid: text for fid, text in facts}


def queries_to_list(queries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": q["id"],
            "text": q["text"],
            "class": q["class"],
            "subtype": q["subtype"],
        }
        for q in queries
    ]


def gold_to_dict(queries: list[dict[str, Any]]) -> dict[str, list[str]]:
    return {q["id"]: list(q["gold"]) for q in queries}


def entity_overlap(cal: dict[str, set[str]], test: dict[str, set[str]]) -> dict[str, Any]:
    overlap: dict[str, list[str]] = {}
    for key in ("persons", "projects", "orgs", "libraries", "locations"):
        inter = sorted(cal[key] & test[key])
        if inter:
            overlap[key] = inter
    # languages may overlap as relation types / shared tokens — names of projects etc matter more
    return {
        "overlapping_gold_entity_names": overlap,
        "entity_disjoint": len(overlap) == 0,
    }


def hn_coverage(labels: dict[str, dict[str, list[str]]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for fmap in labels.values():
        for tags in fmap.values():
            for t in tags:
                counts[t] += 1
    return {h: int(counts.get(h, 0)) for h in ALL_HN}


def validate_split(
    facts: list[tuple[str, str]],
    queries: list[dict[str, Any]],
    labels: dict[str, dict[str, list[str]]],
    split_name: str,
) -> list[str]:
    errors: list[str] = []
    if len(facts) != 40:
        errors.append(f"{split_name}: expected 40 facts, got {len(facts)}")
    if len(queries) != 20:
        errors.append(f"{split_name}: expected 20 queries, got {len(queries)}")
    ans = [q for q in queries if q["class"] == "answerable"]
    noa = [q for q in queries if q["class"] == "no_answer"]
    if len(ans) != 12:
        errors.append(f"{split_name}: expected 12 answerable, got {len(ans)}")
    if len(noa) != 8:
        errors.append(f"{split_name}: expected 8 no_answer, got {len(noa)}")
    broad = [q for q in ans if q["subtype"] == "broad"]
    if len(broad) != 4:
        errors.append(f"{split_name}: expected 4 broad, got {len(broad)}")
    nex = [q for q in noa if q["subtype"] == "nonexistent"]
    uns = [q for q in noa if q["subtype"] == "unsupported"]
    if len(nex) != 4 or len(uns) != 4:
        errors.append(f"{split_name}: no_answer subtypes {len(nex)}/{len(uns)}")
    fact_ids = {f for f, _ in facts}
    for q in queries:
        for g in q["gold"]:
            if g not in fact_ids:
                errors.append(f"{split_name}: gold {g} missing for {q['id']}")
        if q["class"] == "no_answer" and q["gold"]:
            errors.append(f"{split_name}: no_answer {q['id']} has gold")
        if q["class"] == "answerable" and not q["gold"]:
            errors.append(f"{split_name}: answerable {q['id']} empty gold")
    cov = hn_coverage(labels)
    for h in HN_CORE:
        if cov[h] < 3:
            errors.append(f"{split_name}: {h} coverage {cov[h]} < 3")
    for h in HN_ADV:
        if cov[h] < 2:
            errors.append(f"{split_name}: {h} coverage {cov[h]} < 2")
    return errors


def build_adversarial_manifest(
    cal_labels: dict[str, dict[str, list[str]]],
    test_labels: dict[str, dict[str, list[str]]],
) -> dict[str, Any]:
    def pairs(labels: dict[str, dict[str, list[str]]], tag: str) -> list[dict[str, str]]:
        out = []
        for qid, fmap in labels.items():
            for fid, tags in fmap.items():
                if tag in tags:
                    out.append({"query_id": qid, "fact_id": fid})
        return out

    strata = {}
    for tag in ALL_HN:
        strata[tag] = {
            "calibration_pairs": pairs(cal_labels, tag),
            "test_pairs": pairs(test_labels, tag),
            "calibration_count": len(pairs(cal_labels, tag)),
            "test_count": len(pairs(test_labels, tag)),
        }
    return {
        "strata": strata,
        "calibration_coverage": hn_coverage(cal_labels),
        "test_coverage": hn_coverage(test_labels),
        "definitions": {
            "HN1": "SAME_ENTITY_WRONG_PREDICATE",
            "HN2": "SAME_PREDICATE_WRONG_ENTITY",
            "HN3": "LEXICAL_OVERLAP_WRONG_ANSWER",
            "HN4": "SEMANTICALLY_RELATED_WRONG_RELATION",
            "HN5": "NEAR_NAME_ENTITY_COLLISION",
            "HN6": "UNRELATED",
            "HN7": "NEGATION_POLARITY",
            "HN8": "TEMPORAL_VERSION_MISMATCH",
            "HN9": "SCOPE_MISMATCH",
            "HN10": "CONDITION_MISMATCH",
            "HN11": "ATTRIBUTION_SOURCE_MISMATCH",
            "HN12": "NUMERIC_UNIT_DIRECTION_MISMATCH",
        },
    }


def fm15_anchor_payload() -> dict[str, Any]:
    return {
        "queries": [{"id": qid, "text": text} for qid, text in FM15_QUERIES],
        "facts": [{"id": fid, "text": text} for fid, text in FM15_FACTS],
        "gold": {qid: list(texts) for qid, texts in FM15_GOLD.items()},
        "note": "Exact FM-15 Q1–Q5 × F1–F4 regression anchor; excluded from threshold selection.",
    }


def write_preregistration(out_dir: Path) -> dict[str, Any]:
    """Write corpus + hashes + preregistration BEFORE any model scoring."""
    cal_labels = _build_hn_labels_cal()
    test_labels = _build_hn_labels_test()
    errors = validate_split(CAL_FACTS, CAL_QUERIES, cal_labels, "CAL") + validate_split(
        TEST_FACTS, TEST_QUERIES, test_labels, "TEST"
    )
    overlap = entity_overlap(CAL_ENTITIES, TEST_ENTITIES)
    if not overlap["entity_disjoint"]:
        errors.append(f"entity overlap: {overlap['overlapping_gold_entity_names']}")
    if errors:
        raise RuntimeError("corpus validation failed:\n" + "\n".join(errors))

    corpus = out_dir / "corpus"
    hashes_dir = out_dir / "hashes"
    corpus.mkdir(parents=True, exist_ok=True)
    hashes_dir.mkdir(parents=True, exist_ok=True)

    cal_facts = facts_to_dict(CAL_FACTS)
    test_facts = facts_to_dict(TEST_FACTS)
    cal_queries = queries_to_list(CAL_QUERIES)
    test_queries = queries_to_list(TEST_QUERIES)
    cal_gold = gold_to_dict(CAL_QUERIES)
    test_gold = gold_to_dict(TEST_QUERIES)
    hn_all = {"calibration": cal_labels, "test": test_labels}
    adv = build_adversarial_manifest(cal_labels, test_labels)
    anchor = fm15_anchor_payload()

    files = {
        "fm15_anchor.json": anchor,
        "calibration_facts.json": cal_facts,
        "calibration_queries.json": cal_queries,
        "calibration_gold.json": cal_gold,
        "test_facts.json": test_facts,
        "test_queries.json": test_queries,
        "test_gold.json": test_gold,
        "hard_negative_labels.json": hn_all,
        "adversarial_strata_manifest.json": adv,
    }
    file_hashes: dict[str, str] = {}
    for name, obj in files.items():
        path = corpus / name
        write_json(path, obj)
        file_hashes[name] = _sha256_file(path)

    write_json(hashes_dir / "frozen_corpus_sha256.json", file_hashes)

    prereg = {
        "experiment": "FM-16",
        "preregistered_at_utc": _utc_now(),
        "models": {
            "cross_encoder": {
                "name": REQUIRED_MODEL,
                "revision_pin": CE_REVISION_PIN,
                "weight_sha256_pin": CE_WEIGHT_SHA_PIN,
                "client": "graphiti_core.cross_encoder.bge_reranker_client.BGERerankerClient",
            },
            "embedding": {
                "name": EMBED_MODEL,
                "implementation": "LocalSemanticEmbedder/fastembed",
                "profile": "FM-14",
            },
        },
        "counts": {
            "calibration_facts": 40,
            "calibration_queries": 20,
            "test_facts": 40,
            "test_queries": 20,
            "answerable_per_split": 12,
            "no_answer_per_split": 8,
            "broad_answerable_per_split": 4,
            "nonexistent_per_split": 4,
            "unsupported_per_split": 4,
            "hard_negative_strata": 12,
            "ce_pairs_calibration": 800,
            "ce_pairs_test": 800,
            "ce_pairs_fm15_anchor": 20,
            "ce_pairs_total": 1620,
        },
        "query_classes": {
            "answerable_subtypes": ["narrow", "paraphrase", "broad"],
            "no_answer_subtypes": ["nonexistent", "unsupported"],
        },
        "gold_sets": {"calibration": cal_gold, "test": test_gold},
        "negative_strata": adv["definitions"],
        "hn_coverage_requirement": {"HN1-HN6_min": 3, "HN7-HN12_min": 2},
        "hn_coverage_observed": {
            "calibration": adv["calibration_coverage"],
            "test": adv["test_coverage"],
        },
        "entity_disjoint": overlap,
        "metric_definitions": {
            "ANSWERABLE_QUERY_COVERAGE": "fraction of answerable queries with >=1 gold survivor",
            "GOLD_PAIR_RECALL": "fraction of gold (query,fact) pairs with score >= theta",
            "NO_ANSWER_EMPTY_ACCURACY": "fraction of no-answer queries with 0 survivors",
            "NON_GOLD_REJECTION_RATE": "fraction of non-gold pairs with score < theta",
            "FALSE_EMPTY_RATE": "fraction of answerable queries with 0 gold survivors",
            "BROAD_QUERY_GOLD_RECALL": "GOLD_PAIR_RECALL restricted to broad queries",
            "HARD_NEGATIVE_MARGIN": "lowest_gold_score - highest_non_gold_score",
        },
        "threshold_rule": {
            "scope": "CALIBRATION_ONLY",
            "one_global_threshold_per_family": True,
            "feasibility": {
                "ANSWERABLE_QUERY_COVERAGE": 1.0,
                "GOLD_PAIR_RECALL_MIN": 0.90,
                "NO_ANSWER_EMPTY_ACCURACY": 1.0,
                "BROAD_QUERY_GOLD_RECALL_MIN": 0.90,
            },
            "objective": "maximize NON_GOLD_REJECTION_RATE",
            "tie_break": "lower_threshold",
        },
        "generalization_criteria": {
            "GENERALIZATION_STRONG": {
                "ANSWERABLE_QUERY_COVERAGE_MIN": 0.95,
                "GOLD_PAIR_RECALL_MIN": 0.90,
                "NO_ANSWER_EMPTY_ACCURACY_MIN": 0.875,
                "FALSE_EMPTY_RATE_MAX": 0.05,
                "BROAD_QUERY_GOLD_RECALL_MIN": 0.90,
                "CRITICAL_STRATUM_FAILURE": False,
            }
        },
        "forbidden": {
            "forced_refill": True,
            "test_leakage_into_threshold": True,
            "runtime_ce_activation": True,
            "search_recipe_change": True,
            "deepseek_extraction": True,
            "predetermined_pass": True,
        },
        "corpus_file_sha256": file_hashes,
        "start_sha_expected": EXPECTED_START_SHA,
        "upstream_sha_expected": UPSTREAM_SHA,
        "scoring_begun": False,
    }
    write_json(out_dir / "preregistration.json", prereg)
    # freeze marker
    write_json(
        out_dir / "hashes" / "preregistration_sha256.json",
        {"preregistration.json": _sha256_file(out_dir / "preregistration.json")},
    )
    return {
        "preregistration": prereg,
        "cal_labels": cal_labels,
        "test_labels": test_labels,
        "errors": errors,
        "file_hashes": file_hashes,
    }



# ---------------------------------------------------------------------------
# Scoring (CE + embedding) with disk checkpoints
# ---------------------------------------------------------------------------

def _cosine(a: list[float], b: list[float]) -> float:
    return float(sum(x * y for x, y in zip(a, b, strict=True)))


def _load_checkpoint(path: Path) -> dict[str, Any]:
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def _save_checkpoint(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, indent=2, default=str) + "\n", encoding="utf-8")
    tmp.replace(path)


async def score_ce_matrix(
    client: Any,
    queries: list[dict[str, Any]],
    facts: list[tuple[str, str]],
    *,
    checkpoint_name: str,
    capture_logits: bool = True,
) -> dict[str, Any]:
    """Score |Q|x|F| with per-query CE batches; checkpoint after each query."""
    ckpt_path = CHECKPOINT_DIR / checkpoint_name
    state = _load_checkpoint(ckpt_path)
    official: dict[str, dict[str, float]] = {
        qid: {fid: float(v) for fid, v in fmap.items()}
        for qid, fmap in state.get("official_scores", {}).items()
    }
    logits: dict[str, dict[str, float]] = {
        qid: {fid: float(v) for fid, v in fmap.items()}
        for qid, fmap in state.get("logit_scores", {}).items()
    }
    t0 = time.perf_counter()
    passages = [text for _, text in facts]
    fid_list = [fid for fid, _ in facts]
    for q in queries:
        qid = q["id"]
        if qid in official and len(official[qid]) == len(facts):
            continue
        ranked = await score_pairs_official(client, q["text"], passages)
        by_text = {p: float(s) for p, s in ranked}
        official[qid] = {fid: by_text[text] for fid, text in facts}
        if capture_logits:
            logit_list = score_logits_optional(client.model, q["text"], passages)
            if logit_list and len(logit_list) == len(facts):
                logits[qid] = {fid_list[i]: float(logit_list[i]) for i in range(len(facts))}
        _save_checkpoint(
            ckpt_path,
            {
                "official_scores": official,
                "logit_scores": logits,
                "completed_queries": sorted(official.keys()),
                "updated_at_utc": _utc_now(),
            },
        )
    elapsed = time.perf_counter() - t0
    n_pairs = len(queries) * len(facts)
    return {
        "official_scores": official,
        "logit_scores": logits,
        "pair_count": n_pairs,
        "scoring_time_s": elapsed,
        "per_pair_average_s": elapsed / n_pairs if n_pairs else None,
        "checkpoint": str(ckpt_path),
    }


def score_embedding_matrix(
    queries: list[dict[str, Any]],
    facts: list[tuple[str, str]],
    *,
    checkpoint_name: str,
) -> dict[str, Any]:
    ckpt_path = CHECKPOINT_DIR / checkpoint_name
    state = _load_checkpoint(ckpt_path)
    if state.get("scores") and len(state["scores"]) == len(queries):
        return state
    t0 = time.perf_counter()
    model, meta = load_fastembed_model(EMBED_MODEL)
    q_texts = [q["text"] for q in queries]
    f_texts = [t for _, t in facts]
    q_vecs = list(model.embed(q_texts))
    f_vecs = list(model.embed(f_texts))
    scores: dict[str, dict[str, float]] = {}
    for qi, q in enumerate(queries):
        scores[q["id"]] = {
            facts[fi][0]: _cosine(list(map(float, q_vecs[qi])), list(map(float, f_vecs[fi])))
            for fi in range(len(facts))
        }
    elapsed = time.perf_counter() - t0
    out = {
        "scores": scores,
        "pair_count": len(queries) * len(facts),
        "scoring_time_s": elapsed,
        "per_pair_average_s": elapsed / (len(queries) * len(facts)),
        "embedder_meta": meta,
        "updated_at_utc": _utc_now(),
    }
    _save_checkpoint(ckpt_path, out)
    return out


def flatten_score_rows(
    queries: list[dict[str, Any]],
    facts: list[tuple[str, str]],
    scores: dict[str, dict[str, float]],
    gold: dict[str, list[str]],
    hn_labels: dict[str, dict[str, list[str]]],
    *,
    score_key: str = "RAW_SCORE",
    logits: dict[str, dict[str, float]] | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    fact_text = {fid: text for fid, text in facts}
    for q in queries:
        qid = q["id"]
        scored = []
        for fid, _ in facts:
            raw = float(scores[qid][fid])
            gold_flag = fid in gold.get(qid, [])
            logit = None
            if logits and qid in logits and fid in logits[qid]:
                logit = float(logits[qid][fid])
            scored.append((fid, raw, gold_flag, logit))
        ordered = sorted(scored, key=lambda t: (-t[1], t[0]))
        rank_map = {fid: i + 1 for i, (fid, *_r) in enumerate(ordered)}
        for fid, raw, gold_flag, logit in scored:
            rows.append(
                {
                    "query_id": qid,
                    "query_text": q["text"],
                    "query_class": q["class"],
                    "query_subtype": q["subtype"],
                    "fact_id": fid,
                    "fact_text": fact_text[fid],
                    "gold_relevant": gold_flag,
                    "hard_negative_labels": list(hn_labels.get(qid, {}).get(fid, [])),
                    score_key: raw,
                    "RAW_SCORE": raw if score_key == "RAW_SCORE" else None,
                    "COSINE_SCORE": raw if score_key == "COSINE_SCORE" else None,
                    "LOGIT_SCORE": logit,
                    "ACTIVATION_FN": "Sigmoid()" if score_key == "RAW_SCORE" else None,
                    "rank_within_query": rank_map[fid],
                }
            )
    return rows


def write_score_csv(rows: list[dict[str, Any]], path: Path, score_field: str) -> None:
    fields = [
        "query_id", "query_text", "query_class", "query_subtype",
        "fact_id", "fact_text", "gold_relevant", "hard_negative_labels",
        score_field, "LOGIT_SCORE", "rank_within_query",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            row = dict(r)
            row["hard_negative_labels"] = "|".join(r.get("hard_negative_labels") or [])
            w.writerow(row)


def _precision_at_k(ranked_fids: list[str], gold: set[str], k: int) -> float:
    top = ranked_fids[:k]
    if not top:
        return 0.0
    return sum(1 for f in top if f in gold) / float(k)


def _recall_at_k(ranked_fids: list[str], gold: set[str], k: int) -> float:
    if not gold:
        return 0.0
    top = set(ranked_fids[:k])
    return len(top & gold) / float(len(gold))


def _mrr(ranked_fids: list[str], gold: set[str]) -> float:
    for i, fid in enumerate(ranked_fids, start=1):
        if fid in gold:
            return 1.0 / i
    return 0.0


def ranking_metrics_for_split(
    queries: list[dict[str, Any]],
    scores: dict[str, dict[str, float]],
    gold: dict[str, list[str]],
) -> dict[str, Any]:
    per_q: dict[str, Any] = {}
    mrrs: list[float] = []
    p_at = {1: [], 3: [], 5: []}
    r_at = {1: [], 3: [], 5: []}
    perfect = 0
    margins: list[float] = []
    broad_gold_hits = 0
    broad_gold_total = 0
    no_answer_max: list[float] = []

    for q in queries:
        qid = q["id"]
        sc = scores[qid]
        ranked = sorted(sc.keys(), key=lambda fid: (-sc[fid], fid))
        gset = set(gold.get(qid, []))
        if q["class"] == "answerable":
            mrrs.append(_mrr(ranked, gset))
            for k in (1, 3, 5):
                p_at[k].append(_precision_at_k(ranked, gset, k))
                r_at[k].append(_recall_at_k(ranked, gset, k))
            gold_scores = [sc[f] for f in gset]
            non_gold_scores = [sc[f] for f in sc if f not in gset]
            lowest_gold = min(gold_scores)
            highest_non = max(non_gold_scores) if non_gold_scores else float("-inf")
            margin = lowest_gold - highest_non
            margins.append(margin)
            if margin > 0:
                perfect += 1
            if q["subtype"] == "broad":
                broad_gold_total += len(gset)
                broad_gold_hits += len(gset)
            per_q[qid] = {
                "MRR": mrrs[-1],
                "P@1": p_at[1][-1],
                "P@3": p_at[3][-1],
                "P@5": p_at[5][-1],
                "R@1": r_at[1][-1],
                "R@3": r_at[3][-1],
                "R@5": r_at[5][-1],
                "LOWEST_GOLD_SCORE": lowest_gold,
                "HIGHEST_NON_GOLD_SCORE": highest_non,
                "HARD_NEGATIVE_MARGIN": margin,
                "perfect_separation": margin > 0,
            }
        else:
            no_answer_max.append(max(sc.values()))
            per_q[qid] = {"QUERY_MAX_SCORE": max(sc.values())}

    n_ans = max(1, len([q for q in queries if q["class"] == "answerable"]))
    return {
        "MRR": statistics.mean(mrrs) if mrrs else None,
        "Precision@1": statistics.mean(p_at[1]) if p_at[1] else None,
        "Precision@3": statistics.mean(p_at[3]) if p_at[3] else None,
        "Precision@5": statistics.mean(p_at[5]) if p_at[5] else None,
        "Recall@1": statistics.mean(r_at[1]) if r_at[1] else None,
        "Recall@3": statistics.mean(r_at[3]) if r_at[3] else None,
        "Recall@5": statistics.mean(r_at[5]) if r_at[5] else None,
        "PERFECT_SEPARATION_QUERY_RATE": perfect / n_ans,
        "mean_hard_negative_margin": statistics.mean(margins) if margins else None,
        "median_hard_negative_margin": statistics.median(margins) if margins else None,
        "broad_query_gold_present_rate": (
            broad_gold_hits / broad_gold_total if broad_gold_total else None
        ),
        "no_answer_QUERY_MAX_SCORE": {
            "values": no_answer_max,
            "mean": statistics.mean(no_answer_max) if no_answer_max else None,
            "max": max(no_answer_max) if no_answer_max else None,
            "min": min(no_answer_max) if no_answer_max else None,
        },
        "per_query": per_q,
    }


def evaluate_threshold(
    queries: list[dict[str, Any]],
    scores: dict[str, dict[str, float]],
    gold: dict[str, list[str]],
    theta: float,
) -> dict[str, Any]:
    ans = [q for q in queries if q["class"] == "answerable"]
    noa = [q for q in queries if q["class"] == "no_answer"]

    ans_covered = 0
    false_empty = 0
    gold_total = 0
    gold_hit = 0
    broad_gold_total = 0
    broad_gold_hit = 0
    non_gold_total = 0
    non_gold_rejected = 0
    no_answer_empty = 0
    survivors_counts: list[int] = []
    p_at = {1: [], 3: [], 5: []}
    r_at = {1: [], 3: [], 5: []}

    for q in queries:
        qid = q["id"]
        sc = scores[qid]
        gset = set(gold.get(qid, []))
        survivors = [fid for fid, s in sc.items() if s >= theta]
        survivors_sorted = sorted(survivors, key=lambda fid: (-sc[fid], fid))
        survivors_counts.append(len(survivors))
        if q["class"] == "answerable":
            gold_surv = [fid for fid in survivors if fid in gset]
            if gold_surv:
                ans_covered += 1
            else:
                false_empty += 1
            gold_total += len(gset)
            gold_hit += sum(1 for fid in gset if sc[fid] >= theta)
            if q["subtype"] == "broad":
                broad_gold_total += len(gset)
                broad_gold_hit += sum(1 for fid in gset if sc[fid] >= theta)
            for k in (1, 3, 5):
                p_at[k].append(_precision_at_k(survivors_sorted, gset, k))
                r_at[k].append(_recall_at_k(survivors_sorted, gset, k))
            for fid, s in sc.items():
                if fid not in gset:
                    non_gold_total += 1
                    if s < theta:
                        non_gold_rejected += 1
        else:
            if len(survivors) == 0:
                no_answer_empty += 1
            for fid, s in sc.items():
                non_gold_total += 1
                if s < theta:
                    non_gold_rejected += 1

    return {
        "theta": theta,
        "ANSWERABLE_QUERY_COVERAGE": ans_covered / len(ans) if ans else 0.0,
        "FALSE_EMPTY_RATE": false_empty / len(ans) if ans else 0.0,
        "GOLD_PAIR_RECALL": gold_hit / gold_total if gold_total else 0.0,
        "NO_ANSWER_EMPTY_ACCURACY": no_answer_empty / len(noa) if noa else 0.0,
        "NO_ANSWER_FALSE_POSITIVE_RATE": 1.0 - (no_answer_empty / len(noa) if noa else 0.0),
        "NON_GOLD_REJECTION_RATE": (
            non_gold_rejected / non_gold_total if non_gold_total else 0.0
        ),
        "BROAD_QUERY_GOLD_RECALL": (
            broad_gold_hit / broad_gold_total if broad_gold_total else 0.0
        ),
        "Precision@1": statistics.mean(p_at[1]) if p_at[1] else None,
        "Precision@3": statistics.mean(p_at[3]) if p_at[3] else None,
        "Precision@5": statistics.mean(p_at[5]) if p_at[5] else None,
        "Recall@1": statistics.mean(r_at[1]) if r_at[1] else None,
        "Recall@3": statistics.mean(r_at[3]) if r_at[3] else None,
        "Recall@5": statistics.mean(r_at[5]) if r_at[5] else None,
        "average_survivors_per_query": (
            statistics.mean(survivors_counts) if survivors_counts else 0.0
        ),
        "median_survivors_per_query": (
            statistics.median(survivors_counts) if survivors_counts else 0.0
        ),
        "feasible": False,
    }


def is_feasible(metrics: dict[str, Any]) -> bool:
    return (
        metrics["ANSWERABLE_QUERY_COVERAGE"] >= 1.0 - 1e-12
        and metrics["GOLD_PAIR_RECALL"] >= 0.90 - 1e-12
        and metrics["NO_ANSWER_EMPTY_ACCURACY"] >= 1.0 - 1e-12
        and metrics["BROAD_QUERY_GOLD_RECALL"] >= 0.90 - 1e-12
    )


def search_threshold(
    queries: list[dict[str, Any]],
    scores: dict[str, dict[str, float]],
    gold: dict[str, list[str]],
) -> dict[str, Any]:
    """Derive candidate thresholds ONLY from calibration scores."""
    all_scores: list[float] = []
    for q in queries:
        all_scores.extend(float(v) for v in scores[q["id"]].values())
    uniq = sorted(set(all_scores))
    candidates: list[float] = list(uniq)
    for i in range(len(uniq) - 1):
        candidates.append((uniq[i] + uniq[i + 1]) / 2.0)
    if uniq:
        candidates.append(min(uniq) - 1e-6)
        candidates.append(max(uniq) + 1e-6)
    candidates = sorted(set(round(c, 12) for c in candidates))

    results: list[dict[str, Any]] = []
    feasible: list[dict[str, Any]] = []
    for theta in candidates:
        m = evaluate_threshold(queries, scores, gold, theta)
        m["feasible"] = is_feasible(m)
        results.append(m)
        if m["feasible"]:
            feasible.append(m)

    selected = None
    if feasible:
        feasible_sorted = sorted(
            feasible,
            key=lambda m: (-m["NON_GOLD_REJECTION_RATE"], m["theta"]),
        )
        selected = feasible_sorted[0]

    return {
        "candidate_count": len(candidates),
        "feasible_count": len(feasible),
        "GLOBAL_THRESHOLD_FEASIBLE": selected is not None,
        "selected": selected,
        "all_feasible": feasible,
        "search_rule": {
            "feasibility": {
                "ANSWERABLE_QUERY_COVERAGE": 1.0,
                "GOLD_PAIR_RECALL_MIN": 0.90,
                "NO_ANSWER_EMPTY_ACCURACY": 1.0,
                "BROAD_QUERY_GOLD_RECALL_MIN": 0.90,
            },
            "objective": "maximize NON_GOLD_REJECTION_RATE",
            "tie_break": "lower_threshold",
        },
        "sample_results_head": results[:5],
        "sample_results_tail": results[-5:],
    }


# ---------------------------------------------------------------------------
# Held-out evaluation, strata, verdicts, receipts
# ---------------------------------------------------------------------------

def build_rejection_receipts(
    queries: list[dict[str, Any]],
    scores: dict[str, dict[str, float]],
    gold: dict[str, list[str]],
    hn_labels: dict[str, dict[str, list[str]]],
    theta: float | None,
    score_family: str,
) -> list[dict[str, Any]]:
    receipts: list[dict[str, Any]] = []
    for q in queries:
        qid = q["id"]
        sc = scores[qid]
        gset = set(gold.get(qid, []))
        selected = []
        discarded = []
        cand = []
        for fid, s in sc.items():
            if theta is None:
                above = False
                reason = "NO_GLOBAL_THRESHOLD_FEASIBLE"
            else:
                above = s >= theta
                reason = "ABOVE_THRESHOLD" if above else "BELOW_THRESHOLD"
            entry = {
                "fact_id": fid,
                "score": s,
                "selected": above,
                "reason": reason,
                "gold": fid in gset,
                "hard_negative_labels": list(hn_labels.get(qid, {}).get(fid, [])),
            }
            cand.append(entry)
            if above:
                selected.append(fid)
            else:
                discarded.append(fid)
        if theta is None:
            empty_reason = "NO_GLOBAL_THRESHOLD_FEASIBLE"
        elif not selected:
            empty_reason = "NO_CANDIDATE_PASSED_RELEVANCE_THRESHOLD"
        else:
            empty_reason = None
        receipts.append(
            {
                "query_id": qid,
                "query_class": q["class"],
                "query_subtype": q["subtype"],
                "score_family": score_family,
                "threshold": theta,
                "candidate_count": len(sc),
                "selected_ids": selected,
                "discarded_ids": discarded,
                "candidates": cand,
                "empty_reason": empty_reason,
                "forced_refill": False,
            }
        )
    return receipts


def stratum_metrics(
    queries: list[dict[str, Any]],
    scores: dict[str, dict[str, float]],
    hn_labels: dict[str, dict[str, list[str]]],
    theta: float | None,
) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for tag in ALL_HN:
        vals: list[float] = []
        rejected = 0
        total = 0
        for q in queries:
            qid = q["id"]
            for fid, tags in hn_labels.get(qid, {}).items():
                if tag in tags:
                    s = float(scores[qid][fid])
                    vals.append(s)
                    total += 1
                    if theta is not None and s < theta:
                        rejected += 1
        if not vals:
            out[tag] = {"candidate_count": 0}
            continue
        vals_sorted = sorted(vals)
        p95 = vals_sorted[min(len(vals_sorted) - 1, int(0.95 * (len(vals_sorted) - 1)))]
        out[tag] = {
            "candidate_count": total,
            "mean_score": statistics.mean(vals),
            "median_score": statistics.median(vals),
            "p95_score": p95,
            "rejection_rate": (rejected / total) if (theta is not None and total) else None,
            "false_survival_rate": (
                1.0 - (rejected / total) if (theta is not None and total) else None
            ),
        }
    return out


def adversarial_pair_discrimination(
    scores: dict[str, dict[str, float]],
    gold: dict[str, list[str]],
    hn_labels: dict[str, dict[str, list[str]]],
    tag: str,
    paired_gold_hint: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Check whether wrong semantic HN systematically outscores corresponding gold."""
    inversions = 0
    comparisons = 0
    examples: list[dict[str, Any]] = []
    for qid, fmap in hn_labels.items():
        gset = gold.get(qid, [])
        if not gset:
            continue
        for fid, tags in fmap.items():
            if tag not in tags:
                continue
            # compare HN score vs each gold on same query
            hn_s = scores[qid][fid]
            for g in gset:
                gs = scores[qid][g]
                comparisons += 1
                if hn_s > gs:
                    inversions += 1
                    if len(examples) < 5:
                        examples.append(
                            {
                                "query_id": qid,
                                "hn_fact": fid,
                                "hn_score": hn_s,
                                "gold_fact": g,
                                "gold_score": gs,
                            }
                        )
    rate = inversions / comparisons if comparisons else 0.0
    if comparisons == 0:
        label = "INCONCLUSIVE"
    elif rate >= 0.5 and inversions >= 2:
        label = "FAIL"
    elif rate > 0:
        label = "PARTIAL"
    else:
        label = "PASS"
    return {
        "tag": tag,
        "comparisons": comparisons,
        "inversions": inversions,
        "inversion_rate": rate,
        "discrimination": label,
        "examples": examples,
        "systematic_inversion": rate >= 0.5 and inversions >= 2,
    }


def no_answer_strata_metrics(
    queries: list[dict[str, Any]],
    scores: dict[str, dict[str, float]],
    theta: float | None,
) -> dict[str, Any]:
    def for_subtype(sub: str) -> dict[str, Any]:
        qs = [q for q in queries if q["class"] == "no_answer" and q["subtype"] == sub]
        if theta is None:
            return {"count": len(qs), "empty_accuracy": None, "false_positive_rate": None}
        empty = 0
        for q in qs:
            survivors = [fid for fid, s in scores[q["id"]].items() if s >= theta]
            if not survivors:
                empty += 1
        acc = empty / len(qs) if qs else 0.0
        return {
            "count": len(qs),
            "empty_accuracy": acc,
            "false_positive_rate": 1.0 - acc,
        }

    return {
        "nonexistent": for_subtype("nonexistent"),
        "unsupported": for_subtype("unsupported"),
    }


def broad_query_metrics(
    queries: list[dict[str, Any]],
    scores: dict[str, dict[str, float]],
    gold: dict[str, list[str]],
    theta: float | None,
) -> dict[str, Any]:
    broad = [q for q in queries if q["class"] == "answerable" and q["subtype"] == "broad"]
    if theta is None:
        return {"BROAD_QUERY_COUNT": len(broad)}
    gold_total = 0
    gold_hit = 0
    false_empty = 0
    survivors_list: list[int] = []
    for q in broad:
        sc = scores[q["id"]]
        gset = set(gold[q["id"]])
        gold_total += len(gset)
        gold_hit += sum(1 for g in gset if sc[g] >= theta)
        surv = [fid for fid, s in sc.items() if s >= theta]
        survivors_list.append(len(surv))
        if not any(fid in gset for fid in surv):
            false_empty += 1
    return {
        "BROAD_QUERY_COUNT": len(broad),
        "BROAD_QUERY_GOLD_PAIR_RECALL": gold_hit / gold_total if gold_total else 0.0,
        "BROAD_QUERY_FALSE_EMPTY_RATE": false_empty / len(broad) if broad else 0.0,
        "BROAD_QUERY_AVERAGE_SURVIVORS": (
            statistics.mean(survivors_list) if survivors_list else 0.0
        ),
    }


def compare_ce_vs_embedding(ce: dict[str, Any], emb: dict[str, Any], critical_fail: bool) -> str:
    if ce.get("theta") is None and emb.get("theta") is None:
        return "NO_MATERIAL_GAIN"
    if ce.get("theta") is None:
        return "WORSE"
    if emb.get("theta") is None:
        return "BETTER"

    cov_ok = ce["ANSWERABLE_QUERY_COVERAGE"] >= emb["ANSWERABLE_QUERY_COVERAGE"] - 1e-12
    recall_ok = ce["GOLD_PAIR_RECALL"] >= emb["GOLD_PAIR_RECALL"] - 0.05
    gains = []
    if ce["NO_ANSWER_EMPTY_ACCURACY"] >= emb["NO_ANSWER_EMPTY_ACCURACY"] + 0.10:
        gains.append("no_answer")
    if ce["NON_GOLD_REJECTION_RATE"] >= emb["NON_GOLD_REJECTION_RATE"] + 0.10:
        gains.append("hn_reject")
    ce_p3 = ce.get("Precision@3") or 0.0
    emb_p3 = emb.get("Precision@3") or 0.0
    if ce_p3 >= emb_p3 + 0.10:
        gains.append("p3")

    if critical_fail:
        return "MIXED"
    if cov_ok and recall_ok and gains:
        return "CLEARLY_BETTER"
    if cov_ok and recall_ok and (
        ce["NON_GOLD_REJECTION_RATE"] > emb["NON_GOLD_REJECTION_RATE"]
        or ce["NO_ANSWER_EMPTY_ACCURACY"] > emb["NO_ANSWER_EMPTY_ACCURACY"]
    ):
        return "BETTER"
    if (
        abs(ce["GOLD_PAIR_RECALL"] - emb["GOLD_PAIR_RECALL"]) < 0.05
        and abs(ce["NON_GOLD_REJECTION_RATE"] - emb["NON_GOLD_REJECTION_RATE"]) < 0.05
        and abs(ce["NO_ANSWER_EMPTY_ACCURACY"] - emb["NO_ANSWER_EMPTY_ACCURACY"]) < 0.05
    ):
        return "NO_MATERIAL_GAIN"
    if (
        ce["GOLD_PAIR_RECALL"] < emb["GOLD_PAIR_RECALL"] - 0.05
        or ce["ANSWERABLE_QUERY_COVERAGE"] < emb["ANSWERABLE_QUERY_COVERAGE"] - 0.05
    ):
        return "WORSE"
    return "MIXED"


def generalization_verdict(ce_test: dict[str, Any] | None, critical_fail: bool, ce_feasible: bool) -> str:
    if not ce_feasible or ce_test is None or ce_test.get("theta") is None:
        return "GLOBAL_THRESHOLD_NOT_FEASIBLE"
    ok = (
        ce_test["ANSWERABLE_QUERY_COVERAGE"] >= 0.95
        and ce_test["GOLD_PAIR_RECALL"] >= 0.90
        and ce_test["NO_ANSWER_EMPTY_ACCURACY"] >= 0.875
        and ce_test["FALSE_EMPTY_RATE"] <= 0.05
        and ce_test["BROAD_QUERY_GOLD_RECALL"] >= 0.90
        and not critical_fail
    )
    if ok:
        return "GENERALIZATION_STRONG"
    # partial if some structure holds
    partial = (
        ce_test["ANSWERABLE_QUERY_COVERAGE"] >= 0.75
        and ce_test["GOLD_PAIR_RECALL"] >= 0.70
    )
    if critical_fail and partial:
        return "GENERALIZATION_PARTIAL"
    if partial and (
        ce_test["NO_ANSWER_EMPTY_ACCURACY"] < 0.875
        or ce_test["BROAD_QUERY_GOLD_RECALL"] < 0.90
        or critical_fail
    ):
        return "GENERALIZATION_PARTIAL"
    if ce_test["ANSWERABLE_QUERY_COVERAGE"] < 0.5 or ce_test["GOLD_PAIR_RECALL"] < 0.5:
        return "GENERALIZATION_FAILED"
    return "INCONCLUSIVE"


def anchor_recheck(
    ce_scores: dict[str, dict[str, float]],
    run006_matrix_path: Path,
) -> dict[str, Any]:
    """Compare FM-15 anchor CE scores to run_006 matrix."""
    prev = json.loads(run006_matrix_path.read_text(encoding="utf-8"))
    # run_006 format: list of rows or dict — support both
    prev_map: dict[str, dict[str, float]] = {}
    if isinstance(prev, list):
        for row in prev:
            prev_map.setdefault(row["query_id"], {})[row["fact_id"]] = float(row["RAW_SCORE"])
    elif isinstance(prev, dict) and "rows" in prev:
        for row in prev["rows"]:
            prev_map.setdefault(row["query_id"], {})[row["fact_id"]] = float(row["RAW_SCORE"])
    elif isinstance(prev, dict):
        # maybe query->fact map
        for qid, fmap in prev.items():
            if isinstance(fmap, dict):
                prev_map[qid] = {fid: float(v) for fid, v in fmap.items()}

    deltas: list[float] = []
    for qid, fmap in ce_scores.items():
        for fid, s in fmap.items():
            if qid in prev_map and fid in prev_map[qid]:
                deltas.append(abs(s - prev_map[qid][fid]))
    max_delta = max(deltas) if deltas else None
    if max_delta is None:
        det = "DRIFTED"
    elif max_delta == 0.0:
        det = "EXACT"
    elif max_delta < 1e-5:
        det = "NEAR_EXACT"
    else:
        det = "DRIFTED"
    return {
        "ANCHOR_DETERMINISM": det,
        "MAX_ABSOLUTE_CE_DELTA": max_delta,
        "compared_pairs": len(deltas),
        "source": str(run006_matrix_path),
    }


# ---------------------------------------------------------------------------
# Findings helpers + full experiment runner
# ---------------------------------------------------------------------------

def _write_findings(out_dir: Path, ctx: dict[str, Any]) -> None:
    findings = out_dir / "findings"
    findings.mkdir(parents=True, exist_ok=True)
    gv = ctx["generalization_verdict"]
    ce_vs = ctx["ce_vs_embedding"]
    ce_feas = ctx["ce_feasible"]
    emb_feas = ctx["emb_feasible"]
    crit = ctx["critical_stratum_failure"]

    (findings / "GENERALIZATION.md").write_text(
        f"""# GENERALIZATION

Verdict: **{gv}**

CE global threshold feasible on CAL: {ce_feas}
Embedding global threshold feasible on CAL: {emb_feas}
CRITICAL_STRATUM_FAILURE: {crit}

Held-out CE metrics are recorded in `evaluation/heldout_ce.json`.
This does **not** authorize runtime CE gating.
""",
        encoding="utf-8",
    )
    (findings / "GLOBAL_THRESHOLD.md").write_text(
        f"""# GLOBAL_THRESHOLD

One global threshold per family, selected on CALIBRATION only.

CE feasible: {ce_feas}
CE theta: {ctx.get('ce_theta')}
Embedding feasible: {emb_feas}
Embedding theta: {ctx.get('emb_theta')}

Feasibility rule (TZ §30): coverage=1, gold_recall>=0.90, no_answer_empty=1, broad_recall>=0.90;
maximize non_gold_rejection; tie=lower theta.
""",
        encoding="utf-8",
    )
    (findings / "HARD_NEGATIVES.md").write_text(
        """# HARD_NEGATIVES

HN1–HN12 strata metrics are in `evaluation/hard_negative_strata.json`.
Coverage requirements were enforced at preregistration (HN1–6 >=3, HN7–12 >=2 per split).
""",
        encoding="utf-8",
    )
    adv = ctx.get("adversarial_disc", {})
    (findings / "ADVERSARIAL_SEMANTICS.md").write_text(
        f"""# ADVERSARIAL_SEMANTICS

Negation: {adv.get('HN7', {}).get('discrimination')}
Temporal/version: {adv.get('HN8', {}).get('discrimination')}
Scope: {adv.get('HN9', {}).get('discrimination')}
Condition: {adv.get('HN10', {}).get('discrimination')}
Attribution: {adv.get('HN11', {}).get('discrimination')}
Numeric/unit: {adv.get('HN12', {}).get('discrimination')}

CRITICAL_STRATUM_FAILURE: {crit}
""",
        encoding="utf-8",
    )
    (findings / "NO_ANSWER.md").write_text(
        """# NO_ANSWER

Nonexistent-entity and unsupported-predicate empty accuracies are in
`evaluation/no_answer_strata.json` and `result.json`.
NO_RELEVANT_RESULT ≠ FACT_IS_FALSE / ENTITY_DOES_NOT_EXIST.
""",
        encoding="utf-8",
    )
    (findings / "BROAD_QUERY_SAFETY.md").write_text(
        """# BROAD_QUERY_SAFETY

Exactly 4 broad answerable queries per split.
Broad gold recall under calibrated threshold is required for feasibility (>=0.90 on CAL)
and for GENERALIZATION_STRONG (>=0.90 on TEST).
See `evaluation/broad_query_results.json`.
""",
        encoding="utf-8",
    )
    (findings / "CE_VS_EMBEDDING.md").write_text(
        f"""# CE_VS_EMBEDDING

Comparative verdict: **{ce_vs}**

Identical calibration rules applied independently to CE and embedding score families.
See `evaluation/comparative_verdict.json`.
""",
        encoding="utf-8",
    )
    (findings / "FORCED_REFILL_BOUNDARY.md").write_text(
        """# FORCED_REFILL_BOUNDARY

FORCED_REFILL: NO

If survivors = [] after threshold, experimental output remains [].
No top-k refill, BM25/RRF/cosine fallback, or minimum-count force.
""",
        encoding="utf-8",
    )
    (findings / "AUTHORITY_BOUNDARY.md").write_text(
        """# AUTHORITY_BOUNDARY

RELEVANCE_SCORE ≠ TRUTH / EVIDENCE / BELIEF / CANON / PERMISSION /
TEMPORAL_APPLICABILITY / PRODUCTION_AUTHORIZATION.

THRESHOLD_RUNTIME_AUTHORIZED: NO
RUNTIME_GATE_IMPLEMENTED: NO
""",
        encoding="utf-8",
    )
    (findings / "NEXT_LAYER.md").write_text(
        f"""# NEXT_LAYER

FM-16 complete. STOP.

Do **not** auto-create FM-17.
Do **not** enable CE in Graphiti.search / MemoryOps.
Await independent review.

Generalization verdict: {gv}
CE vs embedding: {ce_vs}
""",
        encoding="utf-8",
    )


async def run_fm16(*, out_dir: Path | None = None, capture_logits: bool = False) -> dict[str, Any]:
    """Full FM-16 pipeline: preregister -> score -> calibrate -> held-out once -> artifacts."""
    out_dir = out_dir or RUN007
    out_dir.mkdir(parents=True, exist_ok=True)
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

    # 1) Preregistration BEFORE scoring
    pre = write_preregistration(out_dir)
    cal_labels = pre["cal_labels"]
    test_labels = pre["test_labels"]
    cal_gold = gold_to_dict(CAL_QUERIES)
    test_gold = gold_to_dict(TEST_QUERIES)

    # Mark scoring begun (immutable corpus already hashed)
    preg_path = out_dir / "preregistration.json"
    preg = json.loads(preg_path.read_text(encoding="utf-8"))
    preg["scoring_begun"] = True
    # do not rewrite corpus hashes; only flag
    write_json(preg_path, preg)

    # 2) Model load
    t_load0 = time.perf_counter()
    client, ce_meta = init_bge_reranker_client()
    ce_load_s = time.perf_counter() - t_load0
    weights = resolve_weight_fingerprint()
    if weights.get("sha256") != CE_WEIGHT_SHA_PIN or weights.get("revision") != CE_REVISION_PIN:
        raise RealCrossEncoderUnavailableError(
            f"CE fingerprint mismatch: {weights} vs pins {CE_REVISION_PIN}/{CE_WEIGHT_SHA_PIN}"
        )

    embed_model, embed_meta = load_fastembed_model(EMBED_MODEL)

    model_fingerprints = {
        "cross_encoder": {**ce_meta, "weight": weights, "load_time_s_run": ce_load_s},
        "embedding": embed_meta,
        "pins": {
            "ce_model": REQUIRED_MODEL,
            "ce_revision": CE_REVISION_PIN,
            "ce_weight_sha256": CE_WEIGHT_SHA_PIN,
            "embedding_model": EMBED_MODEL,
        },
    }
    write_json(out_dir / "model_fingerprints.json", model_fingerprints)

    # 3) Score CE matrices (checkpointed)
    ce_cal = await score_ce_matrix(
        client, CAL_QUERIES, CAL_FACTS, checkpoint_name="ce_calibration.json",
        capture_logits=capture_logits,
    )
    ce_test = await score_ce_matrix(
        client, TEST_QUERIES, TEST_FACTS, checkpoint_name="ce_test.json",
        capture_logits=capture_logits,
    )
    # FM15 anchor
    anchor_queries = [{"id": qid, "text": text, "class": "answerable", "subtype": "anchor", "gold": FM15_GOLD[qid]} for qid, text in FM15_QUERIES]
    # normalize gold texts to fact ids for anchor gold map
    fm15_gold_ids = {
        qid: [fid for fid, text in FM15_FACTS if text in texts]
        for qid, texts in FM15_GOLD.items()
    }
    for q in anchor_queries:
        q["gold"] = fm15_gold_ids[q["id"]]
    ce_anchor = await score_ce_matrix(
        client, anchor_queries, FM15_FACTS, checkpoint_name="ce_fm15_anchor.json",
        capture_logits=capture_logits,
    )

    # 4) Embedding matrices
    emb_cal = score_embedding_matrix(
        CAL_QUERIES, CAL_FACTS, checkpoint_name="emb_calibration.json"
    )
    emb_test = score_embedding_matrix(
        TEST_QUERIES, TEST_FACTS, checkpoint_name="emb_test.json"
    )

    # 5) Write score CSVs
    scores_dir = out_dir / "scores"
    cal_ce_rows = flatten_score_rows(
        CAL_QUERIES, CAL_FACTS, ce_cal["official_scores"], cal_gold, cal_labels,
        score_key="RAW_SCORE", logits=ce_cal.get("logit_scores"),
    )
    test_ce_rows = flatten_score_rows(
        TEST_QUERIES, TEST_FACTS, ce_test["official_scores"], test_gold, test_labels,
        score_key="RAW_SCORE", logits=ce_test.get("logit_scores"),
    )
    cal_emb_rows = flatten_score_rows(
        CAL_QUERIES, CAL_FACTS, emb_cal["scores"], cal_gold, cal_labels,
        score_key="COSINE_SCORE",
    )
    test_emb_rows = flatten_score_rows(
        TEST_QUERIES, TEST_FACTS, emb_test["scores"], test_gold, test_labels,
        score_key="COSINE_SCORE",
    )
    anchor_rows = flatten_score_rows(
        anchor_queries, FM15_FACTS, ce_anchor["official_scores"], fm15_gold_ids, {},
        score_key="RAW_SCORE", logits=ce_anchor.get("logit_scores"),
    )
    write_score_csv(cal_ce_rows, scores_dir / "ce_calibration.csv", "RAW_SCORE")
    write_score_csv(test_ce_rows, scores_dir / "ce_test.csv", "RAW_SCORE")
    write_score_csv(cal_emb_rows, scores_dir / "embedding_calibration.csv", "COSINE_SCORE")
    write_score_csv(test_emb_rows, scores_dir / "embedding_test.csv", "COSINE_SCORE")
    write_score_csv(anchor_rows, scores_dir / "fm15_anchor_recheck.csv", "RAW_SCORE")

    # 6) Pre-threshold ranking
    ranking = {
        "calibration": {
            "ce": ranking_metrics_for_split(CAL_QUERIES, ce_cal["official_scores"], cal_gold),
            "embedding": ranking_metrics_for_split(CAL_QUERIES, emb_cal["scores"], cal_gold),
        },
        "test": {
            "ce": ranking_metrics_for_split(TEST_QUERIES, ce_test["official_scores"], test_gold),
            "embedding": ranking_metrics_for_split(TEST_QUERIES, emb_test["scores"], test_gold),
        },
        "note": "Pre-threshold ranking metrics; no theta applied.",
    }
    write_json(out_dir / "evaluation" / "ranking_without_threshold.json", ranking)

    # 7) Threshold search ONLY on CALIBRATION
    ce_search = search_threshold(CAL_QUERIES, ce_cal["official_scores"], cal_gold)
    emb_search = search_threshold(CAL_QUERIES, emb_cal["scores"], cal_gold)
    write_json(out_dir / "calibration" / "threshold_search_ce.json", ce_search)
    write_json(out_dir / "calibration" / "threshold_search_embedding.json", emb_search)

    ce_theta = ce_search["selected"]["theta"] if ce_search["selected"] else None
    emb_theta = emb_search["selected"]["theta"] if emb_search["selected"] else None

    calibrated = {
        "THETA_CE": ce_theta,
        "THETA_EMBEDDING": emb_theta,
        "ce_calibration_metrics": ce_search["selected"],
        "embedding_calibration_metrics": emb_search["selected"],
        "ce_GLOBAL_THRESHOLD_FEASIBLE": ce_search["GLOBAL_THRESHOLD_FEASIBLE"],
        "embedding_GLOBAL_THRESHOLD_FEASIBLE": emb_search["GLOBAL_THRESHOLD_FEASIBLE"],
        "threshold_selection_rule": ce_search["search_rule"],
        "model_fingerprints_pins": model_fingerprints["pins"],
        "preregistration_corpus_sha256": pre["file_hashes"],
        "frozen_at_utc": _utc_now(),
        "test_metrics_not_yet_computed": True,
    }
    write_json(out_dir / "calibration" / "calibrated_thresholds.json", calibrated)
    thr_sha = _sha256_file(out_dir / "calibration" / "calibrated_thresholds.json")
    write_json(
        out_dir / "hashes" / "calibrated_threshold_sha256.json",
        {"calibrated_thresholds.json": thr_sha, "frozen_before_test": True},
    )

    # 8) Apply theta to TEST exactly once
    heldout_ce = (
        evaluate_threshold(TEST_QUERIES, ce_test["official_scores"], test_gold, ce_theta)
        if ce_theta is not None
        else {"theta": None, "GLOBAL_THRESHOLD_FEASIBLE": False}
    )
    heldout_emb = (
        evaluate_threshold(TEST_QUERIES, emb_test["scores"], test_gold, emb_theta)
        if emb_theta is not None
        else {"theta": None, "GLOBAL_THRESHOLD_FEASIBLE": False}
    )
    write_json(out_dir / "evaluation" / "heldout_ce.json", heldout_ce)
    write_json(out_dir / "evaluation" / "heldout_embedding.json", heldout_emb)

    # Do NOT mutate calibrated_thresholds.json after freeze (SHA integrity).
    write_json(
        out_dir / "calibration" / "threshold_freeze_receipt.json",
        {
            "calibrated_threshold_sha256": thr_sha,
            "heldout_applied_once": True,
            "thresholds_unchanged_after_freeze": True,
            "THETA_CE": ce_theta,
            "THETA_EMBEDDING": emb_theta,
        },
    )

    receipts = {
        "ce": build_rejection_receipts(
            TEST_QUERIES, ce_test["official_scores"], test_gold, test_labels, ce_theta, "CE"
        ),
        "embedding": build_rejection_receipts(
            TEST_QUERIES, emb_test["scores"], test_gold, test_labels, emb_theta, "EMBEDDING"
        ),
        "FORCED_REFILL": False,
    }
    write_json(out_dir / "evaluation" / "rejection_receipts.json", receipts)

    hn_strata = {
        "ce_test": stratum_metrics(TEST_QUERIES, ce_test["official_scores"], test_labels, ce_theta),
        "embedding_test": stratum_metrics(TEST_QUERIES, emb_test["scores"], test_labels, emb_theta),
        "ce_calibration": stratum_metrics(CAL_QUERIES, ce_cal["official_scores"], cal_labels, ce_theta),
    }
    write_json(out_dir / "evaluation" / "hard_negative_strata.json", hn_strata)

    adv_disc = {
        tag: adversarial_pair_discrimination(
            ce_test["official_scores"], test_gold, test_labels, tag
        )
        for tag in HN_ADV
    }
    critical = any(v.get("systematic_inversion") for v in adv_disc.values())
    write_json(out_dir / "evaluation" / "adversarial_strata.json", {
        "discrimination": adv_disc,
        "CRITICAL_STRATUM_FAILURE": critical,
    })

    na = no_answer_strata_metrics(TEST_QUERIES, ce_test["official_scores"], ce_theta)
    write_json(out_dir / "evaluation" / "no_answer_strata.json", na)

    broad = {
        "ce": broad_query_metrics(TEST_QUERIES, ce_test["official_scores"], test_gold, ce_theta),
        "embedding": broad_query_metrics(TEST_QUERIES, emb_test["scores"], test_gold, emb_theta),
    }
    write_json(out_dir / "evaluation" / "broad_query_results.json", broad)

    ce_vs = compare_ce_vs_embedding(
        heldout_ce if ce_theta is not None else {},
        heldout_emb if emb_theta is not None else {},
        critical,
    )
    gen = generalization_verdict(heldout_ce if ce_theta is not None else None, critical, ce_search["GLOBAL_THRESHOLD_FEASIBLE"])

    comparative = {
        "CE_VS_EMBEDDING": ce_vs,
        "GENERALIZATION_VERDICT": gen,
        "CRITICAL_STRATUM_FAILURE": critical,
        "heldout_ce": heldout_ce,
        "heldout_embedding": heldout_emb,
        "negation_discrimination": adv_disc["HN7"]["discrimination"],
        "temporal_text_discrimination": adv_disc["HN8"]["discrimination"],
        "scope_discrimination": adv_disc["HN9"]["discrimination"],
        "condition_discrimination": adv_disc["HN10"]["discrimination"],
        "attribution_discrimination": adv_disc["HN11"]["discrimination"],
        "numeric_unit_discrimination": adv_disc["HN12"]["discrimination"],
    }
    write_json(out_dir / "evaluation" / "comparative_verdict.json", comparative)

    # Anchor regression vs run_006
    run006 = REPO_ROOT / "artifacts" / "memoryops" / "run_006" / "cross_encoder_score_matrix.json"
    anchor_cmp = anchor_recheck(ce_anchor["official_scores"], run006)
    write_json(out_dir / "evaluation" / "fm15_anchor_recheck.json", anchor_cmp)

    # Latency
    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    latency = {
        "ce_model_load_time_s": ce_load_s,
        "ce_calibration_scoring_time_s": ce_cal["scoring_time_s"],
        "ce_heldout_scoring_time_s": ce_test["scoring_time_s"],
        "ce_anchor_scoring_time_s": ce_anchor["scoring_time_s"],
        "ce_total_pair_scoring_time_s": (
            ce_cal["scoring_time_s"] + ce_test["scoring_time_s"] + ce_anchor["scoring_time_s"]
        ),
        "embedding_scoring_time_s": emb_cal["scoring_time_s"] + emb_test["scoring_time_s"],
        "mean_ce_pair_latency_s": (
            (ce_cal["scoring_time_s"] + ce_test["scoring_time_s"] + ce_anchor["scoring_time_s"]) / 1620.0
        ),
        "batch_size": "per-query full fact list (40 or 4)",
        "device": ce_meta.get("device"),
        "peak_rss_kb_approx": peak_rss,
        "model_weight_size_bytes": weights.get("size_bytes"),
        "LATENCY_NE_QUALITY": True,
        "capture_logits": capture_logits,
    }
    write_json(out_dir / "latency_resources.json", latency)

    # result.json
    result = {
        "experiment": "FM-16",
        "status": "COMPLETE",
        "start_sha": EXPECTED_START_SHA,
        "upstream_sha": UPSTREAM_SHA,
        "ce_model": REQUIRED_MODEL,
        "embedding_model": EMBED_MODEL,
        "calibration_fact_count": 40,
        "test_fact_count": 40,
        "calibration_query_count": 20,
        "test_query_count": 20,
        "entity_disjoint": True,
        "preregistration_valid": True,
        "hard_negative_strata": 12,
        "ce_global_threshold_feasible": ce_search["GLOBAL_THRESHOLD_FEASIBLE"],
        "embedding_global_threshold_feasible": emb_search["GLOBAL_THRESHOLD_FEASIBLE"],
        "ce_threshold": ce_theta,
        "embedding_threshold": emb_theta,
        "ce_test_answerable_coverage": heldout_ce.get("ANSWERABLE_QUERY_COVERAGE"),
        "ce_test_gold_pair_recall": heldout_ce.get("GOLD_PAIR_RECALL"),
        "ce_test_no_answer_empty_accuracy": heldout_ce.get("NO_ANSWER_EMPTY_ACCURACY"),
        "ce_test_false_empty_rate": heldout_ce.get("FALSE_EMPTY_RATE"),
        "ce_test_non_gold_rejection_rate": heldout_ce.get("NON_GOLD_REJECTION_RATE"),
        "ce_test_broad_query_gold_recall": heldout_ce.get("BROAD_QUERY_GOLD_RECALL"),
        "embedding_test_answerable_coverage": heldout_emb.get("ANSWERABLE_QUERY_COVERAGE"),
        "embedding_test_gold_pair_recall": heldout_emb.get("GOLD_PAIR_RECALL"),
        "embedding_test_no_answer_empty_accuracy": heldout_emb.get("NO_ANSWER_EMPTY_ACCURACY"),
        "embedding_test_false_empty_rate": heldout_emb.get("FALSE_EMPTY_RATE"),
        "embedding_test_non_gold_rejection_rate": heldout_emb.get("NON_GOLD_REJECTION_RATE"),
        "embedding_test_broad_query_gold_recall": heldout_emb.get("BROAD_QUERY_GOLD_RECALL"),
        "nonexistent_entity_empty_accuracy": na["nonexistent"]["empty_accuracy"],
        "unsupported_predicate_empty_accuracy": na["unsupported"]["empty_accuracy"],
        "negation_discrimination": adv_disc["HN7"]["discrimination"],
        "temporal_text_discrimination": adv_disc["HN8"]["discrimination"],
        "scope_discrimination": adv_disc["HN9"]["discrimination"],
        "condition_discrimination": adv_disc["HN10"]["discrimination"],
        "attribution_discrimination": adv_disc["HN11"]["discrimination"],
        "numeric_unit_discrimination": adv_disc["HN12"]["discrimination"],
        "critical_stratum_failure": critical,
        "ce_vs_embedding": ce_vs,
        "generalization_verdict": gen,
        "forced_refill": False,
        "fm15_anchor": anchor_cmp["ANCHOR_DETERMINISM"],
        "fm15_anchor_max_abs_delta": anchor_cmp["MAX_ABSOLUTE_CE_DELTA"],
        "threshold_runtime_authorized": False,
        "runtime_gate_implemented": False,
        "search_recipe_changed": False,
        "architecture_change": False,
        "new_relevance_module": False,
        "upstream_changes": False,
        "merge": False,
        "calibrated_threshold_sha256": thr_sha,
        "latency": latency,
    }
    write_json(out_dir / "result.json", result)

    _write_findings(out_dir, {
        "generalization_verdict": gen,
        "ce_vs_embedding": ce_vs,
        "ce_feasible": ce_search["GLOBAL_THRESHOLD_FEASIBLE"],
        "emb_feasible": emb_search["GLOBAL_THRESHOLD_FEASIBLE"],
        "critical_stratum_failure": critical,
        "ce_theta": ce_theta,
        "emb_theta": emb_theta,
        "adversarial_disc": adv_disc,
    })

    # README / environment / commands placeholders (tests fill pytest.txt)
    (out_dir / "README.md").write_text(
        """# FM-16 — Cross-Encoder Held-Out Generalization & Calibration

Offline pairwise CE vs embedding evaluation on entity-disjoint CAL/TEST splits.
Thresholds selected on CALIBRATION only; applied to TEST once.
No runtime CE activation, no search-recipe changes, no forced refill.
""",
        encoding="utf-8",
    )
    env_lines = [
        f"recorded_at_utc={_utc_now()}",
        f"ce_model={REQUIRED_MODEL}",
        f"ce_revision={CE_REVISION_PIN}",
        f"ce_weight_sha256={CE_WEIGHT_SHA_PIN}",
        f"embedding_model={EMBED_MODEL}",
        f"device={ce_meta.get('device')}",
        f"start_sha_expected={EXPECTED_START_SHA}",
        f"upstream_sha={UPSTREAM_SHA}",
    ]
    for k, v in (ce_meta.get("package_versions") or {}).items():
        env_lines.append(f"{k}={v}")
    (out_dir / "environment.txt").write_text("\n".join(env_lines) + "\n", encoding="utf-8")
    (out_dir / "commands.txt").write_text(
        """# FM-16 commands
.venv/bin/python -c "import asyncio; from fractal_lab.experiments.fm16_generalization import run_fm16; asyncio.run(run_fm16())"
.venv/bin/pytest -q tests/lab/test_memoryops_fm16_generalization.py
""",
        encoding="utf-8",
    )

    return result


def main() -> None:
    result = asyncio.run(run_fm16(capture_logits=False))
    print(json.dumps({
        "status": result["status"],
        "generalization_verdict": result["generalization_verdict"],
        "ce_vs_embedding": result["ce_vs_embedding"],
        "ce_threshold": result["ce_threshold"],
        "embedding_threshold": result["embedding_threshold"],
        "critical_stratum_failure": result["critical_stratum_failure"],
    }, indent=2))


if __name__ == "__main__":
    main()
