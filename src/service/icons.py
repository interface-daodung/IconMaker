"""Build icon .ico chất lượng cao từ sprite trong `sprites_out/`.

Chiến lược giữ chất lượng:
- Không cắt/xéo hình: pad vào khung vuông bằng nền trong suốt (chừa lề)
  rồi mới resize — ảnh gốc giữ nguyên tỉ lệ.
- Mọi size sinh ra trực tiếp từ master lớn nhất bằng LANCZOS (không resize
  dây chuyền từ size nhỏ -> vỡ hạt).
- Pillow 12 lưu frame 256px trong ICO bằng PNG lossless, không phải BMP.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from service.convert import validate_sizes


def pad_to_square(img: Image.Image) -> Image.Image:
    """Đặt ảnh vào giữa khung vuông cạnh = cạnh lớn nhất, nền trong suốt."""
    w, h = img.size
    side = max(w, h)
    out = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    out.paste(img, ((side - w) // 2, (side - h) // 2))
    return out


def sprite_to_ico(
    source: str | Path,
    dest: str | Path,
    sizes: list[int] | None = None,
) -> str:
    """Sprite -> file ICO với đủ các size, chất lượng cao, không biến dạng."""
    resolved = validate_sizes(sizes)
    with Image.open(source) as raw:
        master = pad_to_square(raw.convert("RGBA"))
    try:
        frames = [
            master.resize((s, s), Image.Resampling.LANCZOS) for s in resolved
        ]
    finally:
        master.close()

    dest_path = Path(dest)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    *others, base = frames
    try:
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


def build_from_sprites(
    sprites_dir: str | Path = "sprites_out",
    icon_dir: str | Path = "icon_out",
    sizes: list[int] | None = None,
) -> list[Path]:
    """Mọi PNG trong `sprites_dir` (đệ quy) -> ICO trong `icon_dir` (phẳng).

    Tên file ghép `<sheet>-<sprite>` để mọi thông tin nằm gọn trong tên,
    không cần thư mục con và không trùng nhau giữa các sheet:
    `sprites_out/0/001-skill.md.png` -> `icon_out/0-001-skill.md.ico`.
    """
    root = Path(sprites_dir)
    out_root = Path(icon_dir)
    out_root.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for png in sorted(root.rglob("*.png")):
        rel = png.relative_to(root)
        name = f"{rel.parent.name}-{rel.stem}.ico" if rel.parent != Path(".") else f"{rel.stem}.ico"
        written.append(Path(sprite_to_ico(png, out_root / name, sizes)))
    return written


def main(argv: list[str] | None = None) -> int:
    import sys

    from core.paths import OUTPUT_ICONS, OUTPUT_SPRITES

    args = [a for a in (sys.argv[1:] if argv is None else argv) if a]
    sprites_dir = Path(args[0]) if args else OUTPUT_SPRITES
    icon_dir = Path(args[1]) if len(args) > 1 else OUTPUT_ICONS
    written = build_from_sprites(sprites_dir, icon_dir)
    if not written:
        print(f"Không có sprite PNG nào trong {sprites_dir}", file=sys.stderr)
        return 1
    print(f"{len(written)} icon -> {icon_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())