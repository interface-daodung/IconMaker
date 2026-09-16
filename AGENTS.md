# AGENTS.md — IconMaker

Hướng dẫn và luật cho agent làm việc trong dự án này. Mọi agent bắt buộc đọc file này trước khi làm việc.

## Dự án

- **Tên:** IconMaker
- **Mục đích:** Xử lý ảnh/icon bằng Pillow (convert ảnh→ICO, bo góc, tách sprite + OCR, build ICO chất lượng cao, đặt icon thư mục qua desktop.ini), giao diện **CustomTkinter** tab; kèm khung **Launcher C#** (template tray-clone cho app server khác, không dùng để chạy app này).
- **Stack:** Python 3.13, Pillow, CustomTkinter, .NET / C# (launcher).
- **Kiến trúc (plan 008):** `src/main.py` (entry, tự thêm `src/` vào sys.path để chạy bằng shortcut `pythonw`) + `src/core/` (share thuần: paths, file_utils, formats, exceptions, cấm import GUI) + `src/service/` (logic riêng từng tool: convert, format_convert, image_ops, sprites, icons, foldericon, junction, launcher) + `src/gui/` (chỉ hiển thị: main_window, base_tool, widgets, theme) + `src/tools/<tenTool>/` (mỗi tool 1 package: `controller.py` gọi service + `view.py` Tab, đăng ký ở `registry.py`) + `assets/`. `input/` là đầu vào mặc định, `output/<tenTool>/` là đầu ra. Plan + trạng thái trong `.agents/README.md`.

## Đường dẫn quan trọng

| Đường dẫn | Nội dung |
| --- | --- |
| `AGENTS.md` | Luật dành cho agent (file này) |
| `src/main.py` | Entry point GUI — chạy trực tiếp bằng `pythonw "…/src/main.py"` từ bất kỳ cwd nào (tự thêm `src/` vào sys.path) |
| `src/core/` | Logic share thuần, không phụ thuộc GUI (paths, file_utils, formats, exceptions) |
| `src/service/` | Logic riêng từng tool (convert, format_convert, image_ops, sprites, icons, resize, export, foldericon, folder_search, junction, launcher) |
| `src/gui/` | Chỉ hiển thị (main_window, base_tool, widgets, theme) |
| `src/tools/` | Mỗi tool 1 package `view.py` + `controller.py`; đăng ký ở `registry.py` |
| `input/` | Đầu vào mặc định của tool (GUI prefill) |
| `output/<tenTool>/` | Đầu ra của tool (export, rounded, resize, sprites, icons, launchers) |
| `.agents/README.md` | Bảng chỉ dẫn của toàn bộ `.agents/` |
| `.agents/plan/` | Các bản plan chi tiết từng phần |
| `.agents/decisions.md` | Nhật ký quyết định |
| `Makefile` | chỉ còn target `run` (mở GUI) và `cls` (xóa cache) |
| `.opencode/` | Cấu hình và agent của opencode |

## Luật bắt buộc

