"""Schema v1 fixtures: valid files validate twice, invalid files fail as named (NFR-5, NFR-8).

``tests/fixtures/schema/v1/valid/`` holds the spine seeds in completed form and two minimal
files; ``invalid/`` holds one file per malformed-input class, named
``<kind>__<error type>__<dotted field path>.json`` so the expectation is read from the
file name and cannot diverge from the data. Valid fixtures are validated with the Pydantic
model and with ``jsonschema`` (Draft 2020-12, a ``referencing.Registry`` with no retrieve
hook, never ``RefResolver``) against the committed schema. Invalid fixtures must fail the
model with the named error type at the named location; whether ``jsonschema`` also rejects
them is stated per fixture in ``JSONSCHEMA_REJECTS`` and asserted both ways, because a
JSON Schema cannot express duplicate ids, ``seq`` contiguity, or a counts tally.

Fixtures are data: they are parsed with ``json.loads`` and handed to validators, never
executed. The one exception to JSON is the NaN fixture, which carries the bare ``NaN``
token that Python's ``json.loads`` accepts by default; it exists to prove the model
rejects what the parser lets through, and no JSON Schema validator can read it.
"""

import json
import re
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from pydantic import BaseModel, ValidationError
from referencing import Registry

from agentproof.constants import REDACTED
from agentproof.models import canonical
from agentproof.models.export_schemas import KINDS, file_name

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
SCHEMAS_DIR = PACKAGE_ROOT.parents[1] / "schemas"  # repository root (spine Structural Seed)
FIXTURES_DIR = PACKAGE_ROOT / "tests" / "fixtures" / "schema" / "v1"
VALID = sorted((FIXTURES_DIR / "valid").glob("*.json"))
INVALID = sorted((FIXTURES_DIR / "invalid").glob("*.json"))

# The completed spine seeds: written in Canonical form with every key, so they also prove
# the parse -> dump -> text round trip. The ``.minimal`` files carry only required keys.
CANONICAL_VALID = {"suite.json", "trace.json", "report.json"}

# Known gap, found by this story and not fixed here (a validation change is outside its
# boundary; routed in deferred-work.md): ``Scenario.skip`` rejects a present ``null``
# ("presence means skipped", story 2.2 review finding 3) while
# ``model_dump(mode="json")`` writes ``skip: null`` for an unskipped Scenario, so a Suite
# does not read back from its own dump, although AD-19 makes null and absent equivalent on
# input and the exported schema accepts ``null`` there. Strict xfail: these tests flip to
# failures the moment the model is fixed, which is the reminder to remove the mark.
SUITE_DUMP_GAP = pytest.mark.xfail(
    strict=True,
    reason="Scenario.skip rejects a present null, so a Suite does not read back from its dump",
)

# What ``jsonschema`` does with the invalid fixture: a list of the (failing keyword, JSON
# pointer) pairs it reports, False (weaker than the model: the rule is not expressible in
# JSON Schema, so it reports nothing), or None (the file is not JSON, so it is not run).
JSONSCHEMA_REJECTS: dict[str, list[tuple[str, str]] | bool | None] = {
    # unknown field
    "suite__extra_forbidden__scenarios.0.retries.json": [("additionalProperties", "/scenarios/0")],
    "trace__extra_forbidden__events.0.hostname.json": [("additionalProperties", "/events/0")],
    "report__extra_forbidden__defaults.telemetry.json": [("additionalProperties", "/defaults")],
    # disallowed environment key (the Environment allowlist, PRD AC-5.5)
    "trace__extra_forbidden__environment.HOME.json": [("additionalProperties", "/environment")],
    # missing version
    "suite__missing__version.json": [("required", "/")],
    "trace__missing__version.json": [("required", "/")],
    "report__missing__version.json": [("required", "/")],
    # unsupported version (the Suite reports Pydantic's literal_error; see the plan)
    "suite__literal_error__version.json": [("const", "/version"), ("enum", "/version")],
    "trace__unsupported_version__version.json": [("enum", "/version")],
    "report__unsupported_version__version.json": [("enum", "/version")],
    # duplicate id: not expressible in JSON Schema
    "suite__duplicate_scenario_id__scenarios.1.id.json": False,
    "suite__duplicate_assertion_id__scenarios.0.assertions.1.id.json": False,
    "report__duplicate_id__scenarios.1.scenario_id.json": False,
    # seq gap: not expressible in JSON Schema
    "trace__seq_not_contiguous__events.2.seq.json": False,
    # naive timestamp: caught by the exported pattern
    "trace__timestamp_format__started_at.json": [("pattern", "/started_at")],
    "trace__timestamp_format__events.1.timestamp.json": [("anyOf", "/events/1/timestamp")],
    "report__timestamp_format__created_at.json": [("pattern", "/created_at")],
    # unknown event type
    "trace__literal_error__events.1.type.json": [("enum", "/events/1/type")],
    # NaN: not JSON, so jsonschema is not run
    "trace__finite_number__events.1.arguments.json": None,
    # zero assertions
    "suite__too_short__scenarios.0.assertions.json": [("minItems", "/scenarios/0/assertions")],
    "report__too_short__scenarios.0.assertions.json": [("minItems", "/scenarios/0/assertions")],
    # counts tally: not expressible in JSON Schema
    "report__counts_mismatch__counts.json": False,
}

