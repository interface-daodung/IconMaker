using System;
using System.Threading;
using System.Windows.Forms;

namespace __APP_NAME__;

static class Program
{
    private static Mutex? _mutex;

    [STAThread]
    static void Main()
    {
        _mutex = new Mutex(true, AppConfig.MutexName, out bool createdNew);
        if (!createdNew)
        {
            MessageBox.Show(
                AppConfig.MsgAlreadyRunning,
                AppConfig.AppName,
                MessageBoxButtons.OK,
                MessageBoxIcon.Information);
            return;
        }

        ApplicationConfiguration.Initialize();
        Application.Run(new TrayAppContext());

        _mutex.ReleaseMutex();
    }
}
