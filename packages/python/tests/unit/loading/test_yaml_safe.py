"""``loading.yaml_safe.load``: the AD-19 rejections, each with its line, and the plain path.

One fixture file per rejection class lives under ``tests/fixtures/yaml``; inline text covers
the variants. Every rejection is asserted as ``SuiteError`` carrying the source, the
1-based ``line:column`` in ``Violation.field``, and the key or tag named in the message.
The billion-laughs case also proves that construction never started and that memory
stayed flat, and two tests pin the loader to PyYAML's pure-Python classes.
"""

import inspect
import math
import re
import tracemalloc
import unicodedata
from pathlib import Path
from typing import Any

import pytest
import yaml

from agentproof import constants
from agentproof.errors import InputError, SuiteError, Violation
from agentproof.loading import yaml_safe
from agentproof.loading.yaml_safe import _StrictLoader, load

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "yaml"
SRC = Path(__file__).resolve().parents[3] / "src" / "agentproof"
SOURCE = "agentproof.yaml"
TIMESTAMP_TAG = "tag:yaml.org,2002:timestamp"
FALLBACK_FRAGMENT = "could not be parsed"
ESCAPE_MESSAGE = "the document has a character escape that is not a valid Unicode character"
# A fully expanded billion-laughs fixture holds 9**9 strings; a parse that never expands
# stays far below this (measured: about 8 KiB).
BILLION_LAUGHS_PEAK_BYTES = 1024 * 1024
# A message may echo at most 80 characters of user text; the longest fixed wording around
# it is under 100 more.
MAX_MESSAGE_LENGTH = 200

SEED = {
    "version": 1,
    "suite": "expense-agent",
    "description": "...",
    "defaults": {
        "adapter": "fixture",
        "fail_on_missing_trace": True,
        "fixture": {"deterministic": True},
        "compare": {"include_arguments": ["approve_expense.amount"]},
        "redact": {"keys": [], "paths": [], "env": ["OPENAI_API_KEY"]},
    },
    "scenarios": [
        {
            "id": "reject-over-limit",
            "description": "...",
            "skip": "reason",
            "input": {"expense_amount": 5000},
            "trace": "traces/reject-over-limit.trace.json",
            "assertions": [
                {"type": "tool_not_called", "tool": "approve_expense"},
                {"type": "tool_call_count", "tool": "reject_expense", "equals": 1},
                {
                    "id": "says-rejected",
                    "type": "final_output_contains",
                    "value": "rejected",
                    "case_sensitive": True,
                },
            ],
        }
    ],
}


def _fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def _reject(text: str, source: str = SOURCE) -> SuiteError:
    with pytest.raises(SuiteError) as excinfo:
        load(text, source=source)
    return excinfo.value


def _only(exc: SuiteError) -> Violation:
    assert len(exc.violations) == 1, exc.violations
    return exc.violations[0]


