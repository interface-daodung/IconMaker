"""Resize ảnh đầu vào thành nhiều cỡ ảnh vuông cho icon."""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from core.exceptions import BadImageError, MissingFileError
from core.file_utils import ensure_parent_dir, first_image
from core.formats import READABLE_IMAGE_EXTENSIONS
from core.paths import INPUT_DIR, OUTPUT_RESIZE

RESIZE_SIZES = [16, 48, 128]
RESIZE_NAMES = ["icon16", "icon48", "icon128"]
DEFAULT_FORMAT = ".png"

_FORMAT_MAP = {"jpg": "JPEG", "jpeg": "JPEG"}


def _pillow_format(ext: str) -> str:
    name = ext.lstrip(".").lower()
    return _FORMAT_MAP.get(name, name.upper())


def resize_to_square(img: Image.Image, size: int) -> Image.Image:
    """Resize ảnh vuông `size x size`, giữ nguyên RGBA."""
    rgba = img.convert("RGBA") if img.mode != "RGBA" else img.copy()
    return rgba.resize((size, size), Image.LANCZOS)


def resize_image_file(
    source: str | Path,
    out_dir: str | Path | None = None,
    ext: str = DEFAULT_FORMAT,
) -> list[str]:
    """Resize ảnh `source` thành 3 cỡ 16/48/128 vuông.

    Trả về danh sách đường dẫn 3 file đã ghi.
    """
    src = Path(source)
    if not src.is_file():
        raise MissingFileError(f"Không tìm thấy file nguồn: {src}")
    if src.suffix.lower() not in READABLE_IMAGE_EXTENSIONS:
        raise BadImageError(
            f"Chỉ hỗ trợ {sorted(READABLE_IMAGE_EXTENSIONS)}, nhận được '{src.suffix}'"
        )
    try:
        img = Image.open(src)
    except UnidentifiedImageError as exc:
        raise BadImageError(f"Không đọc được ảnh: {src}") from exc

    out_folder = Path(out_dir) if out_dir else OUTPUT_RESIZE
    ext = ext if ext.startswith(".") else f".{ext}"
    results: list[str] = []
    for size, name in zip(RESIZE_SIZES, RESIZE_NAMES):
        resized = resize_to_square(img, size)
        dest = out_folder / f"{name}{ext}"
        ensure_parent_dir(dest)
        fmt = _pillow_format(ext)
        if fmt == "JPEG":
            resized = resized.convert("RGB")
        try:
            resized.save(dest, format=fmt)
        finally:
            resized.close()
        results.append(str(dest))
    img.close()
    return results


def main(argv: list[str] | None = None) -> int:
    """Entry point: python -m service.resize [nguon] [--ext .png]

    Mặc định: nguồn = ảnh đầu tiên trong input/.
    """
    args = [a for a in list(sys.argv[1:] if argv is None else argv) if a]
    ext = DEFAULT_FORMAT
    if "--ext" in args:
        idx = args.index("--ext")
        if idx + 1 >= len(args):
            print("Lỗi: --ext cần đuôi file kèm theo (vd: .png)", file=sys.stderr)
            return 2
        ext = args[idx + 1]
        del args[idx : idx + 2]
    if len(args) > 1:
        print("Dùng: python -m service.resize [nguon] [--ext .png]")
        return 2
    if args:
        source = args[0]
    else:
        found = first_image(INPUT_DIR)
        if found is None:
            print(
                f"Lỗi: không có ảnh nào trong {INPUT_DIR}"
                " — đặt ảnh vào đó hoặc truyền <nguon>",
                file=sys.stderr,
            )
            return 1
        source = str(found)
    try:
        results = resize_image_file(source, ext=ext)
        for p in results:
            print(p)
    except (BadImageError, MissingFileError, OSError) as exc:
        print(f"Lỗi: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
