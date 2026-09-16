<#
.SYNOPSIS
    04-cleanup-project.ps1 - Chuyển file .exe về thư mục đích và xóa sạch toàn bộ dự án tạm.
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectName,

    [Parameter(Mandatory = $true)]
    [string]$TempDir,

    [Parameter(Mandatory = $true)]
    [string]$PublishOutDir,

    [Parameter(Mandatory = $true)]
    [string]$FinalOutDir
)

$ErrorActionPreference = "Stop"

Write-Host " [Bước 4/4] Lưu file .exe đầu ra và dọn dẹp dự án..." -ForegroundColor Cyan

# Đảm bảo thư mục đích tồn tại
if (-not (Test-Path $FinalOutDir)) {
    New-Item -ItemType Directory -Path $FinalOutDir -Force | Out-Null
}

$sourceExe = Join-Path $PublishOutDir "$ProjectName.exe"
$destExe = Join-Path $FinalOutDir "$ProjectName.exe"

if (-not (Test-Path $sourceExe)) {
    Write-Error "Không tìm thấy file exe nguồn tại: $sourceExe"
    exit 1
}

# Đóng tiến trình cũ nếu đang chạy để ghi đè file exe thành công
$runningProcs = Get-Process -Name $ProjectName -ErrorAction SilentlyContinue
if ($runningProcs) {
    Write-Host "  -> Phát hiện $ProjectName đang chạy, đang dừng để cập nhật file mới..." -ForegroundColor Yellow
    foreach ($p in $runningProcs) {
        try { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue } catch { }
    }
    Start-Sleep -Milliseconds 1000
}

# Sao chép file exe vào thư mục kết quả cuối cùng (thử lại tối đa 3 lần nếu file bị delay unlock)
$copied = $false
for ($i = 0; $i -lt 3; $i++) {
    try {
        Copy-Item -Path $sourceExe -Destination $destExe -Force -ErrorAction Stop
        $copied = $true
        break
    } catch {
        Start-Sleep -Milliseconds 800
    }
}

if (-not $copied) {
    Copy-Item -Path $sourceExe -Destination $destExe -Force
}

Write-Host "  -> Đã lưu Launcher .exe vào: $destExe" -ForegroundColor Green

# Xóa bỏ thư mục publish tạm
if (Test-Path $PublishOutDir) {
    Remove-Item -Path $PublishOutDir -Recurse -Force -ErrorAction SilentlyContinue
}

# Xóa bỏ hoàn toàn thư mục dự án tạm thời (chỉ giữ lại file exe đầu ra)
Write-Host "  -> Đang xóa thư mục dự án tạm thời: $TempDir" -ForegroundColor DarkGray
for ($i = 0; $i -lt 3; $i++) {
    try {
        if (Test-Path $TempDir) {
            Remove-Item -Path $TempDir -Recurse -Force -ErrorAction Stop
        }
        break
    } catch {
        Start-Sleep -Milliseconds 500
    }
}

if (-not (Test-Path $TempDir)) {
    Write-Host "  -> Đã dọn dẹp sạch sẽ toàn bộ mã nguồn tạm, chỉ giữ lại file exe." -ForegroundColor Green
} else {
    Write-Host "  -> Lưu ý: Chưa xóa được hoàn toàn thư mục tạm (có thể file đang bị khóa bởi tiến trình khác)." -ForegroundColor Yellow
}

exit 0
