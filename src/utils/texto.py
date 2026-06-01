"""
Texto: busca sem acento e campos em maiúsculas.
"""

import unicodedata


def normalizar_busca(txt: str) -> str:
    t = unicodedata.normalize("NFD", str(txt or ""))
    return "".join(c for c in t if unicodedata.category(c) != "Mn").upper()


def vincular_maiusculas(entry):
    """Força letras maiúsculas enquanto o usuário digita."""

    def _ajustar(_event=None):
        valor = entry.get()
        alto = valor.upper()
        if valor == alto:
            return
        pos = entry.index("insert")
        entry.delete(0, "end")
        entry.insert(0, alto)
        try:
            entry.icursor(min(pos, len(alto)))
        except Exception:
            pass

    entry.bind("<KeyRelease>", _ajustar)
