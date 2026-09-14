"""Controller bo góc: parse radius + gọi service.image_ops."""

from __future__ import annotations

from pathlib import Path

from service import image_ops

DEFAULT_RADIUS = 64


def parse_radius(text: str, width: int, height: int) -> int:
    """Chuỗi nhập vào → bán kính hợp lệ 0..min(w,h)//2."""
    radius = int(text)
    return image_ops.clamp_radius(radius, width, height)


def run_round(
    source: str | Path,
    dest: str | Path | None = None,
    radius: int = DEFAULT_RADIUS,
    out_dir: str | Path | None = None,
) -> str:
    """Bo góc file ảnh, lưu PNG, trả về đường dẫn file đã ghi."""
    return image_ops.round_image_file(source, dest, radius, out_dir)
