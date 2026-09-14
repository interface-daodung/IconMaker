using System;
using System.Drawing;
using System.Windows.Forms;

namespace IconMakerLauncher;

sealed class ServerLogForm : Form
{
    private readonly RichTextBox _txtLog;
    private bool _reallyClose;
    private const int MaxLogChars = 200_000;

    public ServerLogForm()
    {
        Text = AppConfig.LogWindowTitle;
        Width = 900;
        Height = 600;
        StartPosition = FormStartPosition.CenterScreen;
        ShowInTaskbar = true;
        MinimumSize = new Size(600, 400);
        BackColor = Color.FromArgb(12, 12, 12);

        Icon = LoadIcon();

        _txtLog = new RichTextBox
        {
            ReadOnly = true,
            DetectUrls = false,
            WordWrap = true,
            ScrollBars = RichTextBoxScrollBars.Vertical,
            BorderStyle = BorderStyle.None,
            Dock = DockStyle.Fill,
            Font = new Font("Consolas", 9.5f),
            BackColor = Color.FromArgb(12, 12, 12),
            ForeColor = Color.White,
        };

        var ctx = new ContextMenuStrip();
        ctx.Items.Add("Copy", null, (_, __) => { if (!string.IsNullOrEmpty(_txtLog.SelectedText)) Clipboard.SetText(_txtLog.SelectedText); });
        ctx.Items.Add("Select All", null, (_, __) => _txtLog.SelectAll());
        ctx.Items.Add(new ToolStripSeparator());
        ctx.Items.Add("Clear", null, (_, __) => _txtLog.Clear());
        _txtLog.ContextMenuStrip = ctx;

        Controls.Add(_txtLog);
        FormClosing += OnFormClosing;
    }

    private static Icon LoadIcon()
    {
        try
        {
            var asm = typeof(ServerLogForm).Assembly;
            foreach (var n in asm.GetManifestResourceNames())
                if (n.EndsWith("icon.ico", StringComparison.OrdinalIgnoreCase))
                    using (var s = asm.GetManifestResourceStream(n))
                        if (s != null) return new Icon(s);
        }
        catch { }
        try
        {
            var candidates = new[]
            {
                System.IO.Path.Combine(AppContext.BaseDirectory, AppConfig.IconRelativePath),
                System.IO.Path.Combine(AppContext.BaseDirectory, "icon.ico"),
            };
            foreach (var p in candidates)
                if (System.IO.File.Exists(p)) return new Icon(p);
        }
        catch { }
        return SystemIcons.Application;
    }

    private void OnFormClosing(object? sender, FormClosingEventArgs e)
    {
        if (!_reallyClose && e.CloseReason == CloseReason.UserClosing)
        {
            e.Cancel = true;
            Hide();
        }
    }

    public void AllowClose() => _reallyClose = true;

    public void AppendLog(string line)
    {
        if (IsDisposed) return;
        if (InvokeRequired)
        {
            BeginInvoke(new Action<string>(AppendLog), line);
            return;
        }

        if (_txtLog.TextLength > MaxLogChars)
        {
            _txtLog.Select(0, _txtLog.TextLength - MaxLogChars / 2);
            _txtLog.SelectedText = string.Empty;
        }

        _txtLog.SelectionStart = _txtLog.TextLength;
        _txtLog.SelectionLength = 0;
        _txtLog.SelectionColor = Color.White;
        _txtLog.AppendText(line + Environment.NewLine);
        _txtLog.SelectionStart = _txtLog.TextLength;
        _txtLog.ScrollToCaret();
    }
}
