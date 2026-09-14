"""Test logic các tool (controller) + theme + registry, không mở cửa sổ."""

from pathlib import Path

import pytest

from core import convert, foldericon
from core.file_utils import resolve_output_path
from gui.base_tool import ToolTab
from gui.theme import next_theme
from tools import registry
from tools.convert_tool import parse_sizes, run_conversion
from tools.foldericon_tool import parse_new_name, run_apply
from tools.rounded_tool import parse_radius, run_round


def test_parse_sizes_all_returns_default_sizes():
    assert parse_sizes("Tất cả") == convert.get_default_sizes()


def test_parse_sizes_single_value():
    assert parse_sizes("48") == [48]


def test_parse_sizes_invalid_raises():
    with pytest.raises(ValueError):
        parse_sizes("abc")


def test_resolve_output_path_next_to_source_when_no_dir():
    out = resolve_output_path(r"C:\pics\logo.png")
    assert out == str(Path(r"C:\pics") / "logo.ico")


def test_resolve_output_path_custom_ext_and_dir():
    out = resolve_output_path("logo.png", "out_dir", ".png")
    assert out == str(Path("out_dir") / "logo.png")


def test_run_conversion_creates_file(tmp_path, png_rgb):
    out = run_conversion(png_rgb, tmp_path / "dest", [16, 32])
    assert Path(out).is_file()
    assert Path(out).name == "rgb.ico"


def test_run_apply_chains_install_then_set(tmp_path, monkeypatch):
    calls: list[tuple] = []
    monkeypatch.setattr(
        foldericon,
        "install_icon",
        lambda icon: calls.append(("install", icon)) or tmp_path / "store" / "x.ico",
    )
    monkeypatch.setattr(
        foldericon,
        "set_folder_icon",
        lambda folder, installed: calls.append(("set", folder, installed)) or "ini-path",
    )
    assert run_apply("raw.ico", "some_folder") == "ini-path"
    assert calls == [
        ("install", "raw.ico"),
        ("set", "some_folder", tmp_path / "store" / "x.ico"),
    ]


def test_parse_new_name_blank_means_keep_original():
    assert parse_new_name(None) is None
    assert parse_new_name("") is None
    assert parse_new_name("   ") is None
    assert parse_new_name("MyApp") == "MyApp.ico"


def test_parse_new_name_invalid_raises():
    with pytest.raises(ValueError):
        parse_new_name("a/b")


def test_run_apply_forwards_new_name(tmp_path, monkeypatch):
    seen: dict = {}
    monkeypatch.setattr(
        foldericon,
        "install_icon",
        lambda icon, store=None, new_name=None: seen.update(
            icon=icon, store=store, new_name=new_name
        )
        or tmp_path / "store" / "MyApp.ico",
    )
    monkeypatch.setattr(
        foldericon, "set_folder_icon", lambda folder, installed: "ini-path"
    )
    assert run_apply("raw.ico", "some_folder", "MyApp") == "ini-path"
    assert seen == {"icon": "raw.ico", "store": None, "new_name": "MyApp.ico"}


def test_parse_radius_ok_and_clamped():
    assert parse_radius("20", 100, 60) == 20
    assert parse_radius("999", 100, 60) == 30


def test_parse_radius_invalid_raises():
    with pytest.raises(ValueError):
        parse_radius("abc", 100, 100)
    with pytest.raises(ValueError):
        parse_radius("-5", 100, 100)


def test_run_round_writes_png(tmp_path, png_rgba):
    out = run_round(png_rgba, radius=25)
    assert Path(out).is_file()
    assert Path(out).suffix == ".png"


def test_next_theme_toggles_dark_light():
    assert next_theme("Dark") == "Light"
    assert next_theme("Light") == "Dark"


def test_registry_lists_all_tool_tabs():
    specs = registry.get_tools()
    assert [s.title for s in specs] == [
        "PNG → ICO",
        "Bo góc",
        "Tách sprite",
        "Sprite → ICO",
        "Icon thư mục",
    ]
    assert all(issubclass(s.tab_class, ToolTab) for s in specs)
