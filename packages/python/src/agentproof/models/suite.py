"""Suite, Suite defaults, and Scenario models (architecture Schemas seed; AD-3, AD-8, AD-14).

The shape of what a user writes. Every rule the PRD places at load time is a validator on
these models, so the loader (``loading.parse_suite``), the public API, and every test
agree on what a valid Suite is: the integer schema version, the scenario id charset and
Windows device names (AD-14; ``constants`` holds the definitions and this module is the
only validator), case-insensitive scenario id uniqueness, at least one Assertion per
Scenario, default Assertion ids ``<type>-<0-based index>`` (AD-8), and unique Assertion
ids within a Scenario.

The uniqueness rules run over the raw input lists in ``wrap`` validators and their
findings are merged with the element errors, so a duplicate id is reported even when a
sibling item is invalid (PRD AC-2.4: every violation, not only the first) and every
finding carries the path of the offending item.

Models are shallow-frozen: sequence fields are tuples; mapping fields (``input``) stay
plain dicts and are not deep-frozen. JSON input lists validate into the tuples and
``model_dump(mode="json")`` writes them back as arrays.

Validation is dict in, model out. Nothing here parses YAML or JSON text, reads a file,
or touches the clock or the environment (AD-1); ``scenario.trace`` is a string the shell
resolves against the Suite file's directory.
"""

from collections.abc import Sequence
from typing import Annotated, Final, Literal, get_args

from pydantic import (
    AfterValidator,
    BaseModel,
    Field,
    ValidationError,
    ValidationInfo,
    ValidatorFunctionWrapHandler,
    field_validator,
)
from pydantic_core import InitErrorDetails, PydanticCustomError
from pydantic_core.core_schema import ErrorType

from agentproof.constants import SCENARIO_ID_RE, WINDOWS_DEVICE_NAMES
from agentproof.models.assertions import (
    ARGUMENT_PATH_PATTERN,
    MODEL_CONFIG,
    ArgumentPath,
    AssertionConfig,
)
from agentproof.models.common import JsonValue

_KNOWN_ERROR_TYPES: Final[frozenset[str]] = frozenset(get_args(ErrorType))


def validate_id(value: str, *, kind: str) -> str:
    """Return ``value`` when it is a safe Suite or Scenario id, else raise ``ValueError``.

    The one implementation of the id rule (AD-14, PRD AC-2.5): a full match of
    ``constants.SCENARIO_ID_RE`` and not a reserved Windows device name in any case.
    ``kind`` names the field in the message (``"scenario id"``, ``"suite id"``). The
    message always quotes the offending id.
    """
    if SCENARIO_ID_RE.fullmatch(value) is None:
        raise ValueError(
            f"{kind} {value!r} must match {SCENARIO_ID_RE.pattern} "
            "(1 to 64 letters, digits, '.', '_' or '-', not starting with punctuation)"
        )
    if value.upper() in WINDOWS_DEVICE_NAMES:
        raise ValueError(
            f"{kind} {value!r} is a reserved Windows device name and cannot be a file name"
        )
    return value


def _pass_through(error: ValidationError) -> list[InitErrorDetails]:
    """The line errors of ``error`` as details ``ValidationError.from_exception_data`` accepts.

    Known error types keep their context so the message is rebuilt verbatim; custom
    types (ours, from a nested model) keep their rendered message.
    """
    details: list[InitErrorDetails] = []
    items = error.errors(include_url=False)
    # pydantic-core's tuple validator counts only the items that validated, so one invalid
    # element also yields "at least 1 item after validation, not 0" at the field itself.
    # That line is noise next to the element's own error; a genuinely empty input has no
    # element error and keeps its ``too_short``.
    element_failed = any(item["loc"] and isinstance(item["loc"][0], int) for item in items)
    for item in items:
        if element_failed and item["type"] == "too_short" and item["loc"] == ():
            continue
        if item["type"] in _KNOWN_ERROR_TYPES:
            detail: InitErrorDetails = {
                "type": item["type"],
                "loc": item["loc"],
                "input": item["input"],
            }
            if "ctx" in item:
                detail["ctx"] = item["ctx"]
        else:
            detail = {
                "type": PydanticCustomError(item["type"], item["msg"]),
                "loc": item["loc"],
                "input": item["input"],
            }
        details.append(detail)
    return details


