# Plan 008 — Tái cấu trúc MVP (core / gui / tools)

**Trạng thái:** ✅ Hoàn thành (2026-09-14). 87/87 test pass. GUI 5 tab + launcher đã kiểm chứng chạy thật.

## Mục tiêu

- GUI chỉ là giao diện: mọi logic nằm trong `core/` (dùng chung) và `tools/` (riêng từng tab).
- Thêm tool bo góc ảnh → PNG (`core.image_ops` + tab "Bo góc").
- Đưa toàn bộ tính năng hiện có vào GUI dạng tab.

## Layout mới (thay `src/iconmaker/` — đã xóa)

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
- `make rounded RSRC=... RDEST=... RADIUS=...` gọi `python -m core.image_ops`.
- Launcher dò `main.py` (thay `src/iconmaker/gui.py`), chạy `pythonw main.py`.
