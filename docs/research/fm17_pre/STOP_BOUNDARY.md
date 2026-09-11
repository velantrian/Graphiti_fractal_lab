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
- ❌ Annotate real CAL/TEST
- ❌ Fabricate a second annotator
- ❌ Use gold/HN/CE/embeddings to build A1/A2 STRUCTURAL fields

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
COMBINED QUERY+FACT ORACLE CEILING ≠ DEPLOYABLE PIPELINE
A3 COMPONENT RETENTION ≠ A1/A2 COMPONENT IDENTIFICATION
HIGH UNRESOLVED RATE ≠ STRUCTURAL SUCCESS
```

After v1.2: **SEND FM-17-PRE v1.2 TO MANUS FOR FINAL INDEPENDENT ENFORCEMENT RE-REVIEW.**

Validator PASS ≠ ablation authorization. `GO_ALLOWED` is an integrity bit only.

```
INVALID INPUT → FAIL CLOSED → STOP
```
  
Do not start annotation or ablation.