def _never_construct(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make any construction step fail the test: the rejection must happen at compose time."""

    def tripwire(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("construction started; the rejection must happen at compose time")

    monkeypatch.setattr(_StrictLoader, "construct_document", tripwire)
    monkeypatch.setattr(_StrictLoader, "construct_object", tripwire)


# -- criterion 1: custom tags ----------------------------------------------------------


def test_custom_tag_fixture_is_rejected_naming_tag_source_and_line(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _never_construct(monkeypatch)
    violation = _only(_reject(_fixture("custom-tag.yaml")))
    assert violation.source == SOURCE
    assert violation.field == "3:14"
    assert "'!shout'" in violation.message
    assert "not allowed" in violation.message


def test_python_object_tag_fixture_is_rejected_before_any_object_is_constructed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _never_construct(monkeypatch)
    violation = _only(_reject(_fixture("python-object-tag.yaml")))
    assert violation.source == SOURCE
    assert violation.field == "2:8"
    assert "'!!python/object/apply:os.system'" in violation.message


@pytest.mark.parametrize(
    ("text", "named"),
    [
        ("a: !!python/name:os.system\n", "!!python/name:os.system"),
        ("a: !!python/module:os\n", "!!python/module:os"),
        ("a: !<tag:example.com,2026:x> hi\n", "tag:example.com,2026:x"),
        ("a: !!binary aGk=\n", "!!binary"),
        ("a: !!set {x: null}\n", "!!set"),
        ("a: !!omap [{x: 1}]\n", "!!omap"),
        ("a: !!pairs [{x: 1}]\n", "!!pairs"),
    ],
)
def test_every_tag_outside_the_plain_set_is_rejected_by_name(
    monkeypatch: pytest.MonkeyPatch, text: str, named: str
) -> None:
    _never_construct(monkeypatch)
    violation = _only(_reject(text))
    assert violation.field == "1:4"
    assert f"tag '{named}' is not allowed" in violation.message


def test_merge_key_is_rejected_as_the_merge_key(monkeypatch: pytest.MonkeyPatch) -> None:
    _never_construct(monkeypatch)
    violation = _only(_reject("base: {x: 1}\na:\n  <<: {x: 2}\n"))
    assert violation.field == "3:3"
    assert violation.message.startswith("merge key '<<' is not allowed")


def test_plain_standard_tags_are_accepted_and_timestamps_stay_text() -> None:
    result = load(
        'a: !!str 123\nb: !!int "7"\nc: 2026-10-22T13:05:00Z\nd: 2026-10-22\n', source=SOURCE
    )
    assert result == {"a": "123", "b": 7, "c": "2026-10-22T13:05:00Z", "d": "2026-10-22"}
    assert all(isinstance(result[key], str) for key in ("c", "d"))


def test_the_stock_safeloader_constructor_table_is_untouched() -> None:
    assert yaml.SafeLoader.yaml_constructors[TIMESTAMP_TAG].__name__ == "construct_yaml_timestamp"
    assert _StrictLoader.yaml_constructors[TIMESTAMP_TAG].__name__ == "construct_timestamp_text"
    for name in ("int", "float", "bool", "null"):
        tag = f"tag:yaml.org,2002:{name}"
        assert yaml.SafeLoader.yaml_constructors[tag].__name__ == f"construct_yaml_{name}"
        assert _StrictLoader.yaml_constructors[tag].__name__ == f"construct_{name}_checked"


def test_plain_equals_sign_is_reserved_and_rejected_with_a_clear_message() -> None:
    violation = _only(_reject("a: =\n"))
    assert violation.field == "1:4"
    assert (
        violation.message == "a plain '=' is reserved by YAML 1.1; quote it to use it as a string"
    )
    assert load('a: "="\n', source=SOURCE) == {"a": "="}


# -- the %TAG note names only a handle that was actually remapped -----------------------


def test_tag_written_with_a_remapped_named_handle_is_reported_as_resolved() -> None:
    violation = _only(_reject("%TAG !e! tag:example.com,2026:\n---\na: !e!x 1\n"))
    assert violation.field == "3:4"
    assert violation.message.startswith(
        "tag 'tag:example.com,2026:x' (resolved from a %TAG handle) is not allowed"
    )


def test_tag_written_with_a_remapped_primary_handle_is_reported_as_resolved() -> None:
    violation = _only(_reject("%TAG ! tag:example.com,2026:\n---\na: !x 1\n"))
    assert "(resolved from a %TAG handle)" in violation.message


def test_tag_directive_for_another_handle_adds_no_resolution_note() -> None:
    violation = _only(_reject("%TAG !e! tag:example.com,2026:\n---\na: !shout 1\n"))
    assert violation.message.startswith("tag '!shout' is not allowed")
    assert "%TAG" not in violation.message


def test_verbatim_tag_has_no_handle_and_no_resolution_note() -> None:
    violation = _only(_reject("%TAG !e! tag:example.com,2026:\n---\na: !<tag:foo:x> 1\n"))
    assert violation.message.startswith("tag 'tag:foo:x' is not allowed")
    assert "%TAG" not in violation.message


def test_tag_without_a_tag_directive_carries_no_resolution_note() -> None:
    assert "%TAG" not in _only(_reject("a: !shout x\n")).message


# -- tags must fit their node, and typed scalars must be readable -----------------------


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("a: !!map 5\n", "tag '!!map' expects a mapping, not a scalar"),
        ("a: !!map ab\n", "tag '!!map' expects a mapping, not a scalar"),
        ("a: !!map [x, y]\n", "tag '!!map' expects a mapping, not a sequence"),
        ("a: !!seq 5\n", "tag '!!seq' expects a sequence, not a scalar"),
        ("a: !!seq {x: 1}\n", "tag '!!seq' expects a sequence, not a mapping"),
        ("a: !!str {x: 1}\n", "tag '!!str' expects a scalar, not a mapping"),
        ("a: !!str [x]\n", "tag '!!str' expects a scalar, not a sequence"),
        ("a: !!int [1]\n", "tag '!!int' expects a scalar, not a sequence"),
        ("a: !!null {x: 1}\n", "tag '!!null' expects a scalar, not a mapping"),
        ("a: !!bool [x]\n", "tag '!!bool' expects a scalar, not a sequence"),
        ("a: !!float {x: 1}\n", "tag '!!float' expects a scalar, not a mapping"),
        ("a: !!timestamp [x]\n", "tag '!!timestamp' expects a scalar, not a sequence"),
    ],
)
def test_a_tag_that_does_not_fit_its_node_is_rejected_before_construction(
    monkeypatch: pytest.MonkeyPatch, text: str, message: str
) -> None:
    _never_construct(monkeypatch)
    violation = _only(_reject(text))
    assert (violation.field, violation.message) == ("1:4", message)


def test_correctly_shaped_collection_tags_load() -> None:
    assert load("a: !!map {x: 1}\nb: !!seq [1]\n", source=SOURCE) == {"a": {"x": 1}, "b": [1]}


def test_constructors_guard_their_own_node_shape() -> None:
    """Defense in depth: even called directly, a mis-shaped node is a rejection."""
    loader = _StrictLoader("a: 1", SOURCE)
    scalar = yaml.ScalarNode("tag:yaml.org,2002:map", "5")
    with pytest.raises(SuiteError, match="expected a mapping, not a scalar"):
        loader.construct_mapping(scalar)  # type: ignore[arg-type]
    with pytest.raises(SuiteError, match="expected a sequence, not a scalar"):
        loader.construct_sequence(scalar)  # type: ignore[arg-type]
    loader.dispose()


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("a: !!int x\n", "cannot read 'x' as an integer"),
        ("a: !!int ''\n", "cannot read '' as an integer"),
        ("a: !!int 12:xx\n", "cannot read '12:xx' as an integer"),
        ("a: 0x_\n", "cannot read '0x_' as an integer"),
        ("a: 0b_\n", "cannot read '0b_' as an integer"),
        ("a: !!float x\n", "cannot read 'x' as a number"),
        ("a: !!float ''\n", "cannot read '' as a number"),
        ("a: !!float 0x1A\n", "cannot read '0x1A' as a number"),
        ("a: !!bool x\n", "cannot read 'x' as a boolean"),
        ("a: !!null x\n", "cannot read 'x' as null"),
    ],
)
def test_a_typed_scalar_the_constructor_cannot_read_is_rejected(text: str, message: str) -> None:
    """The stock SafeLoader raises ValueError, IndexError or KeyError for most of these."""
    violation = _only(_reject(text))
    assert (violation.field, violation.message) == ("1:4", message)


def test_a_huge_integer_literal_is_rejected_not_an_escaped_value_error() -> None:
    violation = _only(_reject("a: " + "9" * 5000 + "\n"))
    assert violation.field == "1:4"
    assert violation.message.startswith("cannot read '9999")
    assert len(violation.message) < MAX_MESSAGE_LENGTH


# -- criterion 2: duplicate keys -------------------------------------------------------


def test_duplicate_top_level_key_names_the_key_and_the_second_occurrence() -> None:
    violation = _only(_reject(_fixture("duplicate-key-top-level.yaml")))
    assert violation.source == SOURCE
    assert violation.field == "4:1"
    assert violation.message == "duplicate key 'suite'"


def test_duplicate_nested_key_names_the_key_and_the_second_occurrence() -> None:
    violation = _only(_reject(_fixture("duplicate-key-nested.yaml")))
    assert violation.source == SOURCE
    assert violation.field == "6:5"
    assert violation.message == "duplicate key 'id'"


def test_every_duplicate_key_in_the_document_is_reported_in_document_order() -> None:
    exc = _reject("a: 1\nb: 2\na: 3\nc:\n  d: 1\n  d: 2\nb: 4\n")
    assert [(v.field, v.message) for v in exc.violations] == [
        ("3:1", "duplicate key 'a'"),
        ("6:3", "duplicate key 'd'"),
        ("7:1", "duplicate key 'b'"),
    ]
    assert str(exc) == "3 violations; first: duplicate key 'a'"


def test_keys_are_compared_as_code_points_with_no_normalization() -> None:
    composed = "\u00e9"
    decomposed = "e\u0301"
    assert unicodedata.normalize("NFC", decomposed) == composed
    result = load(f"{composed}: 1\n{decomposed}: 2\n", source=SOURCE)
    assert result == {composed: 1, decomposed: 2}
    assert load('"a": 1\n"\u200ba": 2\n', source=SOURCE) == {"a": 1, "\u200ba": 2}


def test_a_very_long_duplicate_key_is_clipped_in_the_message() -> None:
    key = "k" * 1000
    violation = _only(_reject(f'"{key}": 1\n"{key}": 2\n'))
    assert violation.message == "duplicate key '" + "k" * 77 + "...'"


@pytest.mark.parametrize("key", ["a\u202eb", "a\u0085b", "a\u200bb", "a\x1bb"])
def test_bidirectional_and_control_characters_in_a_key_are_escaped_in_the_message(
    key: str,
) -> None:
    text = "{" + ", ".join(f'"{key}": {n}' for n in (1, 2)) + "}"
    violation = _only(_reject(f"x: {text}\n".replace("\x1b", "\\e").replace("\u0085", "\\N")))
    assert "\\" in violation.message  # escaped by repr, not written raw
    assert not any(ord(ch) > 0x7E or ord(ch) < 0x20 for ch in violation.message)


@pytest.mark.parametrize(
    ("text", "field", "message"),
    [
        ("1: x\n", "1:1", "mapping key '1' is an integer, not a string; quote it"),
        ("true: x\n", "1:1", "mapping key 'true' is a boolean, not a string; quote it"),
        ("~: x\n", "1:1", "mapping key '~' is null, not a string; quote it"),
        ("? [a, b]\n: x\n", "1:3", "a mapping key must be a string, not a sequence"),
        ("? {a: b}\n: x\n", "1:3", "a mapping key must be a string, not a mapping"),
    ],
)
def test_non_string_keys_are_rejected(text: str, field: str, message: str) -> None:
    violation = _only(_reject(text))
    assert (violation.field, violation.message) == (field, message)


# -- criterion 3: anchors and aliases --------------------------------------------------


def test_anchor_fixture_is_rejected_at_the_anchor_before_construction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _never_construct(monkeypatch)
    violation = _only(_reject(_fixture("anchor-alias.yaml")))
    assert violation.source == SOURCE
    assert violation.field == "3:11"
    assert violation.message.startswith("anchor '&shared' is not allowed")


def test_alias_without_an_anchor_is_rejected_at_the_alias(monkeypatch: pytest.MonkeyPatch) -> None:
    _never_construct(monkeypatch)
    violation = _only(_reject("suite: x\nother: *x\n"))
    assert violation.field == "2:8"
    assert violation.message.startswith("alias '*x' is not allowed")


def test_billion_laughs_is_rejected_at_its_first_anchor_without_expansion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _never_construct(monkeypatch)
    text = _fixture("billion-laughs.yaml")
    tracemalloc.start()
    try:
        with pytest.raises(SuiteError) as excinfo:
            load(text, source=SOURCE)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    violation = _only(excinfo.value)
    assert violation.source == SOURCE
    assert violation.field == "2:4"
    assert violation.message.startswith("anchor '&a' is not allowed")
    assert peak < BILLION_LAUGHS_PEAK_BYTES, peak


# -- criterion 4: documents and the plain path -----------------------------------------


def test_second_document_is_rejected_naming_the_line_of_its_marker() -> None:
    violation = _only(_reject(_fixture("multi-document.yaml")))
    assert violation.source == SOURCE
    assert violation.field == "3:1"
    assert violation.message.startswith("a second YAML document starts here")


def test_a_leading_document_marker_alone_is_one_document() -> None:
    assert load("---\nversion: 1\n", source=SOURCE) == {"version": 1}


def test_an_explicit_document_end_alone_is_one_document() -> None:
    assert load("a: 1\n...\n", source=SOURCE) == {"a": 1}


def test_content_after_an_explicit_document_end_is_a_second_document() -> None:
    violation = _only(_reject("a: 1\n...\nb: 2\n"))
    assert violation.field == "3:1"
    assert violation.message == "a second YAML document starts here; a Suite is a single document"


def test_a_yaml_1_2_directive_is_accepted_but_1_1_rules_still_apply() -> None:
    assert load("%YAML 1.2\n---\na: yes\nb: 017\n", source=SOURCE) == {"a": True, "b": 15}


def test_a_yaml_2_directive_is_rejected() -> None:
    violation = _only(_reject("%YAML 2.0\n---\na: 1\n"))
    assert violation.field == "1:1"
    assert "incompatible YAML document" in violation.message


def test_spine_suite_seed_loads_to_the_expected_dict() -> None:
    result = load(_fixture("suite-seed.yaml"), source=SOURCE)
    assert result == SEED
    assert type(result["version"]) is int
    defaults = result["defaults"]
    assert isinstance(defaults, dict)
    assert defaults["fail_on_missing_trace"] is True
    scenario = result["scenarios"][0]  # type: ignore[index]
    assert type(scenario["assertions"][1]["equals"]) is int
    assert scenario["assertions"][2]["case_sensitive"] is True


def _walk(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            assert type(key) is str
            _walk(item)
    elif isinstance(value, list):
        for item in value:
            _walk(item)
    else:
        assert value is None or type(value) in (bool, int, float, str), type(value)


def test_result_holds_only_string_keys_and_json_shaped_values() -> None:
    _walk(load(_fixture("suite-seed.yaml"), source=SOURCE))


def test_native_scalars_survive_and_nothing_is_substituted() -> None:
    result = load(
        'n: null\nt: ~\ny: true\nf: false\ni: 7\nx: 1.5\ns: "7"\nv: ${VAR}\nw: yes\n',
        source=SOURCE,
    )
    assert result == {
        "n": None,
        "t": None,
        "y": True,
        "f": False,
        "i": 7,
        "x": 1.5,
        "s": "7",
        "v": "${VAR}",
        "w": True,
    }
    assert type(result["y"]) is bool
    assert type(result["i"]) is int
    assert type(result["x"]) is float


def test_non_finite_floats_pass_through_for_the_models_to_reject() -> None:
    result = load("a: .nan\nb: .inf\n", source=SOURCE)
    assert isinstance(result["a"], float) and math.isnan(result["a"])
    assert result["b"] == math.inf


def test_yaml_1_1_scalar_surprises_are_as_the_module_docstring_lists() -> None:
    """Pins the list in the ``yaml_safe`` docstring, which the docs page will copy."""
    result = load(
        "sexa: 12:30:00\noct: 017\noct2: 0o17\nhex: 0x1A\nunder: 1_000\nexp: 1e3\n"
        "expdot: 1.0e3\nexpsigned: 1.0e+3\nb1: yes\nb2: Off\nb3: Y\nb4: n\nb5: TRUE\nb6: On\n"
        "b7: y\nb8: N\ninf: -.inf\n",
        source=SOURCE,
    )
    assert result == {
        "sexa": 45000,
        "oct": 15,
        "oct2": "0o17",
        "hex": 26,
        "under": 1000,
        "exp": "1e3",
        "expdot": "1.0e3",
        "expsigned": 1000.0,
        "b1": True,
        "b2": False,
        "b3": "Y",
        "b4": "n",
        "b5": True,
        "b6": True,
        "b7": "y",
        "b8": "N",
        "inf": -math.inf,
    }


def test_explicit_numeric_tags_are_broader_than_plain_scalars() -> None:
    """Pins the "explicit tags are broader" paragraph of the module docstring."""
    result = load(
        "arabic: !!int \u0661\u0662\nsexa: !!int 1:2:3\n"
        "huge: !!float 1e999\nts: !!timestamp hello\n",
        source=SOURCE,
    )
    assert result["arabic"] == 12
    assert result["sexa"] == 3723
    assert result["huge"] == math.inf
    assert result["ts"] == "hello"
    # The same text as a plain scalar is just a string.
    assert load("arabic: \u0661\u0662\nhuge: 1e999\n", source=SOURCE) == {
        "arabic": "\u0661\u0662",
        "huge": "1e999",
    }


def test_scalar_top_level_fixture_is_rejected() -> None:
    violation = _only(_reject(_fixture("scalar-top-level.yaml")))
    assert violation.source == SOURCE
    assert violation.field == "1:1"
    assert violation.message == "the top level is a string, not a mapping; a Suite is a mapping"


@pytest.mark.parametrize(
    ("text", "field", "message"),
    [
        ("- a\n- b\n", "1:1", "the top level is a sequence, not a mapping; a Suite is a mapping"),
        ("7\n", "1:1", "the top level is an integer, not a mapping; a Suite is a mapping"),
        ("---\n", "2:1", "the top level is null, not a mapping; a Suite is a mapping"),
        ("", "1:1", "the document is empty; a Suite is a mapping"),
        ("# only a comment\n", "1:1", "the document is empty; a Suite is a mapping"),
    ],
)
def test_non_mapping_or_empty_top_level_is_rejected(text: str, field: str, message: str) -> None:
    violation = _only(_reject(text))
    assert (violation.field, violation.message) == (field, message)


# -- strings: surrogates, byte order marks, escapes ------------------------------------


@pytest.mark.parametrize(
    ("text", "field", "code"),
    [
        ('a: "\\uD800"\n', "1:4", "D800"),
        ('a: "\\U0000D800"\n', "1:4", "D800"),
        ('"\\uDFFF": 1\n', "1:1", "DFFF"),
        ('a: ["ok", "x\\uDC00y"]\n', "1:11", "DC00"),
        ('a:\n  b: "\\uD83D"\n', "2:6", "D83D"),
    ],
)
def test_a_lone_surrogate_written_as_an_escape_is_rejected_in_keys_and_values(
    text: str, field: str, code: str
) -> None:
    violation = _only(_reject(text))
    assert violation.field == field
    assert violation.message == (
        f"the text contains U+{code}, a lone surrogate, which cannot be written as UTF-8"
    )


def test_a_surrogate_pair_written_as_one_astral_escape_is_fine() -> None:
    assert load('a: "\\U0001F600"\n', source=SOURCE) == {"a": "\U0001f600"}


def test_every_surrogate_in_the_document_is_reported_in_order() -> None:
    exc = _reject('a: "\\uD800"\nb:\n  c: "\\uDC00"\n')
    assert [(v.field, v.message[:27]) for v in exc.violations] == [
        ("1:4", "the text contains U+D800, a"),
        ("3:6", "the text contains U+DC00, a"),
    ]


def test_a_raw_surrogate_in_the_text_is_rejected_by_pyyamls_reader() -> None:
    violation = _only(_reject("a: x\ud800y\n"))
    assert violation.field == "1:5"
    assert "U+D800" in violation.message


@pytest.mark.parametrize(
    "text",
    ["a: x\ufeffy\n", 'a: "\\uFEFF"\n', '"\\uFEFFa": 1\n', "a: [x\ufeff]\n"],
)
def test_a_byte_order_mark_inside_the_document_is_rejected(text: str) -> None:
    violation = _only(_reject(text))
    assert violation.message == (
        "the text contains U+FEFF, a byte order mark, which is only allowed at the start "
        "of the document"
    )


def test_a_leading_byte_order_mark_is_skipped() -> None:
    assert load("\ufeffa: 1\n", source=SOURCE) == {"a": 1}


def test_control_characters_written_as_escapes_are_accepted_as_documented() -> None:
    """Decision (review round 2, G2): only surrogates and U+FEFF are rejected.

    NUL and ESC survive as ordinary strings; JSON can carry them and ``.encode("utf-8")``
    accepts them, so rejecting them is the models' business, not the loader's.
    """
    assert load('a: "\\x00"\nb: "\\e"\nc: "\\x1b"\n', source=SOURCE) == {
        "a": "\x00",
        "b": "\x1b",
        "c": "\x1b",
    }


@pytest.mark.parametrize("escape", ["\\U0011FFFF", "\\UFFFFFFFF", "\\U00110000"])
def test_a_unicode_escape_above_the_last_code_point_is_a_suite_error(escape: str) -> None:
    """PyYAML's scanner raises a bare ``ValueError`` (or ``OverflowError``) from ``chr()``."""
    with pytest.raises((ValueError, OverflowError)):
        yaml.safe_load(f'a: "{escape}"')
    violation = _only(_reject(f'a: "{escape}"\n'))
    assert violation.message == ESCAPE_MESSAGE
    assert violation.field == ""
    assert violation.source == SOURCE


# -- messages are bounded ------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "start"),
    [
        ("a: !" + "t" * 3000 + " x\n", "tag '!ttt"),
        ("a: &" + "n" * 3000 + " x\n", "anchor '&nnn"),
        ("a: *" + "n" * 3000 + "\n", "alias '*nnn"),
        ("a: !!int " + "q" * 3000 + "\n", "cannot read 'qqq"),
        ("a: !!float " + "q" * 3000 + "\n", "cannot read 'qqq"),
        ("a: !!bool " + "q" * 3000 + "\n", "cannot read 'qqq"),
        ("a: !!null " + "q" * 3000 + "\n", "cannot read 'qqq"),
        ("a: !<" + "t" * 3000 + "> x\n", "tag '" + "t" * 5),
    ],
)
def test_user_text_echoed_in_a_message_is_clipped_to_eighty_characters(
    text: str, start: str
) -> None:
    violation = _only(_reject(text))
    assert violation.message.startswith(start)
    assert "..." in violation.message
    assert len(violation.message) < MAX_MESSAGE_LENGTH
    assert "t" * 100 not in violation.message
    assert "n" * 100 not in violation.message
    assert "q" * 100 not in violation.message


