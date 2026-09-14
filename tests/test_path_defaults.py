"""Test quy ước đường dẫn: input/ là đầu vào mặc định, output/<tool>/ là đầu ra."""

from pathlib import Path

from PIL import Image

from core.file_utils import first_image, newest_file
from service import convert, foldericon, icons, sprites
from core.paths import (
    APP_ICON,
    INPUT_DIR,
    OUTPUT_CONVERT,
    OUTPUT_ICONS,
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
    assert OUTPUT_CONVERT == Path("output/convert")
    assert OUTPUT_ROUNDED == Path("output/rounded")
    assert OUTPUT_SPRITES == Path("output/sprites")
    assert OUTPUT_ICONS == Path("output/icons")
    assert APP_ICON == Path("assets/icons/IconMaker.ico")


def test_app_icon_resolves_to_repo_file(tmp_path, monkeypatch):
    icon = app_icon_path()
    assert icon.is_absolute()
    assert icon.name == "IconMaker.ico"
    assert icon.is_file()
    monkeypatch.chdir(tmp_path)
    assert app_icon_path() == icon


def test_first_image_empty_and_order(tmp_path):
    assert first_image(tmp_path) is None
    assert first_image(tmp_path / "missing") is None
    _png(tmp_path / "b.png")
    _png(tmp_path / "a.png")
    (tmp_path / "note.txt").write_text("x", encoding="utf-8")
    assert first_image(tmp_path).name == "a.png"
    assert first_image(tmp_path, {".png"}).name == "a.png"
    assert first_image(tmp_path, {".jpg"}) is None


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


def test_convert_cli_defaults(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert convert.main([]) == 1  # input/ trống
    (tmp_path / "input").mkdir()
    _png(tmp_path / "input" / "a.png")
    assert convert.main([]) == 0
    assert (tmp_path / "output" / "convert" / "a.ico").is_file()
    capsys.readouterr()


def test_sprites_cli_explicit_dirs(tmp_path, capsys):
    src_dir = tmp_path / "in"
    out_dir = tmp_path / "out"
    src_dir.mkdir()
    img = Image.new("RGB", (200, 200), (0x12, 0x13, 0x15))
    for x in range(20, 91):
        for y in range(20, 91):
            img.putpixel((x, y), (255, 255, 255))
    img.save(src_dir / "s.png", format="PNG")
    img.close()
    assert sprites.main([str(src_dir), str(out_dir)]) == 0
    assert list(out_dir.rglob("*.png"))
    capsys.readouterr()


def test_icons_cli_defaults(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert icons.main([]) == 1  # output/sprites trống
    (tmp_path / "output" / "sprites").mkdir(parents=True)
    _png(tmp_path / "output" / "sprites" / "x.png")
    assert icons.main([]) == 0
    assert (tmp_path / "output" / "icons" / "x.ico").is_file()
    capsys.readouterr()


def test_foldericon_cli_requires_folder_or_icons(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert foldericon.main([]) == 2
    target = tmp_path / "target"
    target.mkdir()
    assert foldericon.main([str(target)]) == 1  # chưa có ICO trong output/icons
    capsys.readouterr()
