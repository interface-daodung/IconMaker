"""Test đổi định dạng ảnh: nén trong bộ nhớ + chuẩn hoá quality (không mở GUI)."""

from pathlib import Path

import pytest
from PIL import Image

from service.format_convert import (
    DEFAULT_QUALITY,
    clamp_quality,
    compress_bytes,
    compressed_preview,
    normalize_ext,
)


def _make(path: Path, fmt: str = "PNG", size=(120, 80), mode="RGBA", color=(200, 100, 50, 255)):
    img = Image.new(mode, size, color)
    img.save(path, format=fmt)
    img.close()
    return str(path)


def test_normalize_ext_maps_jpeg_to_jpg_and_dots():
    assert normalize_ext(".jpeg") == ".jpg"
    assert normalize_ext(".PNG") == ".png"
    assert normalize_ext("webp") == ".webp"
    with pytest.raises(ValueError):
        normalize_ext(".gif")


def test_clamp_quality_bounds():
    assert clamp_quality(100) == 100
    assert clamp_quality(1) == 1
    assert DEFAULT_QUALITY == 100
    with pytest.raises(ValueError):
        clamp_quality(0)
    with pytest.raises(ValueError):
        clamp_quality(101)
    with pytest.raises(ValueError):
        clamp_quality("abc")


def test_compress_bytes_returns_nonempty_for_all_formats(tmp_path):
    src = _make(tmp_path / "a.png")
    with Image.open(src) as img:
        png = compress_bytes(img, ".png")
        jpg = compress_bytes(img, ".jpg", 90)
        webp = compress_bytes(img, ".webp", 90)
    assert png and jpg and webp


def test_compress_bytes_jpeg_is_rgb_lossy(tmp_path):
    src = _make(tmp_path / "logo.png")
    with Image.open(src) as img:
        data = compress_bytes(img, ".jpg", 90)
    dest = tmp_path / "out.jpg"
    dest.write_bytes(data)
    with Image.open(dest) as saved:
        assert saved.format == "JPEG"
        assert saved.mode == "RGB"


def test_compress_bytes_rejects_unknown_format(tmp_path):
    src = _make(tmp_path / "a.png")
    with Image.open(src) as img:
        with pytest.raises(ValueError):
            compress_bytes(img, ".gif")


def test_lower_quality_creates_smaller_jpeg(tmp_path):
    src = _make(tmp_path / "noisy.png", "PNG", size=(300, 300))
    img = Image.open(src)
    data_high = compress_bytes(img, ".jpg", 100)
    data_low = compress_bytes(img, ".jpg", 5)
    img.close()
    assert len(data_low) < len(data_high)


def test_compressed_preview_keeps_size_and_loads(tmp_path):
    src = _make(tmp_path / "src.png")
    with Image.open(src) as img:
        prev = compressed_preview(img, ".jpg", 60)
        assert prev.size == img.size
        prev.close()
        prev2 = compressed_preview(img, ".webp", 50)
        assert prev2.size == img.size
        prev2.close()
