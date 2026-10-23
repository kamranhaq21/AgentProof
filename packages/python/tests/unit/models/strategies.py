"""Hypothesis strategies for the serialized models (story 2.6).

Every strategy produces the JSON shape, a plain ``dict`` or ``list`` such as ``json.loads``
returns, never a model instance, so what a property validates is what a file would hold
(AD-3: the only way in is ``model_validate(dict)``). Each strategy respects every rule the
model it targets enforces, so an instance it yields is valid by construction: the
scenario id charset and the Windows device names, case-insensitive scenario id
uniqueness, at least one Scenario and one Assertion, assertion ids unique within a
Scenario including the ``<type>-<index>`` defaults, exactly one ``tool_call_count``
operator, dotted argument paths, RFC 3339 timestamps with an offset or ``Z``, contiguous
``seq``, Report counts that reconcile, ``execution_failed`` derived from the Scenarios,
unique ids, and ``skip_reason`` / ``execution_error`` tied to the status.

Strings come from ``texts``: the full UTF-8 repertoire without surrogates, plus a biased
sample of the awkward cases (empty, newlines, tabs, combining characters, non-BMP). Floats
are finite only; the non-finite properties build their own inputs. Sizes are small on
purpose (the whole property file must run in about a minute on CI).
"""

import re
from collections.abc import Callable, Mapping
from functools import cache
from typing import Any, Literal

from hypothesis import strategies as st

from agentproof.constants import SCENARIO_ID_RE, WINDOWS_DEVICE_NAMES
from agentproof.models.assertions import ASSERTION_TYPES, OPERATORS
from agentproof.models.common import STATUSES, JsonValue, Status
from agentproof.models.trace import EVENT_TYPES

JsonObject = dict[str, Any]
"""A JSON object as a plain dict; ``Any`` because the dicts here are built incrementally."""

# --- text ----------------------------------------------------------------------------------

COMBINING_MARKS = ("́", "̈", "̧", "⃗", "॓")
"""Combining marks (acute, diaeresis, cedilla, right arrow above, Devanagari grave)."""

AWKWARD_STRINGS = (
    "",
    "\n",
    "\r\n",
    "\t",
    " ",
    "é",
    "ño",
    "日本語",
    "🎉",
    "é ü ß",
    " ",
    "﻿",
    "line one\nline two",
    'quote " and back\\slash',
    "\u0000",
    "\x7f",
    "אָ",
)
"""Strings a user will actually send: empty, newlines of both kinds, tabs, precomposed and
decomposed accents, CJK, an emoji outside the BMP, a line separator, a BOM, a NUL."""

_UTF8_CHARACTERS = st.characters(codec="utf-8")
"""Every code point UTF-8 can encode, so no lone surrogate (which ``str.encode`` rejects)."""

_MIXED_ALPHABET = st.sampled_from([*"ae1 _-\n\t", *COMBINING_MARKS, "日", "🎉", "é", "­", "​"])


@cache
def texts(min_size: int = 0, max_size: int = 12) -> st.SearchStrategy[str]:
    """Cached: building a strategy per draw dominates generation time.

    Strings: general UTF-8, combining-heavy, or one of the awkward samples."""
    general = st.text(alphabet=_UTF8_CHARACTERS, min_size=min_size, max_size=max_size)
    mixed = st.text(alphabet=_MIXED_ALPHABET, min_size=min_size, max_size=max_size)
    awkward = st.sampled_from([s for s in AWKWARD_STRINGS if min_size <= len(s) <= max_size])
    return st.one_of(general, mixed, awkward)


@cache
def non_ascii_texts() -> st.SearchStrategy[str]:
    """Strings guaranteed to contain at least one non-ASCII character."""
    return st.one_of(
        st.tuples(texts(), st.sampled_from(["é", "日", "🎉", "́", " "]), texts()).map("".join),
        st.sampled_from([s for s in AWKWARD_STRINGS if any(ord(ch) >= 0x80 for ch in s)]),
    )


# --- JSON values ---------------------------------------------------------------------------

MAX_JSON_LEAVES = 6
"""Bound on the leaves of a generated ``JsonValue`` so a Report of several Traces stays small."""