1. **Chỉ commit khi chạy được và test pass.** Chỉ được tạo commit khi phiên bản hiện tại chạy được và toàn bộ test case vượt qua. Không commit code dở dang (WIP).
2. **Test phải có ý nghĩa.** Test phải hook vào đúng file/hàm thật, vào những phần dễ hỏng (converter, xử lý ảnh, đường dẫn, edge case). Không viết test chỉ để cho đủ số lượng.
3. **Chủ động xóa test cũ.** Khi một test không còn phản ánh hành vi hiện tại, lỗi thời, hoặc thay thế được bằng test tốt hơn — hãy xóa/chỉnh nó, không giữ lại cho có.
4. **Ghi lại mọi quyết định.** Mỗi khi người dùng đưa ra một quyết định (chọn thư viện, thiết kế, quy trình, ...) → thêm một luật tương ứng vào file này kèm ngày tháng, đồng thời ghi vào `.agents/decisions.md`.
5. **Đọc plan trước khi code.** Trước khi triển khai, đọc `.agents/README.md` và các plan liên quan trong `.agents/plan/`.
6. **Cập nhật plan.** Sau khi hoàn thành một phần việc, cập nhật trạng thái vào plan tương ứng (đánh dấu `✅`, thêm ghi chú) để agent tiếp theo nắm được tình hình.
7. **Makefile chỉ còn `run` và `cls`.** App là GUI thuần, không có CLI/pipeline. `make run` mở GUI (`pythonw src/main.py`), `make cls` xóa cache (`__pycache__`, `.pytest_cache`). Mọi entry point thay đổi thì cập nhật Makefile trong cùng lần thay đổi và chạy thử target.
8. **Icon trỏ từ desktop.ini phải nằm ngoài app.** Trước khi ghi `desktop.ini`, icon `.ico` bắt buộc được copy vào thư viện icon ổn định của user (`~/OneDrive/Pictures/Icon`) bằng `foldericon.install_icon` — không bao giờ trỏ thẳng vào thư mục app, vì di chuyển app sẽ hỏng icon.
9. **Agent cấm tạo file ngoài thư mục app.** Chỉ có code của chính app Python (được test bằng `tmp_path`) mới được ghi vào các vị trí bên ngoài (như thư viện icon). Agent không được dùng lệnh shell để tạo/sửa file rác ngoài `IconMaker/`; mọi thử nghiệm phải dùng fixture `tmp_path` hoặc tự dọn dẹp ngay sau khi chạy (kể cả artifact trong `~/` và các thuộc tính `attrib` đã đặt lên file thật).
10. **GUI chạy bằng pythonw, không hiện console.** Mở GUI trực tiếp bằng `make run` (`pythonw src/main.py`); launcher C# ưu tiên `pythonw`/`pyw` và đặt `CreateNoWindow=true`. Shortcut Windows trỏ thẳng `pythonw "…\src\main.py"` (main.py tự lo `sys.path` + cwd).
11. **GUI dùng CustomTkinter, có nút đổi theme tối/sáng.** `customtkinter` khai báo trong `requirements.txt`; logic đổi theme nằm trong hàm thuần `next_theme()` để test được.
12. **GUI chỉ là giao diện.** Mọi logic nằm trong `src/core/` (dùng chung, cấm import GUI) hoặc `src/service/` (riêng từng tool, gọi core) hoặc `src/tools/<tenTool>/controller.py` (glue `run_*`/`parse_*` gọi service, test được không cần GUI). View nằm ở `src/tools/<tenTool>/view.py` (Tab thuần hiển thị). Tab mới = thêm package trong `src/tools/` + 1 dòng trong `tools/registry.py`.
13. **Launcher chỉ là template tray-clone, không dùng để chạy app này.** `launcher/` lưu khung `TrayDemo` để sau này sửa `AppConfig.cs` rồi build exe cho app server khác (Python/Node); chỉ sửa `AppConfig.cs` + `Assets/icon.ico` khi clone, csproj gen bằng `dotnet new winforms` rồi patch 2 dòng icon (không copy tay); app mới sinh bằng `launcher/new-launcher.ps1` (chạy script trực tiếp). IconMaker chạy trực tiếp bằng `make run` (`pythonw src/main.py`).
14. **Code trong src/, input/ vào — output/<tool> ra.** Mọi mã nguồn Python nằm trong `src/` (test chạy với `pythonpath=src` trong `pytest.ini`). `input/` là đầu vào mặc định của tool, GUI prefill sẵn. Mọi đầu ra của tool vào `output/<tenTool>/` (`core/paths.py` giữ hằng số). App **không có CLI**: mọi thao tác đi qua GUI (service/controller vẫn là logic thuần, test được).
15. **Tab Icon thư mục lấy ICO từ output/icons và cho đổi tên trước khi cài.** Dialog chọn ICO mở thẳng `output/icons` (prefill ICO mới nhất); ô "Tên mới" bỏ trống = giữ tên gốc, nhập vào thì chuẩn hoá qua `sanitize_icon_name` rồi mới `install_icon` vào thư viện `~/OneDrive/Pictures/Icon` trước khi ghi desktop.ini.
16. **Tool Resize icon tạo 3 cỡ vuông cố định.** Từ 1 ảnh png/jpg/webp tạo 3 ảnh vuông 16x16/48x48/128x128 tên `icon16`/`icon48`/`icon128`, đuôi mặc định `.png` có thể đổi (jpg/jpeg lưu bằng convert RGB vì JPEG không có alpha); output vào `output/resize/`. Tên file, danh sách size và đuôi mặc định là hợp đồng của `service/resize.py` (giữ nguyên khi refactor).
17. **Tool Xuất ảnh hợp nhất (jpg/png/webp/ico).** Gộp 2 tab cũ "PNG → ICO" + "Đổi định dạng" thành 1 tab "Xuất ảnh": đầu vào 1 ảnh (png/jpg/jpeg/webp), radio chọn 1 trong 4 đích jpg/png/webp/ico (cho phép trùng đuôi nguồn để ghi lại/re-encode; `.jpeg` chuẩn hoá về `.jpg`). Output chung vào `output/export/` (`OUTPUT_EXPORT` trong `core/paths.py`). Đích jpg/webp hiện thanh trượt chất lượng nén mặc định 100% (1..100) kèm preview roundtrip (`compress_bytes`/`compressed_preview`); đích png lossless không nén; đích ico cho chọn size (mặc định tất cả) và chấp nhận mọi ảnh vào qua `convert.convert_image_to_ico` (không giới hạn PNG). Contract giữ trong `service/export.py` (`normalize_export_fmt`, `export_file`, `EXPORT_FORMATS`, `DEFAULT_FMT=".ico"`) + `service/format_convert.py` (`compress_bytes`, `compressed_preview`, `normalize_ext`, `clamp_quality`); controller `tools/export_tool/controller.py` (`run_export`/`parse_quality`/`parse_sizes`/`preview_export`).
17. **Tool Junction tạo link ảo bằng mklink /J rồi attrib +r /l.** `service/junction.py` validate (ảo chưa tồn tại, thật là thư mục có sẵn), chạy `cmd /c mklink /J` và `attrib +r <ảo> /l` trên chính reparse point (KHÔNG resolve() link — nếu không sẽ đặt +r nhầm vào thư mục thật); tab GUI nhập thư mục cha + tên mới hoặc paste đường dẫn đủ, có checkbox tắt +r.
18. **Tool Icon thư mục tìm hàng loạt bằng `*<tên>`.** Gõ `*<tên>` ở ô Thư mục hiện nút Tìm: quét `Path.home()` khớp tên chính xác không hoa/thường, 1 checkbox cho mỗi ổ đĩa ngoài để quét thêm, luôn bỏ qua cây TEMP/TMP/AppData/LocalAppData và nhánh có phần bắt đầu `.` dưới home (ngoài home cho phép `.`), bỏ qua thư mục ẩn/system, không follow link; kết quả hiện list tick chọn (Chọn hết/Bỏ hết), đặt 1 lần cho mọi thư mục đã tick qua `run_apply_many` (cài icon 1 lần, gom lỗi từng thư mục). Contract trong `service/folder_search.py` (`is_batch_input`, `parse_batch_name`, `find_folders_by_name`).
19. **Tool Build Launcher build exe tray từ 1 thư mục server.** Tab "Build Launcher": ô thư mục server (dialog mở sẵn `C:\Users\inter\Project`), ô chọn 1 file ICO từ dự án (prefill ICO mới nhất `output/icons`), ô nhập tên launcher (bỏ trống = lấy tên thư mục server). Chạy build: copy icon vào thư viện `~/OneDrive/Pictures/Icon` đặt tên `<ten-launcher>.ico` qua `service/launcher.py::install_build_icon` (Luật 8) rồi gọi `launcher/build-launcher.ps1 -ServerDir -Name -Icon -OutDir -Mode`; `.exe` ra `output/launchers/` (`OUTPUT_LAUNCHER` trong `core/paths.py`). Contract trong `service/launcher.py` (`sanitize_launcher_name`, `project_clean_name`, `validate_server_dir`, `build_command`, `run_build`).

