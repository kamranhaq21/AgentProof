"""``io.read_limited``: size limit before reading, root containment, strict UTF-8 (AD-14, AD-19)."""

from pathlib import Path

import pytest

from agentproof import constants, io
from agentproof.errors import PathError
from agentproof.io import read_limited


def _only_message(error: pytest.ExceptionInfo[PathError]) -> str:
    assert len(error.value.violations) == 1
    return error.value.violations[0].message


def test_reads_a_file_under_the_limit(tmp_path: Path) -> None:
    target = tmp_path / "suite.yaml"
    target.write_text("héllo\n", encoding="utf-8", newline="\n")
    assert read_limited(target, 100, base_dir=tmp_path) == "héllo\n"


def test_a_file_exactly_at_the_limit_is_read(tmp_path: Path) -> None:
    target = tmp_path / "suite.yaml"
    target.write_bytes(b"a" * 64)
    assert read_limited(target, 64, base_dir=tmp_path) == "a" * 64


def test_a_file_one_byte_over_the_limit_is_rejected_naming_the_limit(tmp_path: Path) -> None:
    target = tmp_path / "suite.yaml"
    target.write_bytes(b"a" * 65)
    with pytest.raises(PathError) as error:
        read_limited(target, 64, base_dir=tmp_path)
    message = _only_message(error)
    assert "65 bytes" in message
    assert "limit of 64 bytes" in message
    assert error.value.violations[0].source == str(target)


def test_the_size_is_checked_before_the_content_is_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "suite.yaml"
    target.write_bytes(b"a" * 65)

    def forbidden(self: Path, *args: object, **kwargs: object) -> object:
        raise AssertionError("the file was opened although it is over the limit")

    monkeypatch.setattr(Path, "open", forbidden)
    monkeypatch.setattr(Path, "read_bytes", forbidden)
    monkeypatch.setattr(Path, "read_text", forbidden)
    with pytest.raises(PathError):
        read_limited(target, 64, base_dir=tmp_path)


def test_a_file_that_outgrows_its_stat_size_is_still_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # stat reports a size at the limit, but the content is over it: the capped read
    # (max_bytes + 1) is the second guard and must refuse it.
    target = tmp_path / "suite.yaml"
    target.write_bytes(b"a" * 200)
    real_stat = Path.stat

    class FakeStat:
        def __init__(self, inner: object) -> None:
            self._inner = inner

        @property
        def st_size(self) -> int:
            return 64

        def __getattr__(self, name: str) -> object:
            return getattr(self._inner, name)

    def fake_stat(self: Path, *args: object, **kwargs: object) -> object:
        result = real_stat(self, *args, **kwargs)  # type: ignore[arg-type]
        return FakeStat(result) if self.name == "suite.yaml" else result

    monkeypatch.setattr(Path, "stat", fake_stat)
    with pytest.raises(PathError) as error:
        read_limited(target, 64, base_dir=tmp_path)
    assert _only_message(error) == "the file is over the limit of 64 bytes"


def test_the_suite_limit_is_the_constant_not_a_number(tmp_path: Path) -> None:
    target = tmp_path / "suite.yaml"
    target.write_bytes(b"a" * (constants.MAX_SUITE_BYTES + 1))
    with pytest.raises(PathError) as error:
        read_limited(target, constants.MAX_SUITE_BYTES, base_dir=tmp_path)
    assert f"limit of {constants.MAX_SUITE_BYTES} bytes" in _only_message(error)
    target.write_bytes(b"a" * constants.MAX_SUITE_BYTES)
    assert len(read_limited(target, constants.MAX_SUITE_BYTES, base_dir=tmp_path)) == (
        constants.MAX_SUITE_BYTES
    )


def test_invalid_utf8_is_a_path_error_naming_the_encoding(tmp_path: Path) -> None:
    target = tmp_path / "suite.yaml"
    target.write_bytes(b"ok\xff\xfe")
    with pytest.raises(PathError) as error:
        read_limited(target, 100, base_dir=tmp_path)
    message = _only_message(error)
    assert "not valid UTF-8" in message
    assert "offset 2" in message
    assert "\\xff" not in message


def test_a_utf8_bom_is_kept(tmp_path: Path) -> None:
    target = tmp_path / "suite.yaml"
    target.write_bytes(b"\xef\xbb\xbfa: 1\n")
    assert read_limited(target, 100, base_dir=tmp_path) == "﻿a: 1\n"


def test_a_missing_file_is_a_path_error(tmp_path: Path) -> None:
    with pytest.raises(PathError) as error:
        read_limited(tmp_path / "absent.yaml", 100, base_dir=tmp_path)
    assert "does not exist" in _only_message(error)


def test_a_directory_is_a_path_error(tmp_path: Path) -> None:
    with pytest.raises(PathError) as error:
        read_limited(tmp_path, 100, base_dir=tmp_path)
    assert "not a regular file" in _only_message(error)


def test_dot_dot_escape_is_rejected_naming_the_escape(tmp_path: Path) -> None:
    inside = tmp_path / "suite"
    inside.mkdir()
    (tmp_path / "secret.txt").write_text("outside", encoding="utf-8")
    with pytest.raises(PathError) as error:
        read_limited(inside / ".." / "secret.txt", 100, base_dir=inside)
    assert "outside the allowed directory" in _only_message(error)


def test_a_path_in_a_sibling_directory_with_a_common_prefix_is_outside(tmp_path: Path) -> None:
    base = tmp_path / "suite"
    base.mkdir()
    sibling = tmp_path / "suite-evil"
    sibling.mkdir()
    (sibling / "x.yaml").write_text("x", encoding="utf-8")
    with pytest.raises(PathError):
        read_limited(sibling / "x.yaml", 100, base_dir=base)


def _symlink(link: Path, target: Path) -> None:
    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("this environment cannot create symlinks")


def test_a_symlink_resolving_outside_base_dir_is_rejected(tmp_path: Path) -> None:
    inside = tmp_path / "suite"
    inside.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("secret", encoding="utf-8")
    link = inside / "link.yaml"
    _symlink(link, outside)
    with pytest.raises(PathError) as error:
        read_limited(link, 100, base_dir=inside)
    assert "outside the allowed directory" in _only_message(error)


def test_a_symlink_staying_inside_base_dir_is_read(tmp_path: Path) -> None:
    real = tmp_path / "real.yaml"
    real.write_text("inside", encoding="utf-8")
    link = tmp_path / "link.yaml"
    _symlink(link, real)
    assert read_limited(link, 100, base_dir=tmp_path) == "inside"


def test_the_package_exports_read_limited() -> None:
    assert io.__all__ == ["read_limited"]