@cache
def json_scalars() -> st.SearchStrategy[JsonValue]:
    """``null``, booleans, integers beyond 2**53, finite floats including -0.0, strings."""
    return st.one_of(
        st.none(),
        st.booleans(),
        st.integers(min_value=-(2**64), max_value=2**64),
        st.floats(allow_nan=False, allow_infinity=False),
        texts(),
    )


@cache
def json_values() -> st.SearchStrategy[JsonValue]:
    """Any finite ``JsonValue``: scalars, lists, and objects nested up to the leaf bound."""
    return st.recursive(
        json_scalars(),
        lambda children: st.one_of(
            st.lists(children, max_size=3), st.dictionaries(texts(), children, max_size=3)
        ),
        max_leaves=MAX_JSON_LEAVES,
    )


@cache
def json_objects(min_size: int = 0) -> st.SearchStrategy[dict[str, JsonValue]]:
    """A JSON object whose values are any finite ``JsonValue``."""
    return st.dictionaries(texts(), json_values(), min_size=min_size, max_size=3)


# --- identifiers, paths, timestamps -------------------------------------------------------


@cache
def scenario_ids() -> st.SearchStrategy[str]:
    """Ids matching ``SCENARIO_ID_RE`` in full that are not Windows device names (AD-14)."""
    first = st.sampled_from([*"abcXYZ019"])
    rest = st.text(alphabet=st.sampled_from([*"abcXYZ019._-"]), max_size=12)
    return st.builds("{}{}".format, first, rest).filter(
        lambda value: (
            SCENARIO_ID_RE.fullmatch(value) is not None
            and value.upper() not in WINDOWS_DEVICE_NAMES
        )
    )


_SEGMENT_ALPHABET = st.sampled_from([*"abcXYZ019_-", "é", "日", "🎉"])
"""Characters for an argument-path segment: no ``.``, no whitespace (``ARGUMENT_PATH_PATTERN``)."""


@cache
def path_segments() -> st.SearchStrategy[str]:
    """A non-empty, dot-free, whitespace-free name: a path segment or a dict key."""
    return st.text(alphabet=_SEGMENT_ALPHABET, min_size=1, max_size=6)


@cache
def argument_paths(min_segments: int = 1) -> st.SearchStrategy[str]:
    """Dotted argument paths, ``items.0.amount``; ``min_segments=2`` gives ``<tool>.<path>``."""
    return st.lists(path_segments(), min_size=min_segments, max_size=3).map(".".join)


@cache
def timestamps() -> st.SearchStrategy[str]:
    """Strings ``RFC3339_WITH_OFFSET`` matches in full: an explicit offset or ``Z``.

    Built from integers rather than ``from_regex`` (several times faster to draw); the
    shape is the grammar's, and the properties validate the result through the model.
    """
    date = st.builds(
        "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}".format,
        st.integers(0, 9999),
        st.integers(1, 12),
        st.integers(1, 28),
        st.integers(0, 23),
        st.integers(0, 59),
        st.integers(0, 59),
    )
    fraction = st.one_of(st.just(""), st.integers(0, 999_999_999).map(lambda n: f".{n:09d}"[:7]))
    offset = st.one_of(
        st.just("Z"),
        st.builds(
            "{}{:02d}:{:02d}".format,
            st.sampled_from("+-"),
            st.integers(0, 23),
            st.integers(0, 59),
        ),
    )
    return st.builds("{}{}{}".format, date, fraction, offset)


HolePath = tuple[int | str, ...]
"""Where ``json_values_with_a_hole`` put the hole: dict keys and list indexes from the top."""


