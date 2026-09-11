# 🛑 STOP BOUNDARY — FM-17-pre

## AUTHORIZED NOW (this commit)

- ✅ Write protocol document
- ✅ Write annotation schema / template / guide
- ✅ Define exact offline ablation rules (preregistered)
- ✅ Define preregistered metrics + falsification table
- ✅ Reference frozen `artifacts/memoryops/run_007` inputs
- ✅ Commit docs/protocol artifacts on experiment branch
- ❌ **DO NOT MERGE** to main / upstream Fractal

## NOT AUTHORIZED NOW

- ❌ Execute FM-17-pre ablation
- ❌ Produce ablation `result.json` / survivor receipts as completed run
- ❌ Rescore CE or embeddings
- ❌ Download / train new model
- ❌ LLM recognition experiment
- ❌ Graph / path experiment
- ❌ Specialized SLM experiment
- ❌ Modify Graphiti runtime / search recipe
- ❌ Architecture promotion / product change
- ❌ Treat oracle pass as implementation readiness

## After protocol review — user decision only

| Code | Decision |
|------|----------|
| **A** | REQUEST FIXES |
| **B** | SEND FOR INDEPENDENT REVIEW |
| **C** | AUTHORIZE OFFLINE ORACLE ABLATION |
| **D** | CANCEL / DEFER |

**Do not assume C.**

## Interpretation lock

```
ORACLE STRUCTURE ≠ PREDICTED STRUCTURE
ORACLE FILTER PASS ≠ REAL STRUCTURED PIPELINE PASS
SUPPORTED_AS_USEFUL_SIGNAL ≠ IMPLEMENTATION_READINESS
```
