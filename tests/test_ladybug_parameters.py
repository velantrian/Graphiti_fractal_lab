"""Bound data values through the real Ladybug driver, never string interpolation."""

import pytest

from fractal_lab.backends.ladybug_adapter import LadybugAdapter


@pytest.mark.parametrize("value", ["O'Brien", "'}) MATCH (n) DETACH DELETE n //", "заметка\n$token"])
def test_bound_text_is_literal_and_preserves_existing_node(tmp_path, value):
    adapter = LadybugAdapter(tmp_path / "parameters.lbdb")
    adapter.connect()
    try:
        adapter.ensure_smoke_schema()
        adapter.execute("CREATE (:LabPerson {name: 'control', age: 99})")
        adapter.execute("CREATE (:LabPerson {name: $name, age: $age})", {"name": value, "age": 7})
        rows = list(adapter.execute("MATCH (p:LabPerson) WHERE p.name = $name RETURN p.name, p.age",
                                    {"name": value}))
        assert rows == [[value, 7]]
        assert list(adapter.execute("MATCH (p:LabPerson) RETURN count(p)")) == [[2]]
    finally:
        adapter.close()


def test_empty_parameter_mapping_and_unconnected_guard(tmp_path):
    adapter = LadybugAdapter(tmp_path / "empty.lbdb")
    with pytest.raises(RuntimeError, match="not connected"):
        adapter.execute("RETURN 1", {})
    adapter.connect()
    try:
        assert list(adapter.execute("RETURN 1", {})) == [[1]]
    finally:
        adapter.close()


def test_bound_value_survives_close_and_reopen(tmp_path):
    adapter = LadybugAdapter(tmp_path / "reopen.lbdb")
    value = "source 'quoted'\nновая строка"
    adapter.connect()
    try:
        adapter.ensure_smoke_schema()
        adapter.execute("CREATE (:LabPerson {name: $name, age: $age})", {"name": value, "age": 7})
    finally:
        adapter.close()
    adapter.connect()
    try:
        assert list(adapter.execute("MATCH (p:LabPerson) RETURN p.name, p.age")) == [[value, 7]]
    finally:
        adapter.close()