REQUIRED_ERROR_TYPES = {
    "extra_forbidden",
    "missing",
    "unsupported_version",
    "literal_error",
    "duplicate_scenario_id",
    "duplicate_assertion_id",
    "duplicate_id",
    "seq_not_contiguous",
    "timestamp_format",
    "finite_number",
    "too_short",
    "counts_mismatch",
}

_NAME = re.compile(r"^(suite|trace|report)__([a-z_]+)__([A-Za-z0-9_.]+)\.json$")


def _valid_params(names: set[str] | None = None) -> list[Any]:
    """Valid fixtures as parameters; the Suite files carry the known-gap xfail."""
    return [
        pytest.param(
            path, id=path.name, marks=[SUITE_DUMP_GAP] if path.name.startswith("suite") else []
        )
        for path in VALID
        if names is None or path.name in names
    ]


def _kind_of(path: Path) -> str:
    return path.name.split("__")[0].split(".")[0]


def _model_of(path: Path) -> type[BaseModel]:
    return KINDS[_kind_of(path)]


def _expectation(path: Path) -> tuple[str, str, tuple[int | str, ...]]:
    match = _NAME.match(path.name)
    assert match is not None, f"{path.name} is not <kind>__<error type>__<field path>.json"
    kind, error_type, loc_text = match.groups()
    loc = tuple(int(part) if part.isdigit() else part for part in loc_text.split("."))
    return kind, error_type, loc


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _reject_constant(name: str) -> Any:
    raise ValueError(f"{name} is not JSON")


