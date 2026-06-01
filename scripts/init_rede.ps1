# Estrutura em Z:\0 OBRAS para o Sistema de Busca de Atestados
$Raiz = "Z:\0 OBRAS\Sistema_de_atestado_brasul\DATA"
$Pastas = @("input", "output", "backup", "logs")

if (-not (Test-Path $Raiz)) {
    Write-Error "Unidade Z: nao encontrada. Mapeie o compartilhamento de rede antes."
    exit 1
}

foreach ($p in $Pastas) {
    $caminho = Join-Path $Raiz $p
    New-Item -ItemType Directory -Force -Path $caminho | Out-Null
    Write-Host "[OK] $caminho"
}

$Base = Join-Path $Raiz "input\Cofre_atestados_brasul.xlsx"
$Legado = Join-Path $Raiz "input\Base_Mestra_FDE.xlsx"

if ((Test-Path $Legado) -and -not (Test-Path $Base)) {
    Rename-Item -Path $Legado -NewName "Cofre_atestados_brasul.xlsx"
    Write-Host "[OK] Renomeado Base_Mestra_FDE.xlsx -> Cofre_atestados_brasul.xlsx" -ForegroundColor Green
}
elseif (-not (Test-Path $Base)) {
    Write-Host ""
    Write-Host "Coloque a planilha Cofre_atestados_brasul.xlsx em:" -ForegroundColor Yellow
    Write-Host "  $Base"
}

Write-Host "`nEstrutura pronta em Z:\0 OBRAS" -ForegroundColor Green
