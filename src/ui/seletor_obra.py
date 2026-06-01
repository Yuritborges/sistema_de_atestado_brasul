"""
Seletor de obra com lista rolável e busca (substitui o combobox longo).
"""

import customtkinter as ctk

from ui.branding import preparar_janela


class SeletorObra(ctk.CTkFrame):
    def __init__(self, parent, on_selecao, cores: dict, largura=400):
        super().__init__(parent, fg_color="transparent")
        self.on_selecao = on_selecao
        self.c = cores
        self.valor = "Todas as obras"
        self._obras = []
        self._popup = None

        linha = ctk.CTkFrame(self, fg_color="transparent")
        linha.pack(fill="x")

        self.btn_abrir = ctk.CTkButton(
            linha,
            text="Todas as obras",
            width=largura,
            height=38,
            anchor="w",
            fg_color=cores["BRANCO"],
            text_color=cores["PRETO"],
            hover_color=cores["FUNDO"],
            border_width=1,
            border_color=cores["BORDA"],
            font=("Segoe UI", 11),
            command=self._abrir_lista,
        )
        self.btn_abrir.pack(side="left")

        self.btn_limpar = ctk.CTkButton(
            linha,
            text="↩",
            width=42,
            height=38,
            fg_color=cores["AMARELO"],
            text_color=cores["PRETO"],
            hover_color=cores["AMARELO_ESC"],
            font=("Segoe UI", 14, "bold"),
            command=self._todas_obras,
        )
        self.btn_limpar.pack(side="left", padx=(6, 0))

    def get(self) -> str:
        return self.valor

    def set(self, obra: str):
        self.valor = obra or "Todas as obras"
        texto = self.valor if len(self.valor) <= 48 else self.valor[:45] + "..."
        self.btn_abrir.configure(text=texto)

    def set_obras(self, lista: list):
        self._obras = sorted({str(o).strip() for o in lista if str(o).strip()})

    def _todas_obras(self):
        self.set("Todas as obras")
        if self.on_selecao:
            self.on_selecao(self.valor)
        if self._popup and self._popup.winfo_exists():
            self._popup.destroy()

    def _abrir_lista(self):
        if self._popup and self._popup.winfo_exists():
            self._popup.destroy()
            return

        self._popup = ctk.CTkToplevel(self)
        self._popup.geometry("420x420")
        self._popup.resizable(False, True)
        self._popup.configure(fg_color=self.c["FUNDO"])
        self._popup.transient(self.winfo_toplevel())
        preparar_janela(self._popup, "Selecionar obra")

        x = self.btn_abrir.winfo_rootx()
        y = self.btn_abrir.winfo_rooty() + self.btn_abrir.winfo_height() + 4
        self._popup.geometry(f"+{x}+{y}")

        topo = ctk.CTkFrame(self._popup, fg_color=self.c["BRANCO"], corner_radius=12)
        topo.pack(fill="x", padx=12, pady=12)

        ctk.CTkButton(
            topo,
            text="↩  Todas as obras",
            height=40,
            fg_color=self.c["AMARELO"],
            text_color=self.c["PRETO"],
            hover_color=self.c["AMARELO_ESC"],
            font=("Segoe UI", 12, "bold"),
            command=self._todas_obras,
        ).pack(fill="x", padx=10, pady=10)

        self.entry_busca_obra = ctk.CTkEntry(
            topo,
            placeholder_text="Buscar obra...",
            height=36,
        )
        self.entry_busca_obra.pack(fill="x", padx=10, pady=(0, 10))
        self.entry_busca_obra.bind("<KeyRelease>", lambda _e: self._filtrar_lista())

        self.lista = ctk.CTkScrollableFrame(
            self._popup,
            fg_color=self.c["BRANCO"],
            corner_radius=12,
            height=280,
        )
        self.lista.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self._filtrar_lista()
        self.entry_busca_obra.focus()

    def _filtrar_lista(self):
        for w in self.lista.winfo_children():
            w.destroy()

        termo = ""
        if hasattr(self, "entry_busca_obra") and self.entry_busca_obra.winfo_exists():
            termo = self.entry_busca_obra.get().strip().upper()

        for obra in self._obras:
            if termo and termo not in obra.upper():
                continue
            ctk.CTkButton(
                self.lista,
                text=obra,
                height=34,
                anchor="w",
                fg_color="transparent",
                text_color=self.c["PRETO"],
                hover_color=self.c["FUNDO"],
                font=("Segoe UI", 11),
                command=lambda o=obra: self._escolher(o),
            ).pack(fill="x", padx=4, pady=1)

    def _escolher(self, obra: str):
        self.set(obra)
        if self.on_selecao:
            self.on_selecao(obra)
        if self._popup and self._popup.winfo_exists():
            self._popup.destroy()
