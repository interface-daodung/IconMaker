"""Controller Junction: ghép đường dẫn ảo + gọi service.junction."""

from __future__ import annotations

from pathlib import Path

from service import junction

_INVALID_NAME_CHARS = set('<>:"/\\|?*')


def join_link_path(parent: str | Path, name: str) -> str:
    """Đường dẫn ảo = thư mục cha (đã tồn tại) + tên junction mới.

    Cho phép paste thẳng đường dẫn đủ (kèm tên) vào ô cha khi `name` trống.
    """
    raw_parent = str(parent).strip()
    raw_name = str(name or "").strip()
    if not raw_parent:
        raise ValueError("Hãy chọn thư mục cha chứa đường dẫn ảo (vd trong OneDrive).")
    if not raw_name:
        return raw_parent
    if any(ch in raw_name for ch in _INVALID_NAME_CHARS):
        raise ValueError(f"Tên junction chứa ký tự cấm <>:\"/\\|?*: {raw_name!r}")
    return str(Path(raw_parent) / raw_name)


def parse_inputs(link: str | None, target: str | None) -> tuple[str, str]:
    """Hai đường dẫn user nhập: bỏ khoảng trắng, rỗng thì báo lỗi rõ."""
    clean_link = (link or "").strip()
    clean_target = (target or "").strip()
    if not clean_link:
        raise ValueError("Thiếu đường dẫn ảo (junction sẽ tạo).")
    if not clean_target:
        raise ValueError("Hãy chọn đường dẫn thật (thư mục nguồn ở ổ mới).")
    return clean_link, clean_target


def run_create(link: str, target: str, readonly: bool = True) -> str:
    """Tạo junction rồi (tuỳ chọn) attrib +r /l để hiển thị icon."""
    return str(junction.create_junction(link, target, readonly))
