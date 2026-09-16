"""Nén ảnh trong bộ nhớ cho các đích jpg/webp (tham số quality 1..100)."""

from __future__ import annotations

from io import BytesIO

from PIL import Image

FORMAT_NAMES = {".png": "PNG", ".jpg": "JPEG", ".webp": "WEBP"}
DEFAULT_QUALITY = 100


def normalize_ext(ext: str) -> str:
    """Chuẩn hóa đuôi thành .png/.jpg/.webp (.jpeg → .jpg)."""
    value = ext.lower()
    if not value.startswith("."):
        value = f".{value}"
    if value == ".jpeg":
        return ".jpg"
    if value not in FORMAT_NAMES:
        raise ValueError(f"Định dạng không hỗ trợ (chỉ png/jpg/webp): {ext!r}")
    return value


def clamp_quality(quality: object) -> int:
    """Chuẩn hóa quality nguyên trong 1..100 (100 = chất lượng cao nhất)."""
    if isinstance(quality, bool) or not isinstance(quality, int):
        raise ValueError(f"Quality phải là số nguyên 1..100, nhận được {quality!r}")
    if not (1 <= quality <= 100):
        raise ValueError(f"Quality phải trong 1..100, nhận được {quality}")
    return quality


def compress_bytes(img: Image.Image, fmt: str, quality: int = DEFAULT_QUALITY) -> bytes:
    """Nén ảnh trong bộ nhớ theo `fmt` (.png/.jpg/.webp), trả về bytes."""
    fmt_upper = FORMAT_NAMES[normalize_ext(fmt)]
    out = img.convert("RGB") if fmt_upper == "JPEG" else img
    kwargs = {"quality": clamp_quality(quality)} if fmt_upper in ("JPEG", "WEBP") else {}
    buf = BytesIO()
    out.save(buf, format=fmt_upper, **kwargs)
    if out is not img:
        out.close()
    return buf.getvalue()


def compressed_preview(
    img: Image.Image, fmt: str, quality: int = DEFAULT_QUALITY
) -> Image.Image:
    """Giải mã lại ảnh sau nén — preview đúng mức mất chi tiết."""
    data = compress_bytes(img, fmt, quality)
    return Image.open(BytesIO(data)).copy()
