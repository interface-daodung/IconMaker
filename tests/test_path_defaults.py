"""Test quy ước đường dẫn: input/ là đầu vào mặc định, output/<tool>/ là đầu ra."""

from pathlib import Path

import pytest
from PIL import Image

from core.file_utils import iter_image_files, newest_file
from core.paths import (
    APP_ICON,
    INPUT_DIR,
    OUTPUT_EXPORT,
    OUTPUT_ICONS,
    OUTPUT_LAUNCHER,
    OUTPUT_RESIZE,
    OUTPUT_ROUNDED,
    OUTPUT_ROOT,
    OUTPUT_SPRITES,
    app_icon_path,
)


def _png(path: Path, color=(200, 100, 50, 255)) -> str:
    img = Image.new("RGBA", (100, 100), color)
    img.save(path, format="PNG")
    img.close()
    return str(path)


def test_paths_constants():
    assert INPUT_DIR == Path("input")
    assert OUTPUT_ROOT == Path("output")
    assert OUTPUT_ROUNDED == Path("output/rounded")
    assert OUTPUT_SPRITES == Path("output/sprites")
    assert OUTPUT_ICONS == Path("output/icons")
    assert OUTPUT_RESIZE == Path("output/resize")
    assert OUTPUT_EXPORT == Path("output/export")
    assert OUTPUT_LAUNCHER == Path("output/launchers")
    assert APP_ICON == Path("assets/icons/IconMaker.ico")


def test_app_icon_resolves_to_repo_file(tmp_path, monkeypatch):
    icon = app_icon_path()
    assert icon.is_absolute()
    assert icon.name == "IconMaker.ico"
    assert icon.is_file()
    monkeypatch.chdir(tmp_path)
    assert app_icon_path() == icon


def test_iter_image_files_empty_and_order(tmp_path):
    assert iter_image_files(tmp_path) == []
    assert iter_image_files(tmp_path / "missing") == []
    _png(tmp_path / "b.png")
    _png(tmp_path / "a.png")
    (tmp_path / "note.txt").write_text("x", encoding="utf-8")
    assert [p.name for p in iter_image_files(tmp_path)] == ["a.png", "b.png"]
    assert [p.name for p in iter_image_files(tmp_path, {".png"})] == ["a.png", "b.png"]
    assert iter_image_files(tmp_path, {".jpg"}) == []


def test_newest_file_picks_latest(tmp_path):
    assert newest_file(tmp_path, ".ico") is None
    assert newest_file(tmp_path / "missing", ".ico") is None
    old = tmp_path / "old.ico"
    new = tmp_path / "new.ico"
    old.write_bytes(b"0")
    new.write_bytes(b"1")
    import os

    os.utime(old, (1_000_000, 1_000_000))
    os.utime(new, (2_000_000, 2_000_000))
    assert newest_file(tmp_path, ".ico").name == "new.ico"
    assert newest_file(tmp_path, ".ICO").name == "new.ico"


def test_bootstrap_makes_main_importable_from_anywhere(tmp_path, monkeypatch):
    """Shortcut `pythonw src/main.py` chạy từ bất kỳ cwd nào vẫn import được gui."""
    import main

    monkeypatch.chdir(tmp_path)
    root = main._bootstrap()
    assert root == Path(main.__file__).resolve().parents[1]
    assert Path.cwd() == root
    from gui.main_window import MainWindow  # noqa: F401
