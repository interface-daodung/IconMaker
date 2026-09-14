"""Fixture: tạo ảnh test mọi định dạng/kích thước ngay tại chỗ, không cần file mẫu."""

from __future__ import annotations

import pytest
from PIL import Image


def _make_png(path, size, mode, color=(200, 100, 50, 255)):
    img = Image.new(mode, size, color)
    img.save(path, format="PNG")
    img.close()
    return str(path)


@pytest.fixture
def png_rgb(tmp_path):
    """PNG không alpha (RGB) — dễ hỏng vì ICO cần alpha."""
    return _make_png(tmp_path / "rgb.png", (300, 300), "RGB")


@pytest.fixture
def png_rgba(tmp_path):
    """PNG có alpha trong suốt một nửa — dễ hỏng vì alpha có thể bị mất."""
    path = tmp_path / "rgba.png"
    img = Image.new("RGBA", (300, 300), (200, 100, 50, 255))
    for x in range(150):
        for y in range(300):
            img.putpixel((x, y), (200, 100, 50, 0))
    img.save(path, format="PNG")
    img.close()
    return str(path)


@pytest.fixture
def png_small(tmp_path):
    """PNG nhỏ hơn kích thước icon 256 — ép phải upscale."""
    return _make_png(tmp_path / "small.png", (20, 20), "RGBA")


@pytest.fixture
def png_large(tmp_path):
    """PNG lớn — dễ hỏng về hiệu năng/bộ nhớ nếu code sai."""
    return _make_png(tmp_path / "large.png", (4000, 4000), "RGBA")


@pytest.fixture
def jpeg_file(tmp_path):
    """File JPEG hợp lệ nhưng SAI định dạng đầu vào theo hợp đồng converter."""
    path = tmp_path / "notpng.jpg"
    img = Image.new("RGB", (100, 100), (10, 20, 30))
    img.save(path, format="JPEG")
    img.close()
    return str(path)


@pytest.fixture
def broken_file(tmp_path):
    """File giả ảnh: phần mở rộng .png nhưng nội dung rác."""
    path = tmp_path / "broken.png"
    path.write_bytes(b"\x00\x01not a real image\x00")
    return str(path)


@pytest.fixture
def fake_png_nonimage(tmp_path):
    """File văn bản đổi đuôi .png — Pillow phải từ chối."""
    path = tmp_path / "text.png"
    path.write_text("đây không phải ảnh", encoding="utf-8")
    return str(path)