# build.ps1 - build truoc, chi publish khi build thanh cong
param(
    [ValidateSet("framework","standalone")]
    [string]$Mode = "framework",
    [string]$OutDir = ""
)

$proj = (Get-ChildItem $PSScriptRoot -Filter *.csproj | Select-Object -First 1).FullName
if (-not $proj) { Write-Host "Khong tim thay .csproj" -ForegroundColor Red; exit 1 }

Write-Host "=== dotnet build -c Release ===" -ForegroundColor Cyan
dotnet build $proj -c Release
if ($LASTEXITCODE -ne 0) {
    Write-Host "Build FAILED (exit $LASTEXITCODE) - khong publish" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "Build OK - tiep tuc publish ($Mode) ..." -ForegroundColor Green

if (-not $OutDir) {
    if ($Mode -eq "standalone") {
        $OutDir = Join-Path $PSScriptRoot "dist\single-standalone"
    } else {
        $OutDir = Join-Path $PSScriptRoot "dist\single-framework"
    }
}

if ($Mode -eq "standalone") {
    dotnet publish $proj -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true -p:EnableCompressionInSingleFile=true -p:IncludeNativeLibrariesForSelfExtract=true -o $OutDir
} else {
    dotnet publish $proj -c Release --self-contained false -o $OutDir
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "Publish OK -> $OutDir" -ForegroundColor Green
    Get-ChildItem $OutDir | Format-Table Name, Length -AutoSize
} else {
    Write-Host "Publish FAILED (exit $LASTEXITCODE)" -ForegroundColor Red
    exit $LASTEXITCODE
}