def test_a_short_value_is_echoed_whole() -> None:
    assert _only(_reject("a: !!int " + "q" * 80 + "\n")).message == (
        "cannot read '" + "q" * 80 + "' as an integer"
    )


# -- PyYAML's own errors never escape --------------------------------------------------


@pytest.mark.parametrize(
    ("text", "field", "fragment"),
    [
        ("a: [1, 2", "1:9", "expected ',' or ']'"),
        ("a:\n\tb: 1", "2:1", "found character '\\t' that cannot start any token"),
        ('a: "unterminated\n', "2:1", "found unexpected end of stream while scanning a quoted"),
        ("a: 1\n b: 2\n", "2:3", "mapping values are not allowed here"),
        ("a: 1\nb\n", "3:1", "could not find expected ':'"),
        ("a: \x07\n", "1:4", "special characters are not allowed (U+0007)"),
    ],
)
def test_malformed_yaml_becomes_a_suite_error_with_the_line(
    text: str, field: str, fragment: str
) -> None:
    exc = _reject(text)
    assert type(exc) is SuiteError
    assert not isinstance(exc, yaml.YAMLError)
    violation = _only(exc)
    assert violation.source == SOURCE
    assert violation.field == field
    assert fragment in violation.message


def test_pathological_nesting_is_a_suite_error_not_a_recursion_error() -> None:
    violation = _only(_reject("[" * 10_000))
    assert violation.message == "the document nests too deeply"
    assert violation.field == ""


