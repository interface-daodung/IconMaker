using System;
using System.Diagnostics;
using System.Runtime.InteropServices;

namespace TrayLauncher;

/// <summary>
/// Quản lý Windows Job Object để đảm bảo khi dừng server hoặc thoát launcher,
/// toàn bộ cây tiến trình sinh ra từ "make run" (tiến trình con, cháu) đều bị kill triệt để 100%.
/// </summary>
sealed class JobObjectTracker : IDisposable
{
    private IntPtr _jobHandle;
    private bool _disposed;

    public JobObjectTracker(string? name = null)
    {
        _jobHandle = NativeMethods.CreateJobObject(IntPtr.Zero, name);
        if (_jobHandle == IntPtr.Zero)
            return;

        // Cấu hình cờ KILL_ON_JOB_CLOSE: khi handle đóng, toàn bộ process trong job tự động bị kill
        var info = new NativeMethods.JOBOBJECT_BASIC_LIMIT_INFORMATION
        {
            LimitFlags = NativeMethods.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        };

        var extendedInfo = new NativeMethods.JOBOBJECT_EXTENDED_LIMIT_INFORMATION
        {
            BasicLimitInformation = info
        };

        int length = Marshal.SizeOf(typeof(NativeMethods.JOBOBJECT_EXTENDED_LIMIT_INFORMATION));
        IntPtr extendedInfoPtr = Marshal.AllocHGlobal(length);
        try
        {
            Marshal.StructureToPtr(extendedInfo, extendedInfoPtr, false);
            NativeMethods.SetInformationJobObject(
                _jobHandle,
                NativeMethods.JobObjectExtendedLimitInformation,
                extendedInfoPtr,
                (uint)length);
        }
        finally
        {
            Marshal.FreeHGlobal(extendedInfoPtr);
        }
    }

    /// <summary>
    /// Gán một Process (ví dụ: make.exe hoặc cmd.exe) vào Job Object.
    /// Mọi tiến trình con được spawn bởi process này sẽ tự động kế thừa và nằm trong Job Object.
    /// </summary>
    public bool AssignProcess(Process process)
    {
        if (_jobHandle == IntPtr.Zero || process.HasExited)
            return false;

        try
        {
            return NativeMethods.AssignProcessToJobObject(_jobHandle, process.Handle);
        }
        catch
        {
            return false;
        }
    }

    /// <summary>
    /// Chủ động terminate toàn bộ tiến trình trong Job Object
    /// </summary>
    public void TerminateAll(uint exitCode = 1)
    {
        if (_jobHandle != IntPtr.Zero)
        {
            try
            {
                NativeMethods.TerminateJobObject(_jobHandle, exitCode);
            }
            catch { }
        }
    }

    public void Dispose()
    {
        if (!_disposed)
        {
            if (_jobHandle != IntPtr.Zero)
            {
                NativeMethods.CloseHandle(_jobHandle);
                _jobHandle = IntPtr.Zero;
            }
            _disposed = true;
        }
    }
}
