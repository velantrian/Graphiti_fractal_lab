from __future__ import annotations


def assert_no_group_leak(items: list[dict], allowed: set[str], field: str = "group_id") -> None:
    """
    Assert that all dict items have field value within allowed set.
    """
    bad = [it for it in items if it.get(field) not in allowed]
    if bad:
        bad_groups = {it.get(field) for it in bad}
        raise AssertionError(f"Found items outside allowed groups: {bad_groups} (allowed={allowed})")


