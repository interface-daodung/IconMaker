"""Test bo góc ảnh ở service.image_ops (pixel thật, không mở GUI)."""

from pathlib import Path

import pytest
from PIL import Image

from core.exceptions import BadImageError, BadSizeError, MissingFileError
from service import image_ops


def _solid(path: Path, size=(100, 60), mode="RGBA") -> str:
    img = Image.new(mode, size, (200, 100, 50, 255))
    img.save(path, format="PNG")
    img.close()
    return str(path)


def test_rounded_corners_transparent_outside_keeps_size():
    img = Image.new("RGBA", (100, 60), (200, 100, 50, 255))
    out = image_ops.rounded_corners(img, 20)
    assert out.size == (100, 60)
    assert out.getpixel((0, 0))[3] == 0
    assert out.getpixel((50, 30))[3] == 255
    img.close()
    out.close()


def test_rounded_corners_radius_zero_returns_copy():
    img = Image.new("RGB", (40, 40), (1, 2, 3))
    out = image_ops.rounded_corners(img, 0)
    assert out.size == img.size and out is not img
    assert out.getpixel((0, 0))[:3] == (1, 2, 3)
    img.close()
    out.close()


def test_rounded_corners_keeps_original_alpha_inside():
    img = Image.new("RGBA", (80, 80), (10, 20, 30, 128))
    out = image_ops.rounded_corners(img, 16)
    assert out.getpixel((40, 40))[3] == 128
    img.close()
    out.close()


def test_clamp_radius_caps_at_half_min_side():
    assert image_ops.clamp_radius(999, 100, 60) == 30
    assert image_ops.clamp_radius(10, 100, 60) == 10


def test_clamp_radius_negative_raises():
    with pytest.raises(BadSizeError):
        image_ops.clamp_radius(-1, 100, 100)


def test_round_image_file_writes_png(tmp_path):
    src = _solid(tmp_path / "a.png")
    dest = image_ops.round_image_file(src, radius=15)
    assert dest == str(tmp_path / "a-rounded.png")
    with Image.open(dest) as saved:
        assert saved.format == "PNG"
        assert saved.size == (100, 60)
        assert saved.getpixel((0, 0))[3] == 0


def test_round_image_file_explicit_dest_and_out_dir(tmp_path):
    src = _solid(tmp_path / "b.png")
    out = image_ops.round_image_file(src, tmp_path / "sub" / "c.png", radius=10)
    assert Path(out).is_file()
    out2 = image_ops.round_image_file(src, out_dir=tmp_path / "d2", radius=10)
    assert out2 == str(tmp_path / "d2" / "b-rounded.png")


def test_round_image_file_missing_raises(tmp_path):
    with pytest.raises(MissingFileError):
        image_ops.round_image_file(tmp_path / "nope.png")


def test_round_image_file_wrong_extension_raises(tmp_path):
    txt = tmp_path / "note.txt"
    txt.write_text("hello", encoding="utf-8")
    with pytest.raises(BadImageError):
        image_ops.round_image_file(txt)


def test_round_image_file_broken_png_raises(tmp_path, broken_file):
    with pytest.raises(BadImageError):
        image_ops.round_image_file(broken_file)
