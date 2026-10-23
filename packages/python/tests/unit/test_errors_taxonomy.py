"""The error taxonomy (architecture AD-7) and the rule that only ``errors.py`` defines exceptions.

The taxonomy rule is checked by parsing every module under ``src/agentproof`` with ``ast``:
a class whose base is ``BaseException``, a name ending in ``Error``, ``Exception`` or
``Warning``, or any exception class ``agentproof.errors`` exports counts as an exception
class. Files are parsed, never imported, so a module with import-time side effects is
still covered.
"""

import ast
import copy
import inspect
import pickle
from pathlib import Path

import pytest

from agentproof import errors
from agentproof.errors import (
    AdapterLoadError,
    AdapterRunError,
    AgentProofError,
    ArtifactWriteError,
    ExecutionError,
    InputError,
    PathError,
    SuiteError,
    TraceFormatError,
    TraceMissingError,
    UnsupportedVersionError,
    Violation,
)

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = PACKAGE_ROOT / "src" / "agentproof"
ERRORS_MODULE = SOURCE_ROOT / "errors.py"

EXCEPTION_SUFFIXES = ("Error", "Exception", "Warning")

EXPORTED_EXCEPTIONS: frozenset[str] = frozenset(
    name
    for name in errors.__all__
    if isinstance(getattr(errors, name), type) and issubclass(getattr(errors, name), BaseException)
)

INPUT_ERRORS = (SuiteError, TraceFormatError, PathError, UnsupportedVersionError)
EXECUTION_ERRORS = (AdapterLoadError, AdapterRunError, TraceMissingError, ArtifactWriteError)


