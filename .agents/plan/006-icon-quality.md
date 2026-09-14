# Plan 006 — Icon chất lượng cao từ sprites_out

**Trạng thái:** ✅ Hoàn thành (2026-09-13) — quyết định [D10] + [D11].

## Yêu cầu

- Tên sprite: `NNN-<caption>.png` (dấu `-`, không phải `_`).
- Từ `sprites_out/` sinh ra `icon_out/` chứa `.ico` **chất lượng cao**,
  không cắt nhỏ/hư pixel.

## Thiết kế (`src/iconmaker/icons.py`)

- `pad_to_square(img)` — ảnh không vuông được đặt giữa khung vuông cạnh lớn
  nhất, nền trong suốt. Không bao giờ ép tỉ lệ (squash) gây méo.
- `sprite_to_ico(src, dest, sizes=None)` — mỗi size 16..256 resize TRỰC TIẾP
  từ master bằng `LANCZOS` (không resize dây chuyền size nhỏ→lớn gây vỡ hạt).
  Pillow 12 lưu frame trong ICO bằng PNG lossless — kiểm chứng: cả 7/7 frame
  của file xuất đều bắt đầu bằng signature `\x89PNG`.
- `build_from_sprites(sprites_dir, icon_dir)` — đệ quy mọi PNG, ghi **phẳng**
  vào `icon_dir` với tên `<sheet>-<sprite>.ico` ([D12]):
  `sprites_out/0/001-skill.md.png` -> `icon_out/0-001-skill.md.ico`.
  Toàn bộ thông tin nằm trong tên file, không cần thư mục con, không đụng độ
  giữa các sheet (test `test_same_caption_in_two_sheets_does_not_collide`).
- CLI: `python -m iconmaker.icons [sprites_out] [icon_out]`.

## Đã kiểm chứng

- `sprites_out/` (30 sprite) → `icon_out/` 30 file `.ico`, mỗi file 7 size
  16/24/32/48/64/128/256, tất cả frame PNG.
- Test `tests/test_icons.py` (7 test): pad giữ tỉ lệ + canh giữa; sprite
  400×200 ra 32px vẫn band cao ~16px (không méo); đủ size yêu cầu; frame
  256 là PNG; build đệ quy giữ layout; default sizes; thư mục rỗng.

## Ghi chú

- Nếu cần tương thích Windows XP (ICO chỉ BMP): dùng `bitmap_format="bmp"`
  nhưng chỉ ≤ 256px và chấp nhận giảm chất lượng — hiện ưu tiên chất lượng.