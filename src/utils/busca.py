"""
Filtros de busca do painel (texto, tipo, obra).
"""

from __future__ import annotations

from datetime import date

import pandas as pd

from utils.datas import CampoData, aplicar_filtro_periodo
from utils.tipos import eh_acumulado, eh_quantitativa


def aplicar_filtros(
    df: pd.DataFrame,
    termo: str,
    tipo: str,
    obra: str,
    norm,
) -> pd.DataFrame:
    if df.empty:
        return df

    out = df.copy()

    if obra and obra != "Todas as obras":
        out = out[out["Obra"] == obra]

    if termo:
        t = norm(termo)
        mask = (
            out["Desc"].apply(lambda x: t in norm(x))
            | out["Cod"].apply(lambda x: t in norm(x))
            | out["Obra"].apply(lambda x: t in norm(x))
            | out["Obra_Arq"].apply(lambda x: t in norm(x))
        )
        out = out[mask]

    if tipo == "ACUMULADO":
        out = out[out["Tipo"].apply(eh_acumulado)]
    elif tipo == "QUANTITATIVA":
        out = out[out["Tipo"].apply(eh_quantitativa)]

    return out


def aplicar_filtro_data(
    df: pd.DataFrame,
    campo: CampoData | None,
    data_de: date | None,
    data_ate: date | None,
) -> pd.DataFrame:
    if not campo or (data_de is None and data_ate is None):
        return df
    return aplicar_filtro_periodo(df, campo, data_de, data_ate)


def resumo_obra(df: pd.DataFrame, obra: str) -> str:
    if not obra or obra == "Todas as obras" or df.empty:
        return ""
    sub = df[df["Obra"] == obra]
    if sub.empty:
        return ""
    ac = int(sub["Tipo"].apply(eh_acumulado).sum())
    qt = int(sub["Tipo"].apply(eh_quantitativa).sum())
    return f"Obra: {obra}  |  Acumulado: {ac}  |  Quantitativa: {qt}  |  Total: {len(sub)}"
