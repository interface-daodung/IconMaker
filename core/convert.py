"""Lõi chuyển đổi PNG -> ICO bằng Pillow. Không phụ thuộc Tkinter/CLI."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, UnidentifiedImageError

DEFAULT_SIZES: tuple[int, ...] = (16, 24, 32, 48, 64, 128, 256)
MAX_ICON_SIZE = 256


def get_default_sizes() -> list[int]:
    return list(DEFAULT_SIZES)


def validate_sizes(sizes: object) -> list[int]:
    """Trả về list kích thước hợp lệ (đã lọc trùng, sắp xếp).

    Raise ValueError nếu: rỗng, chứa phần tử không phải int dương <= 256.
    """
    if sizes is None:
        return get_default_sizes()
    if isinstance(sizes, int) or not isinstance(sizes, (list, tuple, set)):
        raise ValueError(f"sizes phải là list các int, nhận được {sizes!r}")
    if not sizes:
        raise ValueError("sizes rỗng")
    out: list[int] = []
    for size in sizes:
        if isinstance(size, bool) or not isinstance(size, int):
            raise ValueError(f"kích thước phải là int, nhận được {size!r}")
        if size <= 0 or size > MAX_ICON_SIZE:
            raise ValueError(
                f"kích thước phải trong 1..{MAX_ICON_SIZE}, nhận được {size}"
            )
        out.append(size)
    return sorted(set(out))


def convert_png_to_ico(
    source: str | Path,
    dest: str | Path,
    sizes: list[int] | None = None,
) -> str:
    """Chuyển file PNG `source` thành file ICO `dest`.

    - Ảnh vào phải là PNG đọc được; RGB sẽ được thêm kênh alpha (RGBA).
    - Mỗi kích thước trong `sizes` sẽ được resize (kể cả upscale) bằng LANCZOS
      và ghi đủ vào một file .ico duy nhất.
    - Tạo thư mục cha của `dest` nếu chưa tồn tại.
    - Trả về đường dẫn file ICO đã ghi.
    """
    src = Path(source)
    if not src.is_file():
        raise FileNotFoundError(f"Không tìm thấy file nguồn: {src}")

    try:
        with Image.open(src) as img:
            if img.format != "PNG":
                raise ValueError(
                    f"File nguồn phải là PNG, nhận được {img.format or 'không rõ định dạng'}"
                )
            rgba = img.convert("RGBA")
    except UnidentifiedImageError as exc:
        raise ValueError(f"Không đọc được ảnh (hỏng hoặc không phải ảnh): {src}") from exc

    resolved = validate_sizes(sizes) if sizes is not None else get_default_sizes()

    dest_path = Path(dest)
    if dest_path.is_dir():
        raise ValueError(f"Đích là thư mục, không phải file: {dest_path}")

    frames: list[Image.Image] = []
    try:
        for size in resolved:
            frames.append(rgba.resize((size, size), Image.Resampling.LANCZOS))
    except OSError as exc:
        raise ValueError(f"Ảnh nguồn hỏng, không giải mã được: {src}") from exc
    finally:
        rgba.close()

    try:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        *others, base = frames  # Pillow bỏ mọi size lớn hơn ảnh gốc -> phải dùng ảnh lớn nhất làm base
        base.save(
            dest_path,
            format="ICO",
            sizes=[frame.size for frame in frames],
            append_images=others,
        )
    finally:
        for frame in frames:
            frame.close()

    return str(dest_path)


def main(argv: list[str] | None = None) -> int:
    """Entry point dòng lệnh: python -m core.convert <nguon.png> <dich.ico> [sizes...]"""
    import sys

    args = sys.argv[1:] if argv is None else argv
    if not 2 <= len(args) <= 8:
        print(f"Dùng: {sys.argv[0]} <nguon.png> <dich.ico> [kích_thước...]")
        print(f"Mặc định: {DEFAULT_SIZES}")
        return 2
    try:
        sizes = [int(a) for a in args[2:]] or None
        out = convert_png_to_ico(args[0], args[1], sizes)
    except (ValueError, FileNotFoundError) as exc:
        print(f"Lỗi: {exc}", file=sys.stderr)
        return 1
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())