using System;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Windows.Forms;

namespace IconMakerLauncher;

sealed class ServerProcess : IDisposable
{
    private Process? _process;
    private readonly string _workingDirectory;
    private readonly string _commandFile;

    public event Action<string>? LogReceived;
    public event Action<int>? Exited;

    public ServerProcess(string? workingDirectory = null)
    {
        _workingDirectory = workingDirectory ?? ResolveWorkingDirectory();
        _commandFile = ResolveCommandFile();
    }

    // Thư mục app: AppConfig.ProjectDir nếu tồn tại, ngược lại đi ngược
    // từ thư mục exe tìm src/main.py (đặt exe cạnh app là chạy).
    private static string ResolveWorkingDirectory()
    {
        if (!string.IsNullOrWhiteSpace(AppConfig.ProjectDir) && Directory.Exists(AppConfig.ProjectDir))
            return AppConfig.ProjectDir;

        var appRoot = FindAppRoot();
        if (appRoot is not null)
            return appRoot;

        if (!string.IsNullOrWhiteSpace(AppConfig.ProjectDir))
        {
            var exeDir = AppContext.BaseDirectory;
            var candidate = Path.GetFullPath(Path.Combine(exeDir, "..", "..", "..", "..", Path.GetFileName(AppConfig.ProjectDir)));
            if (Directory.Exists(candidate))
                return candidate;
            return AppConfig.ProjectDir;
        }

        return AppContext.BaseDirectory;
    }

    private static string? FindAppRoot()
    {
        var dir = new DirectoryInfo(AppContext.BaseDirectory);
        while (dir is not null)
        {
            if (File.Exists(Path.Combine(dir.FullName, "src", "main.py")))
                return dir.FullName;
            dir = dir.Parent;
        }
        return null;
    }

    // Lệnh chạy: env ICONMAKER_PYTHON > AppConfig.CommandFile >
    // pythonw/pyw/py/python trong PATH (ưu tiên bản không console).
    private static string ResolveCommandFile()
    {
        var fromEnv = Environment.GetEnvironmentVariable("ICONMAKER_PYTHON");
        if (!string.IsNullOrWhiteSpace(fromEnv))
            return fromEnv;

        if (!string.IsNullOrWhiteSpace(AppConfig.CommandFile) && CommandExists(AppConfig.CommandFile))
            return AppConfig.CommandFile;

        foreach (var candidate in new[] { "pythonw", "pyw", "py", "python" })
        {
            if (CommandExists(candidate))
                return candidate;
        }

        return AppConfig.CommandFile;
    }

    private static bool CommandExists(string fileName)
    {
        try
        {
            var psi = new ProcessStartInfo(fileName, "--version")
            {
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true,
            };
            using var proc = Process.Start(psi);
            if (proc is null) return false;
            proc.WaitForExit(5000);
            return !proc.HasExited ? false : proc.ExitCode == 0;
        }
        catch (Exception)
        {
            return false;
        }
    }

    public bool IsRunning()
    {
        try { return _process != null && !_process.HasExited; }
        catch { return false; }
    }

    public int? Pid => IsRunning() ? _process!.Id : null;

    private static bool IsPortInUse(int port)
    {
        try
        {
            using var client = new System.Net.Sockets.TcpClient();
            var task = client.ConnectAsync("127.0.0.1", port);
            bool connected = task.Wait(500);
            return connected && client.Connected;
        }
        catch { return false; }
    }

    public void Start()
    {
        if (IsRunning()) return;

        // Port <= 0 → app GUI, bỏ qua mọi kiểm tra cổng.
        if (AppConfig.Port > 0 && IsPortInUse(AppConfig.Port))
        {
            LogReceived?.Invoke(AppConfig.PortBusyLine1);
            LogReceived?.Invoke(AppConfig.PortBusyLine2);
            LogReceived?.Invoke(AppConfig.PortBusyLine3);
            return;
        }

        if (!Directory.Exists(_workingDirectory))
        {
            MessageBox.Show(
                $"{AppConfig.MsgNotFoundDir}:\n{_workingDirectory}\n\nVui lòng sửa AppConfig.ProjectDir",
                AppConfig.AppName, MessageBoxButtons.OK, MessageBoxIcon.Error);
            return;
        }

        var psi = new ProcessStartInfo
        {
            FileName = _commandFile,
            Arguments = AppConfig.CommandArgs,
            WorkingDirectory = _workingDirectory,
            UseShellExecute = false,
            CreateNoWindow = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            RedirectStandardInput = false,
            StandardOutputEncoding = Encoding.UTF8,
            StandardErrorEncoding = Encoding.UTF8,
        };
        psi.Environment["PYTHONUTF8"] = "1";
        psi.Environment["PYTHONIOENCODING"] = "utf-8";

        try
        {
            _process = new Process { StartInfo = psi, EnableRaisingEvents = true };
            _process.OutputDataReceived += (s, e) => { if (e.Data != null) LogReceived?.Invoke(e.Data); };
            _process.ErrorDataReceived += (s, e) => { if (e.Data != null) LogReceived?.Invoke(e.Data); };
            _process.Exited += (s, e) =>
            {
                try { Exited?.Invoke(_process?.ExitCode ?? -1); } catch { }
                LogReceived?.Invoke(AppConfig.ServerExitedLog(_process?.ExitCode ?? -1));
            };

            if (!_process.Start())
                throw new InvalidOperationException("Process.Start returned false");

            _process.BeginOutputReadLine();
            _process.BeginErrorReadLine();

            LogReceived?.Invoke(AppConfig.StartedLog(_process.Id, _workingDirectory));
            LogReceived?.Invoke(AppConfig.CommandLogLine);
        }
        catch (System.ComponentModel.Win32Exception ex) when (ex.NativeErrorCode == 2)
        {
            if (string.IsNullOrWhiteSpace(FindPythonProbe()))
            {
                MessageBox.Show(AppConfig.MsgPythonNotFound, AppConfig.AppName,
                    MessageBoxButtons.OK, MessageBoxIcon.Error);
                LogReceived?.Invoke(AppConfig.StartFailedLog(AppConfig.MsgPythonNotFound));
                return;
            }
            LogReceived?.Invoke($"[Launcher] {_commandFile} not found ({ex.Message}), fallback to cmd /c ...");
            StartViaCmdFallback();
        }
        catch (Exception ex)
        {
            MessageBox.Show($"Không khởi động được app:\n{ex.Message}", AppConfig.AppName,
                MessageBoxButtons.OK, MessageBoxIcon.Error);
            LogReceived?.Invoke(AppConfig.StartFailedLog(ex.ToString()));
        }
    }

