"""
Primeira configuração na rede: copia ou renomeia planilha com nome antigo.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from config.settings import (
    CAMINHO_BASE,
    INPUT_DIR,
    NOME_BASE,
    NOME_BASE_LEGADO,
    USAR_REDE,
)


def _candidatos_origem(base_dir_programa: Path) -> list[Path]:
    """Locais onde a planilha antiga ou nova pode estar."""
    pastas = [INPUT_DIR, base_dir_programa / "DATA" / "input"]
    if USAR_REDE:
        pastas.append(base_dir_programa / "DATA" / "input")

    vistos: set[str] = set()
    out: list[Path] = []
    for pasta in pastas:
        pasta = Path(pasta)
        key = str(pasta.resolve()) if pasta.exists() else str(pasta)
        if key in vistos:
            continue
        vistos.add(key)
        for nome in (NOME_BASE, NOME_BASE_LEGADO):
            p = pasta / nome
            if p.exists() and p.resolve() != CAMINHO_BASE.resolve():
                out.append(p)
    return out


def garantir_base_na_rede(base_dir_programa: Path) -> bool:
    """
    Garante Cofre_atestados_brasul.xlsx no input da rede/local.
    Renomeia Base_Mestra_FDE.xlsx se ainda existir com o nome antigo.
    """
    if CAMINHO_BASE.exists():
        return False

    legado_rede = INPUT_DIR / NOME_BASE_LEGADO
    if legado_rede.exists():
        legado_rede.rename(CAMINHO_BASE)
        return True

    for origem in _candidatos_origem(base_dir_programa):
        CAMINHO_BASE.parent.mkdir(parents=True, exist_ok=True)
        if origem.name == NOME_BASE_LEGADO:
            shutil.copy2(origem, CAMINHO_BASE)
        else:
            shutil.copy2(origem, CAMINHO_BASE)
        return True

    return False
