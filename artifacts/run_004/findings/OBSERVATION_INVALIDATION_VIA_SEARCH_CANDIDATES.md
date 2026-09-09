# OBSERVATION: contradiction via invalidation candidates, not related_edges

RUNTIME_LANGUAGE edges target different nodes (Python vs Rust), so `get_between_nodes` related_edges was empty for the NEW edge. Provider EdgeDuplicate receipt showed:

- existing_facts: []
- invalidation_candidates: [OLD Python @ idx 0, Alice OWNED_BY @ idx 1]
- contradicted_facts: [0]  # OLD marker selected from context; Alice not selected

Invalidation still applied: OLD.invalid_at = NEW.valid_at (= T2). expired_at set to wall-clock utc_now() at write time (not T2).