def _validate_with_findings(
    handler: ValidatorFunctionWrapHandler,
    value: object,
    findings: list[InitErrorDetails],
    title: str,
) -> object:
    """Run the inner validation and raise it together with ``findings`` when either fails."""
    try:
        result = handler(value)
    except ValidationError as error:
        findings.extend(_pass_through(error))
        raise ValidationError.from_exception_data(title, findings) from None
    if findings:
        raise ValidationError.from_exception_data(title, findings)
    return result


def _two_segments(value: str) -> str:
    """An ``include_arguments`` entry is ``<tool>.<argument path>``: two or more segments."""
    if "." not in value:
        raise ValueError(
            f"include_arguments entry {value!r} must be <tool>.<argument path>, "
            "for example approve_expense.amount"
        )
    return value


CompareArgumentPath = Annotated[
    str, Field(pattern=ARGUMENT_PATH_PATTERN), AfterValidator(_two_segments)
]
"""A ``<tool>.<argument path>`` entry of ``compare.include_arguments`` (PRD AC-26.5)."""

Name = Annotated[str, Field(min_length=1)]
"""A non-empty name: a redaction key or an environment variable name."""


class FixtureDefaults(BaseModel):
    """``defaults.fixture``: how the Fixture Agent runs (AD-9; ARCH-5).

    With ``deterministic`` the runner derives ``run_id`` (``fixture-<scenario id>``) and
    the timestamps from the fixture Trace instead of the clock, so repeated runs write
    byte-identical artifacts.
    """

    model_config = MODEL_CONFIG

    deterministic: bool = False


class CompareDefaults(BaseModel):
    """``defaults.compare``: what a Comparison looks at beyond statuses and tool sequences.

    ``include_arguments`` lists ``<tool>.<argument path>`` entries, for example
    ``approve_expense.amount``; by default no arguments are compared (PRD AC-26.5).
    """

    model_config = MODEL_CONFIG

    include_arguments: tuple[CompareArgumentPath, ...] = ()


class RedactDefaults(BaseModel):
    """``defaults.redact``: the Redaction rules (AD-10, PRD FR-31).

    ``keys`` extends the built-in key set (``api_key``, ``token``, ``password``,
    ``authorization``) and cannot remove from it; ``paths`` are dotted paths; ``env`` names
    environment variables whose current values the runner scrubs. Names only, never
    values.
    """

    model_config = MODEL_CONFIG

    keys: tuple[Name, ...] = ()
    paths: tuple[ArgumentPath, ...] = ()
    env: tuple[Name, ...] = ()


class SuiteDefaults(BaseModel):
    """Suite-level settings every Scenario inherits (PRD Glossary "Suite defaults").

    Every field is optional in YAML; the Report snapshots the whole model with every
    field written (AD-19), so an absent section serializes as its defaults.
    """

    model_config = MODEL_CONFIG

    adapter: str | None = Field(default=None, min_length=1)
    """Adapter name or ``pkg.module:ClassName``; the CLI ``--adapter`` overrides it."""

    fail_on_missing_trace: bool = True
    """Whether an absent Trace yields ``error`` results (true) or ``skipped`` ones (AD-6)."""

    fixture: FixtureDefaults = Field(default_factory=FixtureDefaults)
    compare: CompareDefaults = Field(default_factory=CompareDefaults)
    redact: RedactDefaults = Field(default_factory=RedactDefaults)


