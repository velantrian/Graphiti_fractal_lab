# MASTER PLAN: Полный путь к Fractal Memory v2 (Historical Plan)

> **Note**: This document outlines the original 9-day implementation plan.
> The project has successfully completed the "Foundation" phase and evolved into a "Graphiti Native" architecture (v2.0).
> Key deviations from this original plan:
> - **Custom Entities**: Simplified in favor of standard Graphiti entities + labeling.
> - **L2/L3**: Implemented using Communities and LLM Synthesis (instead of manual patterns).
> - **Structure**: `scripts/` folder is much richer than planned.

## 📅 TIMELINE: 9 дней + недели интеграции

### WEEK 1: FOUNDATION (Days 1-9)

```
┌─────────────────────────────────────────────────────────┐
│ DAY 1: Setup & First Episode (4 часа)                  │
├─────────────────────────────────────────────────────────┤
│ ✓ Docker Neo4j                                          │
│ ✓ Python venv + Graphiti                               │
│ ✓ First episode added                                  │
│ ✓ Verify in Neo4j Browser                              │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ DAY 2: Custom Entity Types (6 часов)                   │
├─────────────────────────────────────────────────────────┤
│ ✓ Define 4 Pydantic models                             │
│ ✓ Auto-extraction of custom entities                   │
│ ✓ 3 test episodes with different sources               │
│ ✓ Search verification                                  │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ DAY 3: Visualization (4 часа)                          │
├─────────────────────────────────────────────────────────┤
│ ✓ Neo4j Browser Cypher queries                         │
│ ✓ Visual graph confirmation                            │
│ ✓ Quality metrics (no duplicates)                      │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ DAY 4: Context Retrieval (5 часов)                     │
├─────────────────────────────────────────────────────────┤
│ ✓ Multiple search strategies                           │
│ ✓ Context window builder                               │
│ ✓ Test with real queries                               │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ DAY 5: L1 Consolidation (4 часа)                       │
├─────────────────────────────────────────────────────────┤
│ ✓ Recent context extraction (24h window)               │
│ ✓ Automatic summarization                              │
│ ✓ Test with different time windows                     │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ DAY 6: L2 Semantic Patterns (5 часов)                  │
├─────────────────────────────────────────────────────────┤
│ ✓ Relationship pattern extraction                      │
│ ✓ Semantic role identification                         │
│ ✓ Pattern confidence scoring                           │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ DAY 7: L3 Fractal Abstractions (6 часов)               │
├─────────────────────────────────────────────────────────┤
│ ✓ Hierarchical position mapping                        │
│ ✓ Evolution trajectory tracking                        │
│ ✓ Contradiction detection                              │
│ ✓ Fractal self-similarity validation                   │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ DAY 8: Interactive Visualization (5 часов)             │
├─────────────────────────────────────────────────────────┤
│ ✓ Graph export to JSON                                 │
│ ✓ D3.js interactive visualization                      │
│ ✓ Drag-drop node positioning                           │
│ ✓ Hover tooltips                                       │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ DAY 9: Performance & Profiling (4 часа)                │
├─────────────────────────────────────────────────────────┤
│ ✓ Benchmark add_episode                                │
│ ✓ Benchmark search                                     │
│ ✓ Memory usage tracking                                │
│ ✓ Performance report & recommendations                 │
└─────────────────────────────────────────────────────────┘

TOTAL: 43 часа = ~5-6 дней интенсивной работы
```

---

## 🗂️ PROJECT STRUCTURE

```
fractal_memory_v2/
├── .env                           # API keys & DB connection
├── requirements.txt               # pip dependencies
│
├── core/
│   ├── __init__.py
│   ├── graphiti_client.py        # Graphiti wrapper
│   ├── custom_entities.py         # Pydantic models
│   └── config.py                 # Constants & settings
│
├── layers/
│   ├── __init__.py
│   ├── l1_consolidation.py       # Episode summaries
│   ├── l2_semantic.py            # Relationship patterns
│   └── l3_fractal.py             # Hierarchical abstractions
│
├── queries/
│   ├── __init__.py
│   ├── search_strategies.py      # Different search recipes
│   ├── context_builder.py        # LLM context generation
│   └── quality_check.py          # Data quality metrics
│
├── visualization/
│   ├── __init__.py
│   ├── export.py                 # Graph export to JSON
│   ├── visualization.html        # D3.js interactive view
│   └── graph_data.json           # Generated graph data
│
├── benchmarks/
│   ├── __init__.py
│   └── performance.py            # Performance profiling
│
├── tests/
│   ├── __init__.py
│   ├── test_entities.py          # Entity extraction tests
│   ├── test_layers.py            # Layer functionality tests
│   └── test_search.py            # Search functionality tests
│
├── docs/
│   ├── FULL_SPEC.md             # Complete specification
│   ├── QUICK_START.md           # 30-minute setup
│   ├── API_REFERENCE.md         # All function signatures
│   └── ARCHITECTURE.md          # System design
│
└── main.py                       # Entry point for tests
```

