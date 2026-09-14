"""Controller đổi định dạng ảnh: parse quality + gọi service.format_convert."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from service import format_convert
from service.format_convert import (
    DEFAULT_QUALITY,
    FORMAT_NAMES,
    TARGETS_BY_INPUT,
    clamp_quality,
    normalize_ext,
    target_formats,
)


def parse_quality(text: str) -> int:
    """Chuỗi nhập vào → quality hợp lệ 1..100 (100 = tốt nhất, ít nén nhất)."""
    return clamp_quality(int(text))


def options_for(source: str | Path) -> list[str]:
    """Hai định dạng đích còn lại so với file nguồn (vd src .png → ['.jpg', '.webp'])."""
    return target_formats(source)


def preview_format(img: Image.Image, fmt: str, quality: int = DEFAULT_QUALITY) -> Image.Image:
    """Ảnh sau khi nén theo `fmt` ở mức `quality` — dùng để xem trước mất chi tiết."""
    return format_convert.compressed_preview(img, fmt, quality)


def run_format_convert(
    source: str | Path,
    out_dir: str | Path | None = None,
    fmt: str = ".jpg",
    quality: int = DEFAULT_QUALITY,
) -> str:
    """Đổi định dạng file ảnh, trả về đường dẫn file đã ghi."""
    return format_convert.convert_format_file(source, out_dir, fmt, quality)


__all__ = [
    "DEFAULT_QUALITY",
    "FORMAT_NAMES",
    "TARGETS_BY_INPUT",
    "clamp_quality",
    "normalize_ext",
    "options_for",
    "parse_quality",
    "preview_format",
    "run_format_convert",
    "target_formats",
]