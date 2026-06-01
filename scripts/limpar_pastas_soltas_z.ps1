# Remove pastas input/output/logs/backup criadas no lugar errado.

# Destino correto: Z:\0 OBRAS\Sistema_de_atestado_brasul\DATA\



$ErrorActionPreference = "Stop"

$RaizObra = "Z:\0 OBRAS"

$Projeto = "Z:\0 OBRAS\Sistema_de_atestado_brasul"

$ProjetoData = Join-Path $Projeto "DATA"

$Subs = @("input", "output", "backup", "logs")



if (-not (Test-Path $ProjetoData)) {

    Write-Error "Pasta DATA nao encontrada: $ProjetoData"

    exit 1

}



function Move-ParaData {

    param([string]$OrigemPai)

    foreach ($sub in $Subs) {

        $dest = Join-Path $ProjetoData $sub

        $orig = Join-Path $OrigemPai $sub

        if (-not (Test-Path $orig)) { continue }

        New-Item -ItemType Directory -Force -Path $dest | Out-Null

        $itens = Get-ChildItem -Path $orig -Force -ErrorAction SilentlyContinue

        if ($itens) {

            Copy-Item -Path (Join-Path $orig "*") -Destination $dest -Recurse -Force -ErrorAction SilentlyContinue

            Write-Host "[copiado] $orig -> $dest"

        }

    }

}



function Remove-Soltas {

    param([string]$OrigemPai)

    foreach ($sub in $Subs) {

        $orig = Join-Path $OrigemPai $sub

        if (Test-Path $orig) {

            Remove-Item -Path $orig -Recurse -Force

            Write-Host "[OK] Removido: $orig"

        }

    }

}



Write-Host "=== Raiz Z:\0 OBRAS (erro antigo rede.path) ===" -ForegroundColor Cyan

Move-ParaData -OrigemPai $RaizObra

Remove-Soltas -OrigemPai $RaizObra



Write-Host ""

Write-Host "=== Raiz do projeto (sem \DATA no rede.path) ===" -ForegroundColor Cyan

Move-ParaData -OrigemPai $Projeto

Remove-Soltas -OrigemPai $Projeto



Write-Host ""

Write-Host "Dados do programa ficam apenas em:" -ForegroundColor Green

Write-Host "  $ProjetoData"


