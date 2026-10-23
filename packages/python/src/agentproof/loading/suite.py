"""``parse_suite``: Suite text to a ``Suite``, reporting every violation at once (AD-15, AD-19).

Text goes through ``yaml_safe.load`` first; any YAML-safety fault (custom tag, duplicate
key, alias, second document, ...) propagates unchanged as the ``SuiteError`` it already
is, with a ``line:column`` ``Violation.field``. The resulting dict is then validated by
``Suite.model_validate`` and every Pydantic error becomes one ``Violation`` in a single
``SuiteError`` (PRD AC-2.4), so a user fixes a file in one pass.

``Violation.field`` convention (shared with ``yaml_safe``): a field that fully matches
``\\d+:\\d+`` is a 1-based ``line:column`` position in the text; any other non-empty field
is the dotted model path (``scenarios.1.id``; list indexes are 0-based); an empty field
means the whole document. The positional form only ever comes from text-level faults, the
dotted form only from model validation, and the two are never mixed in one ``SuiteError``
because validation runs only on text that loaded cleanly.

Ordering rule: violations are sorted by their path, element by element, with list indexes
compared numerically and names compared as strings, and a name sorts after an index;
violations with an identical path keep the order Pydantic reported them. The order
therefore depends only on the paths, not on Pydantic's internal traversal. The module
does no I/O (the shell reads the file; ``runner.suite_file.load_suite``).
"""

from pydantic import ValidationError

from agentproof.errors import SuiteError, Violation
from agentproof.loading import yaml_safe
from agentproof.models.suite import Suite

__all__ = ["parse_suite"]

_TOO_DEEP = "a value is nested too deeply to validate"


def _sort_key(loc: tuple[int | str, ...]) -> tuple[tuple[int, int, str], ...]:
    return tuple((0, part, "") if isinstance(part, int) else (1, 0, part) for part in loc)


_UNION_TAGS = frozenset({"bool", "int", "float", "str", "none", "nullable"})


def _value_root(loc: tuple[int | str, ...]) -> tuple[int | str, ...]:
    """``loc`` cut before the first union-branch tag Pydantic appends under a JSON value."""
    for position, part in enumerate(loc):
        if isinstance(part, str) and (part in _UNION_TAGS or part.startswith(("list[", "dict["))):
            return loc[:position]
    return loc


def _violations(error: ValidationError, source: str) -> list[Violation]:
    items = [(tuple(item["loc"]), item) for item in error.errors(include_url=False)]
    # A JSON value nested too deeply yields one error per union branch per level (about
    # 500 lines, deferred F3); everything under the value collapses to one violation.
    deep_roots = {_value_root(loc) for loc, item in items if item["type"] == "recursion_loop"}
    found: list[tuple[tuple[int | str, ...], str]] = [(root, _TOO_DEEP) for root in deep_roots]
    for loc, item in items:
        if not any(loc[: len(root)] == root for root in deep_roots):
            found.append((loc, item["msg"]))
    found.sort(key=lambda entry: _sort_key(entry[0]))
    return [
        Violation(source=source, field=".".join(str(part) for part in loc), message=message)
        for loc, message in found
    ]


def parse_suite(text: str, *, source: str) -> Suite:
    """Parse Suite YAML text into a ``Suite`` or raise one ``SuiteError`` with every violation.

    ``source`` labels the text (a path or ``<stdin>``) on every ``Violation``. Nothing in
    the text is executed or constructed beyond what ``yaml_safe.load`` and the Suite model
    do. A validation error that is not a ``ValidationError`` is a bug and propagates,
    except ``RecursionError`` from pathologically deep values, which becomes a violation.
    """
    data = yaml_safe.load(text, source=source)
    try:
        return Suite.model_validate(data)
    except ValidationError as error:
        raise SuiteError(_violations(error, source)) from None
    except RecursionError:
        raise SuiteError([Violation(source=source, field="", message=_TOO_DEEP)]) from None
