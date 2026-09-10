# F-FM-CROSS-PROJECT-CONTRADICTION (lab stub)

**Observed (pre-fix):** ingesting `ProjectNova uses Rust` could mark
`ProjectOrion uses Python` as contradicted because
`DeterministicTemporalLLMClient._edge_duplicate` treated any Rust language fact
as invalidating any Python RUNTIME_LANGUAGE fact, ignoring project subject.

**Impact:** FM multi-project fixtures temporarily showed Python `invalid_at≈T4`
instead of only after T5 Orion language update.

**Mitigation (lab-only):** require matching `ProjectOrion` / `ProjectNova`
subject before language contradiction when the new fact names a project.
Does **not** change Graphiti; P5 marker-based path still preferred when markers present.

**Invariant reminder:** RETRIEVED≠CURRENT; claims remain fixture-scoped.
