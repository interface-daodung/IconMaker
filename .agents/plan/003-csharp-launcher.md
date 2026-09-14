# Plan 003 — Launcher C# (.NET)

**Trạng thái:** ✅ Đã triển khai + build & chạy được (2026-09-13).

## Build

```
dotnet build launcher/IconMakerLauncher/IconMakerLauncher.csproj -c Release
dotnet publish ... -c Release -r win-x64 --self-contained false   # khi đóng gói
```

Yêu cầu .NET 8 SDK (máy đã cài qua winget — xem `decisions.md [D6]`).

## Ghi chú đã kiểm chứng

- Launcher tự dò `py`/`python` (Windows Store Python có tên process `python3.13.exe` — không match theo tên `python.exe` khi kiểm tra tự động; xem `decisions.md [D7]`).
- `FindAppRoot()` đi ngược từ thư mục exe đến folder chứa `src/iconmaker/gui.py`, chạy `python -m iconmaker.gui` với working directory = `src`.
- Đã test end-to-end: chạy exe → GUI "IconMaker" hiện → đóng GUI → launcher thoát.

## Mục tiêu

Chương trình C# chạy trên Windows để khởi động app IconMaker (vì app chạy Python + Tkinter, launcher giúp trải nghiệm "click icon là chạy").

## Trách nhiệm (đề xuất cho `launcher/IconMakerLauncher/Program.cs`)

- Tìm `python.exe` (`py` hoặc `python`) — nếu không có, hiện message thân thiện.
- Chạy script GUI: `python -m iconmaker.gui` (hoặc đường dẫn tương đối đến app).
- Khởi động app Python **bên ngoài process launcher** (không block launcher nếu không cần) hoặc chờ đóng — tùy quyết định.
- Phát hiện python từ venv / đường dẫn cạnh launcher nếu có (ví dụ khi đóng gói).

## Cấu trúc đề xuất

```
launcher/
└── IconMakerLauncher/
    ├── IconMakerLauncher.csproj   # net8.0-windows (hoặc net9/net10 theo máy), OutputType WinExe
    └── Program.cs
```

## Điểm dễ hỏng (chủ yếu kiểm bằng tay khi build, không viết test giả)

- Tìm sai python → ưu tiên: tham số/basename quy định > `py` launcher > `python` trong PATH.
- Working directory sai → script Python không tìm thấy module.
- Cổng / path chứa space → dùng `ProcessStartInfo` với Arguments đúng (array `ArgumentList`).

## Quy ước

- Chỉ cần chạy được trên Windows.
- Không import lib ngoài NuGet trừ khi thực sự cần.
- Ghi chú cách build (dotnet build / publish) vào đây sau khi triển khai.

## Ghi chú triển khai

(Để trống — agent triển khai điền vào sau khi xong.)