using System;
using System.Drawing;
using System.IO;
using System.Windows.Forms;

namespace IconMakerLauncher;

sealed class TrayAppContext : ApplicationContext
{
    private readonly NotifyIcon _tray;
    private readonly ServerProcess _server;
    private ServerLogForm? _logForm;
    private readonly System.Collections.Generic.List<string> _logBuffer = new();
    private const int BufferMax = 2000;

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
            AppendSystem("Restarting server...");
            _server.Kill();
            _server.Start();
            ShowLog();
        });
        var killItem = new ToolStripMenuItem(AppConfig.MenuKill, null, (_, __) =>
        {
            if (MessageBox.Show(AppConfig.ConfirmKillText, AppConfig.ConfirmKillTitle, MessageBoxButtons.YesNo, MessageBoxIcon.Warning) == DialogResult.Yes)
            {
                _server.Kill();
                AppendSystem("Server killed by user");
            }
        });
        var exitItem = new ToolStripMenuItem(AppConfig.MenuExit, null, (_, __) => ExitApplication());

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
        icon = LoadIcon(candidates) ?? SystemIcons.Application;

        _tray = new NotifyIcon
        {
            Icon = icon,
            ContextMenuStrip = menu,
            Visible = true,
            Text = AppConfig.TrayTooltip
        };

        _tray.DoubleClick += (_, __) => ShowLog();
        _tray.MouseClick += (_, e) =>
        {
            if (e.Button == MouseButtons.Left)
                ShowLog();
        };

        _tray.BalloonTipTitle = AppConfig.BalloonTitle;
        _tray.BalloonTipText = AppConfig.BalloonText;
        _tray.ShowBalloonTip(3000);
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
            foreach (var line in _logBuffer)
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
        if (_server.IsRunning() == false)
        {
            var r = MessageBox.Show(
                AppConfig.ConfirmRestartText,
                AppConfig.ConfirmRestartTitle, MessageBoxButtons.YesNo, MessageBoxIcon.Question);
            if (r == DialogResult.Yes)
                _server.Start();
            else return;
        }

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
        _logBuffer.Add(line);
        if (_logBuffer.Count > BufferMax)
            _logBuffer.RemoveAt(0);

        if (_logForm != null && !_logForm.IsDisposed && _logForm.Visible)
            _logForm.AppendLog(line);
        else if (_logForm != null && !_logForm.IsDisposed)
            _logForm.AppendLog(line);
    }

    private void AppendSystem(string msg) => OnLogReceived($"[Launcher] {msg}");

    private void OnServerExited(int code)
    {
        if (code == 0) return;
        bool isPortConflict = false;
        try
        {
            foreach (var l in _logBuffer)
                if (l.Contains("normally permitted") || l.Contains("address already in use") || l.Contains("WinError 10048"))
                { isPortConflict = true; break; }
        }
        catch { }
        _tray.BalloonTipTitle = AppConfig.DisplayName;
        if (isPortConflict && AppConfig.Port > 0)
            _tray.BalloonTipText = AppConfig.BalloonPortBusy;
        else
            _tray.BalloonTipText = AppConfig.BalloonExited(code);
        _tray.ShowBalloonTip(4000);
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
