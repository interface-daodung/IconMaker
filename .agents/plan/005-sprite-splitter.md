# Plan 005 — Tách sprite từ ảnh nền đen

**Trạng thái:** ✅ Hoàn thành (2026-09-13) — gồm cả đặt tên theo caption OCR ([D9]).

## Yêu cầu (quyết định [D8] của người dùng)

Đầu vào: ảnh trong `input/` — nền đen (các mẫu `#111214`, `#101213`, `#121315`...
chủ yếu gần đen, không thuần nhất). Xử lý:

1. Xóa màu đen (nền) -> trong suốt.
2. Cắt từng vùng có pixel (sprite) ra file riêng.
3. Trim phần trong suốt quanh mỗi sprite.

Đầu ra: `sprites_out/<tên file>/NNN-<caption OCR>.png` (RGBA, đã trim).

## Thuật toán (`src/iconmaker/sprites.py`)

- `split_sprites(img, threshold=32, min_area=2000)`:
  1. `threshold`: nền "gần đen" = R,G,B đều <= 32 (bọc các mẫu trên).
  2. **Flood-fill từ biên (4-hướng)**: chỉ pixel gần đen NỐI LIỀN với biên ảnh
     mới là nền -> đốm đen KÍN bên trong sprite (mắt, khối tối) không bị
     khoét thủng. Dùng 4-hướng thay vì 8-hướng để nền không rỉ qua khe chéo
     giữa hai sprite chạm góc nhau.
  3. Gán nhãn 4-hướng các vùng không-nền; mỗi vùng >= `min_area` là một
     sprite (caption nhỏ ~600px bị loại; sprite thật ~100k px).
  4. `_merge_holes_into_hosts`: vùng nhỏ có bbox nằm trọn trong bbox vùng
     khác được nạp vào chủ (giữ chi tiết tối nằm trong bao).
  5. Cắt theo bbox (trim tự nhiên), giữ nguyên màu gốc, phần lại trong suốt.
  6. `_reading_order`: sắp xếp theo hàng (y gần nhau, `ROW_TOLERANCE=32`) rồi
     trái->phải, đặt tên `001..` theo thứ tự đọc.
- CLI: `python -m iconmaker.sprites [input] [sprites_out]`.
- `remove_black_background()`: toàn bộ canvas với nền thành trong suốt.

## Caption OCR ([D9])

- `get_ocr()` — nạp lười engine `rapidocr_onnxruntime.RapidOCR` (ONNX, đã đưa
  `rapidocr-onnxruntime` vào `requirements.txt`).
- `caption_boxes()` — lọc kết quả OCR theo `OCR_MIN_SCORE=0.5`, bỏ text rỗng.
- `associate_captions()` — caption của sprite là text có **tâm nằm trong biên
  ngang sprite**, mép trên từ **đáy sprite trở xuống** (`CAPTION_V_TOL=15`
  overlap) và không quá xa (`CAPTION_MAX_GAP=240`). Quan trọng: text nằm
  TRONG artwork (vd `</>` giữa icon) không phải caption → không được đổi tên.
  Nhiều caption trên cùng một sprite → nối trái→phải (`skill md`).
- `sanitize_name()` — xóa ký tự cấm Windows (`<>:"/\|?*`), gộp space, tên
  trùng → `name (2)` (`_unique`).
- Tên file: `NNN-<caption>.png` (dấu `-` theo [D10]), vẫn giữ số thứ tự đọc `NNN` để sắp xếp ổn định.
- Test OCR dùng `monkeypatch` engine giả (không cần model trong CI) + đã chạy
  thật trên `input/`: `skill.md, commands, agents, games, code, projects`,
  `.vscode, .idea, .config, .git, .opencode, .claude`, ... chính xác.

## Đã kiểm chứng trên dữ liệu thật

`input/0..4.png` (1536×1024) → đúng **6 sprite/file, 30 file**; bbox vừa
khít ảnh xuất (trim chuẩn), nền sạch, không thủng thân tối trong sprite,
tên file khớp caption OCR.

## Điểm dễ hỏng đã có test (`tests/test_sprites.py`, 19 test)

- Đốm đen kín bên trong sprite không bị khoét thủng.
- Hai sprite sát nhau (khe 3px) không bị gộp một.
- Sprite chạm mép ảnh không bị flood-fill ăn mất.
- Nền lẫn nhiều sắc đen gần nhau vẫn xóa sạch.
- `min_area` lọc vụn nhưng không giết chi tiết nằm trong sprite.
- Thứ tự đọc hàng/cột; ảnh toàn đen trả `[]`.
- Caption: đúng sprite phía trên, loại text trong icon, loại text quá xa,
  loại confidence thấp, nối nhiều caption, `sanitize_name` ký tự cấm,
  tên trùng thêm `(2)`, `process_file` đặt tên đúng (OCR giả lập).

## Ghi chú triển khai

- Lõi tách sprite thuần Python stdlib + Pillow (không cần numpy). OCR chỉ
  chạy ở lớp `process_file`, engine nạp lười để import module không nặng.
- ~3s/ảnh 1536×1024 cho phần tách; OCR thêm ~1-2s/ảnh.
- Nếu nguồn sau này là ảnh JPEG nên cân nhắc hạ `threshold` vì ảnh nền
  đen JPEG có quầng ~30-40 quanh sprite.