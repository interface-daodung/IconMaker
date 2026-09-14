# Plan 000 — Tổng quan & Kiến trúc

**Trạng thái:** ✅ Đã triển khai (2026-09-13). Đã thêm `pytest.ini` (`pythonpath = src`, `testpaths = tests`).

## Mục tiêu

App chuyển đổi ảnh **PNG → ICO** (icon) bằng **Pillow**, có:
1. **Lõi chuyển đổi** (Python) — tái sử dụng được từ CLI, GUI và test.
2. **Giao diện Tkinter** — người dùng chọn ảnh, chọn kích thước, xuất icon.
3. **Launcher C#** — phóng đại giao diện / chạy app trên Windows.

## Kiến trúc đề xuất

```
IconMaker/
├── AGENTS.md
├── requirements.txt          # Pillow, pytest, ...
├── src/iconmaker/
│   ├── __init__.py
│   ├── converter.py          # Lõi: PNG -> ICO (Pillow)
│   ├── cli.py                # Entry point dòng lệnh
│   └── gui.py                # Giao diện Tkinter
├── tests/
│   ├── conftest.py           # Fixture tạo ảnh test
│   └── test_converter.py     # Test lõi chuyển đổi
├── launcher/                 # Launcher C# (.NET)
│   └── IconMakerLauncher/
│       ├── IconMakerLauncher.csproj
│       └── Program.cs        # Khởi động app Python
└── .agents/                  # Plan & điều hướng (đã có)
    ├── README.md
    ├── decisions.md
    └── plan/
```

## Phân tầng & kiểm thử

- **converter.py** = lõi thuần túy (không phụ thuộc Tkinter) → có thể test 100% bằng pytest. Đây là nơi dễ hỏng nhất, tập trung test ở đây.
- **gui.py** = lớp mỏng gọi converter; logic GUI nên gọn, phần dễ hỏng (chọn file, đường dẫn) tách ra helper để test được.
- **launcher/** = chỉ khởi động, chủ yếu test tay khi build.

## Luồng dữ liệu

```
PNG (người dùng) → [converter] → resize các kích thước icon → ghép vào ICO
                                        ↓
                              GUI / CLI / Launcher chọn ảnh & nơi lưu
```

## Kích thước icon chuẩn (mặc định)

16, 24, 32, 48, 64, 128, 256 px — bội số cần chứa trong 1 file `.ico` (Pillow `img.save(..., format="ICO", sizes=[...])`).

## Thứ tự triển khai

1. `001-core-pillow.md` — converter + test.
2. `004-testing.md` — áp dụng chiến lược test ngay từ đầu.
3. `002-tkinter-gui.md` — GUI dùng converter.
4. `003-csharp-launcher.md` — Launcher C#.