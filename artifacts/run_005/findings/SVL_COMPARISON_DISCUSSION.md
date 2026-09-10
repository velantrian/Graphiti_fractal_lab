# SVL comparison discussion (P6)

Read-only comparison against SVL `model.py`. **Not imported/copied into Graphiti.**

```json
{
  "source": "velantrian/-Velantrim-State-Validation-Lab-/src/state_validation_lab/model.py",
  "read_only": true,
  "imported_into_graphiti": false,
  "svl_invariant": "SVL ResearchStateModel.restore() writes RESTORED_STALE_CANDIDATE with applicable=False into a quarantined candidate store; it never overwrites current disposition. reconcile() cannot clear later revoke/erase/supersede.",
  "graphiti_p6_b_contrast_this_fixture_only": "P6-B EntityEdge.save(SNAPSHOT_PRE) on Falkor MERGE SET e=$edge_data can overwrite the live edge's invalid_at when classification is STALE_RESURRECTION_OBSERVED. That is RESTORED_BYTES onto the live graph row, not an SVL-style quarantined candidate. This does NOT imply 'Falkor unsafe' universally nor 'SVL must integrate'.",
  "graphiti_p6_a_contrast": "P6-A uses add_episode (high-level). Classification SAFE_HIGH_LEVEL vs RESURRECTION_HIGH_LEVEL is separate from B's low-level save path.",
  "forbidden_claims_not_made": [
    "Graphiti prevents resurrection universally",
    "Falkor unsafe",
    "SVL must integrate"
  ]
}
```
