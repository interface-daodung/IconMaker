"""Test tìm hàng loạt thư mục `*<tên>` + đặt icon nhiều thư mục."""

import os
from pathlib import Path

import pytest

from service import folder_search
from service.folder_search import (
    find_folders_by_name,
    is_batch_input,
    parse_batch_name,
)
from tools.foldericon_tool import controller


def _mkdir(*parts):
    path = parts[0]
    for part in parts[1:]:
        path = path / part
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_is_batch_input_detects_star_prefix():
    assert is_batch_input("*MyApp")
    assert is_batch_input("  *MyApp  ")
    assert not is_batch_input(r"C:\Users\inter\MyApp")
    assert not is_batch_input("")


def test_parse_batch_name_strips_star_and_spaces():
    assert parse_batch_name("*MyApp") == "MyApp"
    assert parse_batch_name("  *  MyApp  ") == "MyApp"


@pytest.mark.parametrize("bad", ["*", "  *  ", "*. ..", "*a/b", "*a\\b", "*a*b", "*"])
def test_parse_batch_name_rejects_bad(bad):
    with pytest.raises(ValueError):
        parse_batch_name(bad)


def test_find_exact_name_case_insensitive(tmp_path):
    _mkdir(tmp_path, "home", "MyApp")
    _mkdir(tmp_path, "home", "docs", "myapp")
    _mkdir(tmp_path, "home", "docs", "myapp-backup")
    home = tmp_path / "home"
    found = find_folders_by_name("MyApp", [home], home_root=home, skip_dirs=[])
    assert sorted(found) == sorted(
        [str(home / "MyApp"), str(home / "docs" / "myapp")]
    )


def test_find_skips_dot_branch_under_home_but_allows_outside(tmp_path):
    home = _mkdir(tmp_path, "home")
    _mkdir(home, ".cache", "MyApp")
    _mkdir(home, "work", "MyApp")
    other = _mkdir(tmp_path, "other")
    _mkdir(other, ".hidden", "MyApp")
    found = find_folders_by_name("MyApp", [home, other], home_root=home, skip_dirs=[])
    assert str(home / "work" / "MyApp") in found
    assert str(home / ".cache" / "MyApp") not in found
    assert str(other / ".hidden" / "MyApp") in found


def test_find_skips_temp_and_appdata_subtrees(tmp_path, monkeypatch):
    home = _mkdir(tmp_path, "home")
    temp = _mkdir(tmp_path, "tempfiles")
    data = _mkdir(tmp_path, "appdata")
    _mkdir(temp, "MyApp")
    _mkdir(data, "MyApp")
    _mkdir(home, "MyApp")
    monkeypatch.setenv("TEMP", str(temp))
    monkeypatch.setenv("TMP", str(temp))
    monkeypatch.setenv("APPDATA", str(data))
    monkeypatch.setenv("LOCALAPPDATA", str(data))
    found = find_folders_by_name("MyApp", [home, temp, data], home_root=home)
    assert found == [str(home / "MyApp")]


def test_find_ignores_files_and_missing_roots(tmp_path):
    home = _mkdir(tmp_path, "home")
    (home / "MyApp.txt").write_text("x", encoding="utf-8")
    found = find_folders_by_name(
        "MyApp", [home, tmp_path / "ghost"], home_root=home, skip_dirs=[]
    )
    assert found == []


def test_controller_run_search_scans_home_plus_extras(tmp_path, monkeypatch):
    seen: dict = {}

    def fake_find(name, roots):
        seen["name"] = name
        seen["roots"] = [str(r) for r in roots]
        return ["hit"]

    monkeypatch.setattr(controller.folder_search, "find_folders_by_name", fake_find)
    monkeypatch.setattr(
        controller.folder_search, "default_root", lambda: tmp_path / "home"
    )
    assert controller.run_search("MyApp", [str(tmp_path / "D")]) == ["hit"]
    assert seen["name"] == "MyApp"
    assert seen["roots"][0] == str(tmp_path / "home")
    assert str(tmp_path / "D") in seen["roots"]


def test_controller_run_apply_many_installs_once_and_collects_errors(
    tmp_path, monkeypatch
):
    from service import foldericon

    installs: list = []
    monkeypatch.setattr(
        foldericon,
        "install_icon",
        lambda icon, store=None, new_name=None: installs.append(
            (icon, new_name)
        )
        or tmp_path / "store" / "x.ico",
    )
    calls: list = []

    def fake_set(folder, installed):
        calls.append(str(folder))
        if str(folder).endswith("bad"):
            raise OSError("locked")

    monkeypatch.setattr(foldericon, "set_folder_icon", fake_set)
    ok, failed = controller.run_apply_many(
        "a.ico", [tmp_path / "good", tmp_path / "bad"], "MyApp"
    )
    assert installs == [("a.ico", "MyApp.ico")]
    assert ok == [str(tmp_path / "good")]
    assert list(failed) == [str(tmp_path / "bad")]
    assert "locked" in failed[str(tmp_path / "bad")]
    assert calls == [str(tmp_path / "good"), str(tmp_path / "bad")]


@pytest.mark.skipif(os.name != "nt", reason="ổ đĩa Windows-only")
def test_list_extra_drives_excludes_home_drive(monkeypatch):
    monkeypatch.setattr(folder_search, "list_drives", lambda: ["C:\\", "D:\\"])
    assert folder_search.list_extra_drives(home=Path("C:\\Users\\inter")) == ["D:\\"]
