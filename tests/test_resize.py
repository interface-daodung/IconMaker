"""Test resize ảnh vuông tại service.resize (pixel thật, không mở GUI)."""

from pathlib import Path

import pytest
from PIL import Image

from core.exceptions import BadImageError, MissingFileError
from service import resize
from service.resize import (
    DEFAULT_FORMAT,
    RESIZE_NAMES,
    RESIZE_SIZES,
    resize_image_file,
    resize_to_square,
)


def _make(path: Path, size=(200, 100), mode="RGBA", color=(200, 100, 50, 255)):
    img = Image.new(mode, size, color)
    img.save(path, format="PNG")
    img.close()
    return str(path)


def test_resize_to_square_returns_correct_size():
    img = Image.new("RGBA", (200, 100), (1, 2, 3, 255))
    out = resize_to_square(img, 48)
    assert out.size == (48, 48)
    assert out.mode == "RGBA"
    img.close()
    out.close()


def test_resize_to_square_converts_rgb():
    img = Image.new("RGB", (60, 60), (10, 20, 30))
    out = resize_to_square(img, 16)
    assert out.size == (16, 16)
    assert out.mode == "RGBA"
    img.close()
    out.close()


def test_resize_image_file_creates_three_files(tmp_path):
    src = _make(tmp_path / "src.png", (500, 300))
    out_dir = tmp_path / "out"
    results = resize_image_file(src, out_dir)
    assert len(results) == 3
    for p in results:
        assert Path(p).is_file()
    names = [Path(p).name for p in results]
    assert names == ["icon16.png", "icon48.png", "icon128.png"]


def test_resize_image_file_sizes(tmp_path):
    src = _make(tmp_path / "big.png", (1000, 1000))
    results = resize_image_file(src, tmp_path / "out")
    for p in results:
        with Image.open(p) as img:
            assert img.size == (16, 16) if "icon16" in p else True
    with Image.open(results[0]) as img:
        assert img.size == (16, 16)
    with Image.open(results[1]) as img:
        assert img.size == (48, 48)
    with Image.open(results[2]) as img:
        assert img.size == (128, 128)


def test_resize_image_file_custom_ext(tmp_path):
    src = _make(tmp_path / "src.png")
    results = resize_image_file(src, tmp_path / "out", ext=".jpg")
    for p in results:
        assert p.endswith(".jpg")
        assert Path(p).is_file()


def test_resize_image_file_missing_raises(tmp_path):
    with pytest.raises(MissingFileError):
        resize_image_file(tmp_path / "nope.png")


def test_resize_image_file_wrong_ext_raises(tmp_path):
    txt = tmp_path / "note.txt"
    txt.write_text("hello", encoding="utf-8")
    with pytest.raises(BadImageError):
        resize_image_file(txt)


def test_resize_image_file_jpeg(tmp_path):
    path = tmp_path / "photo.jpg"
    img = Image.new("RGB", (400, 400), (50, 100, 150))
    img.save(path, format="JPEG")
    img.close()
    results = resize_image_file(path, tmp_path / "out")
    assert len(results) == 3
    for p in results:
        assert Path(p).is_file()


def test_resize_image_file_webp(tmp_path):
    path = tmp_path / "pic.webp"
    img = Image.new("RGBA", (300, 300), (10, 20, 30, 255))
    img.save(path, format="WEBP")
    img.close()
    results = resize_image_file(path, tmp_path / "out")
    assert len(results) == 3
    for p in results:
        assert Path(p).is_file()


def test_resize_names_and_sizes():
    assert RESIZE_SIZES == [16, 48, 128]
    assert RESIZE_NAMES == ["icon16", "icon48", "icon128"]
    assert len(RESIZE_SIZES) == len(RESIZE_NAMES)


def test_resize_default_out_dir_is_output_resize(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    src = _make(tmp_path / "cli.png")
    results = resize_image_file(src)
    assert Path(results[0]) == Path("output") / "resize" / "icon16.png"
    assert (tmp_path / "output" / "resize" / "icon128.png").is_file()
