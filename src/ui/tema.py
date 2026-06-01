"""
Cores e fontes da interface Brasul.
Centralizado aqui para facilitar manutenção visual.
"""

import customtkinter as ctk

ctk.set_appearance_mode("light")

AMARELO = "#FFCC00"
AMARELO_ESC = "#E6B800"
AMARELO_LITE = "#FFF8D6"
PRETO = "#1E293B"
BRANCO = "#FFFFFF"
FUNDO = "#F8FAFC"
CARD_BG = "#FFFFFF"
BORDA = "#E2E8F0"
AZUL = "#3B82F6"
AZUL_LITE = "#EFF6FF"
VERDE = "#22C55E"
VERDE_LITE = "#F0FDF4"
LILAS = "#8B5CF6"
LILAS_LITE = "#F5F3FF"
CINZA_TXT = "#64748B"
CINZA_LINHA = "#F8FAFC"

SIDEBAR_W = 300

F_TITULO = ("Segoe UI", 22, "bold")
F_SECAO = ("Segoe UI", 14, "bold")
F_LABEL = ("Segoe UI", 11)
F_BTN = ("Segoe UI", 12, "bold")
F_BUSCA = ("Segoe UI", 14)
F_KPI_N = ("Segoe UI", 28, "bold")
F_KPI_L = ("Segoe UI", 10, "bold")
F_COD = ("Consolas", 11, "bold")


def paleta() -> dict:
    return {
        "AMARELO": AMARELO,
        "AMARELO_ESC": AMARELO_ESC,
        "PRETO": PRETO,
        "BRANCO": BRANCO,
        "FUNDO": FUNDO,
        "BORDA": BORDA,
        "AZUL": AZUL,
        "VERDE": VERDE,
        "CINZA_TXT": CINZA_TXT,
    }