def _validator(kind: str) -> Draft202012Validator:
    schema = json.loads((SCHEMAS_DIR / file_name(kind)).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    # A Registry with no ``retrieve`` hook: a ``$ref`` to anything outside the document
    # raises instead of being fetched (AGENTS.md policy; never RefResolver).
    return Draft202012Validator(schema, registry=Registry())


def _jsonschema_keyword_errors(kind: str, data: Any) -> list[tuple[str, str]]:
    """Each jsonschema error as ``(failing keyword, JSON pointer of the instance)``, sorted."""
    return sorted(
        (str(error.validator), "/" + "/".join(str(part) for part in error.absolute_path))
        for error in _validator(kind).iter_errors(data)
    )


def _jsonschema_errors(kind: str, data: Any) -> list[str]:
    errors = sorted(_validator(kind).iter_errors(data), key=lambda error: list(error.path))
    return [
        f"{'/'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
        for error in errors
    ]


# --- the archive is complete and consistently named ---------------------------------------


def test_valid_fixtures_cover_every_kind_including_the_completed_spine_seeds() -> None:
    assert {_kind_of(path) for path in VALID} == set(KINDS) == {"suite", "trace", "report"}
    assert CANONICAL_VALID <= {path.name for path in VALID}


def test_every_invalid_fixture_is_named_for_a_kind_an_error_type_and_a_path() -> None:
    assert INVALID, "the invalid archive is empty"
    for path in INVALID:
        kind, _error_type, loc = _expectation(path)
        assert kind in KINDS
        assert loc


def test_invalid_fixtures_cover_every_malformed_input_class() -> None:
    types = {_expectation(path)[1] for path in INVALID}
    assert REQUIRED_ERROR_TYPES <= types, REQUIRED_ERROR_TYPES - types
    names = {path.name for path in INVALID}
    assert "trace__extra_forbidden__environment.HOME.json" in names, "disallowed environment key"
    assert "trace__finite_number__events.1.arguments.json" in names, "NaN"


def test_every_invalid_fixture_has_a_stated_jsonschema_verdict() -> None:
    assert sorted(JSONSCHEMA_REJECTS) == [path.name for path in INVALID]


# --- criterion 3: valid fixtures ----------------------------------------------------------


@pytest.mark.parametrize("path", VALID, ids=lambda path: path.name)
def test_valid_fixture_validates_with_the_model(path: Path) -> None:
    model = _model_of(path).model_validate(_load(path))
    assert model.model_dump()["version"] == 1


@pytest.mark.parametrize("path", VALID, ids=lambda path: path.name)
def test_valid_fixture_validates_with_jsonschema_against_the_committed_schema(path: Path) -> None:
    assert _jsonschema_errors(_kind_of(path), _load(path)) == []


@pytest.mark.parametrize("path", VALID, ids=lambda path: path.name)
def test_valid_fixture_is_written_in_canonical_form(path: Path) -> None:
    # ``read_text`` normalizes a CRLF checkout to LF; the comparison is about content.
    text = path.read_text(encoding="utf-8")
    assert canonical.dumps(json.loads(text)) == text


@pytest.mark.parametrize("path", VALID, ids=lambda path: path.name)
def test_json_mode_dump_of_a_valid_fixture_validates_with_jsonschema(path: Path) -> None:
    model = _model_of(path).model_validate(_load(path))
    assert _jsonschema_errors(_kind_of(path), model.model_dump(mode="json")) == []


@pytest.mark.parametrize("path", _valid_params())
def test_valid_fixture_round_trips_through_a_json_mode_dump(path: Path) -> None:
    model_type = _model_of(path)
    model = model_type.model_validate(_load(path))
    assert model_type.model_validate(model.model_dump(mode="json")) == model


@pytest.mark.parametrize("path", _valid_params(CANONICAL_VALID))
def test_completed_seed_fixture_round_trips_to_the_same_text(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    model = _model_of(path).model_validate(json.loads(text))
    assert canonical.dumps(model.model_dump(mode="json")) == text


def test_suite_schema_accepts_a_null_skip_that_the_model_rejects() -> None:
    """The AD-19 gap behind ``SUITE_DUMP_GAP``, stated as the current behaviour."""
    data = _load(FIXTURES_DIR / "valid" / "suite.minimal.json")
    data["scenarios"][0]["skip"] = None
    assert _jsonschema_errors("suite", data) == []
    with pytest.raises(ValidationError) as excinfo:
        KINDS["suite"].model_validate(data)
    assert [tuple(error["loc"]) for error in excinfo.value.errors()] == [("scenarios", 0, "skip")]


def test_report_fixture_embeds_the_trace_fixture() -> None:
    report = _load(FIXTURES_DIR / "valid" / "report.json")
    trace = _load(FIXTURES_DIR / "valid" / "trace.json")
    assert report["scenarios"][0]["trace"] == trace
    assert report["scenarios"][0]["scenario_id"] == trace["scenario_id"]


# --- criterion 3: invalid fixtures --------------------------------------------------------


@pytest.mark.parametrize("path", INVALID, ids=lambda path: path.name)
def test_invalid_fixture_fails_the_model_with_the_named_error_type_at_the_named_path(
    path: Path,
) -> None:
    kind, error_type, loc = _expectation(path)
    with pytest.raises(ValidationError) as excinfo:
        KINDS[kind].model_validate(_load(path))
    found = [(error["type"], tuple(error["loc"])) for error in excinfo.value.errors()]
    assert (error_type, loc) in found, f"{path.name}: expected {error_type} at {loc}, got {found}"


@pytest.mark.parametrize("path", INVALID, ids=lambda path: path.name)
def test_jsonschema_verdict_on_an_invalid_fixture_matches_the_stated_flag(path: Path) -> None:
    kind, _error_type, _loc = _expectation(path)
    flag = JSONSCHEMA_REJECTS[path.name]
    text = path.read_text(encoding="utf-8")
    if flag is None:
        # Not JSON: a strict parse refuses the NaN token, so no schema validator applies.
        with pytest.raises(ValueError, match="NaN is not JSON"):
            json.loads(text, parse_constant=_reject_constant)
        return
    found = _jsonschema_keyword_errors(kind, json.loads(text))
    if flag is False:
        assert found == [], f"{path.name}: jsonschema is stated to be weaker here, but rejected it"
    else:
        # The expected failing keyword and JSON pointer(s), not merely "some error".
        assert found == sorted(flag), f"{path.name}: jsonschema reported {found}"


def test_jsonschema_locates_an_unknown_field_where_the_model_does() -> None:
    errors = _jsonschema_errors(
        "trace", _load(FIXTURES_DIR / "invalid" / "trace__extra_forbidden__environment.HOME.json")
    )
    assert errors == ["environment: Additional properties are not allowed ('HOME' was unexpected)"]


# --- policy: no secret value in any fixture or written schema -------------------------------


def test_fixtures_carry_only_the_redaction_marker_where_a_secret_would_be() -> None:
    for path in [*VALID, *INVALID]:
        text = path.read_text(encoding="utf-8")
        values = re.findall(r'"api_key":\s*"([^"]*)"', text)
        assert all(value == REDACTED for value in values), path.name
        assert "sk-" not in text, path.name
        assert "OPENAI_API_KEY=" not in text, path.name


def test_schema_files_contain_no_fixture_values() -> None:
    for kind in KINDS:
        text = (SCHEMAS_DIR / file_name(kind)).read_text(encoding="utf-8")
        for planted in (REDACTED, "expense-agent", "reject-over-limit", "fixture-reject"):
            assert planted not in text, f"{file_name(kind)} carries fixture value {planted!r}"
