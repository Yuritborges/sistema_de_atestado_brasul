"""
Sincroniza Cofre_atestados_brasul.xlsx com a cópia de consulta (output).

Uso: python main.py
Interface: python interface.py
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from config.settings import CAMINHO_BASE, CAMINHO_COFRE
from config.version import APP_NAME, APP_VERSION
from base_loader import sincronizar_cofre_se_necessario
from utils.rede_setup import garantir_base_na_rede


def main() -> int:
    garantir_base_na_rede(BASE_DIR)

    print()
    print("=" * 56)
    print(f"  {APP_NAME} v{APP_VERSION}")
    print("  Sincronizar planilha -> cópia de consulta")
    print("=" * 56)
    print(f"\n  Origem:  {CAMINHO_BASE}")
    print(f"  Destino: {CAMINHO_COFRE}")

    try:
        stats = sincronizar_cofre_se_necessario(CAMINHO_BASE, CAMINHO_COFRE)
    except FileNotFoundError as e:
        print(f"\n[ERRO] {e}")
        return 1

    if stats is None:
        print("\n[OK] Cópia de consulta já está atualizada.")
    else:
        print("\n[OK] Cópia de consulta atualizada.")
        print(f"     Itens:          {stats['linhas']}")
        print(f"     Obras:          {stats['obras']}")
        print(f"     Arquivos PDF:   {stats['pdfs']}")
        print(f"     Codigos unicos: {stats['codigos_unicos']}")

    print("\n[OK] Abra a interface para buscar os atestados.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
