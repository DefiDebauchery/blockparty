"""Parameter preparation utilities for Etherscan API calls.

Handles conversion of list parameters to comma-separated strings with
limit enforcement.
"""

from __future__ import annotations


def prepare_list_param(
    value: str | list[str],
    *,
    max_items: int,
    param_name: str,
) -> str:
    """Convert a single string or list of strings to a comma-separated string.

    When *value* is already a plain string it is returned unchanged (it may
    contain commas the caller supplied manually).  When it is a list, items
    are joined with ``","`` and the length is validated against *max_items*.

    Args:
        value: A single string or list of strings.
        max_items: Maximum number of items allowed by the API.
        param_name: Name used in the error message on overflow.

    Returns:
        A comma-separated string ready for the query parameter.

    Raises:
        ValueError: If the list exceeds *max_items*.
    """
    if isinstance(value, str):
        return value

    if len(value) > max_items:
        raise ValueError(f"{param_name} accepts at most {max_items} items, got {len(value)}")
    return ",".join(value)
