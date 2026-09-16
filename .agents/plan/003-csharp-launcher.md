# Plan 003 — Launcher C# (.NET)

**Trạng thái:** ✅ Khung tray-clone (2026-09-14 — theo `TrayDemo`, chỉ sửa `AppConfig.cs` + icon khi sinh app mới).

**2026-09-14 — Template-only:** `launcher/` chỉ là khung mẫu để sau này sửa config rồi build exe cho app server khác (Python/Node — chưa làm vội), **không dùng để chạy IconMaker** (IconMaker chạy trực tiếp bằng `make gui`). Target `make run` đã bỏ vì vô nghĩa.

## Khung tray-clone

`launcher/` là template độc lập (không phải phần của app Python) để sinh
file exe C# gán icon + nối tới folder chứa app run server:

```
launcher/
├── IconMakerLauncher/        # instance mẫu (đồng thời là nguồn khung)
│   ├── AppConfig.cs          # FILE DUY NHẤT CẦN SỬA khi clone
│   ├── ServerProcess.cs      # chạy process ẩn + gom log (Port=0 → bỏ qua check cổng)
│   ├── TrayAppContext.cs     # tray icon + menu Open Log / Restart / Kill / Exit
│   ├── ServerLogForm.cs      # cửa sổ log (đóng → ẩn, không kill)
│   ├── NativeMethods.cs
│   ├── Program.cs            # mutex single-instance + Application.Run
│   ├── Assets/icon.ico       # placeholder — thay bằng icon build từ IconMaker
│   ├── build.ps1             # build trước, chỉ publish khi build pass
│   └── IconMakerLauncher.csproj  # dotnet-new-winforms + 2 dòng icon
└── new-launcher.ps1          # script sinh app mới (xem dưới)
```

`IconMakerLauncher` trỏ về app IconMaker (`CommandFile=pythonw`,
`CommandArgs=src/main.py`, `ProjectDir=""` → tự dò thư mục chứa `src/main.py`,
`Port=0` → không kiểm tra cổng). Logic dò python (`ICONMAKER_PYTHON` →
`pythonw` → `pyw` → `py` → `python`, `CreateNoWindow=true`) giữ từ bản cũ,
chuyển vào `ServerProcess.ResolveCommandFile()`.

## Sinh launcher mới

```powershell
powershell -ExecutionPolicy Bypass -File launcher/new-launcher.ps1 -Name <TenApp> [-Icon path\to.ico]
# hoặc: make new-launcher NAME=<TenApp> [ICON=...ico]
```

Script tự làm theo skill tray-clone: `dotnet new winforms -n <TenApp>` →
copy 6 file khung (kèm `Program.cs` để xóa phụ thuộc `Form1` của `dotnet new`)
+ đổi namespace → xóa `Form1.*` → patch csproj 2 dòng icon → copy
`Assets/icon.ico` + `build.ps1`. Sau đó chỉ sửa 2 chỗ:

1. `<TenApp>\AppConfig.cs` (AppName, ProjectDir, Port, CommandFile/Args, TrayTooltip, messages).
2. Thay `<TenApp>\Assets\icon.ico` (VD icon build từ `make icons`).

## Build

```
dotnet build launcher/IconMakerLauncher/IconMakerLauncher.csproj -c Release
dotnet publish ... -c Release -r win-x64 --self-contained false   # khi đóng gói
```

Hoặc `Set-Location launcher/IconMakerLauncher; .\build.ps1` (framework mặc định;
`-Mode standalone` để ra 1 file ~70MB chạy mọi máy).

Yêu cầu .NET 8 SDK (máy đã cài qua winget — xem `decisions.md [D6]`).

## Ghi chú đã kiểm chứng

- 2026-09-14 — khung tray-clone: `dotnet build launcher/IconMakerLauncher -c Release`
  pass 0 warning; `new-launcher.ps1 -Name TmpTrayTest` + `dotnet build` pass
  (namespace + 2 dòng icon tự patch đúng), đã xóa app thử sau kiểm chứng.
  `pytest` 87/87 pass (không đụng code Python).
- Launcher tự dò `py`/`python` (Windows Store Python có tên process `python3.13.exe` — không match theo tên `python.exe` khi kiểm tra tự động; xem `decisions.md [D7]`).
- `FindAppRoot()` đi ngược từ thư mục exe đến folder chứa `src/iconmaker/gui.py`, chạy `python -m iconmaker.gui` với working directory = `src`.
- Đã test end-to-end: chạy exe → GUI "IconMaker" hiện → đóng GUI → launcher thoát.
- **2026-09-14 — pythonw:** `FindPython()` ưu tiên bản không console (`pythonw` → `pyw` → `py` → `python`; đã kiểm chứng `pythonw --version` exit 0 nên probe được), process GUI đặt `CreateNoWindow = true`. Đã test end-to-end: chạy exe → GUI "IconMaker" hiện dưới process `pythonw3.13` (không cửa sổ console) → kill sau kiểm chứng.

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

## Mục bổ sung (2026-09-14) — Tab "Build Launcher" trong app Python

Tab GUI gọi `launcher/build-launcher.ps1` (README của launcher) thay vì build tay:

- `src/service/launcher.py`: `validate_server_dir` + `sanitize_launcher_name` +
  `install_build_icon` (copy ICO vào thư viện `~/OneDrive/Pictures/Icon` đặt tên
  `<ten-launcher>.ico` — Luật 8) + `build_command`/`run_build` (subprocess
  `powershell -File build-launcher.ps1 -ServerDir -Name -Icon -OutDir -Mode`).
  Tên project C# (`project_clean_name`) mirror đúng regex của ps1.
- `src/tools/launcher_tool/`: view 3 ô (thư mục server mở sẵn
  `C:\Users\inter\Project`, ICO prefill mới nhất `output/icons`, tên launcher
  tự gợi ý theo tên thư mục), build chạy thread nền vì `dotnet publish` lâu.
- `.exe` ra `output/launchers/`; CLI `python -m service.launcher`,
  `make build-launcher SERVER=... ICON=... LNAME=... [MODE=...]`.
- **2026-09-14 — log trong tab, không console ngoài:** powershell là console-app nên
  tự bật cửa sổ console riêng kể cả khi GUI chạy bằng pythonw — `service/launcher.py`
  đặt `CREATE_NO_WINDOW` + `SW_HIDE` (`_hidden_popen_kwargs`, dùng cho cả 2 đường
  `run`/`Popen`) và thêm `stream_command`/`run_build(..., on_output=...)` đẩy từng
  dòng log vào `CTkTextbox` trong tab theo thời gian thực (qua `after`, thread nền).