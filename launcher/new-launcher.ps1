# new-launcher.ps1 - sinh app launcher moi theo khung tray-clone.
#
# Khung: launcher/IconMakerLauncher (AppConfig.cs + ServerProcess.cs +
# TrayAppContext.cs + ServerLogForm.cs + NativeMethods.cs + Program.cs).
# csproj gen bang `dotnet new winforms` (khong copy tay), script tu patch
# 2 dong icon. File duy nhat can sua sau khi sinh: <TenApp>\AppConfig.cs
# (+ thay Assets/icon.ico).
#
# Vi du:
#   powershell -ExecutionPolicy Bypass -File launcher/new-launcher.ps1 -Name VieNeuLauncher
#   powershell -ExecutionPolicy Bypass -File launcher/new-launcher.ps1 -Name MyApiLauncher -Icon C:\path\to\my.ico
#   make new-launcher NAME=MyApiLauncher
param(
    [Parameter(Mandatory = $true)][string]$Name,
    [string]$OutDir = "",
    [string]$Template = "IconMakerLauncher",
    [string]$Icon = ""
)

$ErrorActionPreference = "Stop"

if ($Name -notmatch '^[A-Za-z_][A-Za-z0-9_]*$') {
    Write-Host "Ten app khong hop le: '$Name' (chi chu/cuoi/so, bat dau bang chu/gach duoi)" -ForegroundColor Red
    exit 1
}

$LauncherRoot = $PSScriptRoot
$TemplateDir = Join-Path $LauncherRoot $Template
$FrameFiles = @("AppConfig.cs", "ServerProcess.cs", "TrayAppContext.cs", "ServerLogForm.cs", "NativeMethods.cs", "Program.cs")
foreach ($f in $FrameFiles) {
    if (-not (Test-Path -LiteralPath (Join-Path $TemplateDir $f))) {
        Write-Host "Thieu file khung: $Template/$f" -ForegroundColor Red
        exit 1
    }
}

if (-not $OutDir) { $OutDir = Join-Path $LauncherRoot $Name }
if (Test-Path -LiteralPath $OutDir) {
    Write-Host "Da ton tai: $OutDir (xoa hoac chon ten khac)" -ForegroundColor Red
    exit 1
}

Write-Host "=== dotnet new winforms -n $Name ===" -ForegroundColor Cyan
dotnet new winforms -n $Name -o $OutDir
if ($LASTEXITCODE -ne 0) { Write-Host "dotnet new FAILED" -ForegroundColor Red; exit $LASTEXITCODE }

# Copy khung + doi namespace ve ten app moi (ngoai le duy nhat so voi skill
# goc: copy ca Program.cs de xoa phu thuoc Form1 cua `dotnet new`).
foreach ($f in $FrameFiles) {
    $src = Join-Path $TemplateDir $f
    $dst = Join-Path $OutDir $f
    $text = Get-Content -LiteralPath $src -Raw
    $text = $text -replace 'namespace IconMakerLauncher;', "namespace $Name;"
    $text = $text -replace 'namespace TrayDemo;', "namespace $Name;"
    Set-Content -LiteralPath $dst -Value $text -Encoding UTF8
}

Remove-Item (Join-Path $OutDir "Form1.cs"), (Join-Path $OutDir "Form1.Designer.cs") -ErrorAction SilentlyContinue
Remove-Item (Join-Path $OutDir "Form1.resx") -ErrorAction SilentlyContinue

New-Item -ItemType Directory -Path (Join-Path $OutDir "Assets") -Force | Out-Null
if ($Icon) {
    Copy-Item -LiteralPath $Icon -Destination (Join-Path $OutDir "Assets\icon.ico") -Force
} else {
    Copy-Item -LiteralPath (Join-Path $TemplateDir "Assets\icon.ico") -Destination (Join-Path $OutDir "Assets\icon.ico") -Force
}

# Patch csproj: them 2 dong icon neu chua co.
$csproj = Join-Path $OutDir "$Name.csproj"
$xml = Get-Content -LiteralPath $csproj -Raw
if ($xml -notmatch '<ApplicationIcon>') {
    $xml = $xml -replace '</PropertyGroup>', "    <ApplicationIcon>Assets\icon.ico</ApplicationIcon>`r`n  </PropertyGroup>"
}
if ($xml -notmatch 'EmbeddedResource.*Assets\\icon\.ico') {
    $xml = $xml -replace '</Project>', "  <ItemGroup>`r`n    <EmbeddedResource Include=`"Assets\icon.ico`" />`r`n  </ItemGroup>`r`n`r`n</Project>"
}
Set-Content -LiteralPath $csproj -Value $xml -Encoding UTF8

Copy-Item -LiteralPath (Join-Path $TemplateDir "build.ps1") -Destination (Join-Path $OutDir "build.ps1") -Force

Write-Host ""
Write-Host "Xong: $OutDir" -ForegroundColor Green
Write-Host "2 cho can sua:" -ForegroundColor Cyan
Write-Host "  1. $Name\AppConfig.cs (AppName, ProjectDir, Port, CommandFile/Args, TrayTooltip, messages)"
Write-Host "  2. Thay $Name\Assets\icon.ico bang icon that (VD: build tu IconMaker: make icons)"
Write-Host "Build: Set-Location $OutDir; if ($?) { .\build.ps1 } else { Write-Error 'Build failed' }"
