# Tray Launcher Builder

Bộ công cụ tự động tạo ứng dụng Launcher chạy ngầm trên khay hệ thống (System Tray) cho bất kỳ thư mục server nào chạy bằng lệnh `make run`.

Đầu ra là **1 file `.exe` duy nhất** (Single-file standalone), tự động theo dõi PID và tiêu diệt tiến trình cha/con chính xác 100% bằng **Windows Job Object API** kết hợp **taskkill tree**.

---

## 1. Cách sử dụng nhanh

### Cách 1: Chạy qua file Batch hoặc PowerShell

```cmd
:: Cú pháp cơ bản (chỉ cần truyền đường dẫn folder server)
build-launcher.bat "C:\path\to\your\server"

:: Đầy đủ tham số: tên app và icon
build-launcher.bat "C:\path\to\your\server" --name "MyServer" --icon "C:\path\to\icon.ico"
```

Hoặc chạy trực tiếp với PowerShell:

```powershell
# Chạy với tham số
.\build-launcher.ps1 -ServerDir "C:\path\to\your\server" --name "MyServer" --icon "icon.ico"

# Chạy tương tác (nếu không truyền tham số, script sẽ hỏi đường dẫn)
.\build-launcher.ps1
```

### Cách 2: Tùy chọn chế độ Build

- `-Mode standalone` (Mặc định): Tự động nhúng kèm .NET 8 Runtime vào file `.exe`. File `.exe` có thể chạy trên mọi máy tính Windows x64 mà không cần cài đặt .NET.
- `-Mode framework`: Nhẹ hơn (chỉ vài MB), yêu cầu máy đích đã cài đặt .NET Desktop Runtime.
- `-OutDir <path>`: Thư mục chứa file `.exe` đầu ra (mặc định: `./dist`).

---

## 2. Quy trình 4 bước tự động hóa (PowerShell Scripts)

Toàn bộ quy trình được chia thành 4 script chạy tuần tự:

1. **`scripts/01-create-project.ps1`**:
   - Dùng lệnh `dotnet new winforms` để khởi tạo cấu trúc dự án tạm thời.
   - Tự động xóa các file boilerplate không cần thiết (`Form1.cs`, ...).
2. **`scripts/02-apply-templates.ps1`**:
   - Sao chép toàn bộ bộ template C# chuyên biệt từ thư mục `templates/`.
   - Sinh file `AppConfig.cs` với cấu hình cụ thể: đường dẫn server, lệnh `make run`, tên app, Mutex chống chạy trùng.
   - Nhúng file icon `.ico` vào tài nguyên ứng dụng.
3. **`scripts/03-publish-exe.ps1`**:
   - Thực hiện `dotnet build -c Release`.
   - Thực hiện `dotnet publish` chế độ Single-File để tạo ra 1 file `.exe` duy nhất.
4. **`scripts/04-cleanup-project.ps1`**:
   - Chuyển file `.exe` vừa tạo về thư mục `dist/`.
   - **Xóa sạch toàn bộ mã nguồn tạm**, chỉ giữ lại duy nhất file `.exe` đầu ra!

---

## 3. Cơ chế nắm giữ PID và Kill tiến trình chính xác

Khi chạy `make run`:
1. **Lưu PID**: Launcher lưu lại PID gốc ngay khi `make` khởi động, ghi log chi tiết và lưu file `.launcher.pid` tại thư mục server.
2. **Windows Job Object API**:
   - Sử dụng Windows API `CreateJobObject` và cờ `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`.
   - Gán tiến trình `make` vào Job Object. Tất cả các tiến trình con do `make` sinh ra (Python, Uvicorn, Node.js, Go...) tự động thuộc Job này.
   - Khi bấm **Kill Server**, **Restart Server** hoặc **Exit**, Windows OS tự động triệt tiêu toàn bộ cây tiến trình ngay lập tức.
3. **Taskkill Tree**: Gọi đồng thời `taskkill /PID <PID> /T /F` và `.NET Process.Kill(entireProcessTree: true)` để đảm bảo tính tương thích tối đa.

---

## 4. Tính năng của Launcher App đầu ra

- **Chạy ngầm hoàn toàn**: Không hiện cửa sổ CMD màu đen gây vướng víu.
- **Khay hệ thống (System Tray)**:
  - Click đúp hoặc chuột phải chọn **Open Log**: Xem log trực tiếp thời gian thực, có nút Copy, Select All, Clear.
  - **Restart Server**: Dừng hoàn toàn server và bật lại với PID mới.
  - **Kill Server**: Dừng khẩn cấp toàn bộ tiến trình.
  - **Exit**: Dọn dẹp tiến trình và thoát hẳn launcher.
- **Single-Instance Mutex**: Đảm bảo không bị mở trùng lặp nhiều launcher cùng lúc.
