# OBSERVATION: search hit ≠ temporally current

After T2 contradiction, `Graphiti.search("ProjectOrion RUNTIME_LANGUAGE")` returned **both** OLD (Python, invalid_at=T2) and NEW (Rust, invalid_at=None).

P5-C therefore classifies TEMPORALLY_CURRENT / TEMPORALLY_EXPIRED from edge metadata at Q1/Q2 rather than treating retrieval as applicability. Graphiti 0.29.3 basic `search` does not apply a reference_time "currently valid" filter by default (SearchFilters.valid_at/invalid_at exist but were not assumed).
