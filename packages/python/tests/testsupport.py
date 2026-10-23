"""Shared test support: the two repository roots and the one subprocess helper.

Imported as ``testsupport`` (``pyproject.toml`` puts ``tests/`` on ``pythonpath``). It is a
module rather than a set of pytest fixtures because several test modules need the roots
while pytest collects them (``parametrize`` lists, module-level paths), which a fixture
cannot serve. The devtools modules keep their own path constants: they are installed
code that must not import from ``tests``.
"""

import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path

# ``packages/python``: the directory holding ``pyproject.toml`` and ``uv.lock``.
PACKAGE_ROOT = Path(__file__).resolve().parents[1]
# The git repository root, where ``.importlinter``, ``schemas/`` and ``.github/`` live.
REPOSITORY_ROOT = PACKAGE_ROOT.parents[1]


def run_captured(
    argv: Sequence[str],
    *,
    timeout: float,
    cwd: Path | None = None,
    env: Mapping[str, str] | None = None,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run ``argv`` (never through a shell) and return its UTF-8 text output.

    ``env=None`` inherits the parent environment; a mapping replaces it whole, so a caller
    that wants the parent's variables passes ``{**os.environ, ...}``. ``check`` defaults to
    ``False``: the caller asserts on ``returncode`` and ``stderr``.
    """
    return subprocess.run(
        list(argv),
        cwd=cwd,
        env=None if env is None else dict(env),
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=timeout,
        check=check,
    )
