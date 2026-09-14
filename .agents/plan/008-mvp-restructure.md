# Plan 008 — Tái cấu trúc MVP (core / gui / tools)

**Trạng thái:** ✅ Hoàn thành (2026-09-14). 87/87 test pass. GUI 5 tab + launcher đã kiểm chứng chạy thật.
**Bổ sung 2026-09-14 — layout src/ + output/ (95/95 test pass):** toàn bộ code
vào `src/`, CLI mặc định `input/` → `output/<tenTool>/` (xem "Layout src/" dưới).

## Mục tiêu

- GUI chỉ là giao diện: mọi logic nằm trong `core/` (dùng chung) và `tools/` (riêng từng tab).
- Thêm tool bo góc ảnh → PNG (`core.image_ops` + tab "Bo góc").
- Đưa toàn bộ tính năng hiện có vào GUI dạng tab.

## Layout src/ (2026-09-14 — thay layout gốc, `git mv` giữ history)

```
src/
  main.py                  # entry: pythonw src/main.py
  core/                    # logic thuần, KHÔNG import GUI (+ paths.py giữ hằng số đường dẫn)
  gui/                     # chỉ hiển thị
  tools/                   # mỗi tool 1 tab + run_*
tests/                     # giữ ở gốc; pytest.ini đã có pythonpath=src
input/                     # đầu vào mặc định của tool qua CLI (bỏ trống tham số)
output/<tool>/             # đầu ra: convert/ rounded/ sprites/ icons/
```

- Import giữ nguyên (`core.*`, `gui.*`, `tools.*`); chạy từ gốc với
  `PYTHONPATH=src` (Makefile `export` sẵn; `python src/main.py` tự có src trong sys.path).
- CLI thiếu tham số → lấy mặc định (`convert`: PNG đầu tiên trong `input/` →
  `output/convert/`; `image_ops` tương tự → `output/rounded/`; `sprites`:
  `input/` → `output/sprites/`; `icons`: `output/sprites/` → `output/icons/`;
  `foldericon`: ICO mới nhất `output/icons/`, thư mục đích bắt buộc).
  Không có input → báo lỗi yêu cầu điền rõ, như GUI.
- GUI prefill sẵn các đường dẫn trên (hàng thư mục; `rounded` lưu vào
  `output/rounded/`); `foldericon` vẫn bắt chọn cả 2 như cũ.
- Launcher C# dò `src/main.py` (`AppConfig.CommandArgs`, `FindAppRoot`).

## Layout cũ (trước 2026-09-14 — đã dời bằng git mv)

```
main.py                  # entry: pythonw main.py
core/                    # logic thuần, KHÔNG import GUI
  convert.py             # PNG → ICO (từ converter.py, + CLI main thay cli.py)
  image_ops.py           # bo góc, ensure_rgba, clamp_radius (+ CLI)
  file_utils.py          # resolve_output_path, with_extension, iter_image_files
  formats.py             # tập đuôi file hỗ trợ
  exceptions.py          # IconMakerError (+ subclass ValueError/FileNotFoundError)
  sprites.py / icons.py / foldericon.py   # git mv giữ history, sửa import
gui/                     # chỉ hiển thị
  main_window.py         # MainWindow + CTkTabview, nút đổi theme
  base_tool.py           # ToolTab: khung + status dùng chung
  widgets.py             # FileRow, ImagePreview
  theme.py               # next_theme(), apply_default_theme()
tools/                   # mỗi tool = 1 tab: Tab(ToolTab) + hàm run_* gọi core/
  registry.py            # get_tools() — thứ tự tab
  convert_tool / rounded_tool / sprites_tool / icons_tool / foldericon_tool
assets/icons|styles/     # tài nguyên tĩnh (hiện chỉ có README giữ chỗ)
```

## Quy ước

- `core/` không được import `gui`/`tools`/`customtkinter`.
- Tab mới = thêm module trong `tools/` + 1 dòng trong `registry.get_tools()`.
- Hàm dễ hỏng của tool đặt ở cấp module (`run_*`, `parse_*`) để test không cần mở cửa sổ.
- Plan 001–007 mô tả đúng hành vi từng tính năng; đường dẫn `src/iconmaker/*` trong đó đọc thành `core/*`, GUI (plan 002) đọc thành `gui/` + `tools/`.

## Ghi chú triển khai

- Bo góc bằng Pillow (`rounded_rectangle` mask + `ImageChops.darker` giữ alpha gốc), không cần scipy.
- `make rounded RSRC=... RDEST=... RADIUS=...` gọi `python -m core.image_ops`
  (PYTHONPATH=src do Makefile export; bỏ trống RSRC/RDEST = dùng input/ → output/rounded/).
- Launcher dò `src/main.py`, chạy `pythonw src/main.py`.