class Scenario(BaseModel):
    """One Scenario: an id, an input for the adapter, an optional fixture Trace, Assertions.

    ``skip`` carries a reason and its presence means the Scenario is skipped (AD-6), so a
    present ``skip`` must be a reason string; absent it is ``None``. ``trace`` is a path
    string relative to the Suite file, the fixture source and the replay default; the
    shell resolves it. ``assertions`` has at least one item and every item carries an id
    after validation. ``input`` is a plain dict and is not deep-frozen.
    """

    model_config = MODEL_CONFIG

    id: str
    description: str | None = None
    skip: str | None = Field(default=None, min_length=1)
    input: dict[str, JsonValue]
    trace: str | None = Field(default=None, min_length=1)
    assertions: tuple[AssertionConfig, ...] = Field(min_length=1)

    @field_validator("id", mode="after")
    @classmethod
    def _safe_id(cls, value: str) -> str:
        return validate_id(value, kind="scenario id")

    @field_validator("skip", mode="before")
    @classmethod
    def _present_skip_is_a_reason(cls, value: object) -> object:
        # Runs only when ``skip`` is present in the input; presence means skipped, so a
        # null or non-string reason is a mistake rather than "not skipped".
        if not isinstance(value, str):
            raise ValueError(f"skip needs a reason string; presence means skipped, got {value!r}")
        return value

    @field_validator("assertions", mode="wrap")
    @classmethod
    def _assign_and_check_ids(
        cls, value: object, handler: ValidatorFunctionWrapHandler, info: ValidationInfo
    ) -> object:
        """Fill missing ids with ``<type>-<index>`` and reject duplicates (AD-8, AC-3.1).

        Works on the raw items so a duplicate is reported beside any element error, at
        the path of the later duplicate. Items that are not mappings are left for the
        element validation to report.
        """
        if not isinstance(value, Sequence) or isinstance(value, str | bytes):
            return handler(value)
        scenario = info.data.get("id")
        where = f"scenario {scenario!r}" if isinstance(scenario, str) else "scenario"
        findings: list[InitErrorDetails] = []
        seen: dict[str, int] = {}
        prepared: list[object] = []
        for index, item in enumerate(value):
            if not isinstance(item, dict):
                prepared.append(item)
                continue
            ident = item.get("id")
            if ident is None and isinstance(item.get("type"), str):
                ident = f"{item['type']}-{index}"
                item = {**item, "id": ident}
            prepared.append(item)
            if not isinstance(ident, str):
                continue
            first = seen.get(ident)
            if first is None:
                seen[ident] = index
                continue
            findings.append(
                {
                    "type": PydanticCustomError(
                        "duplicate_assertion_id",
                        "{where}: duplicate assertion id {id} at assertions[{first}] "
                        "and assertions[{index}]",
                        {"where": where, "id": repr(ident), "first": first, "index": index},
                    ),
                    "loc": (index, "id"),
                    "input": ident,
                }
            )
        return _validate_with_findings(handler, prepared, findings, "Scenario")


class Suite(BaseModel):
    """A Suite file: schema version, Suite id, optional description, defaults, Scenarios.

    ``version`` is the integer schema version; ``1`` is the only value this model
    accepts and ``constants.SUPPORTED_VERSIONS["suite"]`` lists it (AD-3). ``suite`` is an
    id with the same rule as Scenario ids. Scenario ids are unique when compared
    case-insensitively so they are safe as file names on every platform (AC-2.5).
    """

    model_config = MODEL_CONFIG

    version: Literal[1]
    suite: str
    description: str | None = None
    defaults: SuiteDefaults = Field(default_factory=SuiteDefaults)
    scenarios: tuple[Scenario, ...] = Field(min_length=1)

    @field_validator("version", mode="before")
    @classmethod
    def _integer_version(cls, value: object) -> object:
        # ``Literal[1]`` alone also accepts ``True`` and ``1.0`` in Python mode (``strict``
        # cannot be applied to a literal schema); AD-3 wants the integer and nothing else.
        if type(value) is not int:
            raise ValueError(f"version must be an integer schema version, got {value!r}")
        return value

    @field_validator("suite", mode="after")
    @classmethod
    def _safe_suite_id(cls, value: str) -> str:
        return validate_id(value, kind="suite id")

    @field_validator("scenarios", mode="wrap")
    @classmethod
    def _unique_ids_case_insensitively(
        cls, value: object, handler: ValidatorFunctionWrapHandler
    ) -> object:
        """Reject scenario ids equal case-insensitively, at the path of the later one.

        Works on the raw items so the duplicate is reported beside any element error.
        """
        if not isinstance(value, Sequence) or isinstance(value, str | bytes):
            return handler(value)
        findings: list[InitErrorDetails] = []
        seen: dict[str, tuple[int, str]] = {}
        for index, item in enumerate(value):
            if not isinstance(item, dict):
                continue
            ident = item.get("id")
            if not isinstance(ident, str):
                continue
            first = seen.get(ident.lower())
            if first is None:
                seen[ident.lower()] = (index, ident)
                continue
            first_index, first_id = first
            findings.append(
                {
                    "type": PydanticCustomError(
                        "duplicate_scenario_id",
                        "duplicate scenario id {id} at scenarios[{index}] matches {first_id} "
                        "at scenarios[{first_index}] (ids are compared case-insensitively)",
                        {
                            "id": repr(ident),
                            "index": index,
                            "first_id": repr(first_id),
                            "first_index": first_index,
                        },
                    ),
                    "loc": (index, "id"),
                    "input": ident,
                }
            )
        return _validate_with_findings(handler, value, findings, "Suite")
