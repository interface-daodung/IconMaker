"""Test logic thuần của GUI (không mở cửa sổ Tk)."""

from pathlib import Path

import pytest

from iconmaker import converter, foldericon
from iconmaker.gui import (
    apply_folder_icon,
    parse_sizes,
    resolve_output_path,
    run_conversion,
)


def test_parse_sizes_all_returns_default_sizes():
    assert parse_sizes("Tất cả") == converter.get_default_sizes()


def test_parse_sizes_single_value():
    assert parse_sizes("48") == [48]


def test_parse_sizes_invalid_raises():
    with pytest.raises(ValueError):
        parse_sizes("abc")


def test_resolve_output_path_next_to_source_when_no_dir():
    out = resolve_output_path(r"C:\pics\logo.png")
    assert out == str(Path(r"C:\pics") / "logo.ico")


def test_resolve_output_path_uses_custom_dir():
    out = resolve_output_path("logo.png", "out_dir")
    assert out == str(Path("out_dir") / "logo.ico")


def test_run_conversion_creates_file(tmp_path, png_rgb):
    out = run_conversion(png_rgb, tmp_path / "dest", [16, 32])
    assert Path(out).is_file()
    assert Path(out).name == "rgb.ico"


def test_apply_folder_icon_chains_install_then_set(tmp_path, monkeypatch):
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
    result = apply_folder_icon("raw.ico", "some_folder")
    assert result == "ini-path"
    assert calls == [
        ("install", "raw.ico"),
        ("set", "some_folder", tmp_path / "store" / "x.ico"),
    ]