def test_reasonable_nesting_loads_and_the_node_limit_does_not_fire_first() -> None:
    depth = 200
    result = load("a: " + "[" * depth + "]" * depth + "\n", source=SOURCE)
    value: Any = result["a"]
    for _ in range(depth - 1):
        assert isinstance(value, list) and len(value) == 1
        value = value[0]
    assert value == []


def test_the_source_label_is_copied_onto_every_violation() -> None:
    exc = _reject("a: 1\na: 2\nb: *x\n", source="<stdin>")
    assert {violation.source for violation in exc.violations} == {"<stdin>"}


def test_suite_error_is_an_input_error_for_exit_two() -> None:
    assert issubclass(SuiteError, InputError)
    assert isinstance(_reject("a: *x\n"), InputError)


NASTY_INPUTS = [
    "a: !!map 5",
    "a: !!map ab",
    "a: !!map [x, y]",
    "a: !!seq 5",
    "a: !!seq {x: 1}",
    "a: !!str {x: 1}",
    "a: !!int [1]",
    "a: !!int x",
    "a: !!int 0x",
    "a: !!int ''",
    "a: !!int -",
    "a: !!float x",
    "a: !!float ''",
    "a: !!float -",
    "a: !!float .",
    "a: !!bool x",
    "a: !!null x",
    "a: !!binary 5",
    "a: !!timestamp [x]",
    "a: !!value x",
    "a: =",
    "a: 0x_",
    "a: 0b_",
    "a: +0o_",
    "a: 1:",
    "a: 1:0:",
    "a: 1:0.",
    "a: 1._",
    "? !!map 5\n: 1",
    "!!map 5",
    "!!seq 5",
    "- !!map 5",
    "{a: 1",
    "a: 'x",
    "\x00",
    "a: \ufeff",
    "a: x\ufeffy",
    'a: "\\uD800"',
    'a: "\\U0000D800"',
    '"\\uDFFF": 1',
    'a: "\\U0011FFFF"',
    'a: "\\UFFFFFFFF"',
    'a: "\\U00110000"',
    'a: "\\x00\\e\\x1b\\N\\L\\P\\_"',
    'a: "\\q"',
    'a: "\\x"',
    'a: "\\u12"',
    "%TAG\n---\na: 1",
    "%TAG ! !\n---",
    "%TAG !e! tag:x:\n---\na: !e!x 1",
    "%TAG !e! tag:x:\n%TAG !e! tag:y:\n---\na: 1",
    "%YAML 2.0\n---\na: 1",
    "%YAML 1.1\n%YAML 1.1\n---\na: 1",
    "---\n---\n",
    "a: &",
    "a: *",
    "a: !",
    "a: !!",
    "a: !<>",
    "a: !<",
    "a: |\n",
    "a: >-\n  x\n b",
    "a:\n- b\n c: 1",
    "a: 1\nb: 2\n...\n...\n",
    "a: 1\n...\nb: 2",
    "...",
    "---",
    "a: @x",
    "a: `x",
    "a: {b: 1, b: 2}",
    "a: [1, 2,,]",
    "a: 1\n\x0c\nb: 2",
    "a: \t1",
    "\ta: 1",
    "a: 1 #\x01",
    "? [a]\n: 1\n? [a]\n: 2",
    "? |\n  x\n: 1",
    "a: " + "9" * 5000,
    "a: !" + "t" * 3000,
    "[" * 5000,
    "{" * 5000,
    "a: " + "[" * 450,
]


