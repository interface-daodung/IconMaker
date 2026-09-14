"""Controller đặt icon thư mục: chuẩn hoá tên + gọi service.foldericon."""

from __future__ import annotations

from pathlib import Path

from core.paths import OUTPUT_ICONS
from service import foldericon


def icons_default_dir() -> str:
    """Thư mục output/icons tuyệt đối (neo theo project root, chạy từ đâu cũng đúng)."""
    root = Path(__file__).resolve().parents[3]
    candidate = root / OUTPUT_ICONS
    if candidate.is_dir():
        return str(candidate)
    fallback = Path(OUTPUT_ICONS).resolve()
    return str(fallback) if fallback.is_dir() else str(candidate)


def parse_new_name(raw: str | None) -> str | None:
    """Tên mới do user nhập: rỗng/None = giữ tên gốc, còn lại chuẩn hoá .ico."""
    if raw is None or not str(raw).strip():
        return None
    return foldericon.sanitize_icon_name(raw)


def run_apply(
    icon_path: str | Path, folder_path: str | Path, new_name: str | None = None
) -> str:
    """Copy icon vào thư viện ổn định (đổi tên nếu có) rồi đặt cho thư mục."""
    clean = parse_new_name(new_name)
    if clean is None:
        installed = foldericon.install_icon(icon_path)
    else:
        installed = foldericon.install_icon(icon_path, None, clean)
    return foldericon.set_folder_icon(folder_path, installed)
