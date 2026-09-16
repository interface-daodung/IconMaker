"""Lõi chuyển đổi ảnh -> ICO đa size bằng Pillow. Không phụ thuộc Tkinter."""

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


def convert_image_to_ico(
    source: str | Path,
    dest: str | Path,
    sizes: list[int] | None = None,
) -> str:
    """Chuyển file ảnh `source` (png/jpg/jpeg/webp) thành file ICO `dest`.

    Dùng chung cho tool Xuất ảnh: mở ảnh bất kỳ đọc được, ép RGBA,
    resize LANCZOS từng size rồi ghi đủ vào một file .ico duy nhất.
    """
    from core.formats import READABLE_IMAGE_EXTENSIONS

    src = Path(source)
    if not src.is_file():
        raise FileNotFoundError(f"Không tìm thấy file nguồn: {src}")
    if src.suffix.lower() not in READABLE_IMAGE_EXTENSIONS:
        raise ValueError(
            f"File nguồn phải là ảnh {sorted(READABLE_IMAGE_EXTENSIONS)}, "
            f"nhận được '{src.suffix}'"
        )

    try:
        with Image.open(src) as img:
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