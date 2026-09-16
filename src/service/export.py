"""Xuất ảnh hợp nhất: 1 ảnh vào (png/jpg/webp) → radio 1 trong 4 đích jpg/png/webp/ico.

Cho phép đích trùng đuôi nguồn (ghi lại/re-encode); riêng .ico chấp nhận
mọi ảnh đọc được. Output mặc định vào output/export/.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, UnidentifiedImageError

from core.exceptions import BadImageError, MissingFileError
from core.file_utils import ensure_parent_dir
from core.formats import READABLE_IMAGE_EXTENSIONS
from core.paths import OUTPUT_EXPORT
from service import convert
from service.format_convert import (
    DEFAULT_QUALITY,
    clamp_quality,
    compress_bytes,
)

EXPORT_FORMATS = (".jpg", ".png", ".webp", ".ico")
DEFAULT_FMT = ".ico"


def normalize_export_fmt(ext: str) -> str:
    """Chuẩn hóa đuôi đích thành .jpg/.png/.webp/.ico (.jpeg → .jpg)."""
    value = ext.lower()
    if not value.startswith("."):
        value = f".{value}"
    if value == ".jpeg":
        return ".jpg"
    if value not in EXPORT_FORMATS:
        raise ValueError(f"Định dạng ra không hỗ trợ (chỉ jpg/png/webp/ico): {ext!r}")
    return value


def export_file(
    source: str | Path,
    out_dir: str | Path | None = None,
    fmt: str = DEFAULT_FMT,
    quality: int = DEFAULT_QUALITY,
    sizes: list[int] | None = None,
) -> str:
    """Xuất `source` sang `fmt`, lưu vào `out_dir` (mặc định output/export/).

    - jpg/png/webp: nén qua compress_bytes (cho phép trùng đuôi nguồn).
    - ico: ghi đa size qua convert.convert_image_to_ico.
    Trả về đường dẫn file đã ghi.
    """
    src = Path(source)
    if not src.is_file():
        raise MissingFileError(f"Không tìm thấy file nguồn: {src}")
    if src.suffix.lower() not in READABLE_IMAGE_EXTENSIONS:
        raise BadImageError(
            f"Chỉ hỗ trợ {sorted(READABLE_IMAGE_EXTENSIONS)}, nhận được '{src.suffix}'"
        )
    out_ext = normalize_export_fmt(fmt)
    out_folder = Path(out_dir) if out_dir else OUTPUT_EXPORT

    if out_ext == ".ico":
        dest = out_folder / f"{src.stem}.ico"
        ensure_parent_dir(dest)
        return convert.convert_image_to_ico(src, dest, sizes)

    quality = clamp_quality(quality)
    try:
        with Image.open(src) as img:
            data = compress_bytes(img, out_ext, quality)
    except UnidentifiedImageError as exc:
        raise BadImageError(f"Không đọc được ảnh: {src}") from exc

    dest = out_folder / f"{src.stem}{out_ext}"
    ensure_parent_dir(dest)
    dest.write_bytes(data)
    return str(dest)