---

## 🚀 EXECUTION CHECKLIST

### Before Starting
- [ ] Read FULL_SPEC.md completely
- [ ] Docker desktop installed
- [ ] Python 3.10+ installed
- [ ] OpenAI API key ready
- [ ] Plan calendar with 9 days

### Day-by-Day Execution
- [ ] **Day 1:** Follow Quick_Start_30min.md exactly
- [ ] **Day 2:** Implement custom_entities.py from Day_2 doc
- [ ] **Day 3:** Copy Cypher queries, run in Neo4j Browser
- [ ] **Day 4:** Test all search strategies
- [ ] **Day 5:** Implement L1 consolidation
- [ ] **Day 6:** Implement L2 semantic extraction
- [ ] **Day 7:** Implement L3 fractal abstractions
- [ ] **Day 8:** Run visualization export, open HTML file
- [ ] **Day 9:** Run benchmarks, get performance report

### After Day 9
- [ ] All 9 documents reviewed
- [ ] Code organized in structure above
- [ ] All tests passing
- [ ] Ready for agent integration

---

## 📊 SUCCESS METRICS

### Day 1 (Setup)
```
✅ Neo4j running
✅ Graphiti initialized
✅ 3+ nodes visible in browser
✅ Search returns results
```

### Day 2 (Custom Entities)
```
✅ 4 Pydantic models defined
✅ Custom types extracted automatically
✅ Search finds custom entities
✅ No errors in extraction
```

### Day 3 (Visualization)
```
✅ Cypher queries execute
✅ Nodes colored by type
✅ Relationships visible
✅ No duplicate nodes
```

### Day 4 (Context)
```
✅ Multiple search strategies work
✅ Context window builds properly
✅ Relevance scores calculated
```

### Day 5 (L1)
```
✅ Recent context extracted
✅ Time window respected
✅ Narrative summary generated
```

### Day 6 (L2)
```
✅ Relationship patterns identified
✅ Confidence scores assigned
✅ Semantic roles determined
```

### Day 7 (L3)
```
✅ Fractal hierarchy created
✅ System role determined
✅ Evolution tracked
✅ Self-similarity validated
```

### Day 8 (Viz)
```
✅ JSON export works
✅ D3.js renders graph
✅ Nodes draggable
✅ Tooltips show info
```

### Day 9 (Performance)
```
✅ add_episode: <1000ms ✓
✅ search: <100ms ✓
✅ Memory: <2GB ✓
✅ Report generated ✓
```

---

## 📞 TROUBLESHOOTING QUICK LINKS

| Problem | Solution |
|---------|----------|
| "Connection refused" | Check `docker ps`, restart Neo4j |
| "OPENAI_API_KEY not found" | Update .env, reload shell |
| "Timeout on indices" | Wait 15-20 seconds, retry |
| "Custom entities not extracted" | Verify Pydantic models have `description` fields |
| "Search returns no results" | Check episodes were added with `await graphiti.add_episode()` |
| "D3.js graph empty" | Run `python visualization_export.py` first |
| "Performance slow" | Check Neo4j heap size (default 512MB) |

---

## 🎯 NEXT PHASES (Week 2+)

### Week 2: Agent Integration
- [ ] Connect to LLM agent logic
- [ ] Test context retrieval in prompts
- [ ] Validate relevance of returned context
- [ ] Measure token efficiency

### Week 3: Self-Learning Module
- [ ] Implement Judge agent
- [ ] Feedback loop: Query → Response → Evaluation
- [ ] Write feedback nodes to graph
- [ ] Temporal invalidation of outdated facts

### Week 4: Advanced Features
- [ ] Graph analytics (centrality, clustering)
- [ ] Recommendation engine
- [ ] Anomaly detection
- [ ] Multi-user isolation

---

## 🏆 COMPLETION CHECKLIST

```
FOUNDATION (Week 1)
  ✓ Vanilla Graphiti running
  ✓ Custom entity extraction
  ✓ All 3 layers functional
  ✓ Interactive visualization
  ✓ Performance baseline

INTEGRATION (Week 2)
  ✓ Agent connected to memory
  ✓ Context retrieval working
  ✓ Relevance validated

INTELLIGENCE (Week 3)
  ✓ Judge agent evaluating
  ✓ Feedback loop active
  ✓ Memory self-improving

PRODUCTION (Week 4+)
  ✓ Advanced analytics
  ✓ Recommendations
  ✓ Multi-user ready
  ✓ Deploy to production
```

---

**You are 9 days away from a fully functional fractal memory system.**

**Start with Day 1. Follow the docs precisely. Ship daily. 🚀**