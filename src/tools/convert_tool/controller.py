"""Controller tool PNG → ICO: parse input + gọi service.convert."""

from __future__ import annotations

from pathlib import Path

from core.file_utils import resolve_output_path
from service import convert

ALL_SIZES_LABEL = "Tất cả"


def parse_sizes(selection: str) -> list[int]:
    """Chuyển lựa chọn combo thành list kích thước hợp lệ cho converter."""
    if selection == ALL_SIZES_LABEL:
        return convert.get_default_sizes()
    return [int(selection)]


def run_conversion(
    source: str | Path,
    out_dir: str | Path | None = None,
    sizes: list[int] | None = None,
) -> str:
    """Chuyển PNG thành ICO, trả về đường dẫn file .ico."""
    dest = resolve_output_path(source, out_dir, ".ico")
    return convert.convert_png_to_ico(source, dest, sizes)
