"""
Configurações do Sistema de Busca de Atestados (Brasul).
Dados somente em .../Sistema_de_atestado_brasul/DATA (nunca na raiz do projeto nem em Z:\\0 OBRAS).
"""

import os
import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

DATA_REDE_PADRAO = Path(r"Z:\0 OBRAS\Sistema_de_atestado_brasul\DATA")


def _ler_caminho_arquivo(caminho: Path) -> str:
    if not caminho.exists():
        return ""
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if linha and not linha.startswith("#"):
            return linha
    return ""


def _normalizar_pasta_dados(raw: Path) -> Path:
    """Garante .../DATA; evita output/logs fora da pasta de dados."""
    p = Path(raw)
    if p.name.upper() == "DATA":
        return p
    if p.name.upper() in ("0 OBRAS", "OBRAS"):
        return DATA_REDE_PADRAO
    if "atestado" in p.name.lower() or (p / "DATA").is_dir():
        return p / "DATA"
    if getattr(sys, "frozen", False) and p == BASE_DIR:
        return DATA_REDE_PADRAO
    return p / "DATA"


def _resolver_pasta_dados() -> Path:
    """Ordem: COFRE_BRASUL_DATA > deploy/rede.path > DATA ao lado do projeto."""
    env = os.environ.get("COFRE_BRASUL_DATA", "").strip()
    if env:
        return _normalizar_pasta_dados(Path(env))
    cfg = _ler_caminho_arquivo(BASE_DIR / "deploy" / "rede.path")
    if cfg:
        return _normalizar_pasta_dados(Path(cfg))
    if getattr(sys, "frozen", False):
        return DATA_REDE_PADRAO
    return BASE_DIR / "DATA"


DATA_DIR = _resolver_pasta_dados()
USAR_REDE = (
    str(DATA_DIR).upper().startswith("Z:")
    or str(DATA_DIR).startswith("\\\\")
)

INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"
BACKUP_DIR = DATA_DIR / "backup"
LOGS_DIR = DATA_DIR / "logs"


def _resolver_assets_dir() -> Path:
    """
    Ícone e logotipo: em dev ficam em BASE_DIR/assets.
    No .exe (PyInstaller): dentro do pacote (_MEIPASS) e/ou em current/assets.
    """
    candidatos: list[Path] = []
    if getattr(sys, "frozen", False):
        candidatos.append(BASE_DIR / "assets")
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            candidatos.append(Path(meipass) / "assets")
    else:
        candidatos.append(BASE_DIR / "assets")
    for pasta in candidatos:
        if pasta.is_dir():
            return pasta
    return BASE_DIR / "assets"


ASSETS_DIR = _resolver_assets_dir()
ICONS_DIR = ASSETS_DIR / "icons"
IMAGES_DIR = ASSETS_DIR / "images"

NOME_BASE = "Cofre_atestados_brasul.xlsx"
NOME_BASE_LEGADO = "Base_Mestra_FDE.xlsx"
CAMINHO_BASE = INPUT_DIR / NOME_BASE
ABA_ATESTADOS = "Atestados de Obras"
ABA_REFERENCIA = "Base de Referência"

NOME_SAIDA = "Cofre_Brasul.xlsx"
CAMINHO_COFRE = OUTPUT_DIR / NOME_SAIDA

COLUNAS_COFRE = [
    "OBRA",
    "Obra_Arquivo",
    "Tipo",
    "Cod",
    "Desc",
    "UN",
    "DATA INICIO",
    "DATA  DE EMISSÃO TRP",
]

HISTORICO_BUSCA = LOGS_DIR / "historico_busca.json"
LOG_CADASTROS = LOGS_DIR / "cadastros.jsonl"
VIGIA_INTERVALO_MS = 2500
MAX_LINHAS_TABELA = 500
MAX_BACKUPS = 30


def garantir_pastas_dados() -> None:
    if DATA_DIR.name.upper() != "DATA":
        raise RuntimeError(
            f"Pasta de dados inválida (deve terminar em \\DATA): {DATA_DIR}"
        )
    for folder in (INPUT_DIR, OUTPUT_DIR, BACKUP_DIR, LOGS_DIR):
        folder.mkdir(parents=True, exist_ok=True)


garantir_pastas_dados()
