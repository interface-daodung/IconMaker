"""Controller tách sprite: gom PNG input/ → service.sprites."""

from __future__ import annotations

from pathlib import Path

from core.file_utils import iter_image_files
from core.formats import PNG_EXTENSIONS
from service import sprites


def run_split(input_dir: str | Path, out_dir: str | Path) -> list[str]:
    """Tách mọi PNG trong `input_dir` vào `out_dir`, trả về danh sách file đã ghi."""
    src = Path(input_dir)
    if not src.is_dir():
        raise FileNotFoundError(f"Không tìm thấy thư mục ảnh vào: {src}")
    files = iter_image_files(src, PNG_EXTENSIONS)
    if not files:
        raise ValueError(f"Không có file PNG nào trong {src}")
    written: list[str] = []
    for f in files:
        written.extend(str(p) for p in sprites.process_file(f, out_dir))
    return written
