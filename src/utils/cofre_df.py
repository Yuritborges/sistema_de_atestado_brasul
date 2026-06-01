"""
Prepara o DataFrame do cofre para a interface (colunas e tipos).
"""

import pandas as pd

from utils.datas import preparar_colunas_data
from utils.tipos import normalizar_tipo


def aliases_colunas(df: pd.DataFrame) -> pd.DataFrame:
    mapa = {"OBRA": "Obra", "Obra_Arquivo": "Obra_Arq"}
    for antigo, novo in mapa.items():
        if antigo in df.columns and novo not in df.columns:
            df = df.rename(columns={antigo: novo})
    return df


def preparar_cofre(df: pd.DataFrame) -> pd.DataFrame:
    df = aliases_colunas(df.fillna(""))
    for col in ["Obra", "Obra_Arq", "Tipo", "Cod", "Desc", "UN"]:
        if col not in df.columns:
            df[col] = ""
    if "Tipo" in df.columns:
        df["Tipo"] = df["Tipo"].apply(normalizar_tipo)
    for col in ["Obra", "Obra_Arq", "Cod", "Desc", "UN"]:
        df[col] = df[col].astype(str).str.strip()
    for col in ("Obra", "Obra_Arq", "Desc"):
        if col in df.columns:
            df[col] = df[col].str.upper()
    return preparar_colunas_data(df)


def linhas_com_codigo_valido(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "Cod" not in df.columns:
        return df
    return df[df["Cod"].str.match(r"\d{2}\.\d{2}", na=False)]
