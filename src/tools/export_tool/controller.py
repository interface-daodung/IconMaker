"""Controller tool Xuất ảnh: parse input + gọi service.export."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from service import convert, export
from service.export import (
    DEFAULT_FMT,
    DEFAULT_QUALITY,
    EXPORT_FORMATS,
    clamp_quality,
    compressed_preview,
    normalize_export_fmt,
)

ALL_SIZES_LABEL = "Tất cả"


def parse_quality(text: str) -> int:
    """Chuỗi nhập vào → quality hợp lệ 1..100."""
    return clamp_quality(int(text))


def parse_sizes(selection: str) -> list[int]:
    """Lựa chọn combo size thành list kích thước cho ICO."""
    if selection == ALL_SIZES_LABEL:
        return convert.get_default_sizes()
    return [int(selection)]


def preview_export(img: Image.Image, fmt: str, quality: int = DEFAULT_QUALITY) -> Image.Image:
    """Ảnh sau nén theo `fmt` — dùng để xem trước (chỉ jpg/png/webp)."""
    return compressed_preview(img, normalize_export_fmt(fmt), quality)


def run_export(
    source: str | Path,
    out_dir: str | Path | None = None,
    fmt: str = DEFAULT_FMT,
    quality: int = DEFAULT_QUALITY,
    sizes: list[int] | None = None,
) -> str:
    """Xuất ảnh sang `fmt`, trả về đường dẫn file đã ghi."""
    return export.export_file(source, out_dir, fmt, quality, sizes)


__all__ = [
    "ALL_SIZES_LABEL",
    "DEFAULT_FMT",
    "DEFAULT_QUALITY",
    "EXPORT_FORMATS",
    "clamp_quality",
    "compressed_preview",
    "normalize_export_fmt",
    "parse_quality",
    "parse_sizes",
    "preview_export",
    "run_export",
]