def _base_name(node: ast.expr) -> str | None:
    """The final identifier of a base-class expression: ``Exception``, ``errors.InputError``."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Subscript):
        return _base_name(node.value)
    return None


# Builtin ``BaseException`` subclasses whose names end in none of the suffixes above.
BUILTIN_EXCEPTIONS_WITHOUT_SUFFIX = frozenset(
    {
        "BaseException",
        "BaseExceptionGroup",
        "ExceptionGroup",
        "GeneratorExit",
        "KeyboardInterrupt",
        "StopAsyncIteration",
        "StopIteration",
        "SystemExit",
    }
)


def _is_exception_base(name: str) -> bool:
    return (
        name in BUILTIN_EXCEPTIONS_WITHOUT_SUFFIX
        or name.endswith(EXCEPTION_SUFFIXES)
        or name in EXPORTED_EXCEPTIONS
    )


def exception_classes_in(source: str, path: Path) -> list[str]:
    """Names of the classes in ``source`` that derive from an exception-looking base."""
    tree = ast.parse(source, filename=str(path))
    found: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        bases = (_base_name(base) for base in node.bases)
        if any(name is not None and _is_exception_base(name) for name in bases):
            found.append(node.name)
    return found


def _source_files() -> list[Path]:
    return sorted(SOURCE_ROOT.rglob("*.py"))


def test_source_tree_is_scanned_and_contains_errors_py() -> None:
    files = _source_files()
    assert ERRORS_MODULE in files
    assert len(files) > 1


@pytest.mark.parametrize(
    "path", [p for p in sorted(SOURCE_ROOT.rglob("*.py")) if p != ERRORS_MODULE], ids=str
)
def test_no_module_outside_errors_defines_an_exception_class(path: Path) -> None:
    assert exception_classes_in(path.read_text(encoding="utf-8"), path) == []


def test_errors_module_defines_exactly_the_exported_taxonomy() -> None:
    defined = exception_classes_in(ERRORS_MODULE.read_text(encoding="utf-8"), ERRORS_MODULE)
    assert sorted(defined) == sorted(EXPORTED_EXCEPTIONS)
    assert len(defined) == 11


@pytest.mark.parametrize(
    "source",
    [
        "class Oops(ValueError):\n    pass\n",
        "class Oops(Exception):\n    pass\n",
        "class Oops(BaseException):\n    pass\n",
        "class Oops(SystemExit):\n    pass\n",
        "import agentproof.errors\n\nclass Oops(agentproof.errors.InputError):\n    pass\n",
        "from agentproof.errors import SuiteError\n\nclass Oops(SuiteError):\n    pass\n",
        "class Oops(SomeWarning):\n    pass\n",
        "def f():\n    class Oops(RuntimeError):\n        pass\n",
    ],
)
def test_scanner_catches_a_planted_exception_class(source: str) -> None:
    assert exception_classes_in(source, Path("planted.py")) == ["Oops"]


def test_scanner_ignores_ordinary_classes() -> None:
    source = (
        "from dataclasses import dataclass\n"
        "@dataclass(frozen=True)\n"
        "class Point:\n    x: int\n"
        "class Handler(Base):\n    pass\n"
        "class Model(BaseModel):\n    pass\n"
    )
    assert exception_classes_in(source, Path("ordinary.py")) == []


def test_all_lists_every_public_class_and_nothing_else() -> None:
    public_classes = {
        name
        for name, member in inspect.getmembers(errors, inspect.isclass)
        if member.__module__ == errors.__name__ and not name.startswith("_")
    }
    assert set(errors.__all__) == public_classes
    assert "Violation" in errors.__all__
    assert errors.__all__ == sorted(errors.__all__)


@pytest.mark.parametrize("name", sorted(EXPORTED_EXCEPTIONS) + ["Violation"])
def test_every_public_name_has_a_docstring(name: str) -> None:
    member = getattr(errors, name)
    assert member.__doc__ and member.__doc__.strip()


def test_root_of_the_taxonomy_is_agentproof_error() -> None:
    assert issubclass(AgentProofError, Exception)
    assert not issubclass(AgentProofError, (ValueError, RuntimeError, OSError))
    for name in EXPORTED_EXCEPTIONS:
        assert issubclass(getattr(errors, name), AgentProofError), name


@pytest.mark.parametrize("cls", INPUT_ERRORS)
def test_input_errors_derive_from_input_error(cls: type[InputError]) -> None:
    assert issubclass(cls, InputError)
    assert not issubclass(cls, ExecutionError)
    assert cls.__mro__[1] is InputError


@pytest.mark.parametrize("cls", EXECUTION_ERRORS)
def test_execution_errors_derive_from_execution_error(cls: type[ExecutionError]) -> None:
    assert issubclass(cls, ExecutionError)
    assert not issubclass(cls, InputError)
    assert cls.__mro__[1] is ExecutionError


def test_input_and_execution_branches_are_disjoint_siblings() -> None:
    assert InputError.__mro__[1] is AgentProofError
    assert ExecutionError.__mro__[1] is AgentProofError
    assert not issubclass(InputError, ExecutionError)
    assert not issubclass(ExecutionError, InputError)


def test_violation_is_a_frozen_dataclass_of_three_strings() -> None:
    violation = Violation(source="suite.yaml", field="scenarios.0.id", message="bad id")
    assert (violation.source, violation.field, violation.message) == (
        "suite.yaml",
        "scenarios.0.id",
        "bad id",
    )
    assert violation == Violation("suite.yaml", "scenarios.0.id", "bad id")
    with pytest.raises(AttributeError):
        violation.message = "changed"  # type: ignore[misc]


def test_input_error_carries_its_violations_as_a_list_copy() -> None:
    given = [Violation("a.yaml", "x", "first"), Violation("a.yaml", "y", "second")]
    error = InputError(given)
    assert error.violations == given
    assert error.violations is not given
    given.append(Violation("a.yaml", "z", "third"))
    assert len(error.violations) == 2


def test_input_error_message_is_the_sole_violation_text() -> None:
    assert str(InputError([Violation("a.yaml", "x", "first")])) == "first"


def test_input_error_message_summarizes_several_violations() -> None:
    error = InputError([Violation("a.yaml", "x", "first"), Violation("a.yaml", "y", "second")])
    assert str(error) == "2 violations; first: first"


def test_input_error_survives_deepcopy_and_pickle() -> None:
    violations = [Violation("a.yaml", "x", "first"), Violation("a.yaml", "y", "second")]
    original = SuiteError(violations)
    for clone in (copy.deepcopy(original), pickle.loads(pickle.dumps(original))):
        assert type(clone) is SuiteError
        assert clone.violations == violations
        assert str(clone) == "2 violations; first: first"


def test_input_error_with_no_violations_still_has_a_message() -> None:
    error = InputError([])
    assert error.violations == []
    assert str(error) == "invalid input"


@pytest.mark.parametrize("cls", INPUT_ERRORS)
def test_input_error_subclasses_take_the_violation_list(cls: type[InputError]) -> None:
    error = cls([Violation("t.json", "version", "unsupported")])
    assert error.violations[0].field == "version"
    assert str(error) == "unsupported"
    with pytest.raises(InputError):
        raise error


@pytest.mark.parametrize("cls", EXECUTION_ERRORS + (ExecutionError,))
def test_execution_errors_take_a_plain_message(cls: type[ExecutionError]) -> None:
    error = cls("adapter exploded")
    assert str(error) == "adapter exploded"
    with pytest.raises(AgentProofError):
        raise error
