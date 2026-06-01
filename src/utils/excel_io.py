"""
Leitura/gravação segura de Excel (rede, backup, arquivo em uso).
"""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from config.settings import BACKUP_DIR, MAX_BACKUPS


class PlanilhaEmUsoError(PermissionError):
    """Planilha aberta no Excel ou bloqueada na rede."""


def garantir_excel_livre(caminho: Path) -> None:
    """Falha com mensagem clara se outro processo mantém o arquivo aberto."""
    if not caminho.exists():
        return
    try:
        with open(caminho, "r+b"):
            pass
    except PermissionError as e:
        raise PlanilhaEmUsoError(
            "A planilha está aberta no Excel ou em uso por outro usuário na rede.\n\n"
            f"Feche o arquivo e tente novamente:\n  {caminho}"
        ) from e


def backup_planilha(
    caminho: Path,
    pasta_backup: Path | None = None,
) -> Path | None:
    """Cópia datada antes de gravar alterações."""
    if not caminho.exists():
        return None

    destino_pasta = pasta_backup or BACKUP_DIR
    destino_pasta.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    copia = destino_pasta / f"{caminho.stem}_{stamp}{caminho.suffix}"
    shutil.copy2(caminho, copia)
    _limpar_backups_antigos(destino_pasta, caminho.stem, caminho.suffix)
    return copia


def _limpar_backups_antigos(pasta: Path, prefixo: str, sufixo: str) -> None:
    arquivos = sorted(
        pasta.glob(f"{prefixo}_*{sufixo}"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for antigo in arquivos[MAX_BACKUPS:]:
        try:
            antigo.unlink()
        except OSError:
            pass


def salvar_workbook(wb, caminho: Path, *, fazer_backup: bool = True) -> None:
    """Backup + gravação com checagem de bloqueio."""
    garantir_excel_livre(caminho)
    if fazer_backup and caminho.exists():
        backup_planilha(caminho)
    try:
        wb.save(str(caminho))
    except PermissionError as e:
        raise PlanilhaEmUsoError(
            "Não foi possível gravar: o Excel ou outro usuário está usando a planilha.\n\n"
            f"  {caminho}"
        ) from e
    finally:
        wb.close()
