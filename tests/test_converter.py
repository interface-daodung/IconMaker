"""Test lõi converter — mỗi test bảo vệ MỘT hành vi dễ hỏng (xem plan 004)."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from service import convert as converter


def ico_frame_sizes(path: str | Path) -> set[tuple[int, int]]:
    """Đọc lại file ICO và trả về tập kích thước frame thật sự chứa trong file."""
    data = Path(path).read_bytes()
    assert data[:4] == b"\x00\x00\x01\x00", "file không có header ICO hợp lệ"
    count = int.from_bytes(data[4:6], "little")
    sizes = set()
    for i in range(count):
        entry = data[6 + i * 16 : 22 + i * 16]
        w = entry[0] or 256
        h = entry[1] or 256
        sizes.add((w, h))
    return sizes


def ico_get_frame(path: str | Path, size: tuple[int, int]) -> Image.Image:
    """Lấy một frame cụ thể ra khỏi file ICO dưới dạng ảnh RGBA đã load."""
    with Image.open(path) as ico:
        assert size in ico.info["sizes"], f"ICO không chứa size {size}"
        ico.size = size
        return ico.convert("RGBA")


# ---------- vùng nhập liệu hỏng ----------


def test_missing_source_raises_filenotfound(tmp_path):
    with pytest.raises(FileNotFoundError):
        converter.convert_image_to_ico(tmp_path / "nope.png", tmp_path / "a.ico")


def test_broken_image_raises_valueerror(broken_file, tmp_path):
    with pytest.raises(ValueError):
        converter.convert_image_to_ico(broken_file, tmp_path / "a.ico")


def test_text_file_with_png_extension_rejected(fake_png_nonimage, tmp_path):
    with pytest.raises(ValueError):
        converter.convert_image_to_ico(fake_png_nonimage, tmp_path / "a.ico")


def test_unreadable_extension_rejected(tmp_path):
    txt = tmp_path / "note.gif"
    txt.write_text("x", encoding="utf-8")
    with pytest.raises(ValueError):
        converter.convert_image_to_ico(txt, tmp_path / "a.ico")


# ---------- vùng màu & alpha ----------


def test_rgb_input_produces_valid_rgba_icon(png_rgb, tmp_path):
    """Ảnh RGB không alpha vẫn phải xuất ra icon 32bpp mở lại được ở RGBA."""
    dest = tmp_path / "rgb.ico"
    out = converter.convert_image_to_ico(png_rgb, dest, sizes=[32])
    assert Path(out) == dest and dest.is_file()
    frame = ico_get_frame(dest, (32, 32))
    assert frame.mode == "RGBA"
    assert frame.getchannel("A").getextrema()[0] == 255


def test_rgba_alpha_is_preserved_in_smallest_frame(png_rgba, tmp_path):
    """Nửa trái rgba.png trong suốt — xuống 16px vẫn phải còn pixel alpha=0."""
    dest = tmp_path / "a.ico"
    converter.convert_image_to_ico(png_rgba, dest, sizes=[16])
    frame = ico_get_frame(dest, (16, 16))
    assert frame.mode == "RGBA"
    assert frame.getchannel("A").getextrema()[0] < 128, "alpha trong suốt đã bị mất khi resize"


def test_solid_rgba_keeps_mostly_opaque(png_rgba, tmp_path):
    dest = tmp_path / "a.ico"
    converter.convert_image_to_ico(png_rgba, dest, sizes=[32])
    frame = ico_get_frame(dest, (32, 32))
    hist = frame.getchannel("A").histogram()
    total = sum(hist)
    opaque_ratio = sum(hist[201:]) / total
    assert opaque_ratio > 0.4, "nửa phải opaque bị làm mờ quá mức"


def test_jpeg_input_accepted_for_ico(jpeg_file, tmp_path):
    """Tool Xuất ảnh cho phép mọi ảnh vào (không chỉ PNG)."""
    dest = tmp_path / "a.ico"
    converter.convert_image_to_ico(jpeg_file, dest, sizes=[32])
    assert (32, 32) in ico_frame_sizes(dest)


# ---------- vùng kích thước ----------


def test_default_sizes_all_present_in_output(png_rgb, tmp_path):
    dest = tmp_path / "a.ico"
    converter.convert_image_to_ico(png_rgb, dest)
    assert ico_frame_sizes(dest) == {
        (s, s) for s in converter.get_default_sizes()
    }, "file ICO thiếu size so với danh sách mặc định"


def test_small_source_is_upscaled_to_requested_size(png_small, tmp_path):
    dest = tmp_path / "a.ico"
    converter.convert_image_to_ico(png_small, dest, sizes=[256])
    assert (256, 256) in ico_frame_sizes(dest), "upscale không được ghi vào ICO"


def test_large_image_converts_without_error(png_large, tmp_path):
    dest = tmp_path / "big.ico"
    converter.convert_image_to_ico(png_large, dest, sizes=[256, 32])
    assert ico_frame_sizes(dest) == {(32, 32), (256, 256)}


def test_duplicate_and_unsorted_sizes_deduplicated(png_rgb, tmp_path):
    dest = tmp_path / "a.ico"
    converter.convert_image_to_ico(png_rgb, dest, sizes=[48, 32, 48])
    assert ico_frame_sizes(dest) == {(32, 32), (48, 48)}


# ---------- vùng validate_sizes (hàm pure, hay bị sửa sai) ----------


@pytest.mark.parametrize(
    "bad",
    [
        [],
        [0],
        [-16],
        [257],
        [16, 300],
        ["32"],
        [None],
        [16.0],
        [True],
    ],
)
def test_validate_sizes_rejects_invalid(bad):
    with pytest.raises(ValueError):
        converter.validate_sizes(bad)


def test_validate_sizes_accepts_and_sorts():
    assert converter.validate_sizes([64, 16, 64]) == [16, 64]


def test_none_sizes_falls_back_to_default():
    assert converter.validate_sizes(None) == converter.get_default_sizes()


# ---------- vùng đường dẫn (dễ hỏng nhất trên Windows) ----------


def test_creates_missing_parent_directories(png_rgb, tmp_path):
    dest = tmp_path / "x" / "y" / "z" / "a.ico"
    converter.convert_image_to_ico(png_rgb, dest, sizes=[16])
    assert dest.is_file()


def test_destination_directory_is_rejected(png_rgb, tmp_path):
    with pytest.raises(ValueError):
        converter.convert_image_to_ico(png_rgb, tmp_path)


def test_unicode_and_space_path(png_rgb, tmp_path):
    dest = tmp_path / "tên tiếng Việt có space" / "a.ico"
    out = converter.convert_image_to_ico(png_rgb, dest, sizes=[32])
    assert Path(out).is_file()


# ---------- chống hồi quy: output phải đọc lại được như ICO thật ----------


def test_output_is_readable_ico_with_requested_sizes(png_rgba, tmp_path):
    dest = tmp_path / "a.ico"
    converter.convert_image_to_ico(png_rgba, dest, sizes=[16, 24])
    assert ico_frame_sizes(dest) == {(16, 16), (24, 24)}
    frame = ico_get_frame(dest, (24, 24))
    assert frame.size == (24, 24)
    assert dest.stat().st_size > 100