@st.composite
def json_values_with_a_hole(
    draw: st.DrawFn,
) -> tuple[Callable[[JsonValue], JsonValue], HolePath]:
    """A builder that embeds a given value at a generated path, and that path.

    ``build(x)`` returns a ``JsonValue`` whose only occurrence of ``x`` sits at ``path``
    (a tuple of dict keys and list indexes, empty for "the value itself"). Dict keys are
    non-empty and dot-free so the dotted path in ``_require_finite``'s message is
    unambiguous; siblings are finite scalars.
    """
    depth = draw(st.integers(min_value=0, max_value=3))
    layers: list[tuple[Literal["list", "dict"], int | str, list[JsonValue]]] = []
    for _ in range(depth):
        siblings = draw(st.lists(json_scalars(), max_size=2))
        if draw(st.booleans()):
            layers.append(("list", draw(st.integers(0, len(siblings))), siblings))
        else:
            layers.append(("dict", draw(path_segments()), siblings))

    def build(hole: JsonValue) -> JsonValue:
        value = hole
        for kind, where, siblings in reversed(layers):
            if kind == "list":
                assert isinstance(where, int)
                items = list(siblings)
                items.insert(where, value)
                value = items
            else:
                assert isinstance(where, str)
                mapping: dict[str, JsonValue] = {
                    f"{where}-{index}": sibling for index, sibling in enumerate(siblings)
                }
                mapping[where] = value
                value = mapping
        return value

    return build, tuple(where for _, where, _ in layers)


@cache
def statuses() -> st.SearchStrategy[Status]:
    return st.sampled_from(STATUSES)


@cache
def non_negative_ints() -> st.SearchStrategy[int]:
    return st.integers(min_value=0, max_value=10**6)


@cache
def finite_floats() -> st.SearchStrategy[float]:
    return st.floats(allow_nan=False, allow_infinity=False)


# --- optional-field helpers ---------------------------------------------------------------

Presence = bool | None
"""How optional keys are emitted: ``None`` draws per key, ``False`` omits, ``True`` emits all."""


def _draw_optional(
    draw: st.DrawFn, presence: Presence, optional: Mapping[str, st.SearchStrategy[Any]]
) -> JsonObject:
    """Draw the optional keys that ``presence`` says to emit."""
    out: JsonObject = {}
    for key, strategy in optional.items():
        present = draw(st.booleans()) if presence is None else presence
        if present:
            out[key] = draw(strategy)
    return out


# --- Suite ---------------------------------------------------------------------------------

_DEFAULT_ID_RE = re.compile(rf"(?:{'|'.join(map(re.escape, ASSERTION_TYPES))})-[0-9]+")
"""The shape of a default assertion id; user ids avoid it so they never collide with one."""


@cache
def user_assertion_ids() -> st.SearchStrategy[str]:
    return texts(min_size=1).filter(lambda value: _DEFAULT_ID_RE.fullmatch(value) is None)


@st.composite
def assertion_configs(draw: st.DrawFn) -> JsonObject:
    """One assertion configuration without an ``id``, valid for its ``type``."""
    kind = draw(st.sampled_from(ASSERTION_TYPES))
    config: JsonObject = {"type": kind}
    if kind in ("tool_called", "tool_not_called"):
        config["tool"] = draw(texts(min_size=1))
    elif kind == "tool_call_count":
        config["tool"] = draw(texts(min_size=1))
        operator = draw(st.sampled_from(OPERATORS))
        config[operator] = draw(non_negative_ints())
        if draw(st.booleans()):
            for other in OPERATORS:
                config.setdefault(other, None)
    elif kind == "tool_arguments_match":
        config["tool"] = draw(texts(min_size=1))
        config["arguments"] = draw(
            st.dictionaries(argument_paths(), json_values(), min_size=1, max_size=2)
        )
    elif kind == "tool_order":
        config["tools"] = draw(st.lists(texts(min_size=1), min_size=1, max_size=3))
    else:
        config["value"] = draw(texts(min_size=1))
        config.update(_draw_optional(draw, None, {"case_sensitive": st.booleans()}))
    return config


@st.composite
def assertion_lists(draw: st.DrawFn) -> list[JsonObject]:
    """At least one assertion; ids omitted (default ``<type>-<index>``) or unique user ids."""
    count = draw(st.integers(min_value=1, max_value=3))
    user_ids = draw(st.lists(user_assertion_ids(), min_size=count, max_size=count, unique=True))
    items: list[JsonObject] = []
    for index in range(count):
        config = draw(assertion_configs())
        if draw(st.booleans()):
            config["id"] = user_ids[index]
        items.append(config)
    return items


