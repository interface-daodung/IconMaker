# AGENTS.md — IconMaker

Hướng dẫn và luật cho agent làm việc trong dự án này. Mọi agent bắt buộc đọc file này trước khi làm việc.

## Dự án

- **Tên:** IconMaker
- **Mục đích:** Xử lý ảnh/icon bằng Pillow (convert PNG→ICO, bo góc, tách sprite + OCR, build ICO chất lượng cao, đặt icon thư mục qua desktop.ini), giao diện **CustomTkinter** tab; kèm khung **Launcher C#** (template tray-clone cho app server khác, không dùng để chạy app này).
- **Stack:** Python 3.13, Pillow, CustomTkinter, .NET / C# (launcher).
- **Kiến trúc (plan 008):** `src/main.py` (entry) + `src/core/` (logic thuần, cấm import GUI) + `src/gui/` (chỉ hiển thị: main_window, base_tool, widgets, theme) + `src/tools/` (mỗi tool 1 tab + hàm `run_*` gọi core, đăng ký ở `registry.py`) + `assets/`. `input/` là đầu vào mặc định, `output/<tenTool>/` là đầu ra. Plan + trạng thái trong `.agents/README.md`.

## Đường dẫn quan trọng

| Đường dẫn | Nội dung |
| --- | --- |
| `AGENTS.md` | Luật dành cho agent (file này) |
| `src/main.py` | Entry point GUI (`pythonw src/main.py`) |
| `src/core/` | Logic thuần, không phụ thuộc GUI (convert, image_ops, sprites, icons, foldericon, paths, ...) |
| `src/gui/` | Chỉ hiển thị (main_window, base_tool, widgets, theme) |
| `src/tools/` | Mỗi tool 1 tab + hàm `run_*`; đăng ký ở `registry.py` |
| `input/` | Đầu vào mặc định của tool khi gọi qua CLI |
| `output/<tenTool>/` | Đầu ra của tool (convert, rounded, sprites, icons) |
| `.agents/README.md` | Bảng chỉ dẫn của toàn bộ `.agents/` |
| `.agents/plan/` | Các bản plan chi tiết từng phần |
| `.agents/decisions.md` | Nhật ký quyết định |
| `Makefile` | lối vào của mọi pipeline: `make help` liệt kê target |
| `.opencode/` | Cấu hình và agent của opencode |

## Luật bắt buộc

