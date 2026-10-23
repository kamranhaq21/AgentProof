"""``load_suite``: the shell half of the parse/load split (architecture AD-15).

``loading`` is a core package and may not import ``io``, so the function that reads a
file and then parses it lives here in the shell: ``io.read_limited`` (size limit, symlink
policy, UTF-8) and then ``loading.suite.parse_suite``.
"""

from pathlib import Path

from agentproof.constants import MAX_SUITE_BYTES
from agentproof.io import read_limited
from agentproof.loading.suite import parse_suite
from agentproof.models.suite import Suite

__all__ = ["load_suite"]


def load_suite(path: Path, *, base_dir: Path | None = None) -> Suite:
    """Read ``path`` (at most ``MAX_SUITE_BYTES``) and parse it; ``source`` is ``str(path)``.

    ``base_dir`` defaults to the file's own parent directory, so a symlink that points
    out of the Suite's directory is refused (AD-14); the shell passes a wider directory
    explicitly when it wants to allow one.
    """
    path = Path(path)
    root = path.parent if base_dir is None else base_dir
    text = read_limited(path, MAX_SUITE_BYTES, base_dir=root)
    return parse_suite(text, source=str(path))
