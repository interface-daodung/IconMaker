using System.Diagnostics;

namespace IconMakerLauncher;

internal static class Program
{
    // Tim python theo thu tu: env ICONMAKER_PYTHON -> py launcher -> python trong PATH.
    private static string? FindPython()
    {
        var fromEnv = Environment.GetEnvironmentVariable("ICONMAKER_PYTHON");
        if (!string.IsNullOrWhiteSpace(fromEnv) && File.Exists(fromEnv))
            return fromEnv;

        if (RunAndCheck("py", "--version"))
            return "py";

        if (RunAndCheck("python", "--version"))
            return "python";

        return null;
    }

    private static bool RunAndCheck(string fileName, string args)
    {
        try
        {
            var psi = new ProcessStartInfo(fileName, args)
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

    // Duong dan den thu muc src cua app Python: di ngugc tu exe tim den folder chua "src/iconmaker".
    private static string? FindAppRoot()
    {
        var dir = new DirectoryInfo(AppContext.BaseDirectory);
        while (dir is not null)
        {
            var src = Path.Combine(dir.FullName, "src", "iconmaker", "gui.py");
            if (File.Exists(src)) return Path.Combine(dir.FullName, "src");
            dir = dir.Parent;
        }
        return null;
    }

    [STAThread]
    private static int Main()
    {
        var python = FindPython();
        var appSrc = FindAppRoot();

        if (python is null || appSrc is null)
        {
            MessageBox.Show(
                python is null
                    ? "Khong tim thay Python. Hay cai Python 3.13 hoac dat bien moi truong ICONMAKER_PYTHON."
                    : "Khong tim thay thu muc app (src/iconmaker/gui.py).",
                "IconMaker Launcher",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error);
            return 1;
        }

        var psi = new ProcessStartInfo(python, "-m iconmaker.gui")
        {
            WorkingDirectory = appSrc,
            UseShellExecute = false,
        };

        try
        {
            using var proc = Process.Start(psi);
            proc?.WaitForExit();
            return proc?.ExitCode ?? 1;
        }
        catch (Exception ex)
        {
            MessageBox.Show(
                $"Khong khoi dong duoc app:\n{ex.Message}",
                "IconMaker Launcher",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error);
            return 1;
        }
    }
}