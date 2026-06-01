"""
Tipos de linha do cofre (Acumulado / Quantitativa / Ambos).
Centraliza nomes que vêm diferentes do Excel (ex.: QUANTITATIVO).
"""


def normalizar_tipo(tipo) -> str:
    t = str(tipo or "").strip().upper()
    if not t or t == "0":
        return ""
    if "AMBOS" in t:
        return "AMBOS"
    if "QUANT" in t:
        return "QUANTITATIVA"
    if "ACUM" in t:
        return "ACUMULADO"
    if "EXTRATO" in t:
        return "EXTRATO"
    if "CONTRATO" in t:
        return "QUANT_CONTRATO"
    return t


def eh_acumulado(tipo) -> bool:
    return normalizar_tipo(tipo) == "ACUMULADO"


def eh_quantitativa(tipo) -> bool:
    return normalizar_tipo(tipo) == "QUANTITATIVA"


def eh_ambos(tipo) -> bool:
    return normalizar_tipo(tipo) == "AMBOS"


def tag_e_rotulo_tabela(tipo) -> tuple[str, str]:
    """Retorna (texto na coluna tipo, tag de cor da tabela)."""
    t = normalizar_tipo(tipo)
    if t == "AMBOS":
        return "Ambos", "AMBOS"
    if t == "ACUMULADO":
        return "Acumulado", "ACUMULADO"
    if t == "QUANTITATIVA":
        return "Quantitativa", "QUANTITATIVA"
    if t:
        return t.title(), "PAR"
    return "", "PAR"
