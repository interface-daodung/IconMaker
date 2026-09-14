"""Test module foldericon: logic copy icon vào thư viện + sinh desktop.ini."""

import sys

import pytest

from core import foldericon
from core.foldericon import (
    install_icon,
    make_ini_content,
    sanitize_icon_name,
    set_folder_icon,
)


def _write_ico(path, payload=b"AAABA" + b"\x00" * 10):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return path


def test_install_icon_copies_into_store(tmp_path):
    src = _write_ico(tmp_path / "a" / "logo.ico")
    store = tmp_path / "store"
    dest = install_icon(src, store)
    assert dest == store / "logo.ico"
    assert dest.read_bytes() == src.read_bytes()


def test_install_icon_dedup_identical_content(tmp_path):
    src = _write_ico(tmp_path / "a" / "logo.ico")
    store = tmp_path / "store"
    first = install_icon(src, store)
    second = install_icon(src, store)
    assert first == second
    assert list(store.iterdir()) == [first]


def test_install_icon_same_name_different_content_gets_suffix(tmp_path):
    store = tmp_path / "store"
    src1 = _write_ico(tmp_path / "a" / "logo.ico", b"AAAA" + b"\x01" * 8)
    src2 = _write_ico(tmp_path / "b" / "logo.ico", b"AAAA" + b"\x02" * 8)
    first = install_icon(src1, store)
    second = install_icon(src2, store)
    assert first.name == "logo.ico"
    assert second.name == "logo (2).ico"
    assert second.read_bytes() == src2.read_bytes()


def test_install_icon_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        install_icon(tmp_path / "ghost.ico", tmp_path / "store")


def test_install_icon_non_ico_raises(tmp_path):
    png = tmp_path / "pic.png"
    png.write_bytes(b"\x89PNG")
    with pytest.raises(ValueError):
        install_icon(png, tmp_path / "store")


def test_make_ini_content_absolute_with_index_zero(tmp_path):
    icon = (tmp_path / "Icon" / "my.ico").resolve()
    content = make_ini_content(icon)
    assert content == f"[.ShellClassInfo]\nIconResource={icon},0\n"


def test_make_ini_content_resolves_relative_path():
    content = make_ini_content("sub/../../my.ico")
    assert content.startswith("[.ShellClassInfo]\nIconResource=")
    assert content.rstrip().endswith(",0")
    assert "/../" not in content and "\\..\\" not in content


def test_set_folder_icon_missing_folder_raises(tmp_path):
    icon = _write_ico(tmp_path / "x.ico")
    with pytest.raises(FileNotFoundError):
        set_folder_icon(tmp_path / "nope", icon)


def test_set_folder_icon_missing_icon_raises(tmp_path):
    folder = tmp_path / "target"
    folder.mkdir()
    with pytest.raises(FileNotFoundError):
        set_folder_icon(folder, tmp_path / "ghost.ico")


@pytest.mark.skipif(sys.platform != "win32", reason="desktop.ini + attrib là Windows-only")
def test_set_folder_icon_writes_hidden_ini_on_windows(tmp_path):
    import ctypes

    folder = tmp_path / "target"
    folder.mkdir()
    icon = _write_ico(tmp_path / "store" / "x.ico")

    ini = set_folder_icon(folder, icon)
    ini_path = folder / "desktop.ini"
    assert ini == str(ini_path)
    assert ini_path.read_text(encoding="utf-8") == make_ini_content(icon)

    FILE_ATTRIBUTE_HIDDEN = 0x2
    FILE_ATTRIBUTE_SYSTEM = 0x4
    FILE_ATTRIBUTE_READONLY = 0x1
    attrs = ctypes.windll.kernel32.GetFileAttributesW(str(ini_path))
    assert attrs & FILE_ATTRIBUTE_HIDDEN
    assert attrs & FILE_ATTRIBUTE_SYSTEM
    folder_attrs = ctypes.windll.kernel32.GetFileAttributesW(str(folder))
    assert folder_attrs & FILE_ATTRIBUTE_READONLY


@pytest.mark.skipif(sys.platform != "win32", reason="desktop.ini + attrib là Windows-only")
def test_set_folder_icon_overwrites_existing_ini(tmp_path):
    folder = tmp_path / "target"
    folder.mkdir()
    (folder / "desktop.ini").write_text("old content", encoding="utf-8")
    icon = _write_ico(tmp_path / "y.ico")
    set_folder_icon(folder, icon)
    text = (folder / "desktop.ini").read_text(encoding="utf-8")
    assert "IconResource" in text and "old content" not in text


def test_sanitize_icon_name_adds_ico_and_strips():
    assert sanitize_icon_name("  MyApp ") == "MyApp.ico"
    assert sanitize_icon_name("MyApp.ico") == "MyApp.ico"
    assert sanitize_icon_name("MyApp.ICO") == "MyApp.ico"
    assert sanitize_icon_name("trail.") == "trail.ico"


@pytest.mark.parametrize("bad", ["", "   ", ".", "..", "a/b", "a\\b", "x:icon", 'q"w', "a*b", "a?b", "a|b", "a<b>", "pic.png"])
def test_sanitize_icon_name_rejects_bad_names(bad):
    with pytest.raises(ValueError):
        sanitize_icon_name(bad)


def test_install_icon_with_new_name_renames(tmp_path):
    src = _write_ico(tmp_path / "a" / "logo.ico")
    store = tmp_path / "store"
    dest = install_icon(src, store, "MyApp")
    assert dest == store / "MyApp.ico"
    assert dest.read_bytes() == src.read_bytes()


def test_install_icon_with_new_name_blank_keeps_original(tmp_path):
    src = _write_ico(tmp_path / "a" / "logo.ico")
    store = tmp_path / "store"
    assert install_icon(src, store, "   ").name == "logo.ico"


def test_install_icon_with_new_name_dedups_content(tmp_path):
    src = _write_ico(tmp_path / "a" / "logo.ico")
    store = tmp_path / "store"
    first = install_icon(src, store, "MyApp")
    second = install_icon(src, store, "MyApp")
    assert first == second == store / "MyApp.ico"
    assert list(store.iterdir()) == [first]


def test_install_icon_with_new_name_clash_gets_suffix(tmp_path):
    store = tmp_path / "store"
    src1 = _write_ico(tmp_path / "a" / "one.ico", b"AAAA" + b"\x01" * 8)
    src2 = _write_ico(tmp_path / "b" / "two.ico", b"AAAA" + b"\x02" * 8)
    assert install_icon(src1, store, "Same").name == "Same.ico"
    assert install_icon(src2, store, "Same").name == "Same (2).ico"
