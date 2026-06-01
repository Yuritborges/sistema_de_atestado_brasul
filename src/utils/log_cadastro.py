"""
Registro de auditoria dos cadastros manuais.
"""

from __future__ import annotations

import getpass
import json
from datetime import datetime
from pathlib import Path


def registrar_cadastro(
    caminho_log: Path,
    obra: str,
    arquivo: str,
    itens: list[dict],
    *,
    data_inicio: str = "",
    data_trp: str = "",
) -> None:
    caminho_log.parent.mkdir(parents=True, exist_ok=True)
    registro = {
        "quando": datetime.now().isoformat(timespec="seconds"),
        "usuario": getpass.getuser(),
        "maquina": getpass.getuser(),  # Windows: mesmo; hostname opcional abaixo
        "obra": obra,
        "arquivo": arquivo,
        "data_inicio": data_inicio,
        "data_trp": data_trp,
        "itens": [
            {
                "cod": it.get("cod", it.get("Cod", "")),
                "tipo": it.get("tipo", it.get("Tipo", "")),
            }
            for it in itens
        ],
    }
    try:
        import socket

        registro["maquina"] = socket.gethostname()
    except Exception:
        pass

    with open(caminho_log, "a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")
