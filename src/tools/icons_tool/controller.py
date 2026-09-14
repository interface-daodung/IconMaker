"""Controller build ICO từ sprite: gọi service.icons."""

from __future__ import annotations

from pathlib import Path

from service import icons


def run_build(sprites_dir: str | Path, icon_dir: str | Path) -> list[str]:
    """Mọi PNG trong `sprites_dir` → ICO trong `icon_dir`, trả về danh sách đã ghi."""
    if not Path(sprites_dir).is_dir():
        raise FileNotFoundError(f"Không tìm thấy thư mục sprite: {sprites_dir}")
    written = icons.build_from_sprites(sprites_dir, icon_dir)
    if not written:
        raise ValueError(f"Không có sprite PNG nào trong {sprites_dir}")
    return [str(p) for p in written]
