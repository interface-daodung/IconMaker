"""Tiện ích file dùng chung: suy tên file đích, duyệt ảnh, tạo thư mục."""

from __future__ import annotations

from pathlib import Path


def with_extension(source: str | Path, ext: str) -> Path:
    """Đổi phần mở rộng của `source` thành `ext` (giữ nguyên thư mục)."""
    return Path(source).with_suffix(ext)


def resolve_output_path(
    source: str | Path, out_dir: str | Path | None = None, ext: str = ".ico"
) -> str:
    """Tên file đích tương ứng từ file nguồn, trong `out_dir` hoặc cạnh nguồn."""
    src = Path(source)
    target_dir = Path(out_dir) if out_dir else src.parent
    return str(target_dir / (src.stem + ext))


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


def first_image(
    directory: str | Path, extensions: set[str] | None = None
) -> Path | None:
    """Ảnh đầu tiên (theo tên) trong `directory`, None nếu không có."""
    files = iter_image_files(directory, extensions)
    return files[0] if files else None


def newest_file(directory: str | Path, extension: str) -> Path | None:
    """File có phần mở rộng `extension` mới nhất trong `directory`."""
    folder = Path(directory)
    if not folder.is_dir():
        return None
    ext = extension.lower()
    files = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() == ext]
    return max(files, key=lambda p: p.stat().st_mtime) if files else None