1. **Chỉ commit khi chạy được và test pass.** Chỉ được tạo commit khi phiên bản hiện tại chạy được và toàn bộ test case vượt qua. Không commit code dở dang (WIP).
2. **Test phải có ý nghĩa.** Test phải hook vào đúng file/hàm thật, vào những phần dễ hỏng (converter, xử lý ảnh, đường dẫn, edge case). Không viết test chỉ để cho đủ số lượng.
3. **Chủ động xóa test cũ.** Khi một test không còn phản ánh hành vi hiện tại, lỗi thời, hoặc thay thế được bằng test tốt hơn — hãy xóa/chỉnh nó, không giữ lại cho có.
4. **Ghi lại mọi quyết định.** Mỗi khi người dùng đưa ra một quyết định (chọn thư viện, thiết kế, quy trình, ...) → thêm một luật tương ứng vào file này kèm ngày tháng, đồng thời ghi vào `.agents/decisions.md`.
5. **Đọc plan trước khi code.** Trước khi triển khai, đọc `.agents/README.md` và các plan liên quan trong `.agents/plan/`.
6. **Cập nhật plan.** Sau khi hoàn thành một phần việc, cập nhật trạng thái vào plan tương ứng (đánh dấu `✅`, thêm ghi chú) để agent tiếp theo nắm được tình hình.
7. **Makefile là lối vào của mọi quy trình.** Khi thêm/thay đổi script hoặc entry point, phải cập nhật `Makefile` trong cùng lần thay đổi, và chạy target liên quan để kiểm chứng.
8. **Icon trỏ từ desktop.ini phải nằm ngoài app.** Trước khi ghi `desktop.ini`, icon `.ico` bắt buộc được copy vào thư viện icon ổn định của user (`~/OneDrive/Pictures/Icon`) bằng `foldericon.install_icon` — không bao giờ trỏ thẳng vào thư mục app, vì di chuyển app sẽ hỏng icon.
9. **Agent cấm tạo file ngoài thư mục app.** Chỉ có code của chính app Python (được test bằng `tmp_path`) mới được ghi vào các vị trí bên ngoài (như thư viện icon). Agent không được dùng lệnh shell để tạo/sửa file rác ngoài `IconMaker/`; mọi thử nghiệm phải dùng fixture `tmp_path` hoặc tự dọn dẹp ngay sau khi chạy (kể cả artifact trong `~/` và các thuộc tính `attrib` đã đặt lên file thật).
10. **GUI chạy bằng pythonw, không hiện console.** Mở GUI trực tiếp bằng `make gui` (`pythonw src/main.py`); launcher C# ưu tiên `pythonw`/`pyw` và đặt `CreateNoWindow=true`.
11. **GUI dùng CustomTkinter, có nút đổi theme tối/sáng.** `customtkinter` khai báo trong `requirements.txt`; logic đổi theme nằm trong hàm thuần `next_theme()` để test được.
12. **GUI chỉ là giao diện.** Mọi logic nằm trong `src/core/` (dùng chung, cấm import GUI) hoặc `src/tools/` (hàm `run_*`/`parse_*` cấp module của từng tab). Tab mới = thêm module trong `src/tools/` + 1 dòng trong `tools/registry.py`.
13. **Launcher chỉ là template tray-clone, không dùng để chạy app này.** `launcher/` lưu khung `TrayDemo` để sau này sửa `AppConfig.cs` rồi build exe cho app server khác (Python/Node); chỉ sửa `AppConfig.cs` + `Assets/icon.ico` khi clone, csproj gen bằng `dotnet new winforms` rồi patch 2 dòng icon (không copy tay); app mới sinh bằng `launcher/new-launcher.ps1` (`make new-launcher NAME=...`). IconMaker chạy trực tiếp bằng `make gui` (`pythonw src/main.py`); không có `make run`.
14. **Code trong src/, input/ vào — output/<tool> ra.** Mọi mã nguồn Python nằm trong `src/` (chạy từ gốc với `PYTHONPATH=src`; `pytest.ini` đã đặt sẵn). `input/` là đầu vào mặc định khi gọi tool qua CLI (bỏ trống tham số); thiếu input thì phải điền rõ như GUI. Mọi đầu ra của tool vào `output/<tenTool>/` (`core/paths.py` giữ hằng số); GUI prefill sẵn các đường dẫn này.
15. **Tab Icon thư mục lấy ICO từ output/icons và cho đổi tên trước khi cài.** Dialog chọn ICO mở thẳng `output/icons` (prefill ICO mới nhất); ô "Tên mới" bỏ trống = giữ tên gốc, nhập vào thì chuẩn hoá qua `sanitize_icon_name` rồi mới `install_icon` vào thư viện `~/OneDrive/Pictures/Icon` trước khi ghi desktop.ini.

## Quy ước code

- Python: mã nguồn trong `src/` (`core/` + `gui/` + `tools/` + `main.py`), test trong `tests/` (dùng pytest).
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
- **2026-09-14 — L10:** Launcher là template tray-clone độc lập (clone TrayDemo: chỉ sửa AppConfig.cs + icon, csproj từ dotnet new); sinh app mới bằng new-launcher.ps1 (Luật 13).
- **2026-09-14 — L11:** Code Python vào `src/`, CLI mặc định `input/` → `output/<tenTool>/`, thiếu thì điền rõ như GUI (Luật 14).
- **2026-09-14 — L12:** Launcher chỉ là template cho app server khác, không dùng để chạy IconMaker; bỏ `make run`, IconMaker chạy bằng `make gui` (Luật 13).
- **2026-09-14 — L13:** Tab Icon thư mục lấy ICO từ output/icons và cho đổi tên trước khi cài (Luật 15).