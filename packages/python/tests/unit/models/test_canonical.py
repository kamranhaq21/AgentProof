"""``agentproof.models.canonical``: the golden byte identity, the compact form, the volatile list.

The golden file ``tests/golden/canonical-1.json`` was produced once by ``dumps`` of
``GOLDEN_INPUT`` and is compared byte for byte, so this test fails on either CI platform
if the serializer, the float repr, the key order, or the line endings ever change.
"""

import json
import math
from collections.abc import Callable
from pathlib import Path

import pytest

from agentproof.models.canonical import VOLATILE_PATHS, dumps, dumps_compact
from agentproof.models.common import JsonValue

GOLDEN_FILE = Path(__file__).resolve().parents[2] / "golden" / "canonical-1.json"

# Keys deliberately out of order, with upper and lower case, unicode outside Latin-1 and
# the BMP, escapes, large and negative ints, floats whose repr is stable across CPython
# minors, bools, null, and empty containers.
GOLDEN_INPUT: JsonValue = {
    "zeta": True,
    "version": 1,
    "title": "golden é ü 日本語 🎉",
    "nothing": None,
    "numbers": [0, -1, 42, 9007199254740993, 0.1, 2.5, -3.75, 1e-7, 10.0],
    "nested": {"b": [1, {"d": 2, "c": 3}], "a": "x", "empty_list": [], "empty_object": {}},
    "text": 'line one\nline two\ttab "quoted" back\\slash',
    "flags": [True, False, None],
    "Uppercase": "sorts before lowercase",
}

COMPACT_INPUT: JsonValue = {"b": [1, {"d": 2, "c": 3}], "a": "x"}
COMPACT_EXPECTED = '{"a":"x","b":[1,{"c":3,"d":2}]}'


def test_dumps_matches_the_committed_golden_file_byte_for_byte() -> None:
    assert dumps(GOLDEN_INPUT).encode("utf-8") == GOLDEN_FILE.read_bytes()


def test_golden_file_is_utf8_without_bom_lf_only_with_one_trailing_newline() -> None:
    data = GOLDEN_FILE.read_bytes()
    assert not data.startswith(b"\xef\xbb\xbf")
    assert b"\r" not in data
    assert data.endswith(b"\n")
    assert not data.endswith(b"\n\n")
    assert "日本語" in data.decode("utf-8")
    assert b"\\u" not in data, "non-ASCII must be preserved, not escaped"


def test_dumps_sorts_keys_indents_two_spaces_and_preserves_non_ascii() -> None:
    assert dumps({"b": 1, "a": "é"}) == '{\n  "a": "é",\n  "b": 1\n}\n'


def test_dumps_output_round_trips_through_json_loads() -> None:
    assert json.loads(dumps(GOLDEN_INPUT)) == GOLDEN_INPUT


def test_dumps_compact_of_the_matrix_example_is_one_line_with_sorted_keys() -> None:
    text = dumps_compact(COMPACT_INPUT)
    assert text == COMPACT_EXPECTED
    assert "\n" not in text
    assert " " not in text


def test_dumps_compact_preserves_non_ascii_and_adds_no_newline() -> None:
    assert dumps_compact({"k": "é 🎉"}) == '{"k":"é 🎉"}'
    assert dumps_compact([]) == "[]"
    assert dumps_compact({}) == "{}"


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf], ids=["nan", "inf", "-inf"])
@pytest.mark.parametrize(
    "wrap",
    [
        lambda value: value,
        lambda value: {"x": value},
        lambda value: [1, [value]],
        lambda value: {"a": {"b": [{"c": value}]}},
    ],
    ids=["bare", "in-dict", "in-nested-list", "deep"],
)
def test_non_finite_numbers_raise_value_error_from_both_serializers(
    bad: float, wrap: Callable[[float], JsonValue]
) -> None:
    with pytest.raises(ValueError):
        dumps(wrap(bad))
    with pytest.raises(ValueError):
        dumps_compact(wrap(bad))


def test_same_value_with_different_insertion_order_gives_identical_bytes() -> None:
    first: JsonValue = {"z": 1, "a": {"y": [1, 2], "b": None}, "m": "é"}
    second: JsonValue = {"m": "é", "a": {"b": None, "y": [1, 2]}, "z": 1}
    assert dumps(first) == dumps(second)
    assert dumps(first) == dumps(first)
    assert dumps_compact(first) == dumps_compact(second)


def test_floats_are_written_by_shortest_round_trip_repr() -> None:
    assert dumps_compact([0.1, 2.5, 1e-7, 1e21, 10.0, -0.0]) == "[0.1,2.5,1e-07,1e+21,10.0,-0.0]"


def test_scalars_are_json_literals() -> None:
    assert dumps_compact([True, False, None, 0, -1, 9007199254740993]) == (
        "[true,false,null,0,-1,9007199254740993]"
    )
    assert dumps(None) == "null\n"
    assert dumps("é") == '"é"\n'


def test_volatile_paths_are_exactly_the_spines_patterns() -> None:
    assert isinstance(VOLATILE_PATHS, tuple)
    assert VOLATILE_PATHS == (
        "run_id",
        "created_at",
        "package_version",
        "scenarios[*].trace.run_id",
        "scenarios[*].trace.started_at",
        "scenarios[*].trace.ended_at",
        "scenarios[*].trace.environment",
        "scenarios[*].trace.events[*].timestamp",
        "scenarios[*].trace.events[*].duration_ms",
        "scenarios[*].cost",
    )
    assert len(set(VOLATILE_PATHS)) == len(VOLATILE_PATHS)
