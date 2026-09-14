"""Controller đặt icon thư mục: chuẩn hoá tên + gọi service.foldericon."""

from __future__ import annotations

from pathlib import Path

from core.paths import OUTPUT_ICONS
from service import folder_search, foldericon


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


def is_batch_input(raw: str | None) -> bool:
    """True khi ô thư mục là cú pháp hàng loạt `*<tên>`."""
    return folder_search.is_batch_input(raw)


def parse_batch_name(raw: str | None) -> str:
    """Tách tên thư mục từ `*<tên>` (sai cú pháp thì ValueError)."""
    return folder_search.parse_batch_name(raw)


def default_search_root() -> str:
    """Thư mục quét mặc định (home của user)."""
    return str(folder_search.default_root())


def extra_drives() -> list[str]:
    """Các ổ đĩa ngoài ổ home (GUI dựng 1 checkbox cho mỗi ổ)."""
    return folder_search.list_extra_drives()


def run_search(name: str, extra_roots: list[str] | None = None) -> list[str]:
    """Tìm mọi thư mục tên đúng bằng `name`: home + `extra_roots`."""
    roots: list[str | Path] = [folder_search.default_root()]
    for extra in extra_roots or []:
        if str(extra).strip():
            roots.append(Path(str(extra).strip()))
    return folder_search.find_folders_by_name(name, roots)


def run_apply_many(
    icon_path: str | Path, folders: list[str | Path], new_name: str | None = None
) -> tuple[list[str], dict[str, str]]:
    """Đặt 1 icon cho nhiều thư mục; trả về (ok, {folder: lỗi})."""
    clean = parse_new_name(new_name)
    installed = foldericon.install_icon(
        icon_path, None, clean if clean is not None else None
    )
    ok: list[str] = []
    failed: dict[str, str] = {}
    for folder in folders:
        try:
            foldericon.set_folder_icon(folder, installed)
        except (ValueError, FileNotFoundError, RuntimeError, OSError) as exc:
            failed[str(folder)] = str(exc)
        else:
            ok.append(str(folder))
    return ok, failed
