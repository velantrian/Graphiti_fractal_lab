# Ladybug lab parameter binding

Draft laboratory change based on `aecb3da8fd24f92a2c1d4478505520490a800111`.

`LadybugAdapter.execute(query, parameters)` previously raised NotImplementedError
for a non-empty mapping. The pinned `ladybug==0.20.3` Connection already supports
value binding, so the adapter now delegates parameters directly to that driver.
It never formats source or note values into the Cypher string.

Tests use real on-disk Ladybug databases and cover quotes, a Cypher-looking attack
string, Unicode, newlines, dollar signs, an empty mapping, the unconnected guard,
an unaffected existing node, and persistence through close/reopen in one process.
The original four lab smoke tests plus five new cases produce **9 passed** locally,
Python 3.12.14 / ladybug 0.20.3. The initial three literal-value tests failed on the
baseline because the adapter explicitly did not implement parameter binding.

```bash
python -m pytest tests/test_ladybug_smoke.py tests/test_sqlite_meta.py \
  tests/test_ladybug_parameters.py -q
```

Only data values are bound. Query structure is still trusted caller input; this
does not authorize arbitrary query execution or add an authorization boundary.
Close/reopen is not a crash or power-loss test. Graphiti driver compatibility,
temporal semantics, Neo4j parity, migration and active Fractal memory authority
remain unvalidated/unchanged. No mirrored upstream runtime, stubs or model code changed.

This is original adapter code using the installed driver's documented signature.
No external donor implementation, credentials or source data were imported.
