<#
.SYNOPSIS
    04-cleanup-project.ps1 - Chuyen file .exe ve thu muc dich va xoa sach toan bo du an tam.
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

Write-Host " [Buoc 4/4] Luu file .exe dau ra va don dep du an..." -ForegroundColor Cyan

# Dam bao thu muc dich ton tai
if (-not (Test-Path $FinalOutDir)) {
    New-Item -ItemType Directory -Path $FinalOutDir -Force | Out-Null
}

$sourceExe = Join-Path $PublishOutDir "$ProjectName.exe"
$destExe = Join-Path $FinalOutDir "$ProjectName.exe"

if (-not (Test-Path $sourceExe)) {
    Write-Error "Khong tim thay file exe nguon tai: $sourceExe"
    exit 1
}

# Dong tien trinh cu neu dang chay de ghi de file exe thanh cong
$runningProcs = Get-Process -Name $ProjectName -ErrorAction SilentlyContinue
if ($runningProcs) {
    Write-Host "  -> Phat hien $ProjectName dang chay, dang dung de cap nhat file moi..." -ForegroundColor Yellow
    foreach ($p in $runningProcs) {
        try { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue } catch { }
    }
    Start-Sleep -Milliseconds 1000
}

# Sao chep file exe vao thu muc ket qua cuoi cung (thu lai toi da 3 lan neu file bi delay unlock)
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

Write-Host "  -> Da luu Launcher .exe vao: $destExe" -ForegroundColor Green

# Xoa bo thu muc publish tam
if (Test-Path $PublishOutDir) {
    Remove-Item -Path $PublishOutDir -Recurse -Force -ErrorAction SilentlyContinue
}

# Xoa bo hoan toan thu muc du an tam thoi (chi giu lai file exe dau ra)
Write-Host "  -> Dang xoa thu muc du an tam thoi: $TempDir" -ForegroundColor DarkGray
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
    Write-Host "  -> Da don dep sach se toan bo ma nguon tam, chi giu lai file exe." -ForegroundColor Green
} else {
    Write-Host "  -> Luu y: Chua xoa duoc hoan toan thu muc tam (co the file dang bi khoa boi tien trinh khac)." -ForegroundColor Yellow
}

exit 0
