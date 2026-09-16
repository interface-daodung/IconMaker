<#
.SYNOPSIS
    02-apply-templates.ps1 - Sao chep template C#, nhung icon va cau hinh AppConfig.cs.
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectName,

    [Parameter(Mandatory = $false)]
    [string]$DisplayName = "",

    [Parameter(Mandatory = $true)]
    [string]$TempDir,

    [Parameter(Mandatory = $true)]
    [string]$TemplatesDir,

    [Parameter(Mandatory = $true)]
    [string]$ServerDir,

    [Parameter(Mandatory = $false)]
    [string]$IconPath = "",

    [Parameter(Mandatory = $false)]
    [int]$Port = 0,

    [Parameter(Mandatory = $false)]
    [string]$CommandFile = "make",

    [Parameter(Mandatory = $false)]
    [string]$CommandArgs = "run"
)

$ErrorActionPreference = "Stop"

Write-Host " [Buoc 2/4] Sao chep template va cau hinh file du an..." -ForegroundColor Cyan

if (-not $DisplayName) {
    $DisplayName = $ProjectName
}

# Chuan hoa duong dan ServerDir tuyet doi
$fullServerDir = [System.IO.Path]::GetFullPath($ServerDir)
# Thoat dau gach cheo kep cho C# neu can (chuoi verbatim @"path" chi can xu ly neu co dau ngoac kep)
$escapedServerDir = $fullServerDir.Replace('"', '""')

# Tao thu muc Assets va copy icon
$assetsDir = Join-Path $TempDir "Assets"
New-Item -ItemType Directory -Path $assetsDir -Force | Out-Null
$targetIcon = Join-Path $assetsDir "icon.ico"

if ($IconPath -and (Test-Path $IconPath)) {
    Write-Host "  -> Su dung icon: $IconPath" -ForegroundColor DarkGray
    Copy-Item -Path $IconPath -Destination $targetIcon -Force
} else {
    Write-Host "  -> Khong tim thay icon chi dinh, su dung icon mac dinh" -ForegroundColor DarkGray
    $defaultIcon = Join-Path $TemplatesDir "..\icon.ico"
    if (Test-Path $defaultIcon) {
        Copy-Item -Path $defaultIcon -Destination $targetIcon -Force
    } else {
        # Tao dummy file neu khong co
        New-Item -ItemType File -Path $targetIcon -Force | Out-Null
    }
}

# 1. Cau hinh .csproj
$csprojTemplate = Join-Path $TemplatesDir "LauncherTemplate.csproj"
$csprojTarget = Join-Path $TempDir "$ProjectName.csproj"
$csprojContent = Get-Content -Path $csprojTemplate -Raw -Encoding UTF8
$csprojContent = $csprojContent.Replace("__APP_NAME__", $ProjectName)
[System.IO.File]::WriteAllText($csprojTarget, $csprojContent, [System.Text.Encoding]::UTF8)

# 2. Sinh AppConfig.cs tu template
$configTemplate = Join-Path $TemplatesDir "AppConfig.template.cs"
$configTarget = Join-Path $TempDir "AppConfig.cs"
$configContent = Get-Content -Path $configTemplate -Raw -Encoding UTF8

$mutexName = "${ProjectName}_SingleInstance"
$hostUrl = if ($Port -gt 0) { "http://localhost:$Port" } else { "" }
$fallbackFile = "cmd.exe"
$fallbackArgs = "/c $CommandFile $CommandArgs"

$configContent = $configContent.Replace("__APP_NAME__", $ProjectName)
$configContent = $configContent.Replace("__DISPLAY_NAME__", $DisplayName)
$configContent = $configContent.Replace("__MUTEX_NAME__", $mutexName)
$configContent = $configContent.Replace("__PROJECT_DIR__", $escapedServerDir)
$configContent = $configContent.Replace("__PORT__", $Port.ToString())
$configContent = $configContent.Replace("__HOST_URL__", $hostUrl)
$configContent = $configContent.Replace("__COMMAND_FILE__", $CommandFile)
$configContent = $configContent.Replace("__COMMAND_ARGS__", $CommandArgs)
$configContent = $configContent.Replace("__FALLBACK_FILE__", $fallbackFile)
$configContent = $configContent.Replace("__FALLBACK_ARGS__", $fallbackArgs)

[System.IO.File]::WriteAllText($configTarget, $configContent, [System.Text.Encoding]::UTF8)

# 3. Sao chep cac file ma nguon C# con lai
$csFiles = @(
    "Program.cs",
    "NativeMethods.cs",
    "JobObjectTracker.cs",
    "ServerProcess.cs",
    "ServerLogForm.cs",
    "TrayAppContext.cs"
)

foreach ($file in $csFiles) {
    $srcPath = Join-Path $TemplatesDir $file
    $dstPath = Join-Path $TempDir $file
    $content = Get-Content -Path $srcPath -Raw -Encoding UTF8
    $content = $content.Replace("__APP_NAME__", $ProjectName)
    $content = $content.Replace("namespace TrayLauncher;", "namespace $ProjectName;")
    [System.IO.File]::WriteAllText($dstPath, $content, [System.Text.Encoding]::UTF8)
}

Write-Host "  -> Da tao va cau hinh toan bo ma nguon template cho '$ProjectName'" -ForegroundColor Green
exit 0
