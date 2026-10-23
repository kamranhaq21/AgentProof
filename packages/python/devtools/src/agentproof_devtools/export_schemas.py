"""Write the generated JSON Schemas to the repository's ``schemas/`` (architecture AD-4).

Development-time entry point, run as ``python -m agentproof_devtools.export_schemas
[output directory]`` (``uv run python -m ...`` from ``packages/python``). The schema text
comes from the pure ``agentproof.models.export_schemas``; this module only writes it as
UTF-8 without a byte order mark and with LF line endings. It lives in the devtools
workspace member, which is never part of the shipped wheel, so the product contains no
writer and the core purity rule (AD-1) has nothing to exempt.
"""

import sys
from collections.abc import Sequence
from pathlib import Path

from agentproof.models.export_schemas import KINDS, file_name, render

# ``packages/python``, resolved as ``check.py`` does (editable install of devtools); the
# repository root, where ``schemas/`` lives, is two levels above it.
PACKAGE_ROOT = Path(__file__).resolve().parents[3]
REPOSITORY_ROOT = PACKAGE_ROOT.parents[1]


def default_output_dir() -> Path:
    """``schemas/`` at the repository root (spine Structural Seed)."""
    return REPOSITORY_ROOT / "schemas"


def main(argv: Sequence[str] | None = None) -> int:
    """Write every schema file; return 0, or 2 when more than one argument is given.

    The optional argument is the output directory, created if missing; the default is
    ``default_output_dir()``. Each file is the UTF-8 encoding of ``render(kind)`` with no
    newline translation, so the bytes are the same on every platform.
    """
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) > 1:
        print("usage: python -m agentproof_devtools.export_schemas [output-dir]", file=sys.stderr)
        return 2
    output_dir = Path(args[0]) if args else default_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)
    for kind in KINDS:
        path = output_dir / file_name(kind)
        path.write_bytes(render(kind).encode("utf-8"))
        print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
