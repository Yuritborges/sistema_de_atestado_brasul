"""
Janela para cadastrar atestado manualmente (como no Excel).
"""

import re
from pathlib import Path

import customtkinter as ctk
from tkinter import messagebox, ttk

from base_loader import sincronizar_cofre_da_base
from config.settings import COLUNAS_COFRE, LOG_CADASTROS
from services.atestado_store import adicionar_itens_atestado
from utils.datas import validar_datas_atestado
from utils.excel_io import PlanilhaEmUsoError
from utils.log_cadastro import registrar_cadastro
from base_loader import carregar_base
from services.referencia import _c7, buscar_codigo, carregar_referencia, formatar_codigo
from ui.dialogo_novo_codigo import DialogoNovoCodigoReferencia
from ui.branding import estilo_botao_verde, estilo_botao_vermelho, preparar_janela
from utils.mascaras import vincular_data
from utils.texto import vincular_maiusculas
from utils.tipos import normalizar_tipo

UNIDADES = ["M", "M2", "M3", "UN", "%", "KG", "CJ", "JG", "MV", "KM", "PR", "VG", "L", "ML"]


class CadastroAtestadoDialog(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        caminho_base: Path,
        caminho_cofre: Path,
        cores: dict,
        on_salvo=None,
        on_fechar=None,
    ):
        super().__init__(parent)
        self.caminho_base = Path(caminho_base)
        self.caminho_cofre = Path(caminho_cofre)
        self.on_salvo = on_salvo
        self.on_fechar = on_fechar
        self.catalogo = carregar_referencia(self.caminho_base)
        self._mesclar_catalogo_atestados()
        self.itens_sessao = []
        self._skip_validacao_cod = False

        self.geometry("920x720")
        self.minsize(800, 640)
        self.configure(fg_color=cores["FUNDO"])
        self.transient(parent)
        self.grab_set()

        self._cores = cores
        preparar_janela(self, "Novo atestado — cadastro manual")
        self.protocol("WM_DELETE_WINDOW", self._fechar)
        self._build()
        self.after(100, self.lift)

    def _fechar(self):
        if self.on_fechar:
            self.on_fechar()
        self.destroy()

    def _mesclar_catalogo_atestados(self):
        """Inclui códigos já usados na aba Atestados (além da referência)."""
        try:
            ctx = carregar_base(self.caminho_base)
            for c7, (desc, un) in ctx.por_cod.items():
                if c7 not in self.catalogo:
                    self.catalogo[c7] = {
                        "codigo": formatar_codigo(c7),
                        "descricao": desc,
                        "unidade": un,
                    }
        except Exception:
            pass

    def _build(self):
        c = self._cores
        pad = {"padx": 20, "pady": 8}

        topo = ctk.CTkFrame(self, fg_color=c["BRANCO"], corner_radius=0)
        topo.pack(fill="x")
        ctk.CTkFrame(topo, height=5, fg_color=c["AMARELO"], corner_radius=0).pack(fill="x")
        ctk.CTkLabel(
            topo,
            text="Cadastrar novo atestado",
            font=("Segoe UI", 18, "bold"),
            text_color=c["PRETO"],
        ).pack(anchor="w", padx=20, pady=(16, 4))
        ctk.CTkLabel(
            topo,
            text="Digite o código FDE — descrição e unidade vêm da Base de Referência.",
            font=("Segoe UI", 11),
            text_color=c["CINZA_TXT"],
        ).pack(anchor="w", padx=20, pady=(0, 12))

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=12, pady=8)

        card = ctk.CTkFrame(scroll, fg_color=c["BRANCO"], corner_radius=14, border_width=1, border_color=c["BORDA"])
        card.pack(fill="x", **pad)

        ctk.CTkLabel(card, text="Dados da obra", font=("Segoe UI", 13, "bold"), text_color=c["PRETO"]).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(14, 8)
        )

        self._campo(card, "Nome da obra *", 1)
        self.entry_obra = ctk.CTkEntry(card, height=40, font=("Segoe UI", 12))
        self.entry_obra.grid(row=1, column=1, sticky="ew", padx=16, pady=6)
        vincular_maiusculas(self.entry_obra)

        self._campo(card, "Arquivo PDF (nome)", 2)
        self.entry_arquivo = ctk.CTkEntry(card, height=40, font=("Segoe UI", 12), placeholder_text="Ex.: Minha Obra.pdf")
        self.entry_arquivo.grid(row=2, column=1, sticky="ew", padx=16, pady=6)
        vincular_maiusculas(self.entry_arquivo)
        self.entry_obra.bind("<FocusOut>", self._sugerir_arquivo)

        self._campo(card, "Data início", 3)
        self.entry_data_ini = ctk.CTkEntry(card, height=40, placeholder_text="DD/MM/AAAA")
        self.entry_data_ini.grid(row=3, column=1, sticky="ew", padx=16, pady=6)
        vincular_data(self.entry_data_ini)

        self._campo(card, "Data emissão TRP", 4)
        self.entry_data_trp = ctk.CTkEntry(card, height=40, placeholder_text="DD/MM/AAAA")
        self.entry_data_trp.grid(row=4, column=1, sticky="ew", padx=16, pady=6)
        vincular_data(self.entry_data_trp)

        card.grid_columnconfigure(1, weight=1)

        card2 = ctk.CTkFrame(scroll, fg_color=c["BRANCO"], corner_radius=14, border_width=1, border_color=c["BORDA"])
        card2.pack(fill="x", **pad)

        ctk.CTkLabel(card2, text="Incluir código", font=("Segoe UI", 13, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", padx=16, pady=(14, 8)
        )

        tipo_row = ctk.CTkFrame(card2, fg_color="transparent")
        tipo_row.grid(row=1, column=0, columnspan=3, sticky="w", padx=16, pady=4)
        ctk.CTkLabel(tipo_row, text="Tipo:", text_color=c["CINZA_TXT"]).pack(side="left", padx=(0, 8))
        self.tipo_var = ctk.StringVar(value="ACUMULADO")
        for nome, val in [("Acumulado", "ACUMULADO"), ("Quantitativa", "QUANTITATIVA")]:
            ctk.CTkRadioButton(
                tipo_row, text=nome, variable=self.tipo_var, value=val,
                font=("Segoe UI", 11),
            ).pack(side="left", padx=10)

        self._campo_grid(card2, "Código FDE *", 2, 0)
        self.entry_cod = ctk.CTkEntry(card2, height=40, font=("Consolas", 12, "bold"), placeholder_text="16.04.031")
        self.entry_cod.grid(row=2, column=1, sticky="ew", padx=8, pady=6)
        self.entry_cod.bind("<KeyRelease>", self._ao_digitar_codigo)
        self.entry_cod.bind("<FocusOut>", self._validar_codigo_focus)
        self.entry_cod.bind("<Return>", lambda _e: self._adicionar_linha())

        self._campo_grid(card2, "Descrição", 3, 0)
        self.entry_desc = ctk.CTkEntry(card2, height=40, font=("Segoe UI", 11))
        self.entry_desc.grid(row=3, column=1, sticky="ew", padx=8, pady=6)
        vincular_maiusculas(self.entry_desc)

        self._campo_grid(card2, "UN", 4, 0)
        self.combo_un = ctk.CTkComboBox(card2, values=UNIDADES, height=40, width=120)
        self.combo_un.grid(row=4, column=1, sticky="w", padx=8, pady=6)

        ctk.CTkButton(
            card2, text="+ Adicionar à lista",
            fg_color=c["VERDE"], hover_color="#16A34A", text_color=c["BRANCO"],
            height=42, font=("Segoe UI", 12, "bold"),
            command=self._adicionar_linha,
        ).grid(row=2, column=2, rowspan=2, padx=16, pady=6, sticky="ns")

        card2.grid_columnconfigure(1, weight=1)

        lista_frame = ctk.CTkFrame(scroll, fg_color=c["BRANCO"], corner_radius=14, border_width=1, border_color=c["BORDA"])
        lista_frame.pack(fill="both", expand=True, **pad)

        cab = ctk.CTkFrame(lista_frame, fg_color="transparent")
        cab.pack(fill="x", padx=16, pady=(12, 4))
        ctk.CTkLabel(cab, text="Itens deste atestado", font=("Segoe UI", 13, "bold")).pack(side="left")
        self.lbl_qtd = ctk.CTkLabel(cab, text="0 itens", text_color=c["CINZA_TXT"])
        self.lbl_qtd.pack(side="right")

        cols = ("tipo", "cod", "desc", "un")
        self.tree = ttk.Treeview(lista_frame, columns=cols, show="headings", height=8)
        self.tree.heading("tipo", text="Tipo")
        self.tree.heading("cod", text="Código")
        self.tree.heading("desc", text="Descrição")
        self.tree.heading("un", text="UN")
        self.tree.column("tipo", width=100)
        self.tree.column("cod", width=110)
        self.tree.column("desc", width=480)
        self.tree.column("un", width=60)
        self.tree.pack(fill="both", expand=True, padx=16, pady=8)

        ctk.CTkButton(
            lista_frame, text="Remover selecionado",
            fg_color="#FEE2E2", hover_color="#FECACA", text_color="#B91C1C",
            height=36, command=self._remover_linha,
        ).pack(anchor="e", padx=16, pady=(0, 12))

        rodape = ctk.CTkFrame(self, fg_color=c["BRANCO"])
        rodape.pack(fill="x")
        ctk.CTkButton(
            rodape, text="Cancelar", width=120, height=44,
            fg_color=c["FUNDO"], text_color=c["PRETO"], hover_color=c["BORDA"],
            command=self._fechar,
        ).pack(side="left", padx=20, pady=16)

        ctk.CTkButton(
            rodape, text="Salvar atestado no Excel",
            height=44, font=("Segoe UI", 12, "bold"),
            fg_color=c["AMARELO"], text_color=c["PRETO"], hover_color=c["AMARELO_ESC"],
            command=self._salvar,
        ).pack(side="right", padx=20, pady=16)

    def _campo(self, parent, texto, row):
        ctk.CTkLabel(parent, text=texto, text_color=self._cores["CINZA_TXT"], width=140, anchor="w").grid(
            row=row, column=0, sticky="w", padx=16, pady=6
        )

    def _campo_grid(self, parent, texto, row, col):
        ctk.CTkLabel(parent, text=texto, text_color=self._cores["CINZA_TXT"], width=100, anchor="w").grid(
            row=row, column=col, sticky="w", padx=16, pady=6
        )

    def _sugerir_arquivo(self, _=None):
        if self.entry_arquivo.get().strip():
            return
        obra = self.entry_obra.get().strip()
        if not obra:
            return
        nome = re.sub(r"[^\w\s\-]", "", obra, flags=re.UNICODE)
        nome = " ".join(nome.split()) + ".pdf"
        self.entry_arquivo.insert(0, nome)

    def _ao_digitar_codigo(self, _=None):
        achado = buscar_codigo(self.entry_cod.get(), self.catalogo)
        if not achado:
            return
        self.entry_desc.delete(0, "end")
        self.entry_desc.insert(0, achado["descricao"])
        if achado["unidade"]:
            self.combo_un.set(achado["unidade"])
        if achado["codigo"]:
            self.entry_cod.delete(0, "end")
            self.entry_cod.insert(0, achado["codigo"])

    def _validar_codigo_focus(self, _=None):
        if self._skip_validacao_cod:
            return
        cod = self.entry_cod.get().strip()
        if len(_c7(cod)) < 7:
            return
        if buscar_codigo(cod, self.catalogo):
            return
        self._alerta_codigo_inexistente()

    def _alerta_codigo_inexistente(self):
        self._skip_validacao_cod = True
        dlg = ctk.CTkToplevel(self)
        dlg.geometry("520x240")
        dlg.configure(fg_color=self._cores["FUNDO"])
        dlg.transient(self)
        dlg.grab_set()
        preparar_janela(dlg, "Código não encontrado")

        ctk.CTkLabel(
            dlg,
            text="ESSE CODIGO NÃO EXISTE NA BASE DE REFERÊNCIA",
            font=("Segoe UI", 13, "bold"),
            text_color="#B91C1C",
            wraplength=480,
        ).pack(padx=20, pady=(20, 8))

        ctk.CTkLabel(
            dlg,
            text="Tentar novamente ou criar código na Base de Referência.",
            font=("Segoe UI", 11),
            text_color=self._cores["CINZA_TXT"],
            wraplength=480,
        ).pack(padx=20, pady=(0, 16))

        btns = ctk.CTkFrame(dlg, fg_color="transparent")
        btns.pack(fill="x", padx=20)

        def tentar():
            self.entry_cod.delete(0, "end")
            self.entry_desc.delete(0, "end")
            dlg.destroy()
            self._skip_validacao_cod = False
            self.entry_cod.focus()

        def fechar_dlg():
            dlg.destroy()
            self._skip_validacao_cod = False

        dlg.protocol("WM_DELETE_WINDOW", fechar_dlg)

        ctk.CTkButton(
            btns,
            text="Tentar novamente",
            width=180,
            command=tentar,
            **estilo_botao_vermelho(),
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btns,
            text="Criar na Base de Referência",
            width=240,
            command=lambda: (dlg.destroy(), self._criar_codigo_referencia()),
            **estilo_botao_verde(self._cores),
        ).pack(side="right")

    def _criar_codigo_referencia(self):
        self._skip_validacao_cod = True
        cod = self.entry_cod.get().strip()

        def ao_criar(cod_fmt, desc, un):
            self._skip_validacao_cod = False
            c7 = _c7(cod_fmt)
            self.catalogo[c7] = {
                "codigo": cod_fmt,
                "descricao": desc,
                "unidade": un,
            }
            self.entry_cod.delete(0, "end")
            self.entry_cod.insert(0, cod_fmt)
            self.entry_desc.delete(0, "end")
            self.entry_desc.insert(0, desc)
            if un:
                self.combo_un.set(un)

        DialogoNovoCodigoReferencia(
            self, self.caminho_base, cod, self._cores, on_criado=ao_criar,
        )
        self.after(300, lambda: setattr(self, "_skip_validacao_cod", False))

    def _adicionar_linha(self):
        cod = self.entry_cod.get().strip()
        desc = self.entry_desc.get().strip()
        un = self.combo_un.get().strip()
        tipo = normalizar_tipo(self.tipo_var.get())

        if not cod:
            messagebox.showwarning("Código", "Informe o código FDE.", parent=self)
            return

        achado = buscar_codigo(cod, self.catalogo)
        if achado:
            cod = achado["codigo"]
            if not desc:
                desc = achado["descricao"]
            if not un:
                un = achado["unidade"]

        if not achado:
            self._alerta_codigo_inexistente()
            return

        if not desc:
            messagebox.showwarning("Descrição", "Preencha a descrição do serviço.", parent=self)
            return

        self.itens_sessao.append({"tipo": tipo, "cod": cod, "desc": desc, "un": un})
        self.tree.insert("", "end", values=(tipo, cod, desc, un))
        self.lbl_qtd.configure(text=f"{len(self.itens_sessao)} itens")

        self.entry_cod.delete(0, "end")
        self.entry_desc.delete(0, "end")
        self.entry_cod.focus()

    def _remover_linha(self):
        sel = self.tree.selection()
        if not sel:
            return
        idx = self.tree.index(sel[0])
        self.tree.delete(sel[0])
        if 0 <= idx < len(self.itens_sessao):
            self.itens_sessao.pop(idx)
        self.lbl_qtd.configure(text=f"{len(self.itens_sessao)} itens")

    def _salvar(self):
        obra = self.entry_obra.get().strip()
        arquivo = self.entry_arquivo.get().strip()
        if not obra:
            messagebox.showwarning("Obra", "Informe o nome da obra.", parent=self)
            return
        if not arquivo:
            self._sugerir_arquivo()
            arquivo = self.entry_arquivo.get().strip()
        if not arquivo.lower().endswith(".pdf"):
            arquivo += ".pdf"
        if not self.itens_sessao:
            messagebox.showwarning("Itens", "Adicione pelo menos um código à lista.", parent=self)
            return

        data_ini = self.entry_data_ini.get().strip()
        data_trp = self.entry_data_trp.get().strip()
        erro_data = validar_datas_atestado(data_ini, data_trp)
        if erro_data:
            messagebox.showwarning("Datas", erro_data, parent=self)
            return

        linhas = []
        for it in self.itens_sessao:
            linhas.append({
                "OBRA": obra,
                "Obra_Arquivo": arquivo,
                "Tipo": it["tipo"],
                "Cod": it["cod"],
                "Desc": it["desc"],
                "UN": it["un"],
                "DATA INICIO": data_ini,
                "DATA  DE EMISSÃO TRP": data_trp,
            })

        try:
            n = adicionar_itens_atestado(self.caminho_base, linhas)
            sincronizar_cofre_da_base(self.caminho_base, self.caminho_cofre)
            registrar_cadastro(
                LOG_CADASTROS,
                obra,
                arquivo,
                self.itens_sessao,
                data_inicio=data_ini,
                data_trp=data_trp,
            )
        except (PermissionError, PlanilhaEmUsoError) as e:
            messagebox.showerror("Arquivo em uso", str(e), parent=self)
            return
        except Exception as e:
            messagebox.showerror("Erro", str(e), parent=self)
            return

        messagebox.showinfo(
            "Salvo",
            f"{n} item(ns) gravado(s) em Cofre_atestados_brasul.xlsx.",
            parent=self,
        )
        if self.on_salvo:
            self.on_salvo()
        self._fechar()
