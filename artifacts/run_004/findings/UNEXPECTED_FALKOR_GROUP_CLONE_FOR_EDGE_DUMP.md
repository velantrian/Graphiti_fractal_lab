# UNEXPECTED: Falkor group-graph required for EntityEdge.get_by_group_ids

## Observation
After `open_lab_graphiti(..., database="default_db")` reopen, `EntityEdge.get_by_group_ids(driver, [group_id])` raised `GroupsEdgesNotFoundError` even though `Graphiti.search(..., group_ids=[group_id])` returned the same edges with full temporal metadata.

## Cause (Graphiti 0.29.3 + FalkorDBLite)
Falkor stores each `group_id` as a separate graph database. `search` / `add_episode` use `@handle_multiple_group_ids` to clone the driver to that graph. Raw `EntityEdge.get_by_group_ids` does **not** — it queries `driver._database` as-is.

## Lab mitigation (not a Graphiti patch)
P5 dump helper clones: `driver.clone(database=group_id)` before `get_by_group_ids`. Documented in test `_dump_group_edges`.

## Classification
Lab fixture plumbing note — not FIXTURE_FAIL for temporal contradiction itself once clone is applied. Relevant for any future driver-level edge dumps on Falkor.
