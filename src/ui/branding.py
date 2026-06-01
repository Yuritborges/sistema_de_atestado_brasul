"""
Ícone e logotipo Brasul em todas as janelas do programa.
"""

from __future__ import annotations

import ctypes
import sys
from pathlib import Path

import customtkinter as ctk

from config.settings import ASSETS_DIR, ICONS_DIR, IMAGES_DIR

ICONE_PATH = ICONS_DIR / "iconebrasul2.ico"
LOGO_PATH = IMAGES_DIR / "LOGOTIPOBRASUL.png"


def _resolver_arquivo(*candidatos: Path) -> Path | None:
    for caminho in candidatos:
        if caminho.exists():
            return caminho
    return None

# Área útil da sidebar (~300px) — logotipo grande, margens visuais reduzidas
LOGO_SIDEBAR_LARGURA_MAX = 252
LOGO_SIDEBAR_ALTURA_MAX = 175

_VERMELHO_BTN = "#DC2626"
_VERMELHO_BTN_HOVER = "#B91C1C"


def configurar_app_windows():
    """Ícone na barra de tarefas do Windows."""
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("brasul.busca.atestados")
    except Exception:
        pass


def _caminho_icone() -> str | None:
    icone = _resolver_arquivo(
        ICONE_PATH,
        ASSETS_DIR / "icons" / "iconebrasul2.ico",
        ICONS_DIR / "iconebrasul.ico",
    )
    if icone:
        return str(icone.resolve())
    return None


def aplicar_icone(janela, *, repetir: bool = True) -> None:
    caminho = _caminho_icone()
    if not caminho:
        return

    def _tentar():
        if not janela.winfo_exists():
            return False
        for fn in (
            lambda: janela.iconbitmap(caminho),
            lambda: janela.wm_iconbitmap(caminho),
            lambda: janela.tk.call("wm", "iconbitmap", janela._w, caminho),
        ):
            try:
                fn()
                return True
            except Exception:
                continue
        try:
            from PIL import Image, ImageTk

            img = Image.open(caminho)
            foto = ImageTk.PhotoImage(img)
            janela.wm_iconphoto(True, foto)
            janela._icone_brasul_ref = foto
            return True
        except Exception:
            return False

    def _agendar():
        _tentar()
        if repetir:
            janela.after(80, _tentar)
            janela.after(350, _tentar)

    try:
        janela.after_idle(_agendar)
    except Exception:
        _agendar()


def preparar_janela(janela, titulo: str | None = None) -> None:
    if titulo:
        janela.title(titulo)
    aplicar_icone(janela)


def vincular_icone_em_toplevels(janela_raiz: ctk.CTk) -> None:
    aplicar_icone(janela_raiz)

    def _ao_mapear(event):
        w = event.widget
        try:
            top = w.winfo_toplevel()
        except Exception:
            return
        if top is janela_raiz:
            return
        if getattr(top, "_brasul_icone_ok", False):
            return
        aplicar_icone(top)
        top._brasul_icone_ok = True

    janela_raiz.bind_all("<Map>", _ao_mapear, add="+")


def _recortar_margens_claras(img):
    """Remove faixa branca em volta do PNG (só o desenho do logo)."""
    from PIL import Image, ImageChops

    if img.mode != "RGBA":
        img = img.convert("RGBA")

    fundo = Image.new("RGBA", img.size, (255, 255, 255, 255))
    diff = ImageChops.difference(img, fundo)
    bbox = diff.getbbox()
    if bbox:
        img = img.crop(bbox)

    alpha = img.split()[3]
    bbox_a = alpha.getbbox()
    if bbox_a:
        img = img.crop(bbox_a)

    return img


def carregar_logo_sidebar(
    largura_max: int = LOGO_SIDEBAR_LARGURA_MAX,
    altura_max: int = LOGO_SIDEBAR_ALTURA_MAX,
):
    """Logotipo principal da sidebar — recorte + escala em alta qualidade."""
    from PIL import Image

    logo = _resolver_arquivo(
        LOGO_PATH,
        ASSETS_DIR / "images" / "LOGOTIPOBRASUL.png",
        IMAGES_DIR / "logotipobrasul.png",
    )
    if not logo:
        return None
    try:
        img = Image.open(logo).convert("RGBA")
        img = _recortar_margens_claras(img)

        escala = min(largura_max / img.width, altura_max / img.height)
        novo_w = max(1, int(img.width * escala))
        novo_h = max(1, int(img.height * escala))
        if (novo_w, novo_h) != (img.width, img.height):
            img = img.resize((novo_w, novo_h), Image.Resampling.LANCZOS)

        return ctk.CTkImage(img, size=(img.width, img.height))
    except Exception:
        return None


def estilo_botao_vermelho() -> dict:
    return {
        "fg_color": _VERMELHO_BTN,
        "hover_color": _VERMELHO_BTN_HOVER,
        "text_color": "#FFFFFF",
        "font": ("Segoe UI", 12, "bold"),
        "height": 40,
        "corner_radius": 10,
    }


def estilo_botao_verde(cores: dict) -> dict:
    return {
        "fg_color": cores.get("VERDE", "#22C55E"),
        "hover_color": "#16A34A",
        "text_color": cores.get("BRANCO", "#FFFFFF"),
        "font": ("Segoe UI", 12, "bold"),
        "height": 40,
        "corner_radius": 10,
    }
