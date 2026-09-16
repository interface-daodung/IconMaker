<#
.SYNOPSIS
    03-publish-exe.ps1 - Bien dich va dong goi Launcher thanh file .exe duy nhat.
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

Write-Host " [Buoc 3/4] Bien dich va dong goi Single-File (.exe) [$Mode]..." -ForegroundColor Cyan

$proj = Join-Path $TempDir "$ProjectName.csproj"
if (-not (Test-Path $proj)) {
    Write-Error "Khong tim thay file project: $proj"
    exit 1
}

Write-Host "  -> Dang chay: dotnet build -c Release..." -ForegroundColor DarkGray
dotnet build "$proj" -c Release
if ($LASTEXITCODE -ne 0) {
    Write-Error "Build that bai voi ma loi $LASTEXITCODE. Khong the publish."
    exit $LASTEXITCODE
}

Write-Host "  -> Build thanh cong. Dang tien hanh publish ($Mode)..." -ForegroundColor DarkGray

if (Test-Path $PublishOutDir) {
    Remove-Item -Path $PublishOutDir -Recurse -Force -ErrorAction SilentlyContinue
}
New-Item -ItemType Directory -Path $PublishOutDir -Force | Out-Null

if ($Mode -eq "standalone") {
    # Tu dong goi .NET runtime vao file exe, khong can may dich cai dat .NET
    dotnet publish "$proj" -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true -p:EnableCompressionInSingleFile=true -p:IncludeNativeLibrariesForSelfExtract=true -o "$PublishOutDir"
} else {
    # Nhe hon nhung yeu cau may co cai .NET 8 Desktop Runtime
    dotnet publish "$proj" -c Release -r win-x64 --self-contained false -p:PublishSingleFile=true -o "$PublishOutDir"
}

if ($LASTEXITCODE -ne 0) {
    Write-Error "Publish that bai voi ma loi $LASTEXITCODE"
    exit $LASTEXITCODE
}

$expectedExe = Join-Path $PublishOutDir "$ProjectName.exe"
if (-not (Test-Path $expectedExe)) {
    Write-Error "Khong tim thay file exe sau khi publish: $expectedExe"
    exit 1
}

$exeSizeMB = [math]::Round((Get-Item $expectedExe).Length / 1MB, 2)
Write-Host "  -> Dong goi thanh cong: $ProjectName.exe ($exeSizeMB MB)" -ForegroundColor Green
exit 0
