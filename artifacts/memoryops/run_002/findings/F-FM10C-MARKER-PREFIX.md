# F-FM10C-MARKER-PREFIX (lab note)

FM-10C reopen test uses `FM5_MARKER_FM10C_*` so `DeterministicTemporalLLMClient`
includes the persistence token in the WORKS_ON fact via existing `_EXTENDED_MARKER_RE`.

A novel `FM10C_MARKER_*` prefix is **not** added to the stub (HARD NO: do not expand
DeterministicTemporalLLMClient into huge rules). Search-by-marker then fails because
the token never lands in edge.fact.

Invariant: stub marker recognition stays minimal; tests reuse known prefixes.
