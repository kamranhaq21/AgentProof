"""The fault-injection hook is unreachable from any core package (AD-1, AD-17; story 3.1
criterion 5).

The whole ``src/agentproof`` tree is scanned, not just ``cli/``: the two variable names
and ``inject_fault`` appear only where the hook lives and is used, and no core package
reads the environment at all. Files are parsed or read, never imported.
"""

import ast
from pathlib import Path

from agentproof_devtools.purity import CORE_PACKAGES

SOURCE_ROOT = Path(__file__).resolve().parents[3] / "src" / "agentproof"
HOOK_MODULE = SOURCE_ROOT / "cli" / "commands" / "__init__.py"
HOOK_USERS = {HOOK_MODULE, SOURCE_ROOT / "cli" / "commands" / "version.py"}
HOOK_NAMES = ("AGENTPROOF_TESTING", "AGENTPROOF_FAULT_INJECT", "inject_fault")


def _files() -> list[Path]:
    files = sorted(SOURCE_ROOT.rglob("*.py"))
    assert files
    return files


def _core_files() -> list[Path]:
    core = []
    for name in CORE_PACKAGES:
        package = SOURCE_ROOT / name
        core.extend(
            sorted(package.rglob("*.py")) if package.is_dir() else [package.with_suffix(".py")]
        )
    core.append(SOURCE_ROOT / "__init__.py")
    return core


def test_the_hook_names_appear_only_in_the_hook_and_its_callers() -> None:
    mentions = {
        path.relative_to(SOURCE_ROOT).as_posix()
        for path in _files()
        if any(name in path.read_text(encoding="utf-8") for name in HOOK_NAMES)
    }
    allowed = {path.relative_to(SOURCE_ROOT).as_posix() for path in HOOK_USERS}
    assert mentions <= allowed, (
        f"fault-injection names outside the cli commands: {mentions - allowed}"
    )
    assert HOOK_MODULE.relative_to(SOURCE_ROOT).as_posix() in mentions


def test_only_the_hook_module_reads_the_fault_variables() -> None:
    """The environment variables are named as strings in exactly one module."""
    for path in _files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        strings = {
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
        }
        if any(value.startswith("AGENTPROOF_") for value in strings):
            assert path == HOOK_MODULE, path


def test_no_core_package_reads_the_environment() -> None:
    offenders = {}
    for path in _core_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        hits = sorted(
            {
                ast.unparse(node)
                for node in ast.walk(tree)
                if isinstance(node, ast.Attribute)
                and node.attr in {"environ", "getenv", "environb", "putenv"}
                or isinstance(node, ast.Name)
                and node.id in {"environ", "getenv"}
            }
        )
        if hits:
            offenders[path.relative_to(SOURCE_ROOT).as_posix()] = hits
    assert offenders == {}


def test_no_core_package_imports_the_cli() -> None:
    for path in _core_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            modules = []
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                modules = [node.module or ""]
            assert not any(
                m == "agentproof.cli" or m.startswith("agentproof.cli.") for m in modules
            ), path