@pytest.mark.parametrize("text", NASTY_INPUTS, ids=lambda text: ascii(text[:40]))
def test_any_text_either_loads_to_a_dict_or_raises_suite_error(text: str) -> None:
    """Never another exception, and never the generic fallback, which would mean a gap."""
    try:
        result = load(text, source=SOURCE)
    except SuiteError as exc:
        assert exc.violations
        for violation in exc.violations:
            assert FALLBACK_FRAGMENT not in violation.message, violation
            assert len(violation.message) < MAX_MESSAGE_LENGTH, violation
        return
    assert isinstance(result, dict), result


def test_an_unexpected_parser_exception_is_still_an_input_fault_naming_only_its_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def boom(self: _StrictLoader) -> None:
        raise KeyError("secret-token-in-the-document")

    monkeypatch.setattr(_StrictLoader, "get_single_node", boom)
    violation = _only(_reject("a: 1\n"))
    assert violation.message == "the document could not be parsed (KeyError)"
    assert "secret" not in violation.message


# -- the node bound ----------------------------------------------------------------------


def _flow_sequence_with(node_count: int) -> str:
    """A document of exactly ``node_count`` nodes: the mapping, its key, the sequence, items."""
    return "a: [" + ", ".join("1" for _ in range(node_count - 3)) + "]\n"


