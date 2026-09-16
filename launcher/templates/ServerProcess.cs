using System;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Windows.Forms;

namespace __APP_NAME__;

sealed class ServerProcess : IDisposable
{
    private Process? _process;
    private int? _trackedPid;
    private JobObjectTracker? _jobTracker;
    private readonly string _workingDirectory;
    private readonly string _pidFilePath;

    public event Action<string>? LogReceived;
    public event Action<int>? Exited;

    public ServerProcess(string? workingDirectory = null)
    {
        _workingDirectory = workingDirectory ?? AppConfig.ProjectDir;

        if (!Directory.Exists(_workingDirectory))
        {
            var exeDir = AppContext.BaseDirectory;
            var candidate = Path.GetFullPath(Path.Combine(exeDir, "..", "..", "..", "..", Path.GetFileName(AppConfig.ProjectDir)));
            if (Directory.Exists(candidate))
                _workingDirectory = candidate;
        }

        _pidFilePath = Path.Combine(_workingDirectory, ".launcher.pid");
    }

    public bool IsRunning()
    {
        try { return _process != null && !_process.HasExited; }
        catch { return false; }
    }

    public int? Pid => _trackedPid ?? (IsRunning() ? _process!.Id : null);

    private static bool IsPortInUse(int port)
    {
        if (port <= 0) return false;
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

        // Cleanup tiến trình cũ còn sót lại từ PID file (nếu có)
        CleanUpPreviousPid();

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
                $"{AppConfig.MsgNotFoundDir}:\n{_workingDirectory}",
                AppConfig.AppName, MessageBoxButtons.OK, MessageBoxIcon.Error);
            return;
        }

        // Khởi tạo Windows Job Object để quản lý toàn bộ vòng đời cây tiến trình của make run
        _jobTracker?.Dispose();
        _jobTracker = new JobObjectTracker($"{AppConfig.AppName}_Job_{Guid.NewGuid():N}");

        var psi = new ProcessStartInfo
        {
            FileName = AppConfig.CommandFile,
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
                int exitCode = -1;
                try { exitCode = _process?.ExitCode ?? -1; } catch { }
                DeletePidFile();
                try { Exited?.Invoke(exitCode); } catch { }
                LogReceived?.Invoke(AppConfig.ServerExitedLog(exitCode));
            };

            if (!_process.Start())
                throw new InvalidOperationException("Process.Start returned false");

            _trackedPid = _process.Id;
            SavePidToFile(_trackedPid.Value);

            // Gán process vào Job Object để Windows tự động kill toàn bộ child processes khi job kết thúc
            bool assigned = _jobTracker.AssignProcess(_process);

            _process.BeginOutputReadLine();
            _process.BeginErrorReadLine();

            LogReceived?.Invoke(AppConfig.StartedLog(_trackedPid.Value, _workingDirectory));
            LogReceived?.Invoke($"[Launcher] PID {_trackedPid.Value} saved. Windows Job Object tracking: {(assigned ? "Active" : "Not supported")}");
            LogReceived?.Invoke(AppConfig.CommandLogLine);
        }
        catch (System.ComponentModel.Win32Exception ex) when (ex.NativeErrorCode == 2)
        {
            LogReceived?.Invoke($"[Launcher] Lệnh '{AppConfig.CommandFile}' không tìm thấy trực tiếp, chuyển sang chạy qua cmd.exe /c...");
            StartViaCmdFallback();
        }
        catch (Exception ex)
        {
            MessageBox.Show($"Không khởi động được server:\n{ex.Message}", AppConfig.AppName,
                MessageBoxButtons.OK, MessageBoxIcon.Error);
            LogReceived?.Invoke(AppConfig.StartFailedLog(ex.ToString()));
        }
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

        try
        {
            _process = new Process { StartInfo = psi, EnableRaisingEvents = true };
            _process.OutputDataReceived += (s, e) => { if (e.Data != null) LogReceived?.Invoke(e.Data); };
            _process.ErrorDataReceived += (s, e) => { if (e.Data != null) LogReceived?.Invoke(e.Data); };
            _process.Exited += (s, e) =>
            {
                int exitCode = -1;
                try { exitCode = _process?.ExitCode ?? -1; } catch { }
                DeletePidFile();
                try { Exited?.Invoke(exitCode); } catch { }
                LogReceived?.Invoke(AppConfig.ServerExitedLog(exitCode));
            };

            _process.Start();
            _trackedPid = _process.Id;
            SavePidToFile(_trackedPid.Value);

            bool assigned = _jobTracker?.AssignProcess(_process) ?? false;

            _process.BeginOutputReadLine();
            _process.BeginErrorReadLine();
            LogReceived?.Invoke($"[Launcher] Fallback cmd started PID={_trackedPid.Value} (JobObject: {(assigned ? "Active" : "Off")})");
        }
        catch (Exception ex)
        {
            LogReceived?.Invoke(AppConfig.StartFailedLog(ex.ToString()));
        }
    }

    public void Kill()
    {
        int? targetPid = _trackedPid ?? (_process != null && !_process.HasExited ? _process.Id : null);

        if (targetPid.HasValue)
        {
            int pid = targetPid.Value;
            LogReceived?.Invoke(AppConfig.KillingLog(pid));

            // 1. Tiêu diệt triệt để bằng taskkill cây tiến trình (/T) cưỡng chế (/F)
            try
            {
                var psi = new ProcessStartInfo
                {
                    FileName = "taskkill",
                    Arguments = $"/PID {pid} /T /F",
                    UseShellExecute = false,
                    CreateNoWindow = true,
                };
                using var tk = Process.Start(psi);
                tk?.WaitForExit(5000);
            }
            catch (Exception ex)
            {
                LogReceived?.Invoke($"[Launcher] taskkill /T warning: {ex.Message}");
            }

            // 2. Kill qua .NET Process API (entireProcessTree)
            try
            {
                if (_process != null && !_process.HasExited)
                {
                    _process.Kill(entireProcessTree: true);
                    _process.WaitForExit(3000);
                }
            }
            catch { }

            // 3. Đóng và tiêu diệt Job Object (hệ điều hành Windows sẽ kill toàn bộ con/cháu còn sót)
            try
            {
                _jobTracker?.TerminateAll();
                _jobTracker?.Dispose();
                _jobTracker = null;
            }
            catch { }

            _process?.Dispose();
            _process = null;
            _trackedPid = null;
            DeletePidFile();
            LogReceived?.Invoke($"[Launcher] Đã dừng toàn bộ tiến trình PID={pid} thành công.");
        }
        else
        {
            _jobTracker?.Dispose();
            _jobTracker = null;
            _process?.Dispose();
            _process = null;
        }

        // 4. Nếu có port và vẫn bận, tìm và tiêu diệt PID đang chiếm cổng
        if (AppConfig.Port > 0 && IsPortInUse(AppConfig.Port))
        {
            try
            {
                LogReceived?.Invoke($"[Launcher] {AppConfig.PortStillBusy}");
                var pids = FindPidsByPort(AppConfig.Port);
                foreach (var p in pids)
                {
                    LogReceived?.Invoke(AppConfig.PortHolderLog(p));
                    var psi2 = new ProcessStartInfo
                    {
                        FileName = "taskkill",
                        Arguments = $"/PID {p} /F",
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

    private void SavePidToFile(int pid)
    {
        try
        {
            File.WriteAllText(_pidFilePath, pid.ToString());
        }
        catch { }
    }

    private void DeletePidFile()
    {
        try
        {
            if (File.Exists(_pidFilePath))
                File.Delete(_pidFilePath);
        }
        catch { }
    }

    private void CleanUpPreviousPid()
    {
        try
        {
            if (File.Exists(_pidFilePath))
            {
                string text = File.ReadAllText(_pidFilePath).Trim();
                if (int.TryParse(text, out int oldPid))
                {
                    try
                    {
                        var oldProc = Process.GetProcessById(oldPid);
                        if (oldProc != null && !oldProc.HasExited)
                        {
                            LogReceived?.Invoke($"[Launcher] Phát hiện tiến trình cũ PID={oldPid} từ lần chạy trước, đang dọn dẹp...");
                            var psi = new ProcessStartInfo
                            {
                                FileName = "taskkill",
                                Arguments = $"/PID {oldPid} /T /F",
                                UseShellExecute = false,
                                CreateNoWindow = true,
                            };
                            using var tk = Process.Start(psi);
                            tk?.WaitForExit(3000);
                        }
                    }
                    catch { }
                }
                DeletePidFile();
            }
        }
        catch { }
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
        Kill();
    }
}
