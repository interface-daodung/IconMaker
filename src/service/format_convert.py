"""Đổi định dạng ảnh giữa png/jpg/webp, kèm nén bằng tham số quality."""

from __future__ import annotations

import sys
from io import BytesIO
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from core.exceptions import BadImageError, MissingFileError
from core.file_utils import ensure_parent_dir, first_image
from core.formats import READABLE_IMAGE_EXTENSIONS
from core.paths import INPUT_DIR, OUTPUT_CONVERT_FORMAT

FORMAT_NAMES = {".png": "PNG", ".jpg": "JPEG", ".webp": "WEBP"}
TARGETS_BY_INPUT = {
    ".png": [".jpg", ".webp"],
    ".jpg": [".png", ".webp"],
    ".webp": [".png", ".jpg"],
}
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


def target_formats(source: str | Path | None) -> list[str]:
    """Trả về 2 định dạng còn lại so với định dạng của `source` (path hoặc đuôi)."""
    value = str(source)
    ext = Path(value).suffix if "." in value and not value.startswith(".") else value
    return list(TARGETS_BY_INPUT[normalize_ext(ext)])


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


def convert_format_file(
    source: str | Path,
    out_dir: str | Path | None = None,
    fmt: str = ".jpg",
    quality: int = DEFAULT_QUALITY,
) -> str:
    """Đổi định dạng file ảnh `source` sang `fmt`, lưu vào `out_dir`.

    `fmt` phải khác định dạng nguồn (không cho đổi trùng). Trả về đường dẫn file đã ghi.
    """
    src = Path(source)
    if not src.is_file():
        raise MissingFileError(f"Không tìm thấy file nguồn: {src}")
    src_suffix = src.suffix.lower()
    if src_suffix not in READABLE_IMAGE_EXTENSIONS:
        raise BadImageError(
            f"Chỉ hỗ trợ {sorted(READABLE_IMAGE_EXTENSIONS)}, nhận được '{src_suffix}'"
        )
    in_ext = normalize_ext(src_suffix)
    out_ext = normalize_ext(fmt)
    if out_ext == in_ext:
        raise ValueError(
            f"Định dạng ra phải khác định dạng vào ({in_ext}); chọn 1 trong {TARGETS_BY_INPUT[in_ext]}"
        )
    quality = clamp_quality(quality)
    try:
        with Image.open(src) as img:
            data = compress_bytes(img, out_ext, quality)
    except UnidentifiedImageError as exc:
        raise BadImageError(f"Không đọc được ảnh: {src}") from exc

    out_folder = Path(out_dir) if out_dir else OUTPUT_CONVERT_FORMAT
    dest = out_folder / f"{src.stem}{out_ext}"
    ensure_parent_dir(dest)
    dest.write_bytes(data)
    return str(dest)


def main(argv: list[str] | None = None) -> int:
    """Entry point: python -m service.format_convert [nguon] [--fmt .webp] [--quality 100]

    Mặc định: nguồn = ảnh đầu tiên trong input/, fmt = định dạng còn lại đầu tiên.
    """
    args = [a for a in list(sys.argv[1:] if argv is None else argv) if a]
    positional: list[str] = []
    fmt: str | None = None
    quality = DEFAULT_QUALITY
    quality_value: str | None = None
    i = 0
    while i < len(args):
        flag = args[i]
        if flag in ("--fmt", "--quality"):
            i += 1
            if i >= len(args):
                print(f"Lỗi: {flag} cần giá trị kèm theo", file=sys.stderr)
                return 2
            if flag == "--fmt":
                fmt = args[i]
            else:
                quality_value = args[i]
        else:
            positional.append(flag)
        i += 1
    if len(positional) > 1:
        print("Dùng: python -m service.format_convert [nguon] [--fmt .webp] [--quality 100]")
        return 2
    if quality_value is not None:
        try:
            quality = int(quality_value)
        except ValueError:
            print(
                f"Lỗi: --quality phải là số nguyên, nhận được {quality_value!r}",
                file=sys.stderr,
            )
            return 2
    source = positional[0] if positional else None
    if source is None:
        found = first_image(INPUT_DIR)
        if found is None:
            print(
                f"Lỗi: không có ảnh nào trong {INPUT_DIR}"
                " — đặt ảnh vào đó hoặc truyền <nguon>",
                file=sys.stderr,
            )
            return 1
        source = str(found)
    if fmt is None:
        fmt = target_formats(source)[0]
    try:
        print(convert_format_file(source, fmt=fmt, quality=quality))
    except (BadImageError, MissingFileError, ValueError, OSError) as exc:
        print(f"Lỗi: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())