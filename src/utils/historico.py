"""
Últimas buscas do usuário (arquivo local).
"""

import json
from pathlib import Path

MAX_ITENS = 8


def carregar(caminho: Path) -> list:
    if not caminho.exists():
        return []
    try:
        data = json.loads(caminho.read_text(encoding="utf-8"))
        return list(data)[:MAX_ITENS]
    except Exception:
        return []


def registrar(caminho: Path, termo: str) -> list:
    termo = str(termo or "").strip()
    if len(termo) < 2:
        return carregar(caminho)

    itens = [termo] + [t for t in carregar(caminho) if t != termo]
    itens = itens[:MAX_ITENS]
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(itens, ensure_ascii=False, indent=0), encoding="utf-8")
    return itens
