"""Test tool Xuất ảnh hợp nhất: 1 ảnh vào → jpg/png/webp/ico ra output/export/."""

from pathlib import Path

import pytest
from PIL import Image

from core.exceptions import BadImageError, MissingFileError
from service.export import export_file, normalize_export_fmt


def _make(path: Path, fmt: str = "PNG", size=(120, 80), mode="RGBA"):
    img = Image.new(mode, size, (200, 100, 50, 255) if mode == "RGBA" else (200, 100, 50))
    img.save(path, format=fmt)
    img.close()
    return str(path)


def test_normalize_export_fmt_accepts_all_four_and_jpeg_alias():
    assert normalize_export_fmt(".jpg") == ".jpg"
    assert normalize_export_fmt(".jpeg") == ".jpg"
    assert normalize_export_fmt("PNG") == ".png"
    assert normalize_export_fmt(".webp") == ".webp"
    assert normalize_export_fmt(".ico") == ".ico"
    with pytest.raises(ValueError):
        normalize_export_fmt(".gif")


def test_export_png_to_jpg(tmp_path):
    src = _make(tmp_path / "logo.png")
    out = export_file(src, tmp_path / "out", fmt=".jpg", quality=90)
    assert out == str(tmp_path / "out" / "logo.jpg")
    with Image.open(out) as saved:
        assert saved.format == "JPEG"
        assert saved.size == (120, 80)


def test_export_same_extension_allowed_reencode(tmp_path):
    src = _make(tmp_path / "logo.png")
    out = export_file(src, tmp_path / "out", fmt=".png")
    assert Path(out).is_file()
    with Image.open(out) as saved:
        assert saved.format == "PNG"


def test_export_jpg_input_to_ico(tmp_path):
    src = _make(tmp_path / "photo.jpg", "JPEG", mode="RGB")
    out = export_file(src, tmp_path / "out", fmt=".ico", sizes=[16, 32])
    assert Path(out).is_file()
    data = Path(out).read_bytes()
    assert data[:4] == b"\x00\x00\x01\x00"


def test_export_webp_input_to_png(tmp_path):
    src = _make(tmp_path / "pic.webp", "WEBP")
    out = export_file(src, tmp_path / "out", fmt=".png")
    with Image.open(out) as saved:
        assert saved.format == "PNG"


def test_export_missing_source_raises(tmp_path):
    with pytest.raises(MissingFileError):
        export_file(tmp_path / "nope.png", fmt=".jpg")


def test_export_bad_extension_raises(tmp_path):
    txt = tmp_path / "note.txt"
    txt.write_text("hello", encoding="utf-8")
    with pytest.raises(BadImageError):
        export_file(txt, fmt=".jpg")


def test_export_default_dir_is_output_export(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    src = _make(tmp_path / "t.png")
    out = export_file(src)
    assert out == str(Path("output") / "export" / "t.ico")
    assert Path(out).is_file()