def test_the_node_limit_comes_from_constants() -> None:
    assert yaml_safe.MAX_YAML_NODES is constants.MAX_YAML_NODES
    assert constants.MAX_YAML_NODES == 200_000


def test_a_document_at_the_node_limit_loads(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(yaml_safe, "MAX_YAML_NODES", 50)
    assert load(_flow_sequence_with(50), source=SOURCE) == {"a": [1] * 47}


def test_a_document_over_the_node_limit_is_rejected_naming_the_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _never_construct(monkeypatch)
    monkeypatch.setattr(yaml_safe, "MAX_YAML_NODES", 50)
    violation = _only(_reject(_flow_sequence_with(51)))
    assert violation.message == (
        "the document has more than 50 YAML nodes; a Suite this large must be split"
    )
    # The 51st node is the last ``1`` of the flow sequence: ``a: [`` is four columns, then
    # 47 items of three columns each (``1, ``) precede it.
    assert violation.field == f"1:{4 + 47 * 3 + 1}"


def test_the_real_node_limit_rejects_a_large_alias_free_document(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The real constant, on the smallest text that crosses it (about 600 KB of ``1, ``)."""
    _never_construct(monkeypatch)
    violation = _only(_reject(_flow_sequence_with(constants.MAX_YAML_NODES + 1)))
    assert violation.message.startswith(f"the document has more than {constants.MAX_YAML_NODES}")


# -- the loader is the pure-Python SafeLoader and the only entry point -----------------


def test_loader_is_the_pure_python_safeloader() -> None:
    mro = _StrictLoader.__mro__
    assert yaml.SafeLoader in mro
    assert yaml.composer.Composer in mro
    assert yaml.parser.Parser in mro
    assert yaml.constructor.SafeConstructor in mro
    assert all(cls.__module__ != "yaml.cyaml" for cls in mro)
    if hasattr(yaml, "CSafeLoader"):
        assert yaml.CSafeLoader not in mro


def test_module_never_names_the_c_loader_or_calls_yaml_load() -> None:
    source = inspect.getsource(yaml_safe)
    assert "CSafeLoader" not in source
    assert "cyaml" not in source
    assert "yaml.load(" not in source
    assert "safe_load(" not in source


def test_load_is_the_only_public_name() -> None:
    assert yaml_safe.__all__ == ["load"]


YAML_IMPORT = re.compile(r"^\s*(?:import|from)\s+yaml\b", re.MULTILINE)


def test_yaml_safe_is_the_only_module_that_imports_pyyaml() -> None:
    """AD-19: one YAML entry point, checked mechanically over the whole source tree."""
    modules = sorted(SRC.rglob("*.py"))
    assert len(modules) > 10, modules
    importers = sorted(
        path.relative_to(SRC).as_posix()
        for path in modules
        if YAML_IMPORT.search(path.read_text(encoding="utf-8"))
    )
    assert importers == ["loading/yaml_safe.py"]
