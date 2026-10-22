"""The package version comes from one place: ``pyproject.toml`` via installed metadata."""

import importlib.metadata
import tomllib
from pathlib import Path

import agentproof

PACKAGE_ROOT = Path(__file__).resolve().parents[2]


def test_version_equals_installed_metadata() -> None:
    assert agentproof.__version__ == importlib.metadata.version("agentproof")


def test_version_equals_pyproject_version() -> None:
    with (PACKAGE_ROOT / "pyproject.toml").open("rb") as handle:
        pyproject_version = tomllib.load(handle)["project"]["version"]
    assert agentproof.__version__ == pyproject_version


def test_public_api_is_exactly_version() -> None:
    assert agentproof.__all__ == ["__version__"]
