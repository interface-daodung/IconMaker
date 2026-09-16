<#
.SYNOPSIS
    build-launcher.ps1 - Tự động tạo Launcher Tray Icon (.exe) chạy "make run" cho bất kỳ server folder nào.

.DESCRIPTION
    Script chạy tuần tự 4 bước:
      1. dotnet new winforms để tạo dự án tạm thời
      2. Áp dụng bộ template C#, nhúng icon và tạo cấu hình AppConfig.cs cho make run
      3. Biên dịch và publish Single-File .exe (win-x64)
      4. Thu gom file .exe đầu ra và dọn dẹp xóa toàn bộ thư mục dự án tạm

.PARAMETER ServerDir
    Đường dẫn đến thư mục server (nơi sẽ chạy lệnh "make run").
    Tham số vị trí đầu tiên hoặc qua -ServerDir.

.PARAMETER Name
    Tên của Launcher App (hoặc --name). Nếu không truyền, mặc định lấy tên thư mục server.

.PARAMETER Icon
    Đường dẫn đến file .ico làm icon ứng dụng (hoặc --icon). Mặc định dùng ./icon.ico.

.PARAMETER OutDir
    Thư mục chứa file .exe đầu ra. Mặc định là ./dist.

.PARAMETER Mode
    Chế độ publish: "standalone" (mặc định, tự kèm runtime) hoặc "framework" (nhẹ hơn, dùng runtime máy).

.PARAMETER Port
    Cổng của server (tùy chọn, dùng để kiểm tra cổng bận). Mặc định là 0 (không kiểm tra).

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

# Hỗ trợ parse cờ kiểu GNU (--name, --icon, --server) và xử lý đối số còn lại
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
Write-Host "   TỰ ĐỘNG TẠO TRAY LAUNCHER .EXE (MAKE RUN & PID TRACKING)     " -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

# 1. Kiểm tra đầu vào ServerDir
if (-not $ServerDir) {
    Write-Host "Chưa chỉ định thư mục server." -ForegroundColor Yellow
    $ServerDir = Read-Host "Nhập đường dẫn đến thư mục server (hoặc kéo thả folder vào đây)"
    if ($ServerDir) {
        $ServerDir = $ServerDir.Trim().Trim('"').Trim("'")
    }
}

if (-not $ServerDir -or -not (Test-Path $ServerDir)) {
    Write-Host "Lỗi: Thư mục server không tồn tại: '$ServerDir'" -ForegroundColor Red
    exit 1
}

$fullServerDir = [System.IO.Path]::GetFullPath($ServerDir)
$folderName = Split-Path $fullServerDir -Leaf

# 2. Xử lý tên ứng dụng
if (-not $Name) {
    $Name = $folderName
}
$DisplayName = $Name
# Làm sạch tên project cho C# identifier (chỉ gồm chữ cái, số, gạch dưới)
$CleanName = $Name -replace '[^a-zA-Z0-9_]', ''
if ($CleanName -match '^[0-9]') { $CleanName = "App_$CleanName" }
if (-not $CleanName) { $CleanName = "ServerLauncher" }

# 3. Xử lý Icon
if (-not $Icon) {
    $defaultIcon = Join-Path $root "icon.ico"
    if (Test-Path $defaultIcon) {
        $Icon = $defaultIcon
    }
} elseif (-not (Test-Path $Icon)) {
    $checkIcon = Join-Path $root $Icon
    if (Test-Path $checkIcon) { $Icon = $checkIcon }
}

# 4. Xử lý OutDir
if (-not $OutDir) {
    $OutDir = Join-Path $root "dist"
}
$finalOutDir = [System.IO.Path]::GetFullPath($OutDir)

# 5. Đường dẫn các thư mục làm việc tạm thời
$scriptsDir = Join-Path $root "scripts"
$templatesDir = Join-Path $root "templates"
$randomId = [Guid]::NewGuid().ToString("N").Substring(0, 8)
$tempDir = Join-Path $root ".tmp_build_${CleanName}_${randomId}"
$publishTempDir = Join-Path $root ".tmp_pub_${CleanName}_${randomId}"

Write-Host "Thông tin cấu hình:" -ForegroundColor Green
Write-Host " - Server Directory : $fullServerDir"
Write-Host " - Command          : make run"
Write-Host " - App Name         : $CleanName ($DisplayName)"
Write-Host " - Icon             : $(if ($Icon) { $Icon } else { 'Default' })"
Write-Host " - Output Directory : $finalOutDir"
Write-Host " - Build Mode       : $Mode"
if ($Port -gt 0) { Write-Host " - Port             : $Port" }
Write-Host "----------------------------------------------------------------"

try {
    # BƯỚC 1: Tạo dự án mới với dotnet new winforms
    $s1 = Join-Path $scriptsDir "01-create-project.ps1"
    & $s1 -ProjectName $CleanName -TempDir $tempDir
    if ($LASTEXITCODE -ne 0) { throw "Bước 1 thất bại." }

    # BƯỚC 2: Áp dụng templates C#, tạo AppConfig.cs
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
    if ($LASTEXITCODE -ne 0) { throw "Bước 2 thất bại." }

    # BƯỚC 3: Biên dịch và Publish Single-File .exe
    $s3 = Join-Path $scriptsDir "03-publish-exe.ps1"
    & $s3 -ProjectName $CleanName `
          -TempDir $tempDir `
          -PublishOutDir $publishTempDir `
          -Mode $Mode
    if ($LASTEXITCODE -ne 0) { throw "Bước 3 thất bại." }

    # BƯỚC 4: Chuyển .exe ra dist và dọn dẹp xóa thư mục tạm
    if (-not $KeepTemp) {
        $s4 = Join-Path $scriptsDir "04-cleanup-project.ps1"
        & $s4 -ProjectName $CleanName `
              -TempDir $tempDir `
              -PublishOutDir $publishTempDir `
              -FinalOutDir $finalOutDir
        if ($LASTEXITCODE -ne 0) { throw "Bước 4 thất bại." }
    } else {
        Write-Host "  -> [KeepTemp] Giữ lại thư mục tạm: $tempDir" -ForegroundColor Yellow
        Copy-Item -Path (Join-Path $publishTempDir "$CleanName.exe") -Destination (Join-Path $finalOutDir "$CleanName.exe") -Force
    }

    $finalExePath = Join-Path $finalOutDir "$CleanName.exe"
    Write-Host "`n================================================================" -ForegroundColor Green
    Write-Host " HOÀN TẤT TẠO TRAY LAUNCHER THÀNH CÔNG!" -ForegroundColor Green
    Write-Host " File EXE đầu ra: $finalExePath" -ForegroundColor Cyan
    if (Test-Path $finalExePath) {
        $sizeMB = [math]::Round((Get-Item $finalExePath).Length / 1MB, 2)
        Write-Host " Kích thước      : $sizeMB MB" -ForegroundColor Gray
    }
    Write-Host " Thư mục dự án tạm đã được dọn dẹp sạch sẽ." -ForegroundColor Green
    Write-Host "================================================================" -ForegroundColor Green

} catch {
    Write-Host "`nĐÃ XẢY RA LỖI TRONG QUÁ TRÌNH TẠO DỰ ÁN:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red

    # Dọn dẹp an toàn khi lỗi
    if (-not $KeepTemp) {
        if (Test-Path $tempDir) { Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue }
        if (Test-Path $publishTempDir) { Remove-Item -Path $publishTempDir -Recurse -Force -ErrorAction SilentlyContinue }
    }
    exit 1
}