## Quy ước code

- Python: mã nguồn trong `src/` (`core/` + `service/` + `gui/` + `tools/` + `main.py`), test trong `tests/` (dùng pytest).
- Launcher C#: đặt trong `launcher/`.
- Không thêm comment thừa. Viết code sạch, theo phong cách các file xung quanh.
- Không import thư viện nào chưa khai báo trong `requirements.txt`.
- Công việc phải tự kiểm chứng trước khi báo hoàn thành (chạy thử, chạy test).

## Nhật ký luật

Luật mới được thêm khi người dùng đưa ra quyết định (xem `.agents/decisions.md`).

- **2026-09-13 — L1:** Chỉ commit khi phiên bản chạy được và pass toàn bộ test (Luật 1).
- **2026-09-13 — L2:** Test phải có ý nghĩa, hook vào hàm thật, chủ động xóa test lỗi thời (Luật 2, 3).
- **2026-09-13 — L3:** Mọi quyết định của người dùng phải được ghi thành luật + vào decision log (Luật 4).
- **2026-09-14 — L4:** Makefile là lối vào của mọi pipeline; cập nhật Makefile cùng lần thay đổi entry point (Luật 7).
- **2026-09-14 — L5:** Icon dùng cho desktop.ini phải copy vào thư viện icon ổn định của user trước (Luật 8).
- **2026-09-14 — L6:** Agent không được tạo file bên ngoài thư mục app; chỉ code app (test qua tmp_path) mới được ghi ra ngoài, agent phải tự dọn mọi artifact (Luật 9).
- **2026-09-14 — L7:** GUI chạy bằng pythonw không hiện console; launcher ưu tiên pythonw/pyw (Luật 10).
- **2026-09-14 — L8:** GUI dùng CustomTkinter, có nút đổi theme tối/sáng qua hàm thuần `next_theme()` (Luật 11).
- **2026-09-14 — L9:** Tái cấu trúc core/gui/tools; GUI chỉ hiển thị, logic trong core/tools; tab mới = 1 module tools + 1 dòng registry (Luật 12).
- **2026-09-14 — L9b:** Tách core share vs service riêng + tool thành package view/controller; core chỉ giữ share (paths, file_utils, formats, exceptions), logic riêng vào service/, controller glue gọi service, view thuần hiển thị (Luật 12).
- **2026-09-14 — L10:** Launcher là template tray-clone độc lập (clone TrayDemo: chỉ sửa AppConfig.cs + icon, csproj từ dotnet new); sinh app mới bằng new-launcher.ps1 (Luật 13).
- **2026-09-14 — L11:** Code Python vào `src/`, CLI mặc định `input/` → `output/<tenTool>/`, thiếu thì điền rõ như GUI (Luật 14).
- **2026-09-14 — L12:** Launcher chỉ là template cho app server khác, không dùng để chạy IconMaker; bỏ `make run`, IconMaker chạy bằng `make gui` (Luật 13). *(Đã bị L18 thay thế: nay chỉ còn `make run`.)*
- **2026-09-14 — L13:** Tab Icon thư mục lấy ICO từ output/icons và cho đổi tên trước khi cài (Luật 15).
- **2026-09-14 — L14:** Tool Resize icon tạo 3 cỡ vuông 16/48/128 tên icon16/icon48/icon128, đuôi mặc định .png đổi được, jpg/jpeg lưu bằng RGB (Luật 16).
- **2026-09-14 — L15:** Tool Xuất ảnh hợp nhất (gộp PNG→ICO + Đổi định dạng): 1 ảnh vào, radio 1 trong 4 đích jpg/png/webp/ico (cho trùng đuôi; ico nhận mọi ảnh qua convert_image_to_ico), output chung output/export/, CLI `python -m service.export`, `make export` (Luật 17).
- **2026-09-14 — L15b:** Tool Junction tạo link ảo bằng mklink /J rồi attrib +r /l trên chính link (không resolve, tránh đặt +r nhầm vào thư mục thật); GUI nhập cha + tên mới hoặc paste đường dẫn đủ, CLI `--no-readonly`, `make junction JLINK=... JTARGET=...` (Luật 17).
- **2026-09-14 — L16:** Tool Icon thư mục tìm hàng loạt `*<tên>`: quét home khớp tên chính xác không hoa/thường + checkbox từng ổ đĩa ngoài, bỏ qua TEMP/AppData/nhánh dot dưới home/ẩn-system/không follow link; list tick chọn, đặt 1 lần qua `run_apply_many` (Luật 18).
- **2026-09-14 — L17:** Tool Build Launcher: tab chọn thư mục server (dialog mở sẵn `C:\Users\inter\Project`) + 1 ICO từ dự án (prefill mới nhất `output/icons`) + ô tên launcher; cài icon vào thư viện đặt tên `<ten-launcher>.ico` rồi gọi `launcher/build-launcher.ps1`, exe ra `output/launchers/`, CLI `python -m service.launcher`, `make build-launcher` (Luật 19).
- **2026-09-16 — L18:** Bỏ toàn bộ CLI/pipeline: app chỉ còn GUI. Makefile rút còn `run` (pythonw) + `cls` (xóa cache); xóa `main()`/`__main__` khỏi mọi service và các hàm chỉ CLI dùng; `src/main.py` tự thêm `src/` vào sys.path + neo cwd để shortcut `pythonw "…/src/main.py"` chạy được từ bất kỳ đâu (Luật 7, 10, 14).