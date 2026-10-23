"""``agentproof.models.common``: the recursive JSON value alias and the status literal."""

from types import NoneType
from typing import TypeAliasType, get_args, get_origin

from agentproof.models.common import STATUSES, JsonValue, Status


def test_json_value_is_a_named_recursive_type_alias() -> None:
    assert isinstance(JsonValue, TypeAliasType)
    assert JsonValue.__name__ == "JsonValue"
    members = get_args(JsonValue.__value__)
    assert set(members[:5]) == {NoneType, bool, int, float, str}
    # The alias names itself inside ``list`` and ``dict`` so nesting is unbounded.
    # Compared structurally: the ``str()`` of a TypeAliasType is qualified on 3.15+.
    list_member, dict_member = members[5:]
    assert get_origin(list_member) is list
    assert get_args(list_member) == (JsonValue,)
    assert get_origin(dict_member) is dict
    assert get_args(dict_member) == (str, JsonValue)


def test_status_is_the_four_value_literal() -> None:
    assert get_args(Status) == ("passed", "failed", "error", "skipped")


def test_statuses_tuple_matches_the_literal_in_order() -> None:
    assert isinstance(STATUSES, tuple)
    assert STATUSES == get_args(Status)
    assert len(set(STATUSES)) == len(STATUSES)
