using System;
using System.Drawing;
using System.IO;
using System.Windows.Forms;

namespace __APP_NAME__;

sealed class TrayAppContext : ApplicationContext
{
    private readonly NotifyIcon _tray;
    private readonly ServerProcess _server;
    private ServerLogForm? _logForm;
    private readonly object _logLock = new();
    private readonly System.Collections.Generic.List<string> _logBuffer = new();
    private const int BufferMax = 2000;

    private volatile bool _isIntentionalStop = false;

    public TrayAppContext()
    {
        _server = new ServerProcess();
        _server.LogReceived += OnLogReceived;
        _server.Exited += OnServerExited;
        _server.Start();

        var menu = new ContextMenuStrip();

        var toggleItem = new ToolStripMenuItem(AppConfig.MenuOpenLog, null, (_, __) => ToggleLog());
        var restartItem = new ToolStripMenuItem(AppConfig.MenuRestart, null, (_, __) =>
        {
            _isIntentionalStop = true;
            AppendSystem("Restarting server...");
            _server.Kill();
            _isIntentionalStop = false;
            _server.Start();
            ShowLog();
        });
        var killItem = new ToolStripMenuItem(AppConfig.MenuKill, null, (_, __) =>
        {
            _isIntentionalStop = true;
            _server.Kill();
            AppendSystem("Server đã dừng theo yêu cầu của người dùng.");
        });
        var exitItem = new ToolStripMenuItem(AppConfig.MenuExit, null, (_, __) =>
        {
            _isIntentionalStop = true;
            ExitApplication();
        });

        menu.Items.Add(toggleItem);
        menu.Items.Add(new ToolStripSeparator());
        menu.Items.Add(restartItem);
        menu.Items.Add(killItem);
        menu.Items.Add(new ToolStripSeparator());
        menu.Items.Add(exitItem);

        menu.Opening += (_, __) =>
        {
            bool visible = _logForm != null && !_logForm.IsDisposed && _logForm.Visible;
            toggleItem.Text = visible ? AppConfig.MenuHideLog : AppConfig.MenuOpenLog;
        };

        Icon icon;
        string exeDir = AppContext.BaseDirectory;
        string[] candidates =
        {
            Path.Combine(exeDir, AppConfig.IconRelativePath),
            Path.Combine(exeDir, "icon.ico"),
            Path.Combine(exeDir, "..", "..", "..", AppConfig.IconRelativePath),
        };
        icon = LoadEmbeddedIcon() ?? LoadIcon(candidates) ?? SystemIcons.Application;

        _tray = new NotifyIcon
        {
            Icon = icon,
            ContextMenuStrip = menu,
            Visible = true,
            Text = AppConfig.TrayTooltip.Length > 63 ? AppConfig.TrayTooltip.Substring(0, 63) : AppConfig.TrayTooltip
        };

        _tray.DoubleClick += (_, __) => ShowLog();
        _tray.MouseClick += (_, e) =>
        {
            if (e.Button == MouseButtons.Left)
                ShowLog();
        };
    }

    private static Icon? LoadEmbeddedIcon()
    {
        try
        {
            var asm = typeof(TrayAppContext).Assembly;
            foreach (var n in asm.GetManifestResourceNames())
                if (n.EndsWith("icon.ico", StringComparison.OrdinalIgnoreCase))
                    using (var s = asm.GetManifestResourceStream(n))
                        if (s != null) return new Icon(s);
        }
        catch { }
        return null;
    }

    private static Icon? LoadIcon(string[] candidates)
    {
        foreach (var p in candidates)
        {
            try { if (File.Exists(p)) return new Icon(p); } catch { }
        }
        return null;
    }

    private void EnsureLogForm()
    {
        if (_logForm == null || _logForm.IsDisposed)
        {
            _logForm = new ServerLogForm();
            _logForm.FormClosed += (_, __) => _logForm = null;
            string[] snapshot;
            lock (_logLock)
            {
                snapshot = _logBuffer.ToArray();
            }
            foreach (var line in snapshot)
                _logForm.AppendLog(line);
        }
    }

    private void ToggleLog()
    {
        bool visible = _logForm != null && !_logForm.IsDisposed && _logForm.Visible;
        if (visible) HideLog();
        else ShowLog();
    }

    private void ShowLog()
    {
        EnsureLogForm();
        if (!_logForm!.Visible)
            _logForm.Show();
        _logForm.WindowState = FormWindowState.Normal;
        _logForm.BringToFront();
        _logForm.Activate();
    }

    private void HideLog() => _logForm?.Hide();

    private void OnLogReceived(string line)
    {
        lock (_logLock)
        {
            _logBuffer.Add(line);
            if (_logBuffer.Count > BufferMax)
                _logBuffer.RemoveAt(0);
        }

        if (_logForm != null && !_logForm.IsDisposed)
            _logForm.AppendLog(line);
    }

    private void AppendSystem(string msg) => OnLogReceived($"[Launcher] {msg}");

    private void OnServerExited(int code)
    {
        // Nếu người dùng chủ động bấm dừng/restart/thoát thì không thông báo
        if (_isIntentionalStop) return;

        // Chỉ thông báo khi có bất thường: xung đột cổng hoặc crash / bị kill bởi app khác
        bool isPortConflict = false;
        try
        {
            string[] snapshot;
            lock (_logLock)
            {
                snapshot = _logBuffer.ToArray();
            }
            foreach (var l in snapshot)
                if (l.Contains("normally permitted") || l.Contains("address already in use") || l.Contains("WinError 10048"))
                { isPortConflict = true; break; }
        }
        catch { }

        _tray.BalloonTipTitle = AppConfig.DisplayName;
        if (isPortConflict)
        {
            _tray.BalloonTipText = AppConfig.BalloonPortBusy;
            _tray.ShowBalloonTip(4000);
        }
        else if (code != 0)
        {
            _tray.BalloonTipText = $"Máy chủ bị dừng bất thường (mã {code}) hoặc bị tắt bởi ứng dụng khác!";
            _tray.ShowBalloonTip(4000);
        }
    }

    private void ExitApplication()
    {
        _tray.Visible = false;
        _logForm?.AllowClose();
        _logForm?.Close();
        _server.Kill();
        _tray.Dispose();
        ExitThread();
    }

    protected override void Dispose(bool disposing)
    {
        if (disposing)
        {
            _tray.Dispose();
            _server.Dispose();
            _logForm?.Dispose();
        }
        base.Dispose(disposing);
    }
}
