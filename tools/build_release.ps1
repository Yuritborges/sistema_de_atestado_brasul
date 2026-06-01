# Build PyInstaller + publica em releases/ e espelha em current/ (padrao Brasul).
# Uso: powershell -ExecutionPolicy Bypass -File tools\build_release.ps1
#      ou: ATUALIZAR_ATESTADO.bat

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

$Version = "0.0.0"
$vf = Join-Path $Root "config\version.py"
if (Test-Path $vf) {
    $m = Select-String -Path $vf -Pattern 'APP_VERSION\s*=\s*"([^"]+)"'
    if ($m) { $Version = $m.Matches[0].Groups[1].Value }
}

$stamp = Get-Date -Format "yyyyMMdd_HHmm"
$ExeName = "Cofre_Brasul.exe"

Write-Host "=== Sistema de Busca de Atestados - Release v$Version ===" -ForegroundColor Cyan

# venv + dependencias
$VenvPy = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPy)) {
    Write-Host "Criando .venv ..."
    python -m venv (Join-Path $Root ".venv")
}
& $VenvPy -m pip install -q --upgrade pip
& $VenvPy -m pip install -q -r (Join-Path $Root "requirements.txt")

$PyInstaller = Join-Path $Root ".venv\Scripts\pyinstaller.exe"
if (-not (Test-Path $PyInstaller)) {
    & $VenvPy -m pip install -q pyinstaller
}

Write-Host "[1/4] PyInstaller ..."
& $PyInstaller (Join-Path $Root "Cofre_Brasul.spec") --clean --noconfirm
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$builtExe = Join-Path $Root "dist\$ExeName"
if (-not (Test-Path $builtExe)) {
    throw "Build incompleto: $builtExe nao encontrado."
}

# Pacote para current (exe + deploy com rede.path)
$stage = Join-Path $Root "dist\release_stage"
if (Test-Path $stage) { Remove-Item -Recurse -Force $stage }
New-Item -ItemType Directory -Force -Path $stage | Out-Null
Copy-Item -Force $builtExe (Join-Path $stage $ExeName)
$deploySrc = Join-Path $Root "deploy"
if (Test-Path $deploySrc) {
    Copy-Item -Recurse -Force $deploySrc (Join-Path $stage "deploy")
}
$assetsSrc = Join-Path $Root "assets"
if (Test-Path $assetsSrc) {
    Copy-Item -Recurse -Force $assetsSrc (Join-Path $stage "assets")
    Write-Host "       assets (icone + logotipo) incluidos no pacote current"
}

$releaseName = "Cofre_Brasul_v${Version}_$stamp"
$destRelease = Join-Path $Root "releases\$releaseName"
Write-Host "[2/4] Copiando para releases\$releaseName ..."
New-Item -ItemType Directory -Force -Path (Join-Path $Root "releases") | Out-Null
Copy-Item -Recurse -Force $stage $destRelease

Write-Host "[3/4] Atualizando current/ (usuarios fecham e abrem de novo) ..."
$cur = Join-Path $Root "current"
New-Item -ItemType Directory -Force -Path $cur | Out-Null
. (Join-Path $PSScriptRoot "robocopy_mirror.ps1")
$rc = Invoke-RobocopyMirror -Source $stage -Destination $cur
if ($rc -ge 8) {
    throw "Falha ao atualizar current (robocopy $rc). Feche o programa em todos os PCs e tente de novo."
}

Write-Host "[4/4] Concluido." -ForegroundColor Green
Write-Host "  releases: $destRelease\$ExeName"
Write-Host "  current:  $cur\$ExeName"
Write-Host ""
Write-Host "Atalho na rede: Z:\0 OBRAS\Sistema_de_atestado_brasul\current\$ExeName" -ForegroundColor Yellow
Write-Host "Apos atualizar, peca para fechar o programa e abrir o atalho novamente."
