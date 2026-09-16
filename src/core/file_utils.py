"""Tiện ích file dùng chung: duyệt ảnh, tạo thư mục."""

from __future__ import annotations

from pathlib import Path


def ensure_parent_dir(dest: str | Path) -> Path:
    """Tạo thư mục cha của `dest` nếu chưa có, trả về Path của đích."""
    dest_path = Path(dest)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    return dest_path


def iter_image_files(
    directory: str | Path, extensions: set[str] | None = None
) -> list[Path]:
    """Liệt kê file ảnh trong `directory` (sắp xếp theo tên)."""
    from core.formats import READABLE_IMAGE_EXTENSIONS

    wanted = extensions or READABLE_IMAGE_EXTENSIONS
    folder = Path(directory)
    if not folder.is_dir():
        return []
    return sorted(p for p in folder.iterdir() if p.suffix.lower() in wanted)


def newest_file(directory: str | Path, extension: str) -> Path | None:
    """File có phần mở rộng `extension` mới nhất trong `directory`."""
    folder = Path(directory)
    if not folder.is_dir():
        return None
    ext = extension.lower()
    files = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() == ext]
    return max(files, key=lambda p: p.stat().st_mtime) if files else None