    private static string? FindPythonProbe()
    {
        foreach (var candidate in new[] { "pythonw", "pyw", "py", "python" })
        {
            if (CommandExists(candidate))
                return candidate;
        }
        return null;
    }

    private void StartViaCmdFallback()
    {
        var psi = new ProcessStartInfo
        {
            FileName = AppConfig.FallbackFile,
            Arguments = AppConfig.FallbackArgs,
            WorkingDirectory = _workingDirectory,
            UseShellExecute = false,
            CreateNoWindow = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            StandardOutputEncoding = Encoding.UTF8,
            StandardErrorEncoding = Encoding.UTF8,
        };
        psi.Environment["PYTHONUTF8"] = "1";
        psi.Environment["PYTHONIOENCODING"] = "utf-8";

        _process = new Process { StartInfo = psi, EnableRaisingEvents = true };
        _process.OutputDataReceived += (s, e) => { if (e.Data != null) LogReceived?.Invoke(e.Data); };
        _process.ErrorDataReceived += (s, e) => { if (e.Data != null) LogReceived?.Invoke(e.Data); };
        _process.Exited += (s, e) => { try { Exited?.Invoke(_process?.ExitCode ?? -1); } catch { } };

        _process.Start();
        _process.BeginOutputReadLine();
        _process.BeginErrorReadLine();
        LogReceived?.Invoke($"[Launcher] Fallback cmd started PID={_process.Id}");
    }

    public void Show() { /* no-op: log form handled by TrayAppContext */ }
    public void Hide() { /* no-op */ }

    public void Kill()
    {
        if (IsRunning())
        {
            try
            {
                int pid = _process!.Id;
                LogReceived?.Invoke(AppConfig.KillingLog(pid));
                var psi = new ProcessStartInfo
                {
                    FileName = "taskkill",
                    Arguments = $"/PID {pid} /T /F",
                    UseShellExecute = false,
                    CreateNoWindow = true,
                };
                using var tk = Process.Start(psi);
                tk?.WaitForExit(5000);
                _process.WaitForExit(3000);
                if (!_process.HasExited)
                    _process.Kill(entireProcessTree: true);
            }
            catch
            {
                try { _process?.Kill(entireProcessTree: true); } catch { }
            }
            finally
            {
                try { _process?.Dispose(); } catch { }
                _process = null;
            }
        }
        else
        {
            _process?.Dispose();
            _process = null;
        }

        // Chỉ dọn cổng khi launcher cấu hình Port > 0 (server).
        if (AppConfig.Port > 0 && IsPortInUse(AppConfig.Port))
        {
            try
            {
                LogReceived?.Invoke($"[Launcher] {AppConfig.PortStillBusy}");
                var pids = FindPidsByPort(AppConfig.Port);
                foreach (var pid in pids)
                {
                    LogReceived?.Invoke(AppConfig.PortHolderLog(pid));
                    var psi2 = new ProcessStartInfo
                    {
                        FileName = "taskkill",
                        Arguments = $"/PID {pid} /F",
                        UseShellExecute = false,
                        CreateNoWindow = true,
                    };
                    using var tk2 = Process.Start(psi2);
                    tk2?.WaitForExit(3000);
                }
                for (int i = 0; i < 10 && IsPortInUse(AppConfig.Port); i++)
                    System.Threading.Thread.Sleep(200);
            }
            catch (Exception ex)
            {
                LogReceived?.Invoke($"[Launcher] Kill port holder failed: {ex.Message}");
            }
        }
    }

    private static System.Collections.Generic.List<int> FindPidsByPort(int port)
    {
        var list = new System.Collections.Generic.List<int>();
        try
        {
            var psi = new ProcessStartInfo
            {
                FileName = "netstat",
                Arguments = "-ano",
                UseShellExecute = false,
                CreateNoWindow = true,
                RedirectStandardOutput = true,
                StandardOutputEncoding = Encoding.UTF8,
            };
            using var p = Process.Start(psi);
            if (p == null) return list;
            string output = p.StandardOutput.ReadToEnd();
            p.WaitForExit(2000);
            foreach (var line in output.Split('\n'))
            {
                if (!line.Contains($":{port}")) continue;
                if (!line.Contains("LISTENING")) continue;
                var parts = line.Trim().Split(new[] { ' ', '\t' }, StringSplitOptions.RemoveEmptyEntries);
                if (parts.Length > 0 && int.TryParse(parts[^1], out int pid))
                    list.Add(pid);
            }
        }
        catch { }
        return list;
    }

    public void Dispose()
    {
        _process?.Dispose();
    }
}
