# .agents/ — Điều hướng

Kho tài liệu điều hướng và plan cho các agent làm việc trong dự án **IconMaker**.

## Cấu trúc

| Đường dẫn | Nội dung |
| --- | --- |
| `README.md` | File này — bảng chỉ dẫn toàn bộ `.agents/` |
| `plan/000-overview.md` | Tổng quan dự án, kiến trúc, cấu trúc thư mục, thứ tự triển khai |
| `plan/001-core-pillow.md` | Module chuyển đổi PNG → ICO bằng Pillow (lõi) |
| `plan/002-tkinter-gui.md` | Giao diện Tkinter |
| `plan/003-csharp-launcher.md` | Launcher C# chạy app |
| `plan/004-testing.md` | Chiến lược test — test có nghĩa, hook vào hàm dễ hỏng |
| `plan/005-sprite-splitter.md` | Tính năng tách sprite từ ảnh nền đen |
| `plan/006-icon-quality.md` | Xuất icon `.ico` chất lượng cao từ sprites_out |
| `plan/007-folder-icon.md` | Đặt icon cho thư mục Windows qua desktop.ini |
| `plan/008-mvp-restructure.md` | Tái cấu trúc core/gui/tools + tool bo góc (thay layout `src/iconmaker/`) |
| `plan/009-junction.md` | Tool tạo Junction Point (`mklink /J` + `attrib +r /l`) |
| `decisions.md` | Nhật ký quyết định của người dùng |

## Cách dùng

1. Luôn đọc `AGENTS.md` ở thư mục gốc trước.
2. Đọc `plan/000-overview.md` để nắm bức tranh tổng thể.
3. Đọc plan của phần đang làm (theo trạng thái ⏳).
4. Sau khi xong: cập nhật trạng thái plan, thêm ghi chú cần thiết.

## Trạng thái tổng (Legend)

- ⏳ Chưa bắt đầu
- 🔧 Đang triển khai
- ✅ Hoàn thành
- ❌ Bỏ / thay thế

| Phần | Plan | Trạng thái |
| --- | --- | --- |
| Core conversion (Pillow) | 001 | ✅ |
| GUI (Tkinter) | 002 | ✅ |
| Launcher (C#) | 003 | ✅ (khung tray-clone: AppConfig.cs + new-launcher.ps1, build pass) |
| Testing strategy | 004 | ✅ (32 test converter + 6 test logic GUI, pass 100%) |
| Sprite splitter (nền đen + OCR) | 005 | ✅ (19 test sprites, tổng 51/51 pass) |
| Icon chất lượng cao | 006 | ✅ (7 test icons, 58/58 pass) |
| Đặt icon thư mục (desktop.ini) | 007 | ✅ (12 test foldericon + 1 test GUI, 71/71 pass) |
| Tái cấu trúc MVP + bo góc | 008 | ✅ (layout src/, GUI 5 tab, input/ → output/<tool>/, 95/95 pass) |
| Tạo Junction Point | 009 | ✅ (mklink /J + attrib +r /l, tab Junction, 145/145 pass) |
| Xuất ảnh hợp nhất (gộp PNG→ICO + Đổi định dạng) | — | ✅ (service/export.py + tools/export_tool, radio jpg/png/webp/ico → output/export/, 185/185 pass) |
| Build Launcher (tab GUI theo launcher/README.md) | 003 (mục bổ sung) | ✅ (service/launcher.py + tools/launcher_tool, cài icon `<ten>.ico` vào thư viện rồi gọi build-launcher.ps1 → output/launchers/) |
| GUI thuần, bỏ CLI (chỉ `make run` + `make cls`) | — | ✅ (xóa `main()`/`__main__` khỏi service, `src/main.py` tự bootstrap sys.path cho shortcut pythonw) |

## Cách chạy

App là GUI thuần — chạy bằng `make run` (hoặc shortcut `pythonw "…\src\main.py"`):

```powershell
make run        # mo GUI (pythonw, khong console)
make cls        # xoa cache (__pycache__, .pytest_cache)
```

Chạy tay (không cần make):

```powershell
pip install -r requirements.txt
pythonw "C:\Users\inter\Project\MyHub\IconMaker\src\main.py"   # GUI — chay tu bat ky cwd nao
python -m pytest                                              # test (pythonpath=src trong pytest.ini)
```