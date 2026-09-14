# Nhật ký quyết định (Decision Log)

Luật 4 trong `AGENTS.md`: mỗi quyết định của người dùng → thêm 1 luật vào `AGENTS.md` kèm ngày tháng + 1 bản ghi ở file này.

Định dạng:

```
## YYYY-MM-DD
- **[ID] Quyết định:** mô tả
  → Luật tương ứng: <mô tả> (`AGENTS.md`)
```

---

## 2026-09-13

- **[D1] Sản phẩm:** Chuyển đổi ảnh PNG → ICO bằng Pillow, có giao diện Tkinter và Launcher C# chạy trên Windows.
  → Ghi vào mục "Dự án" của `AGENTS.md`.
- **[D2] Quy trình commit:** Chỉ commit khi phiên bản chạy được và pass toàn bộ test. Không commit WIP.
  → Luật 1 (`AGENTS.md`).
- **[D3] Chất lượng test:** Test phải có ý nghĩa — hook vào file/hàm dễ hỏng, không viết cho đủ số lượng; chủ động xóa test lỗi thời.
  → Luật 2, 3 (`AGENTS.md`).
- **[D4] Quy trình agent:** Mọi quyết định của người dùng phải được ghi thành luật trong `AGENTS.md` và ghi vào nhật ký này.
  → Luật 4 (`AGENTS.md`).
- **[D5] Trạng thái dự án:** Ở bước khởi tạo chỉ tạo khung (cấu trúc + plan), chưa viết code — agent khác làm tiếp theo plan.

## 2026-09-13 (build)

- **[D6] Công cụ build launcher:** Cài .NET 8 SDK qua `winget install Microsoft.DotNet.SDK.8` để build/kiểm chứng launcher C#. Launcher dùng WinForms chỉ cho hộp thoại lỗi (`UseWindowsForms=true`).
  → Ghi chú trong `plan/003-csharp-launcher.md`.
- **[D7] Kiểm chứng launcher trên Windows Store Python:** Process GUI có tên `python3.13.exe` chứ không phải `python.exe`; script kiểm tra tự động phải match theo MainWindowTitle `IconMaker`.
  → Ghi chú trong `plan/003-csharp-launcher.md`.

## 2026-09-13 (sprite splitter)

