# Plan 008 — Tái cấu trúc MVP (core / service / gui / tools)

**Trạng thái:** ✅ Hoàn thành (2026-09-14). 87/87 test pass. GUI 5 tab + launcher đã kiểm chứng chạy thật.
**Bổ sung 2026-09-14 — layout src/ + output/ (95/95 test pass):** toàn bộ code
vào `src/`, CLI mặc định `input/` → `output/<tenTool>/` (xem "Layout src/" dưới).
**Bổ sung 2026-09-14 — tách service + tools package (117/117 test pass):**
`core/` chỉ giữ share, logic riêng dời sang `service/`, mỗi tool thành
package `view.py` + `controller.py` (xem "Layout mới" dưới).
**Bổ sung 2026-09-16 — app GUI thuần, bỏ CLI (185/185 test pass):** xóa toàn
bộ `main()`/`__main__` khỏi `service/*` cùng các hàm/hằng chỉ CLI dùng;
`Makefile` còn `run` + `cls`; `src/main.py` tự thêm `src/` vào `sys.path` và
neo cwd về gốc project nên shortcut `pythonw "…/src/main.py"` chạy được từ
bất kỳ đâu. Mọi mục "CLI" trong plan 001–009 nay đọc là **hàm service** (GUI
là lối vào duy nhất).

## Mục tiêu

- GUI chỉ là giao diện: mọi logic nằm trong `core/` (share) + `service/` (riêng từng tool) + `tools/*/controller.py` (glue gọi service).
- Thêm tool bo góc ảnh → PNG (`service.image_ops` + tab "Bo góc").
- Đưa toàn bộ tính năng hiện có vào GUI dạng tab.

## Layout mới (2026-09-14 — tách service + tools package, `git mv` giữ history)

```
src/
  main.py                  # entry: pythonw src/main.py
  core/                    # share thuần, KHÔNG import GUI: paths, file_utils, formats, exceptions
  service/                 # logic riêng từng tool: convert, image_ops, sprites, icons, foldericon (+ CLI main)
  gui/                     # chỉ hiển thị: main_window, base_tool, widgets, theme
  tools/<tenTool>/         # mỗi tool 1 package: __init__ re-export + controller.py (run_*/parse_*) + view.py (Tab)
    convert_tool/ rounded_tool/ sprites_tool/ icons_tool/ foldericon_tool/
    registry.py            # get_tools() — thứ tự tab
```

- `controller.py` cấm import GUI/customtkinter, chỉ parse input + gọi `service/`
  → test được không cần mở cửa sổ (`tools.*.controller`).
- `view.py` (Tab) chỉ hiển thị, gọi `controller.*` + `core.paths` prefill.
- `service/` là logic thuần (không `main()`/`__main__`), GUI gọi qua controller;
  app không có CLI, chạy bằng `make run`.
- `__init__.py` mỗi tool re-export `Tab` + hàm controller để `registry.py` và code cũ vẫn chạy.

## Layout src/ (2026-09-14 — thay layout gốc, `git mv` giữ history)

```
src/
  main.py                  # entry: pythonw src/main.py
  core/                    # logic thuần, KHÔNG import GUI (+ paths.py giữ hằng số đường dẫn)
  gui/                     # chỉ hiển thị
  tools/                   # mỗi tool 1 tab + run_*
tests/                     # giữ ở gốc; pytest.ini đã có pythonpath=src
input/                     # đầu vào mặc định của tool (GUI prefill)
output/<tool>/             # đầu ra: export/ rounded/ resize/ sprites/ icons/ launchers/
```

- Import giữ nguyên (`core.*`, `gui.*`, `tools.*`); test chạy với `pythonpath=src`
  (trong `pytest.ini`); `pythonw "…/src/main.py"` tự thêm `src/` vào `sys.path`
  và neo cwd về gốc project nên shortcut chạy được từ bất kỳ đâu.
- Mọi thao tác đi qua GUI; `input/` là đầu vào mặc định prefill sẵn, `output/<tool>/`
  là nơi lưu. Không còn nhánh CLI "bỏ trống tham số → lấy mặc định".
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

- `core/` + `service/` không được import `gui`/`tools`/`customtkinter`.
- Tab mới = thêm package trong `src/tools/<tenTool>/` (`controller.py` + `view.py` + `__init__.py` re-export) + 1 dòng trong `registry.get_tools()`.
- Hàm dễ hỏng của tool đặt trong `controller.py` (`run_*`, `parse_*`) để test không cần mở cửa sổ.
- Plan 001–007 mô tả đúng hành vi từng tính năng; đường dẫn `src/iconmaker/*` trong đó đọc thành `service/*` (riêng) hoặc `core/*` (share), GUI (plan 002) đọc thành `gui/` + `tools/*/view.py`.

## Ghi chú triển khai

- Bo góc bằng Pillow (`rounded_rectangle` mask + `ImageChops.darker` giữ alpha gốc), không cần scipy.
- Launcher dò `src/main.py`, chạy `pythonw src/main.py`.
- `make run` = `pythonw src/main.py`, `make cls` = xóa cache; không còn target pipeline.
