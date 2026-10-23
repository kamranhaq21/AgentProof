"""``redaction.scrub_text`` (story 3.5 criterion 1; AD-10; PRD AC-28.2)."""

import pytest

from agentproof.constants import REDACTED
from agentproof.redaction import scrub_text


def test_longest_value_first_leaves_no_fragment_of_the_longer_value() -> None:
    text = "x abcdefghijkl y abcdefgh z"
    expected = f"x {REDACTED} y {REDACTED} z"
    assert scrub_text(text, ["abcdefgh", "abcdefghijkl"]) == expected
    # Order of the declared values must not matter.
    assert scrub_text(text, ["abcdefghijkl", "abcdefgh"]) == expected


def test_empty_secret_values_return_the_text_unchanged() -> None:
    assert scrub_text("nothing to hide", []) == "nothing to hide"
    assert scrub_text("nothing to hide", iter(())) == "nothing to hide"


def test_an_empty_string_value_contributes_nothing() -> None:
    assert scrub_text("abc", ["", "b"]) == f"a{REDACTED}c"
    assert scrub_text("abc", [""]) == "abc"


def test_every_occurrence_is_replaced_and_duplicates_are_harmless() -> None:
    assert scrub_text("k k k", ["k", "k"]) == f"{REDACTED} {REDACTED} {REDACTED}"


def test_the_marker_is_the_constant() -> None:
    assert scrub_text("sekret", ["sekret"]) == REDACTED == "[REDACTED]"


def test_a_generator_of_values_is_consumed_once() -> None:
    assert scrub_text("a b", (value for value in ("a", "b"))) == f"{REDACTED} {REDACTED}"


def test_overlapping_values_leave_no_fragment_of_either_in_any_order() -> None:
    """``abcXY`` and ``XYdef`` overlap in ``abcXYdef`` without either containing the other.
    The result is one marker over the merged span, whatever order the values arrive in."""
    for values in (["abcXY", "XYdef"], ["XYdef", "abcXY"], {"abcXY", "XYdef"}):
        assert scrub_text("abcXYdef", values) == REDACTED
        assert scrub_text("a abcXYdef b", values) == f"a {REDACTED} b"


@pytest.mark.allow_subprocess
def test_overlap_result_does_not_depend_on_the_hash_seed() -> None:
    import os
    import subprocess
    import sys

    code = (
        "from agentproof.redaction import scrub_text;"
        "print(scrub_text('abcXYdef', ['abcXY', 'XYdef']))"
    )
    outputs = set()
    for seed in ("0", "1", "2", "3", "random"):
        env = {**os.environ, "PYTHONHASHSEED": seed}
        done = subprocess.run(
            [sys.executable, "-I", "-c", code], capture_output=True, text=True, env=env
        )
        assert done.returncode == 0, done.stderr
        outputs.add(done.stdout)
    assert outputs == {f"{REDACTED}\n"}


def test_touching_spans_merge_and_a_chain_of_overlaps_collapses() -> None:
    assert scrub_text("abcdef", ["abc", "def"]) == REDACTED
    assert scrub_text("abcdefgh", ["abcd", "cdef", "efgh"]) == REDACTED
    assert scrub_text("aXa", ["aXa", "a"]) == REDACTED