@st.composite
def suite_defaults(draw: st.DrawFn, presence: Presence = None) -> JsonObject:
    """A ``defaults`` mapping; every key is optional and ``presence`` decides which appear."""
    return _draw_optional(
        draw,
        presence,
        {
            "adapter": st.one_of(st.none(), texts(min_size=1)),
            "fail_on_missing_trace": st.booleans(),
            "fixture": st.fixed_dictionaries({}, optional={"deterministic": st.booleans()}),
            "compare": st.fixed_dictionaries(
                {}, optional={"include_arguments": st.lists(argument_paths(2), max_size=2)}
            ),
            "redact": st.fixed_dictionaries(
                {},
                optional={
                    "keys": st.lists(texts(min_size=1), max_size=2),
                    "paths": st.lists(argument_paths(), max_size=2),
                    "env": st.lists(texts(min_size=1), max_size=2),
                },
            ),
        },
    )


@st.composite
def scenario_dicts(draw: st.DrawFn, scenario_id: str, skipped: Presence = None) -> JsonObject:
    """One Scenario with the given id; ``skipped`` decides whether ``skip`` is present."""
    scenario: JsonObject = {
        "id": scenario_id,
        "input": draw(json_objects()),
        "assertions": draw(assertion_lists()),
    }
    scenario.update(
        _draw_optional(
            draw,
            None,
            {
                "description": st.one_of(st.none(), texts()),
                "trace": st.one_of(st.none(), texts(min_size=1)),
            },
        )
    )
    scenario.update(_draw_optional(draw, skipped, {"skip": texts(min_size=1)}))
    return scenario


@st.composite
def suite_dicts(draw: st.DrawFn, skipped: Presence = None) -> JsonObject:
    """A valid Suite: version 1, safe ids, case-insensitively unique Scenario ids."""
    ids = draw(st.lists(scenario_ids(), min_size=1, max_size=2, unique_by=str.lower))
    suite: JsonObject = {
        "version": 1,
        "suite": draw(scenario_ids()),
        "scenarios": [draw(scenario_dicts(scenario_id, skipped)) for scenario_id in ids],
    }
    suite.update(
        _draw_optional(
            draw,
            None,
            {"description": st.one_of(st.none(), texts()), "defaults": suite_defaults()},
        )
    )
    return suite


# --- Trace ---------------------------------------------------------------------------------


@st.composite
def tool_refs(draw: st.DrawFn, presence: Presence) -> JsonObject:
    ref: JsonObject = {"name": draw(texts())}
    ref.update(_draw_optional(draw, presence, {"call_id": st.one_of(st.none(), texts())}))
    return ref


@st.composite
def event_errors(draw: st.DrawFn) -> JsonObject:
    return {"type": draw(texts()), "message": draw(texts()), "unhandled": draw(st.booleans())}


@st.composite
def trace_events(draw: st.DrawFn, seq: int, presence: Presence) -> JsonObject:
    """One event at position ``seq``; ``presence`` decides which optional keys appear."""
    event: JsonObject = {"seq": seq, "type": draw(st.sampled_from(EVENT_TYPES))}
    event.update(
        _draw_optional(
            draw,
            presence,
            {
                "timestamp": timestamps(),
                "duration_ms": non_negative_ints(),
                "tool": tool_refs(presence),
                "arguments": json_values(),
                "result": json_values(),
                "status": texts(),
                "error": event_errors(),
                "output": json_values(),
                "redacted": st.booleans(),
                "metadata": json_objects(),
            },
        )
    )
    return event


