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
