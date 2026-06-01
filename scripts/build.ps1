# Build do Sistema de Busca de Atestados (exe + instalador opcional)
# Uso: .\scripts\build.ps1
#      .\scripts\build.ps1 -Installer

param(
    [switch]$Installer,
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

Write-Host "=== Busca de Atestados - Build ===" -ForegroundColor Cyan

# Versão
$VersionFile = Join-Path $Root "config\version.py"
$Version = "0.0.0"
if (Test-Path $VersionFile) {
    $m = Select-String -Path $VersionFile -Pattern 'APP_VERSION\s*=\s*"([^"]+)"'
    if ($m) { $Version = $m.Matches[0].Groups[1].Value }
}
Write-Host "Versao: $Version"

# Ambiente virtual
$Venv = Join-Path $Root ".venv"
$Python = Join-Path $Venv "Scripts\python.exe"
if (-not (Test-Path $Python)) {
    Write-Host "Criando .venv ..."
    python -m venv $Venv
}
& $Python -m pip install -q --upgrade pip
& $Python -m pip install -q -r (Join-Path $Root "requirements.txt")

if ($Clean) {
    Remove-Item -Recurse -Force (Join-Path $Root "build"), (Join-Path $Root "dist") -ErrorAction SilentlyContinue
}

# PyInstaller
Write-Host "Gerando Cofre_Brasul.exe ..."
& $Python -m PyInstaller (Join-Path $Root "Cofre_Brasul.spec") --noconfirm
if ($LASTEXITCODE -ne 0) { throw "PyInstaller falhou." }

$Exe = Join-Path $Root "dist\Cofre_Brasul.exe"
if (-not (Test-Path $Exe)) { throw "Exe nao encontrado: $Exe" }
Write-Host "[OK] $Exe" -ForegroundColor Green

# Inno Setup (opcional)
if ($Installer) {
    $Iscc = @(
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
    ) | Where-Object { Test-Path $_ } | Select-Object -First 1

    if (-not $Iscc) {
        Write-Warning "Inno Setup nao encontrado. Instale: https://jrsoftware.org/isinfo.php"
    }
    else {
        Write-Host "Gerando instalador ..."
        & $Iscc (Join-Path $Root "instaler.iss")
        $Setup = Join-Path $Root "installer\Cofre_Brasul_Setup.exe"
        if (Test-Path $Setup) {
            Write-Host "[OK] $Setup" -ForegroundColor Green
        }
    }
}

Write-Host "`nBuild concluido." -ForegroundColor Cyan