@st.composite
def trace_dicts(draw: st.DrawFn, presence: Presence = None, max_events: int = 3) -> JsonObject:
    """A valid Trace: version 1, offset timestamps, contiguous ``seq`` from 0.

    ``presence=False`` omits every optional key at every level (criterion 2's input);
    ``None`` draws each; ``True`` emits each.
    """
    agent: JsonObject = {"name": draw(texts())}
    agent.update(_draw_optional(draw, presence, {"version": st.one_of(st.none(), texts())}))
    count = draw(st.integers(min_value=0, max_value=max_events))
    trace: JsonObject = {
        "version": 1,
        "run_id": draw(texts()),
        "scenario_id": draw(texts()),
        "started_at": draw(timestamps()),
        "ended_at": draw(timestamps()),
        "agent": agent,
        "adapter": {"name": draw(texts()), "version": draw(texts())},
        "events": [draw(trace_events(seq, presence)) for seq in range(count)],
    }
    nullable_text = st.one_of(st.none(), texts())
    trace.update(
        _draw_optional(
            draw,
            presence,
            {
                "model": st.fixed_dictionaries(
                    {}, optional={"provider": nullable_text, "name": nullable_text}
                ),
                "capture": st.fixed_dictionaries(
                    {},
                    optional={"tool_calls": st.sampled_from(["complete", "partial", "unknown"])},
                ),
                "environment": st.fixed_dictionaries(
                    {},
                    optional={
                        "package_version": nullable_text,
                        "python_version": nullable_text,
                        "os": nullable_text,
                        "source_revision": nullable_text,
                    },
                ),
                "redaction": st.fixed_dictionaries(
                    {},
                    optional={
                        "applied": st.booleans(),
                        "paths": st.lists(texts(), max_size=2),
                        "env_names": st.lists(texts(), max_size=2),
                    },
                ),
            },
        )
    )
    return trace


# --- Report --------------------------------------------------------------------------------


def _tally(items: list[JsonObject]) -> dict[str, int]:
    counts = {status: 0 for status in STATUSES}
    for item in items:
        counts[item["status"]] += 1
    return counts


@st.composite
def assertion_results(draw: st.DrawFn, assertion_id: str) -> JsonObject:
    result: JsonObject = {
        "assertion_id": assertion_id,
        "type": draw(st.one_of(st.sampled_from(ASSERTION_TYPES), texts(min_size=1))),
        "status": draw(statuses()),
        "message": draw(texts()),
        "evidence": draw(st.lists(non_negative_ints(), max_size=3)),
    }
    result.update(_draw_optional(draw, None, {"detail": json_values()}))
    return result


@st.composite
def scenario_results(draw: st.DrawFn, scenario_id: str) -> JsonObject:
    """One Scenario Result with reconciled counts and a cause tied to its status."""
    ids = draw(st.lists(texts(min_size=1), min_size=1, max_size=2, unique=True))
    assertions = [draw(assertion_results(assertion_id)) for assertion_id in ids]
    status = draw(statuses())
    result: JsonObject = {
        "scenario_id": scenario_id,
        "status": status,
        "counts": _tally(assertions),
        "assertions": assertions,
    }
    if status == "skipped":
        result.update(_draw_optional(draw, None, {"skip_reason": texts(min_size=1)}))
    elif status == "error":
        result.update(_draw_optional(draw, None, {"execution_error": texts(min_size=1)}))
    result.update(
        _draw_optional(
            draw,
            None,
            {
                "trace": st.one_of(st.none(), trace_dicts(max_events=2)),
                "duration_ms": st.one_of(st.none(), non_negative_ints()),
                "cost": st.one_of(st.none(), finite_floats()),
            },
        )
    )
    return result


@st.composite
def report_dicts(draw: st.DrawFn) -> JsonObject:
    """A valid Report: unique Scenario ids, counts and ``execution_failed`` derived right."""
    ids = draw(st.lists(texts(min_size=1), min_size=1, max_size=2, unique=True))
    scenarios = [draw(scenario_results(scenario_id)) for scenario_id in ids]
    every_result = [result for scenario in scenarios for result in scenario["assertions"]]
    return {
        "version": 1,
        "suite_id": draw(texts(min_size=1)),
        "run_id": draw(texts(min_size=1)),
        "created_at": draw(timestamps()),
        "package_version": draw(texts(min_size=1)),
        "schema_versions": {
            "suite": draw(st.integers(min_value=1, max_value=9)),
            "trace": draw(st.integers(min_value=1, max_value=9)),
        },
        "defaults": draw(suite_defaults()),
        "suite_status": draw(statuses()),
        "execution_failed": any(s.get("execution_error") is not None for s in scenarios),
        "counts": _tally(every_result),
        "scenarios": scenarios,
    }
