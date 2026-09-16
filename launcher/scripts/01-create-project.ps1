<#
.SYNOPSIS
    01-create-project.ps1 - Khởi tạo dự án WinForms mới bằng dotnet new vào thư mục tạm.
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectName,

    [Parameter(Mandatory = $true)]
    [string]$TempDir
)

$ErrorActionPreference = "Stop"

Write-Host " [Bước 1/4] Khởi tạo dự án mới bằng dotnet new winforms..." -ForegroundColor Cyan

if (Test-Path $TempDir) {
    Write-Host "  -> Dọn dẹp thư mục tạm cũ: $TempDir" -ForegroundColor DarkGray
    Remove-Item -Path $TempDir -Recurse -Force -ErrorAction SilentlyContinue
}

New-Item -ItemType Directory -Path $TempDir -Force | Out-Null

Write-Host "  -> Đang chạy: dotnet new winforms -n `"$ProjectName`" -o `"$TempDir`"" -ForegroundColor DarkGray
dotnet new winforms -n "$ProjectName" -o "$TempDir" --framework net8.0

if ($LASTEXITCODE -ne 0) {
    Write-Error "Lệnh dotnet new thất bại với mã lỗi $LASTEXITCODE"
    exit $LASTEXITCODE
}

# Xóa các file Form1 mặc định do dotnet new sinh ra để tránh xung đột
$defaultFiles = @("Form1.cs", "Form1.Designer.cs", "Form1.resx", "Program.cs")
foreach ($f in $defaultFiles) {
    $targetPath = Join-Path $TempDir $f
    if (Test-Path $targetPath) {
        Remove-Item -Path $targetPath -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "  -> Khởi tạo dự án thành công tại: $TempDir" -ForegroundColor Green
exit 0
