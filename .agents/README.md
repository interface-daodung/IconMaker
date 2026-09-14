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

## Cách chạy

Khuyến nghị dùng `make` (cài qua winget `ezwinports.make`):

```powershell
make all        # install + test + sprites + icons
make test       # pytest
make gui        # mo GUI truc tiep bang pythonw (khong console)
make new-launcher NAME=<TenApp>  # sinh launcher moi theo khung tray-clone
make rounded RSRC=in.png RDEST=out.png RADIUS=64  # bo goc anh
make foldericon ICON=... FOLDER=...   # đặt icon cho thư mục
make help       # danh sách target
```

Thủ công (không cần make — chạy từ thư mục gốc, đặt PYTHONPATH=src):

```powershell
pip install -r requirements.txt
$env:PYTHONPATH = "src"
python -m pytest                                  # test
pythonw src/main.py                               # GUI
python -m service.convert                        # CLI convert: input/ -> output/convert/
python -m service.image_ops --radius 64          # CLI bo goc: input/ -> output/rounded/
python -m service.sprites                        # tach sprite: input/ -> output/sprites/
python -m service.icons                          # build ICO: output/sprites/ -> output/icons/
python -m service.foldericon C:\path\thu-muc     # đặt icon thư mục (ICO mới nhất output/icons/)
dotnet build launcher/IconMakerLauncher -c Release                # build khung launcher (template)
```