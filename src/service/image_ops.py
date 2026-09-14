"""Xử lý ảnh dùng chung bằng Pillow: bo góc, resize, đảm bảo kênh alpha."""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, UnidentifiedImageError

from core.exceptions import BadImageError, BadSizeError, MissingFileError
from core.file_utils import ensure_parent_dir, first_image
from core.formats import READABLE_IMAGE_EXTENSIONS
from core.paths import INPUT_DIR, OUTPUT_ROUNDED


def ensure_rgba(img: Image.Image) -> Image.Image:
    """Trả về bản RGBA của ảnh (copy nếu đã RGBA)."""
    return img.convert("RGBA") if img.mode != "RGBA" else img.copy()


def clamp_radius(radius: int, width: int, height: int) -> int:
    """Kẹp bán kính bo góc vào đoạn hợp lệ 0..min(w,h)//2."""
    if radius < 0:
        raise BadSizeError(f"bán kính bo góc phải >= 0, nhận được {radius}")
    return min(radius, min(width, height) // 2)


def rounded_corners(img: Image.Image, radius: int) -> Image.Image:
    """Trả về ảnh mới đã bo góc (giữ kích thước, alpha gốc được giữ lại).

    Ngoài vùng bo góc trở nên trong suốt; pixel bán trong suốt bên trong
    vẫn giữ đúng độ mờ ban đầu.
    """
    rgba = ensure_rgba(img)
    radius = clamp_radius(radius, *rgba.size)
    if radius == 0:
        return rgba
    mask = Image.new("L", rgba.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [(0, 0), (rgba.width - 1, rgba.height - 1)], radius=radius, fill=255
    )
    _, _, _, alpha = rgba.split()
    rgba.putalpha(ImageChops.darker(alpha, mask))
    return rgba


def round_image_file(
    source: str | Path,
    dest: str | Path | None = None,
    radius: int = 64,
    out_dir: str | Path | None = None,
) -> str:
    """Bo góc file ảnh `source`, lưu PNG vào `dest` (mặc định `<tên>-rounded.png`).

    Trả về đường dẫn file PNG đã ghi.
    """
    src = Path(source)
    if not src.is_file():
        raise MissingFileError(f"Không tìm thấy file nguồn: {src}")
    if src.suffix.lower() not in READABLE_IMAGE_EXTENSIONS:
        raise BadImageError(
            f"Chỉ hỗ trợ {sorted(READABLE_IMAGE_EXTENSIONS)}, nhận được '{src.suffix}'"
        )
    try:
        with Image.open(src) as img:
            out = rounded_corners(img, radius)
    except UnidentifiedImageError as exc:
        raise BadImageError(f"Không đọc được ảnh: {src}") from exc

    if dest is not None:
        dest_path = Path(dest)
    elif out_dir is not None:
        dest_path = Path(out_dir) / f"{src.stem}-rounded.png"
    else:
        dest_path = src.with_name(f"{src.stem}-rounded.png")
    try:
        ensure_parent_dir(dest_path)
        out.save(dest_path, format="PNG")
    finally:
        out.close()
    return str(dest_path)


def main(argv: list[str] | None = None) -> int:
    """Entry point: python -m service.image_ops [nguon] [dich] [--radius N]

    Mặc định: nguồn = ảnh đầu tiên trong input/,
    đích = output/rounded/<tên>-rounded.png.
    """
    args = [a for a in list(sys.argv[1:] if argv is None else argv) if a]
    radius = 64
    if "--radius" in args:
        idx = args.index("--radius")
        if idx + 1 >= len(args):
            print("Lỗi: --radius cần một số kèm theo", file=sys.stderr)
            return 2
        try:
            radius = int(args[idx + 1])
        except ValueError:
            print(f"Lỗi: --radius phải là số nguyên, nhận được {args[idx + 1]!r}",
                  file=sys.stderr)
            return 2
        del args[idx : idx + 2]
    if len(args) > 2:
        print("Dùng: python -m service.image_ops [nguon] [dich] [--radius N]")
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
    dest = args[1] if len(args) == 2 else None
    out_dir = None if len(args) == 2 else OUTPUT_ROUNDED
    try:
        print(round_image_file(source, dest, radius, out_dir))
    except (BadImageError, BadSizeError, MissingFileError, OSError) as exc:
        print(f"Lỗi: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
