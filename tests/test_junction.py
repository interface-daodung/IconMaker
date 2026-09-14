"""Test module junction: validate đường dẫn + ghép lệnh mklink/attrib."""

import sys

import pytest

from service import junction
from service.junction import (
    build_link_command,
    create_junction,
    validate_junction_paths,
)


def test_validate_returns_absolute_pair(tmp_path):
    target = tmp_path / "real"
    target.mkdir()
    link, resolved_target = validate_junction_paths(
        tmp_path / "virtual", target
    )
    assert link == (tmp_path / "virtual").resolve()
    assert resolved_target == target.resolve()


def test_validate_rejects_blank_inputs():
    with pytest.raises(ValueError):
        validate_junction_paths("  ", "x")
    with pytest.raises(ValueError):
        validate_junction_paths("x", "")


def test_validate_rejects_same_paths(tmp_path):
    target = tmp_path / "real"
    target.mkdir()
    with pytest.raises(ValueError):
        validate_junction_paths(target, target)


def test_validate_rejects_existing_link(tmp_path):
    target = tmp_path / "real"
    target.mkdir()
    link = tmp_path / "virtual"
    link.mkdir()
    with pytest.raises(FileExistsError):
        validate_junction_paths(link, target)


def test_validate_rejects_missing_parent(tmp_path):
    target = tmp_path / "real"
    target.mkdir()
    with pytest.raises(FileNotFoundError):
        validate_junction_paths(tmp_path / "nope" / "deep" / "virtual", target)


def test_validate_rejects_missing_target(tmp_path):
    with pytest.raises(FileNotFoundError):
        validate_junction_paths(tmp_path / "virtual", tmp_path / "ghost")


def test_build_link_command_quotes_via_list():
    cmd = build_link_command(r"C:\OneDrive\App Virtual", r"D:\Data\App")
    assert cmd == [
        "cmd",
        "/c",
        "mklink",
        "/J",
        r"C:\OneDrive\App Virtual",
        r"D:\Data\App",
    ]


def test_create_junction_refuses_non_windows(monkeypatch):
    monkeypatch.setattr(junction.sys, "platform", "linux")
    with pytest.raises(RuntimeError):
        create_junction("a", "b")


@pytest.mark.skipif(sys.platform != "win32", reason="mklink /J là Windows-only")
def test_create_junction_real_roundtrip(tmp_path):
    target = tmp_path / "real"
    target.mkdir()
    (target / "file.txt").write_text("data", encoding="utf-8")
    link = tmp_path / "virtual"

    created = create_junction(link, target, readonly=True)

    assert created == link
    assert link.is_dir()
    assert link.is_junction()
    assert (link / "file.txt").read_text(encoding="utf-8") == "data"
    assert link.resolve() == target.resolve()
    try:
        junction.set_link_readonly(link)
        import os
        import stat

        attrs = os.lstat(link).st_file_attributes
        assert attrs & stat.FILE_ATTRIBUTE_READONLY
    finally:
        junction._run_attrib("-r", str(link), "/l")
        link.rmdir()


@pytest.mark.skipif(sys.platform != "win32", reason="mklink /J là Windows-only")
def test_create_junction_without_readonly_leaves_link_writable(tmp_path):
    target = tmp_path / "real"
    target.mkdir()
    link = tmp_path / "virtual"
    try:
        create_junction(link, target, readonly=False)
        import os
        import stat

        attrs = os.lstat(link).st_file_attributes
        assert not attrs & stat.FILE_ATTRIBUTE_READONLY
    finally:
        link.rmdir()
