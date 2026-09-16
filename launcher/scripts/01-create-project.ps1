<#
.SYNOPSIS
    01-create-project.ps1 - Khoi tao du an WinForms moi bang dotnet new vao thu muc tam.
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectName,

    [Parameter(Mandatory = $true)]
    [string]$TempDir
)

$ErrorActionPreference = "Stop"

Write-Host " [Buoc 1/4] Khoi tao du an moi bang dotnet new winforms..." -ForegroundColor Cyan

if (Test-Path $TempDir) {
    Write-Host "  -> Don dep thu muc tam cu: $TempDir" -ForegroundColor DarkGray
    Remove-Item -Path $TempDir -Recurse -Force -ErrorAction SilentlyContinue
}

New-Item -ItemType Directory -Path $TempDir -Force | Out-Null

Write-Host "  -> Dang chay: dotnet new winforms -n `"$ProjectName`" -o `"$TempDir`"" -ForegroundColor DarkGray
dotnet new winforms -n "$ProjectName" -o "$TempDir" --framework net8.0

if ($LASTEXITCODE -ne 0) {
    Write-Error "Lenh dotnet new that bai voi ma loi $LASTEXITCODE"
    exit $LASTEXITCODE
}

# Xoa cac file Form1 mac dinh do dotnet new sinh ra de tranh xung dot
$defaultFiles = @("Form1.cs", "Form1.Designer.cs", "Form1.resx", "Program.cs")
foreach ($f in $defaultFiles) {
    $targetPath = Join-Path $TempDir $f
    if (Test-Path $targetPath) {
        Remove-Item -Path $targetPath -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "  -> Khoi tao du an thanh cong tai: $TempDir" -ForegroundColor Green
exit 0
