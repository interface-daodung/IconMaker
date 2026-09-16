<#
.SYNOPSIS
    build-launcher.ps1 - Tu dong tao Launcher Tray Icon (.exe) chay "make run" cho bat ky server folder nao.

.DESCRIPTION
    Script chay tuan tu 4 buoc:
      1. dotnet new winforms de tao du an tam thoi
      2. Ap dung bo template C#, nhung icon va tao cau hinh AppConfig.cs cho make run
      3. Bien dich va publish Single-File .exe (win-x64)
      4. Thu gom file .exe dau ra va don dep xoa toan bo thu muc du an tam

.PARAMETER ServerDir
    Duong dan den thu muc server (noi se chay lenh "make run").
    Tham so vi tri dau tien hoac qua -ServerDir.

.PARAMETER Name
    Ten cua Launcher App (hoac --name). Neu khong truyen, mac dinh lay ten thu muc server.

.PARAMETER Icon
    Duong dan den file .ico lam icon ung dung (hoac --icon). Mac dinh dung ./icon.ico.

.PARAMETER OutDir
    Thu muc chua file .exe dau ra. Mac dinh la ./dist.

.PARAMETER Mode
    Che do publish: "standalone" (mac dinh, tu kem runtime) hoac "framework" (nhe hon, dung runtime may).

.PARAMETER Port
    Cong cua server (tuy chon, dung de kiem tra cong ban). Mac dinh la 0 (khong kiem tra).

.EXAMPLE
    .\build-launcher.ps1 -ServerDir "D:\Projects\MyServer"
    .\build-launcher.ps1 -ServerDir "D:\Projects\MyServer" -Name "MyServerLauncher" -Icon "D:\icon.ico"
    .\build-launcher.ps1 "D:\Projects\MyServer" --name "MyServer" --icon "icon.ico"
#>
param(
    [Parameter(Position = 0, Mandatory = $false)]
    [Alias("Path", "Folder")]
    [string]$ServerDir = "",

    [Parameter(Mandatory = $false)]
    [Alias("n")]
    [string]$Name = "",

    [Parameter(Mandatory = $false)]
    [Alias("i")]
    [string]$Icon = "",

    [Parameter(Mandatory = $false)]
    [string]$OutDir = "",

    [Parameter(Mandatory = $false)]
    [ValidateSet("standalone", "framework")]
    [string]$Mode = "framework",

    [Parameter(Mandatory = $false)]
    [int]$Port = 0,

    [Parameter(Mandatory = $false)]
    [switch]$KeepTemp = $false,

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$RemainingArgs
)

# Ho tro parse co kieu GNU (--name, --icon, --server) va xu ly doi so con lai
if ($RemainingArgs) {
    for ($i = 0; $i -lt $RemainingArgs.Count; $i++) {
        $arg = $RemainingArgs[$i]
        if ($arg -in @("--name", "-name") -and ($i + 1 -lt $RemainingArgs.Count)) {
            $Name = $RemainingArgs[++$i]
        } elseif ($arg -in @("--icon", "-icon") -and ($i + 1 -lt $RemainingArgs.Count)) {
            $Icon = $RemainingArgs[++$i]
        } elseif ($arg -in @("--server", "--serverdir", "-serverdir") -and ($i + 1 -lt $RemainingArgs.Count)) {
            $ServerDir = $RemainingArgs[++$i]
        } elseif ($arg -in @("--out", "--outdir", "-outdir") -and ($i + 1 -lt $RemainingArgs.Count)) {
            $OutDir = $RemainingArgs[++$i]
        } elseif ($arg -in @("--mode", "-mode") -and ($i + 1 -lt $RemainingArgs.Count)) {
            $Mode = $RemainingArgs[++$i]
        } elseif ($arg -in @("--port", "-port") -and ($i + 1 -lt $RemainingArgs.Count)) {
            $Port = [int]$RemainingArgs[++$i]
        } elseif ((-not $ServerDir -or $ServerDir -eq '""' -or $ServerDir -eq "''") -and -not $arg.StartsWith("-")) {
            $ServerDir = $arg
        }
    }
}

if ($ServerDir) {
    $ServerDir = $ServerDir.Trim().Trim('"').Trim("'")
}

$root = $PSScriptRoot
if (-not $root) { $root = (Get-Location).Path }

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "   TU DONG TAO TRAY LAUNCHER .EXE (MAKE RUN & PID TRACKING)     " -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

# 1. Kiem tra dau vao ServerDir
if (-not $ServerDir) {
    Write-Host "Chua chi dinh thu muc server." -ForegroundColor Yellow
    $ServerDir = Read-Host "Nhap duong dan den thu muc server (hoac keo tha folder vao day)"
    if ($ServerDir) {
        $ServerDir = $ServerDir.Trim().Trim('"').Trim("'")
    }
}

if (-not $ServerDir -or -not (Test-Path $ServerDir)) {
    Write-Host "Loi: Thu muc server khong ton tai: '$ServerDir'" -ForegroundColor Red
    exit 1
}

$fullServerDir = [System.IO.Path]::GetFullPath($ServerDir)
$folderName = Split-Path $fullServerDir -Leaf

