"""Size-limited reading of input files (architecture AD-14, AD-19; PRD AC-1.2).

``read_limited`` is the one way the shell turns an input file into text for the core
parsers. It does the three things the core cannot (AD-1):

- it resolves the path (following symlinks and ``..``) and refuses a file whose real path
  is outside ``base_dir``'s real path, naming the escape;
- it refuses a file larger than ``max_bytes`` before decoding or parsing anything, naming
  the limit. The size comes from ``stat`` first; the read itself is then capped at
  ``max_bytes + 1`` bytes, so a file that grows between the check and the read still
  cannot cost more than the limit;
- it decodes the bytes as strict UTF-8 and reports a decode failure as a ``PathError``
  naming the byte offset (never the content), so no raw ``UnicodeDecodeError`` escapes.

Every refusal is a ``PathError`` with one ``Violation`` whose ``source`` is the path as
given and whose ``field`` is empty. File content is never echoed in a message.
"""

from pathlib import Path

from agentproof.errors import PathError, Violation

__all__ = ["read_limited"]


def _refuse(path: Path, message: str) -> PathError:
    return PathError([Violation(source=str(path), field="", message=message)])


def read_limited(path: Path, max_bytes: int, *, base_dir: Path) -> str:
    """Return the UTF-8 text of ``path`` or raise ``PathError``.

    ``base_dir`` is the directory the file must stay inside once symlinks and ``..`` are
    resolved. A BOM, if any, is kept (the YAML loader accepts one at the very start).

    Known limit (TOCTOU): containment is checked against the resolved real path before the
    file is opened, so a path component swapped to a symlink between that check and the
    open could still escape. This is an accepted limit of path-based checks for a local
    CLI and is not fixed here.
    """
    try:
        real = path.resolve(strict=False)
        root = base_dir.resolve(strict=False)
    except (OSError, RuntimeError, ValueError) as error:
        raise _refuse(path, f"the path cannot be resolved ({type(error).__name__})") from None
    if not real.is_relative_to(root):
        raise _refuse(
            path,
            f"the path resolves outside the allowed directory {str(root)!r} (to {str(real)!r}); "
            "symlinks and '..' may not escape it",
        )
    try:
        size = real.stat().st_size
        if not real.is_file():
            raise _refuse(path, "the path is not a regular file")
        if size > max_bytes:
            raise _refuse(path, f"the file is {size} bytes, over the limit of {max_bytes} bytes")
        with real.open("rb") as handle:
            data = handle.read(max_bytes + 1)
    except FileNotFoundError:
        raise _refuse(path, "the file does not exist") from None
    except PermissionError:
        raise _refuse(path, "the file cannot be read: permission denied") from None
    except OSError as error:
        raise _refuse(path, f"the file cannot be read ({type(error).__name__})") from None
    if len(data) > max_bytes:
        raise _refuse(path, f"the file is over the limit of {max_bytes} bytes")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise _refuse(
            path, f"the file is not valid UTF-8 (invalid byte at offset {error.start})"
        ) from None
