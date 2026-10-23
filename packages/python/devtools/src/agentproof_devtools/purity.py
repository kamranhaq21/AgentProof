"""AST purity checker for the core packages (architecture AD-1).

ruff's TID251 bans importable names (``subprocess``, ``os.environ``, ``time``, ...), but a
bare ``open(`` call and a ``pathlib.Path`` I/O method call are not imports, so ruff cannot
see them. This module parses each core file with ``ast`` and reports those two shapes:

* a call to the bare builtin ``open``;
* an attribute call whose name is a ``Path`` I/O method (``read_text``, ``mkdir``,
  ``exists``, ...; see ``IO_METHOD_NAMES``) on any receiver.

The files are parsed, never imported or executed. Receivers are not type-resolved, so the
second rule has a known false-positive surface: ``s.replace("a", "b")`` on a ``str`` is
reported like ``path.replace(target)``. In core code either write it as
``str.replace(s, "a", "b")`` (a receiver that is the name ``str`` or ``bytes``, or a literal
such as ``"a-b".replace(...)``, is skipped) or suppress the one line with ``# purity: ok``.

Run as ``python -m agentproof_devtools.purity <target>...`` where each target is a core
package directory or module path under ``src/agentproof``; a module given without its
``.py`` suffix (``src/agentproof/constants``) is resolved to the file. Findings are printed
one per line as ``path:line:col: purity: <call>`` and the exit code is 1 when there is
any finding, 2 when a target is missing or a file cannot be parsed (a syntax error, or
bytes that are not valid UTF-8).
"""

import ast
import re
import sys
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path

# The nine core packages and modules of ``agentproof`` bound by AD-1 (plan boundary).
CORE_PACKAGES: tuple[str, ...] = (
    "constants",
    "errors",
    "models",
    "loading",
    "redaction",
    "assertions",
    "engine",
    "reports",
    "compare",
)

# ``pathlib.Path`` methods that touch the filesystem.
IO_METHOD_NAMES: frozenset[str] = frozenset(
    {
        "read_text",
        "read_bytes",
        "write_text",
        "write_bytes",
        "open",
        "mkdir",
        "unlink",
        "rename",
        "replace",
        "touch",
        "exists",
        "is_file",
        "is_dir",
        "iterdir",
        "glob",
        "rglob",
        "stat",
    }
)

# Receivers that are plainly not a ``Path``: ``str.replace(s, ...)`` and ``bytes.replace``.
_NON_PATH_RECEIVER_NAMES: frozenset[str] = frozenset({"str", "bytes"})

SUPPRESSION_MARKER = "# purity: ok"

# The newlines the Python tokenizer recognises. ``str.splitlines`` also splits on form
# feeds and other separators, which would put a suppression marker on the wrong line.
_NEWLINE = re.compile(r"\r\n|\r|\n")


@dataclass(frozen=True)
class Violation:
    """One banned call: where it is, the method or builtin name, and the callee source."""

    path: Path
    line: int
    col: int  # 1-based character column, like ruff's
    name: str
    call: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}:{self.col}: purity: {self.call}"


def _is_exempt_receiver(receiver: ast.expr) -> bool:
    if isinstance(receiver, ast.Constant):
        return True
    return isinstance(receiver, ast.Name) and receiver.id in _NON_PATH_RECEIVER_NAMES


def _banned_name(call: ast.Call) -> str | None:
    """Return the banned name a call hits, or ``None`` when the call is allowed."""
    func = call.func
    if isinstance(func, ast.Name):
        return "open" if func.id == "open" else None
    if isinstance(func, ast.Attribute) and func.attr in IO_METHOD_NAMES:
        return None if _is_exempt_receiver(func.value) else func.attr
    return None


def scan_source(source: str, path: Path) -> list[Violation]:
    """Return the violations in ``source``; ``path`` is used for messages only.

    A line containing ``# purity: ok`` suppresses findings whose call starts on it.
    """
    tree = ast.parse(source, filename=str(path))
    lines = _NEWLINE.split(source)
    violations: list[Violation] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _banned_name(node)
        if name is None:
            continue
        line = lines[node.lineno - 1]
        if SUPPRESSION_MARKER in line:
            continue
        # ``col_offset`` counts UTF-8 bytes; report characters, as ruff does.
        col = len(line.encode("utf-8")[: node.col_offset].decode("utf-8")) + 1
        violations.append(
            Violation(
                path=path,
                line=node.lineno,
                col=col,
                name=name,
                call=ast.unparse(node.func),
            )
        )
    return sorted(violations, key=lambda violation: (violation.line, violation.col))


def find_violations(path: Path) -> list[Violation]:
    """Parse the file at ``path`` and return its violations in source order."""
    return scan_source(path.read_text(encoding="utf-8"), path)


def resolve_target(target: Path) -> Path:
    """Return the directory or module file a target names.

    ``src/agentproof/constants`` resolves to ``constants.py`` while ``constants`` is a
    module, and to the directory once it becomes a package.
    """
    if target.is_dir() or target.is_file():
        return target
    module = target.with_suffix(".py")
    if module.is_file():
        return module
    raise FileNotFoundError(f"no package directory or module for {target}")


def iter_python_files(target: Path) -> Iterator[Path]:
    """Yield the ``.py`` files under a directory target, or the module file itself."""
    if target.is_dir():
        yield from sorted(target.rglob("*.py"))
    else:
        yield target


def main(argv: Sequence[str] | None = None) -> int:
    """Check every target; print findings; return 1 on findings, 2 on usage errors."""
    targets = list(sys.argv[1:] if argv is None else argv)
    if not targets:
        print("usage: python -m agentproof_devtools.purity <target>...", file=sys.stderr)
        return 2
    found = 0
    for raw in targets:
        try:
            target = resolve_target(Path(raw))
        except FileNotFoundError as error:
            print(f"purity: {error}", file=sys.stderr)
            return 2
        for file in iter_python_files(target):
            try:
                violations = find_violations(file)
            except (SyntaxError, UnicodeDecodeError) as error:
                print(f"purity: cannot parse {file}: {error}", file=sys.stderr)
                return 2
            for violation in violations:
                print(violation, flush=True)
            found += len(violations)
    if found:
        print(f"purity: {found} banned call(s) in core code (AD-1)", flush=True)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
