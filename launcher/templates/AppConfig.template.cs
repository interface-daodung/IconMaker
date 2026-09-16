namespace __APP_NAME__;

/// <summary>
/// File cấu hình cho Tray Launcher được sinh tự động bởi build-launcher.ps1
/// Chạy lệnh "make run" tại thư mục server, theo dõi PID và kill chính xác.
/// </summary>
static class AppConfig
{
    // ===== App identity =====
    public const string AppName = "__APP_NAME__";
    public const string DisplayName = "__DISPLAY_NAME__";
    public const string MutexName = "__MUTEX_NAME__";
    public const string Description = "Tray Launcher cho __DISPLAY_NAME__ - chay make run an, xem log, quan ly PID";

    // ===== Server =====
    public const string ProjectDir = @"__PROJECT_DIR__";
    public const int Port = __PORT__;
    public const string HostUrl = "__HOST_URL__";

    // Lệnh chạy server
    public const string CommandFile = "__COMMAND_FILE__";
    public const string CommandArgs = "__COMMAND_ARGS__";
    public const string CommandLog = "__COMMAND_FILE__ __COMMAND_ARGS__";

    // Fallback khi không tìm thấy lệnh trực tiếp
    public const string FallbackFile = "__FALLBACK_FILE__";
    public const string FallbackArgs = "__FALLBACK_ARGS__";

    // ===== UI =====
    public const string TrayTooltip = "__DISPLAY_NAME__";
    public const string LogWindowTitle = "__DISPLAY_NAME__ - Server Log";

    // Icon nhúng
    public const string IconRelativePath = "Assets/icon.ico";

    // ===== Messages =====
    public const string MsgAlreadyRunning = "__DISPLAY_NAME__ da dang chay (kiem tra khay he thong - System Tray).";
    public const string MsgNotFoundDir = "Khong tim thay thu muc server:";

    // Menu labels
    public const string MenuOpenLog = "Open Log";
    public const string MenuHideLog = "Hide Log";
    public const string MenuRestart = "Restart Server";
    public const string MenuKill = "Kill Server";
    public const string MenuExit = "Exit";

    // Port & Process logs
    public static string PortBusyLine1 => $"[Launcher] Cong {Port} da co tien trinh khac dang lang nghe.";
    public static string PortBusyLine2 => $"[Launcher] Bo qua khoi dong moi - hay kiem tra lai hoac Tray -> Restart Server.";
    public static string PortBusyLine3 => $"[Launcher] Kill tien trinh giu cong: netstat -ano | findstr {Port} roi taskkill /PID <PID> /F";
    public const string PortStillBusy = "Cong van ban sau kill - dang tim PID giu cong de don dep...";
    public static string PortHolderLog(int pid) => $"[Launcher] taskkill /PID {pid} /F (port holder {Port})";

    // Lifecycle logs
    public static string StartedLog(int pid, string dir) => $"[Launcher] Started PID={pid} | WorkingDir={dir}";
    public static string CommandLogLine => $"[Launcher] Executing: {CommandLog} (hidden, tracking PID & child processes)";
    public static string KillingLog(int pid) => $"[Launcher] Terminating PID={pid} (killing entire process tree)...";
    public static string ServerExitedLog(int code) => $"[Launcher] Server exited with code {code}";
    public static string StartFailedLog(string ex) => $"[Launcher] Start failed: {ex}";

    // Balloon notifications
    public static string BalloonPortBusy => $"Cong {Port} dang ban. Mo log hoac Tray -> Restart Server.";
    public static string BalloonExited(int code) => $"May chu da dung (exit code {code}). Vao Tray -> Restart Server de bat lai.";
}
