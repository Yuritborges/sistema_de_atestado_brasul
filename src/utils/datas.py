"""
Datas do cofre (início e emissão TRP) — leitura, exibição e filtro por período.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

import pandas as pd

from config.settings import COLUNAS_COFRE

COL_EXCEL_INICIO = "DATA INICIO"
COL_EXCEL_TRP = "DATA  DE EMISSÃO TRP"
COL_DT_INICIO = "_dt_inicio"
COL_DT_TRP = "_dt_trp"
COL_VIEW_INICIO = "Data_Inicio"
COL_VIEW_TRP = "Data_TRP"

CampoData = Literal["inicio", "trp"]


def _candidatos_inicio() -> tuple[str, ...]:
    return (
        COL_EXCEL_INICIO,
        "DATA INÍCIO",
        "Data de inicio",
        "Data de início",
        "DATA DE INICIO",
    )


def _candidatos_trp() -> tuple[str, ...]:
    return (
        COL_EXCEL_TRP,
        "DATA DE EMISSÃO TRP",
        "DATA DE EMISSAO TRP",
        "Data de Emissão da TPR",
        "data de Emissão da TPR",
    )


def _achar_coluna(df: pd.DataFrame, candidatos: tuple[str, ...]) -> str | None:
    cols = {str(c).strip(): c for c in df.columns}
    norm = {k.upper().replace("  ", " "): v for k, v in cols.items()}
    for nome in candidatos:
        chave = nome.upper().replace("  ", " ")
        if chave in norm:
            return str(norm[chave])
    return None


def _para_datetime(serie: pd.Series) -> pd.Series:
    if serie.empty:
        return serie
    out = pd.to_datetime(serie, errors="coerce", dayfirst=True)
    if out.isna().all():
        out = pd.to_datetime(serie, errors="coerce", dayfirst=False)
    return out


def formatar_data_exibicao(val) -> str:
    """Data para tela/Excel; vazio se não houver data (nunca 'NaT')."""
    if val is None or pd.isna(val):
        return ""
    if isinstance(val, str):
        t = val.strip()
        if not t or t.upper() in ("NAT", "NAN", "NONE", "<NA>"):
            return ""
    try:
        if isinstance(val, (pd.Timestamp, datetime)):
            if pd.isna(val):
                return ""
            dt = val.to_pydatetime() if hasattr(val, "to_pydatetime") else val
        elif isinstance(val, date):
            dt = datetime.combine(val, datetime.min.time())
        else:
            parsed = pd.to_datetime(val, errors="coerce", dayfirst=True)
            if pd.isna(parsed):
                return ""
            dt = parsed.to_pydatetime()
        return dt.strftime("%d/%m/%Y")
    except Exception:
        t = str(val).strip()
        return "" if t.upper() in ("NAT", "NAN", "NONE", "<NA>") else t


def texto_celula_data(val) -> str:
    """Texto seguro para célula da tabela (sem NaT)."""
    return formatar_data_exibicao(val)


def parse_data_br(texto: str) -> date | None:
    t = (texto or "").strip()
    if not t:
        return None
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(t, fmt).date()
        except ValueError:
            continue
    try:
        return pd.to_datetime(t, dayfirst=True).date()
    except Exception:
        return None


def preparar_colunas_data(df: pd.DataFrame) -> pd.DataFrame:
    """Garante colunas de data do Excel + versões para tela e filtro."""
    df = df.copy()
    col_ini = _achar_coluna(df, _candidatos_inicio())
    col_trp = _achar_coluna(df, _candidatos_trp())

    if col_ini:
        df[COL_DT_INICIO] = _para_datetime(df[col_ini])
    else:
        df[COL_DT_INICIO] = pd.NaT

    if col_trp:
        df[COL_DT_TRP] = _para_datetime(df[col_trp])
    else:
        df[COL_DT_TRP] = pd.NaT

    df[COL_VIEW_INICIO] = df[COL_DT_INICIO].apply(formatar_data_exibicao)
    df[COL_VIEW_TRP] = df[COL_DT_TRP].apply(formatar_data_exibicao)
    return df


def aplicar_filtro_periodo(
    df: pd.DataFrame,
    campo: CampoData,
    data_de: date | None,
    data_ate: date | None,
) -> pd.DataFrame:
    if df.empty or (data_de is None and data_ate is None):
        return df

    col = COL_DT_INICIO if campo == "inicio" else COL_DT_TRP
    if col not in df.columns:
        df = preparar_colunas_data(df)

    serie = df[col]
    mask = serie.notna()
    if data_de is not None:
        mask &= serie.dt.date >= data_de
    if data_ate is not None:
        mask &= serie.dt.date <= data_ate
    return df[mask]


def rotulo_campo(campo: CampoData) -> str:
    return "Data de início" if campo == "inicio" else "Data de emissão da TPR"


def validar_datas_atestado(data_ini: str, data_trp: str) -> str | None:
    """
    Valida datas do cadastro manual.
    Retorna mensagem de erro ou None se estiver OK.
    """
    ini_txt = (data_ini or "").strip()
    trp_txt = (data_trp or "").strip()

    d_ini = parse_data_br(ini_txt) if ini_txt else None
    d_trp = parse_data_br(trp_txt) if trp_txt else None

    if ini_txt and d_ini is None:
        return "Data de início inválida. Use o formato DD/MM/AAAA."
    if trp_txt and d_trp is None:
        return "Data de emissão TRP inválida. Use o formato DD/MM/AAAA."
    if d_ini and d_trp and d_trp < d_ini:
        return "A data de emissão TRP não pode ser anterior à data de início."

    return None


def garantir_colunas_excel(df: pd.DataFrame) -> pd.DataFrame:
    """Alinha com COLUNAS_COFRE ao sincronizar/exportar."""
    for col in COLUNAS_COFRE:
        if col not in df.columns:
            df[col] = ""
    return df
