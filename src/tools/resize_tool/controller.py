"""Controller resize: gọi service.resize để tạo ảnh vuông nhiều cỡ."""

from __future__ import annotations

from pathlib import Path

from service import resize
from service.resize import DEFAULT_FORMAT, RESIZE_NAMES, RESIZE_SIZES


def run_resize(
    source: str | Path,
    out_dir: str | Path | None = None,
    ext: str = DEFAULT_FORMAT,
) -> list[str]:
    """Resize ảnh thành 3 cỡ vuông, trả về danh sách đường dẫn file đã ghi."""
    return resize.resize_image_file(source, out_dir, ext)