- **[D8] Tính năng tách sprite:** Ảnh vào đặt trong `input/` (nền đen #101213/#111214/#121315 lẫn các mẫu đen gần nhau); pipeline: xóa nền đen → cắt từng vùng có pixel ra file riêng → trim phần trong suốt; kết quả vào `sprites_out/`.
  → Luật mới (`AGENTS.md`): quy ước đường dẫn `input/` → `sprites_out/`; cả hai là dữ liệu/output, cho vào `.gitignore`.
- **[D9] Đặt tên theo caption OCR:** Dùng RapidOCR (ONNXRuntime) đọc chữ caption bên DƯỚI mỗi sprite, đặt tên file `NNN_<caption>.png`; text nằm trong icon (vd `</>` giữa artwork) không tính là caption; thêm `rapidocr-onnxruntime` vào `requirements.txt`.
  → Plan `plan/005-sprite-splitter.md` cập nhật mục Caption OCR.
- **[D10] Đổi dấu phân cách tên sprite:** `NNN_<caption>.png` → `NNN-<caption>.png`.
  → Sửa trong `sprites.py::process_file` + test.
- **[D11] Xuất icon chất lượng cao từ sprites_out → icon_out/:** Không cắt xéo pixel — pad vào khung vuông trong suốt rồi resize; sinh đủ size 16..256 bằng LANCZOS trực tiếp từ master lớn; frame PNG lossless trong ICO.
  → Module mới `src/iconmaker/icons.py`, plan `006-icon-quality.md`, `icon_out/` vào `.gitignore`.
- **[D12] `icon_out/` phẳng:** Không có thư mục con — mọi icon cùng 1 tầng; tên file ghép `<sheet>-<sprite>` (`0-001-skill.md.ico`) để toàn bộ thông tin hiện trong tên và không đụng độ giữa các sheet.
  → Sửa `icons.build_from_sprites` + test; cập nhật `plan/006-icon-quality.md`.

## 2026-09-14

- **[D13] Makefile hóa mọi pipeline:** Thêm `Makefile` ở gốc làm điểm vào duy nhất (all/install/test/sprites/icons/ico/launcher/run/clean), cài `make` qua winget (ezwinports.make). Khi đổi entry point phải cập nhật Makefile cùng lần thay đổi.
  → Luật 7 (`AGENTS.md`).
- **[D14] Tính năng đổi icon thư mục:** GUI cho chọn 1 file ICO + 1 thư mục rồi ghi `desktop.ini` ẩn (`attrib +h +s`, folder `+r`, `ie4uinit -show`). Icon bắt buộc copy vào `C:\Users\inter\OneDrive\Pictures\Icon` trước khi trỏ tới, để di chuyển app không hỏng icon.
  → Luật 8 (`AGENTS.md`); module `src/iconmaker/foldericon.py`; plan `007-folder-icon.md`.
- **[D15] Cấm agent tạo file ngoài app:** Phát hiện rác `C:\Users\inter\icon_check.txt` do agent previous loop ghi tay ra `~/` khi kiểm tra. Chỉ code app (test bằng `tmp_path`) mới được ghi ra ngoài; agent thử nghiệm xong phải tự dọn (cả artifact lẫn thuộc tính attrib).
  → Luật 9 (`AGENTS.md`).

## 2026-09-14 (gui pythonw + customtkinter)

- **[D16] GUI chạy bằng pythonw (không hiện cửa sổ console):** Thêm target `make gui` (`GUI_PYTHON=pythonw` trên Windows, `python3` các OS khác); launcher C# dò `pythonw` → `pyw` → `py` → `python` và đặt `CreateNoWindow=true`.
  → Luật 10 (`AGENTS.md`).
- **[D17] GUI dùng CustomTkinter + nút đổi theme tối/sáng:** `IconMakerApp(ctk.CTk)`, mặc định Dark, nút "Đổi sang Sáng/Tối" qua hàm thuần `next_theme()`; thêm `customtkinter>=5.2` vào `requirements.txt`.
  → Luật 11 (`AGENTS.md`).

## 2026-09-14 (tái cấu trúc MVP + bo góc)

- **[D18] Kiến trúc tham khảo, tự đặt tên theo tình huống, dùng CustomTkinter:** Layout gốc `main.py` + `core/` + `gui/` + `tools/` + `assets/` (xóa `src/iconmaker/`); GUI chỉ hiển thị, logic trong `core/`/`tools/`; tab mới = 1 module `tools/` + 1 dòng `registry.py`.
  → Luật 12 (`AGENTS.md`); plan `008-mvp-restructure.md`.
- **[D19] Bo góc bằng Pillow, không dùng scipy:** `core.image_ops` (mask `rounded_rectangle` + giữ alpha gốc), CLI `python -m core.image_ops`, target `make rounded`, tab "Bo góc" có xem trước Trước/Sau.

## 2026-09-14 (launcher theo khung tray-clone)

- **[D20] Launcher là template tray-clone độc lập, không phải phần của app:** `launcher/` theo khung `TrayDemo` (skill tray-clone) — mục đích là sinh file exe C# có gán icon + nối tới folder chứa app run server. Mọi giá trị gom vào `AppConfig.cs` (file duy nhất cần sửa khi clone) + `Assets/icon.ico`; csproj gen bằng `dotnet new winforms` rồi patch 2 dòng icon (không copy tay); `Port=0` + `ProjectDir=""` nghĩa là app GUI/tự dò root; sinh app mới bằng `launcher/new-launcher.ps1` (`make new-launcher NAME=...`).
  → Luật 13 (`AGENTS.md`); plan `003-csharp-launcher.md` viết lại theo khung.