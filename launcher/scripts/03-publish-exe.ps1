<#
.SYNOPSIS
    03-publish-exe.ps1 - Biên dịch và đóng gói Launcher thành file .exe duy nhất.
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectName,

    [Parameter(Mandatory = $true)]
    [string]$TempDir,

    [Parameter(Mandatory = $true)]
    [string]$PublishOutDir,

    [Parameter(Mandatory = $false)]
    [ValidateSet("standalone", "framework")]
    [string]$Mode = "standalone"
)

$ErrorActionPreference = "Stop"

Write-Host " [Bước 3/4] Biên dịch và đóng gói Single-File (.exe) [$Mode]..." -ForegroundColor Cyan

$proj = Join-Path $TempDir "$ProjectName.csproj"
if (-not (Test-Path $proj)) {
    Write-Error "Không tìm thấy file project: $proj"
    exit 1
}

Write-Host "  -> Đang chạy: dotnet build -c Release..." -ForegroundColor DarkGray
dotnet build "$proj" -c Release
if ($LASTEXITCODE -ne 0) {
    Write-Error "Build thất bại với mã lỗi $LASTEXITCODE. Không thể publish."
    exit $LASTEXITCODE
}

Write-Host "  -> Build thành công. Đang tiến hành publish ($Mode)..." -ForegroundColor DarkGray

if (Test-Path $PublishOutDir) {
    Remove-Item -Path $PublishOutDir -Recurse -Force -ErrorAction SilentlyContinue
}
New-Item -ItemType Directory -Path $PublishOutDir -Force | Out-Null

if ($Mode -eq "standalone") {
    # Tự đóng gói .NET runtime vào file exe, không cần máy đích cài đặt .NET
    dotnet publish "$proj" -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true -p:EnableCompressionInSingleFile=true -p:IncludeNativeLibrariesForSelfExtract=true -o "$PublishOutDir"
} else {
    # Nhẹ hơn nhưng yêu cầu máy có cài .NET 8 Desktop Runtime
    dotnet publish "$proj" -c Release -r win-x64 --self-contained false -p:PublishSingleFile=true -o "$PublishOutDir"
}

if ($LASTEXITCODE -ne 0) {
    Write-Error "Publish thất bại với mã lỗi $LASTEXITCODE"
    exit $LASTEXITCODE
}

$expectedExe = Join-Path $PublishOutDir "$ProjectName.exe"
if (-not (Test-Path $expectedExe)) {
    Write-Error "Không tìm thấy file exe sau khi publish: $expectedExe"
    exit 1
}

$exeSizeMB = [math]::Round((Get-Item $expectedExe).Length / 1MB, 2)
Write-Host "  -> Đóng gói thành công: $ProjectName.exe ($exeSizeMB MB)" -ForegroundColor Green
exit 0
