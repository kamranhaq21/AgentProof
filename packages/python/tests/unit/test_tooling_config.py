"""The tool configuration in ``pyproject.toml`` matches the architecture's typing convention."""

import tomllib
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[2]


def _pyproject() -> dict[str, object]:
    with (PACKAGE_ROOT / "pyproject.toml").open("rb") as handle:
        return tomllib.load(handle)


def test_mypy_is_strict_with_pydantic_plugin_on_src_only() -> None:
    mypy = _pyproject()["tool"]["mypy"]  # type: ignore[index]
    assert mypy["strict"] is True
    assert mypy["plugins"] == ["pydantic.mypy"]
    assert mypy["files"] == ["src"]


def test_runtime_dependencies_are_unchanged() -> None:
    project = _pyproject()["project"]  # type: ignore[index]
    names = sorted(dep.split(">=")[0] for dep in project["dependencies"])  # type: ignore[index]
    assert names == ["pydantic", "pyyaml", "rich", "typer"]


UNSAFE_DESERIALIZATION_RULES = ("S102", "S301", "S302", "S307", "S506")


def test_unsafe_deserialization_rules_are_selected_and_never_ignored_under_src() -> None:
    """AD-19 (story 3.2): exec, eval, pickle, marshal and yaml.load are banned everywhere.

    The rules are in ``select`` for the whole tree, and no ``per-file-ignores`` entry whose
    pattern lives under ``src/`` names any S rule (the shell packages are exempt only from
    the AD-1 TID251 list).
    """
    lint = _pyproject()["tool"]["ruff"]["lint"]  # type: ignore[index]
    assert set(UNSAFE_DESERIALIZATION_RULES) <= set(lint["select"])
    banned = lint["flake8-tidy-imports"]["banned-api"]
    assert {"pickle", "marshal", "shelve"} <= set(banned)
    for pattern, codes in lint["per-file-ignores"].items():
        if pattern.startswith("src/"):
            s_codes = [code for code in codes if code.startswith("S")]
            assert s_codes == [], (pattern, s_codes)


def test_the_only_s_rule_ignore_is_the_pickle_round_trip_test() -> None:
    ignores = _pyproject()["tool"]["ruff"]["lint"]["per-file-ignores"]  # type: ignore[index]
    with_s = {
        pattern: [code for code in codes if code.startswith("S")]
        for pattern, codes in ignores.items()
        if any(code.startswith("S") for code in codes)
    }
    assert with_s == {"tests/unit/test_errors_taxonomy.py": ["S301"]}
