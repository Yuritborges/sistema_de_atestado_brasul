"""
Cadastro de código novo na Base de Referência.
"""

from pathlib import Path

import customtkinter as ctk
from tkinter import messagebox

from services.referencia_store import adicionar_codigo_referencia
from ui.branding import estilo_botao_verde, preparar_janela
from utils.excel_io import PlanilhaEmUsoError
from utils.texto import vincular_maiusculas

UNIDADES = ["M", "M2", "M3", "UN", "%", "KG", "CJ", "JG", "MV", "KM", "PR", "VG", "L", "ML"]


class DialogoNovoCodigoReferencia(ctk.CTkToplevel):
    def __init__(self, parent, caminho_base: Path, codigo_inicial: str, cores: dict, on_criado=None):
        super().__init__(parent)
        self.caminho_base = Path(caminho_base)
        self.on_criado = on_criado
        self._cores = cores

        self.geometry("540x400")
        self.minsize(480, 380)
        self.configure(fg_color=cores["FUNDO"])
        self.transient(parent)
        self.grab_set()
        preparar_janela(self, "Novo código na Base de Referência")

        ctk.CTkLabel(
            self,
            text="Cadastrar código na Base de Referência",
            font=("Segoe UI", 15, "bold"),
            text_color=cores["PRETO"],
        ).pack(anchor="w", padx=20, pady=(16, 8))

        # Rodapé fixo embaixo (antes do card, para não sumir)
        rod = ctk.CTkFrame(self, fg_color="transparent")
        rod.pack(side="bottom", fill="x", padx=20, pady=(8, 16))

        ctk.CTkButton(
            rod,
            text="Cancelar",
            width=110,
            height=42,
            fg_color=cores["FUNDO"],
            text_color=cores["PRETO"],
            hover_color=cores["BORDA"],
            border_width=1,
            border_color=cores["BORDA"],
            command=self.destroy,
        ).pack(side="left")

        ctk.CTkButton(
            rod,
            text="Adicionar à base",
            width=200,
            command=self._salvar,
            **estilo_botao_verde(cores),
        ).pack(side="right")

        card = ctk.CTkFrame(self, fg_color=cores["BRANCO"], corner_radius=12)
        card.pack(fill="both", expand=True, padx=20, pady=(0, 8))

        ctk.CTkLabel(card, text="Código FDE", text_color=cores["CINZA_TXT"]).pack(
            anchor="w", padx=16, pady=(14, 0),
        )
        self.entry_cod = ctk.CTkEntry(card, height=40, font=("Consolas", 12, "bold"))
        self.entry_cod.pack(fill="x", padx=16, pady=4)
        if codigo_inicial:
            self.entry_cod.insert(0, codigo_inicial)

        ctk.CTkLabel(card, text="Descrição", text_color=cores["CINZA_TXT"]).pack(
            anchor="w", padx=16, pady=(10, 0),
        )
        self.entry_desc = ctk.CTkEntry(card, height=40)
        self.entry_desc.pack(fill="x", padx=16, pady=4)
        vincular_maiusculas(self.entry_desc)

        ctk.CTkLabel(card, text="Unidade (UN)", text_color=cores["CINZA_TXT"]).pack(
            anchor="w", padx=16, pady=(10, 0),
        )
        self.combo_un = ctk.CTkComboBox(card, values=UNIDADES, height=38, width=120)
        self.combo_un.pack(anchor="w", padx=16, pady=(4, 16))

        self.entry_cod.bind("<Return>", self._ao_enter)
        self.entry_desc.bind("<Return>", self._ao_enter)
        self.bind("<Return>", self._ao_enter)
        self.entry_cod.focus_set()
        self.after(100, self.lift)

    def _ao_enter(self, _event=None):
        self._salvar()

    def _salvar(self):
        if not self.entry_desc.get().strip():
            messagebox.showwarning(
                "Descrição",
                "Informe a descrição do código.",
                parent=self,
            )
            self.entry_desc.focus_set()
            return

        try:
            cod = adicionar_codigo_referencia(
                self.caminho_base,
                self.entry_cod.get(),
                self.entry_desc.get(),
                self.combo_un.get(),
            )
        except (PermissionError, PlanilhaEmUsoError) as e:
            messagebox.showerror("Arquivo em uso", str(e), parent=self)
            return
        except Exception as e:
            messagebox.showerror("Erro", str(e), parent=self)
            return

        if self.on_criado:
            self.on_criado(cod, self.entry_desc.get().strip(), self.combo_un.get().strip())

        messagebox.showinfo(
            "Salvo",
            f"Código {cod} gravado na planilha:\n\n"
            f"{self.caminho_base}\n\n"
            f"Aba: Base de Referência\n"
            f"(no Excel, use essa aba na parte inferior — "
            f"não está no arquivo da pasta output).",
            parent=self,
        )
        self.destroy()