# 2. Xu ly ten ung dung
if (-not $Name) {
    $Name = $folderName
}
$DisplayName = $Name
# Lam sach ten project cho C# identifier (chi gom chu cai, so, gach duoi)
$CleanName = $Name -replace '[^a-zA-Z0-9_]', ''
if ($CleanName -match '^[0-9]') { $CleanName = "App_$CleanName" }
if (-not $CleanName) { $CleanName = "ServerLauncher" }

# 3. Xu ly Icon
if (-not $Icon) {
    $defaultIcon = Join-Path $root "icon.ico"
    if (Test-Path $defaultIcon) {
        $Icon = $defaultIcon
    }
} elseif (-not (Test-Path $Icon)) {
    $checkIcon = Join-Path $root $Icon
    if (Test-Path $checkIcon) { $Icon = $checkIcon }
}

# 4. Xu ly OutDir
if (-not $OutDir) {
    $OutDir = Join-Path $root "dist"
}
$finalOutDir = [System.IO.Path]::GetFullPath($OutDir)

# 5. Duong dan cac thu muc lam viec tam thoi
$scriptsDir = Join-Path $root "scripts"
$templatesDir = Join-Path $root "templates"
$randomId = [Guid]::NewGuid().ToString("N").Substring(0, 8)
$tempDir = Join-Path $root ".tmp_build_${CleanName}_${randomId}"
$publishTempDir = Join-Path $root ".tmp_pub_${CleanName}_${randomId}"

Write-Host "Thong tin cau hinh:" -ForegroundColor Green
Write-Host " - Server Directory : $fullServerDir"
Write-Host " - Command          : make run"
Write-Host " - App Name         : $CleanName ($DisplayName)"
Write-Host " - Icon             : $(if ($Icon) { $Icon } else { 'Default' })"
Write-Host " - Output Directory : $finalOutDir"
Write-Host " - Build Mode       : $Mode"
if ($Port -gt 0) { Write-Host " - Port             : $Port" }
Write-Host "----------------------------------------------------------------"

try {
    # BUOC 1: Tao du an moi voi dotnet new winforms
    $s1 = Join-Path $scriptsDir "01-create-project.ps1"
    & $s1 -ProjectName $CleanName -TempDir $tempDir
    if ($LASTEXITCODE -ne 0) { throw "Buoc 1 that bai." }

    # BUOC 2: Ap dung templates C#, tao AppConfig.cs
    $s2 = Join-Path $scriptsDir "02-apply-templates.ps1"
    & $s2 -ProjectName $CleanName `
          -DisplayName $DisplayName `
          -TempDir $tempDir `
          -TemplatesDir $templatesDir `
          -ServerDir $fullServerDir `
          -IconPath $Icon `
          -Port $Port `
          -CommandFile "make" `
          -CommandArgs "run"
    if ($LASTEXITCODE -ne 0) { throw "Buoc 2 that bai." }

    # BUOC 3: Bien dich va Publish Single-File .exe
    $s3 = Join-Path $scriptsDir "03-publish-exe.ps1"
    & $s3 -ProjectName $CleanName `
          -TempDir $tempDir `
          -PublishOutDir $publishTempDir `
          -Mode $Mode
    if ($LASTEXITCODE -ne 0) { throw "Buoc 3 that bai." }

    # BUOC 4: Chuyen .exe ra dist va don dep xoa thu muc tam
    if (-not $KeepTemp) {
        $s4 = Join-Path $scriptsDir "04-cleanup-project.ps1"
        & $s4 -ProjectName $CleanName `
              -TempDir $tempDir `
              -PublishOutDir $publishTempDir `
              -FinalOutDir $finalOutDir
        if ($LASTEXITCODE -ne 0) { throw "Buoc 4 that bai." }
    } else {
        Write-Host "  -> [KeepTemp] Giu lai thu muc tam: $tempDir" -ForegroundColor Yellow
        Copy-Item -Path (Join-Path $publishTempDir "$CleanName.exe") -Destination (Join-Path $finalOutDir "$CleanName.exe") -Force
    }

    $finalExePath = Join-Path $finalOutDir "$CleanName.exe"
    Write-Host "`n================================================================" -ForegroundColor Green
    Write-Host " HOAN TAT TAO TRAY LAUNCHER THANH CONG!" -ForegroundColor Green
    Write-Host " File EXE dau ra: $finalExePath" -ForegroundColor Cyan
    if (Test-Path $finalExePath) {
        $sizeMB = [math]::Round((Get-Item $finalExePath).Length / 1MB, 2)
        Write-Host " Kich thuoc      : $sizeMB MB" -ForegroundColor Gray
    }
    Write-Host " Thu muc du an tam da duoc don dep sach se." -ForegroundColor Green
    Write-Host "================================================================" -ForegroundColor Green

} catch {
    Write-Host "`nDA XAY RA LOI TRONG QUA TRINH TAO DU AN:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red

    # Don dep an toan khi loi
    if (-not $KeepTemp) {
        if (Test-Path $tempDir) { Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue }
        if (Test-Path $publishTempDir) { Remove-Item -Path $publishTempDir -Recurse -Force -ErrorAction SilentlyContinue }
    }
    exit 1
}
