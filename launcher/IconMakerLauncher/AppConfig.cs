namespace IconMakerLauncher;

/// <summary>
/// FILE DUY NHẤT CẦN SỬA KHI TẠO APP LAUNCHER MỚI
/// Copy cả thư mục IconMakerLauncher → TenAppMoi (hoặc chạy
/// launcher/new-launcher.ps1), sửa các giá trị bên dưới,
/// thay icon ở Assets/icon.ico, rồi dotnet build/publish.
/// Logic tray/menu/log/hide không cần đụng.
///
/// Quy ước riêng của khung này:
/// - Port = 0 → bỏ qua mọi kiểm tra cổng (dùng cho app GUI như
///   IconMaker, vốn không mở cổng TCP nào).
/// - ProjectDir = "" → tự dò thư mục app chứa src/main.py đi ngược
///   từ thư mục exe (khi đóng gói chỉ cần đặt exe cạnh app).
/// </summary>
static class AppConfig
{
    // ===== App identity =====
    public const string AppName = "IconMakerLauncher";               // AssemblyName, RootNamespace, Mutex
    public const string DisplayName = "IconMaker";                    // Tooltip tray, balloon title
    public const string MutexName = "IconMakerLauncher_SingleInstance";
    public const string Description = "IconMaker tray launcher - chạy GUI pythonw, xem log, restart/kill từ tray";

    // ===== Server (ở đây là GUI pythonw src/main.py) =====
    public const string ProjectDir = "";                             // rỗng = tự dò thư mục chứa src/main.py
    public const int Port = 0;                                       // 0 = không kiểm tra cổng (app GUI)
    public const string HostUrl = "";                                // không dùng cho app GUI

    // Lệnh chạy app (hidden, không hiện CMD; ưu tiên bản không console)
    public const string CommandFile = "pythonw";
    public const string CommandArgs = "src/main.py";
    public const string CommandLog = "pythonw src/main.py";          // hiện trong log

    // Fallback khi pythonw không tìm thấy (tự dò pyw/py/python)
    public const string FallbackFile = "cmd.exe";
    public const string FallbackArgs = "/c python src/main.py";

    // ===== UI =====
    public const string TrayTooltip = "IconMaker";
    public const string LogWindowTitle = "IconMaker - Launcher Log";

    // Icon nhúng + exe icon
    public const string IconRelativePath = "Assets/icon.ico";

    // ===== Messages (sửa ở đây thay vì rải rác nhiều file) =====
    public const string MsgAlreadyRunning = "IconMakerLauncher đã đang chạy (kiểm tra tray icon).";
    public const string MsgNotFoundDir = "Không tìm thấy thư mục dự án";
    public const string MsgPythonNotFound = "Không tìm thấy Python. Hãy cài Python 3.13 hoặc đặt biến môi trường ICONMAKER_PYTHON.";

    // Balloon lúc khởi động
    public const string BalloonTitle = "IconMaker";
    public const string BalloonText = "IconMaker đang chạy.\nNhấn vào tray → Open Log để xem nhật ký. Đóng cửa sổ log sẽ ẩn, không tắt app.";

    // Menu labels
    public const string MenuOpenLog = "Open Log";
    public const string MenuHideLog = "Hide Log";
    public const string MenuRestart = "Restart App";
    public const string MenuKill = "Kill App";
    public const string MenuExit = "Exit";
    public const string ConfirmKillTitle = "IconMakerLauncher";
    public const string ConfirmKillText = "Kill app?";
    public const string ConfirmRestartTitle = "IconMakerLauncher";
    public const string ConfirmRestartText = "App đã dừng. Khởi động lại?";

    // Port busy (chỉ dùng khi Port > 0, tức launcher cho server)
    public static string PortBusyLine1 => $"[Launcher] Cổng {Port} đã có tiến trình khác đang lắng nghe (có thể server cũ chưa tắt).";
    public static string PortBusyLine2 => $"[Launcher] Bỏ qua khởi động mới — hãy mở {HostUrl} hoặc Tray → Restart Server để khởi động lại.";
    public static string PortBusyLine3 => $"[Launcher] Nếu cần kill tiến trình cũ: netstat -ano | findstr {Port} rồi taskkill /PID <PID> /F";
    public const string PortStillBusy = "Cổng vẫn bận sau kill — thử tìm PID giữ cổng để kill...";
    public static string PortHolderLog(int pid) => $"[Launcher] taskkill /PID {pid} /F (holder {Port})";

    // Server lifecycle
    public static string StartedLog(int pid, string dir) => $"[Launcher] Started PID={pid} dir={dir}";
    public static string CommandLogLine => $"[Launcher] Command: {CommandLog} (hidden, no CMD window)";
    public static string KillingLog(int pid) => $"[Launcher] Killing PID {pid} ...";
    public static string ServerExitedLog(int code) => $"[Launcher] Server exited (code {code})";
    public static string StartFailedLog(string ex) => $"[Launcher] Start failed: {ex}";

    // OnServerExited
    public static string BalloonPortBusy => $"Cổng {Port} đang bận — server cũ vẫn chạy. Mở {HostUrl} hoặc Tray → Restart Server.";
    public static string BalloonExited(int code) => $"App đã thoát (mã {code}). Vào Tray → Restart App để chạy lại.";
}
