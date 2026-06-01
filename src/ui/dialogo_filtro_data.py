"""
Diálogo para filtrar resultados por período (data início ou emissão TPR).
"""

from __future__ import annotations

from datetime import date
from tkinter import messagebox

import customtkinter as ctk

from ui.branding import preparar_janela
from utils.datas import CampoData, parse_data_br, rotulo_campo
from utils.mascaras import formatar_data_entry, vincular_data


class DialogoFiltroData(ctk.CTkToplevel):
    def __init__(
        self,
        master,
        filtro_atual: dict | None,
        cores: dict,
        on_aplicar,
    ):
        super().__init__(master)
        self.on_aplicar = on_aplicar
        self.cores = cores

        preparar_janela(self, "Filtrar por data")
        self.geometry("440x340")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        atual = filtro_atual or {}
        campo_ini = atual.get("campo") == "inicio"
        de_txt = self._fmt(atual.get("de"))
        ate_txt = self._fmt(atual.get("ate"))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=20)

        ctk.CTkLabel(
            body,
            text="Filtrar pela coluna:",
            font=("Segoe UI", 12, "bold"),
            text_color=cores.get("PRETO", "#1E293B"),
        ).pack(anchor="w", pady=(0, 8))

        self.var_campo = ctk.StringVar(value="inicio" if campo_ini else "trp")
        ctk.CTkRadioButton(
            body,
            text="Data de início",
            variable=self.var_campo,
            value="inicio",
            font=("Segoe UI", 11),
        ).pack(anchor="w", pady=2)
        ctk.CTkRadioButton(
            body,
            text="Data de emissão da TPR",
            variable=self.var_campo,
            value="trp",
            font=("Segoe UI", 11),
        ).pack(anchor="w", pady=(2, 16))

        ctk.CTkLabel(
            body,
            text="Período (DD/MM/AAAA) — deixe vazio para sem limite:",
            font=("Segoe UI", 11),
            text_color=cores.get("CINZA_TXT", "#64748B"),
        ).pack(anchor="w", pady=(0, 8))

        grid = ctk.CTkFrame(body, fg_color="transparent")
        grid.pack(fill="x")
        grid.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(grid, text="De:", font=("Segoe UI", 11)).grid(
            row=0, column=0, sticky="w", padx=(0, 10), pady=6
        )
        self.entry_de = ctk.CTkEntry(
            grid, placeholder_text="DD/MM/AAAA", height=36, width=200
        )
        self.entry_de.grid(row=0, column=1, sticky="ew", pady=6)
        vincular_data(self.entry_de)
        if de_txt:
            self.entry_de.insert(0, de_txt)
            formatar_data_entry(self.entry_de)

        ctk.CTkLabel(grid, text="Até:", font=("Segoe UI", 11)).grid(
            row=1, column=0, sticky="w", padx=(0, 10), pady=6
        )
        self.entry_ate = ctk.CTkEntry(
            grid, placeholder_text="DD/MM/AAAA", height=36, width=200
        )
        self.entry_ate.grid(row=1, column=1, sticky="ew", pady=6)
        vincular_data(self.entry_ate)
        if ate_txt:
            self.entry_ate.insert(0, ate_txt)
            formatar_data_entry(self.entry_ate)

        btns = ctk.CTkFrame(body, fg_color="transparent")
        btns.pack(fill="x", pady=(24, 0))

        ctk.CTkButton(
            btns,
            text="Limpar filtro",
            fg_color="#F0F0F0",
            text_color=cores.get("PRETO", "#1E293B"),
            hover_color=cores.get("BORDA", "#E2E8F0"),
            height=40,
            command=self._limpar,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btns,
            text="Aplicar",
            fg_color=cores.get("AZUL", "#3B82F6"),
            hover_color="#2563EB",
            text_color="#FFFFFF",
            height=40,
            font=("Segoe UI", 12, "bold"),
            command=self._aplicar,
        ).pack(side="right")

        self.bind("<Return>", lambda _e: self._aplicar())
        self.after(100, self.entry_de.focus)

    @staticmethod
    def _fmt(d: date | None) -> str:
        if not d:
            return ""
        return d.strftime("%d/%m/%Y")

    def _limpar(self):
        self.on_aplicar(None)
        self.destroy()

    def _aplicar(self):
        de = parse_data_br(self.entry_de.get())
        ate = parse_data_br(self.entry_ate.get())
        if self.entry_de.get().strip() and de is None:
            messagebox.showwarning(
                "Data inválida",
                "Informe a data inicial no formato DD/MM/AAAA.",
                parent=self,
            )
            return
        if self.entry_ate.get().strip() and ate is None:
            messagebox.showwarning(
                "Data inválida",
                "Informe a data final no formato DD/MM/AAAA.",
                parent=self,
            )
            return
        if de and ate and de > ate:
            messagebox.showwarning(
                "Período inválido",
                "A data inicial não pode ser maior que a data final.",
                parent=self,
            )
            return
        if de is None and ate is None:
            messagebox.showinfo(
                "Sem período",
                "Informe ao menos uma data (De ou Até) ou use Limpar filtro.",
                parent=self,
            )
            return

        campo: CampoData = "inicio" if self.var_campo.get() == "inicio" else "trp"
        self.on_aplicar({"campo": campo, "de": de, "ate": ate})
        self.destroy()
