"""The AST purity checker on inline sources: bare ``open``, Path I/O methods, exemptions."""

import sys
from pathlib import Path

import pytest

from agentproof_devtools.purity import (
    CORE_PACKAGES,
    IO_METHOD_NAMES,
    Violation,
    find_violations,
    main,
    resolve_target,
    scan_source,
)

SOURCE_PATH = Path("src/agentproof/engine/__init__.py")


def _names(source: str) -> list[str]:
    return [violation.name for violation in scan_source(source, SOURCE_PATH)]


def test_core_packages_are_the_nine_from_the_architecture() -> None:
    assert CORE_PACKAGES == (
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


def test_bare_open_is_reported_with_position_and_call() -> None:
    violations = scan_source('x = 1\nhandle = open("x")\n', SOURCE_PATH)
    assert violations == [Violation(SOURCE_PATH, 2, 10, "open", "open")]
    assert str(violations[0]) == f"{SOURCE_PATH}:2:10: purity: open"


@pytest.mark.parametrize("method", sorted(IO_METHOD_NAMES))
def test_every_path_io_method_is_reported_on_a_path_receiver(method: str) -> None:
    assert _names(f'from pathlib import Path\n\nPath("x").{method}()\n') == [method]
    assert _names(f"def f(p):\n    return p.{method}()\n") == [method]


def test_call_text_names_the_receiver_for_the_report() -> None:
    violations = scan_source('from pathlib import Path\nPath("x").read_text()\n', SOURCE_PATH)
    assert [violation.call for violation in violations] == ["Path('x').read_text"]


def test_qualified_open_calls_are_reported_as_attribute_calls() -> None:
    assert _names('import builtins\nimport io\nbuiltins.open("a")\nio.open("b")\n') == [
        "open",
        "open",
    ]


def test_nested_and_multiple_calls_are_reported_in_source_order() -> None:
    source = (
        "from pathlib import Path\n"
        "\n"
        "def load(p: Path) -> str:\n"
        "    if p.exists():\n"
        "        return p.read_text()\n"
        '    with open("fallback") as handle:\n'
        "        return handle.read()\n"
    )
    violations = scan_source(source, SOURCE_PATH)
    assert [(v.line, v.name) for v in violations] == [(4, "exists"), (5, "read_text"), (6, "open")]


def test_literal_and_str_receivers_are_exempt() -> None:
    assert _names('"a-b".replace("-", "_")\n') == []
    assert _names('b"a-b".replace(b"-", b"_")\n') == []
    assert _names('def f(s: str) -> str:\n    return str.replace(s, "a", "b")\n') == []
    assert _names('def f(s: bytes) -> bytes:\n    return bytes.replace(s, b"a", b"b")\n') == []


def test_replace_on_an_unresolved_receiver_is_the_documented_false_positive() -> None:
    # Receivers are not type-resolved: ``s.replace`` on a str is reported like Path.replace.
    assert _names('def f(s: str) -> str:\n    return s.replace("a", "b")\n') == ["replace"]


def test_suppression_marker_silences_the_line_only() -> None:
    source = (
        "def f(s: str, p):\n"
        '    a = s.replace("a", "b")  # purity: ok\n'
        '    b = s.replace("c", "d")\n'
        "    return a + b\n"
    )
    assert [(v.line, v.name) for v in scan_source(source, SOURCE_PATH)] == [(3, "replace")]


def test_columns_are_characters_and_form_feeds_do_not_shift_lines() -> None:
    # Line 2 is a lone form feed, which str.splitlines would count as a line break; the
    # ``éé`` prefix is two characters but four UTF-8 bytes.
    source = 'x = 1\n\x0c\ns = "éé"; open(s)  # purity: ok\nt = "éé"; open(t)\n'
    violations = scan_source(source, SOURCE_PATH)
    assert [(v.line, v.col, v.name) for v in violations] == [(4, 11, "open")]


def test_unrelated_calls_and_attributes_are_not_reported() -> None:
    source = (
        "from pathlib import Path\n"
        "\n"
        "def f(p: Path, d: dict[str, int], xs: list[int]) -> int:\n"
        "    _ = p.name, p.suffix, p.parent / 'x', p.with_suffix('.json'), p.as_posix()\n"
        "    _ = d.get('k'), len(xs), sorted(xs), d.open_count if hasattr(d, 'open_count') else 0\n"
        "    _ = p.exists\n"
        "    return 0\n"
    )
    assert _names(source) == []


def test_files_are_parsed_not_imported(tmp_path: Path) -> None:
    """A module whose import would fail loudly is still checked, and the side effect never runs."""
    marker = tmp_path / "imported.txt"
    module = tmp_path / "mod.py"
    module.write_text(
        "import this_module_does_not_exist_anywhere\n"
        f"open({str(marker)!r}, 'w').close()\n"
        "raise SystemExit(99)\n",
        encoding="utf-8",
    )
    assert [v.name for v in find_violations(module)] == ["open"]
    assert not marker.exists()


def test_resolve_target_accepts_directory_module_file_and_suffixless_module(
    tmp_path: Path,
) -> None:
    package = tmp_path / "models"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    module = tmp_path / "constants.py"
    module.write_text("", encoding="utf-8")
    assert resolve_target(package) == package
    assert resolve_target(module) == module
    assert resolve_target(tmp_path / "constants") == module
    with pytest.raises(FileNotFoundError):
        resolve_target(tmp_path / "missing")


def test_main_reports_findings_per_file_and_exits_one(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    engine = tmp_path / "engine"
    engine.mkdir()
    (engine / "__init__.py").write_text("", encoding="utf-8")
    (engine / "fold.py").write_text('from pathlib import Path\nPath("x").read_text()\n', "utf-8")
    (tmp_path / "errors.py").write_text('open("x")\n', encoding="utf-8")
    assert main([str(engine), str(tmp_path / "errors")]) == 1
    out = capsys.readouterr().out.splitlines()
    assert out == [
        f"{engine / 'fold.py'}:2:1: purity: Path('x').read_text",
        f"{tmp_path / 'errors.py'}:1:1: purity: open",
        "purity: 2 banned call(s) in core code (AD-1)",
    ]


def test_main_is_silent_and_exits_zero_on_clean_targets(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "constants.py").write_text('SCHEMA_VERSION = "1"\n', encoding="utf-8")
    assert main([str(tmp_path / "constants")]) == 0
    assert capsys.readouterr().out == ""


def test_main_exits_two_on_missing_target_or_no_targets(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main([str(tmp_path / "missing")]) == 2
    assert "no package directory or module" in capsys.readouterr().err
    assert main([]) == 2
    assert "usage" in capsys.readouterr().err


def test_main_exits_two_on_unparsable_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "broken.py").write_text("def (:\n", encoding="utf-8")
    assert main([str(tmp_path / "broken.py")]) == 2
    assert "cannot parse" in capsys.readouterr().err


def test_main_reads_sys_argv_when_called_without_arguments(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "errors.py").write_text("", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["purity", str(tmp_path / "errors.py")])
    assert main() == 0
