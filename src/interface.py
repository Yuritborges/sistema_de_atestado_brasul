"""
Interface principal — consulta e cadastro de atestados FDE (Brasul).
"""

import os
import sys
import threading
from pathlib import Path

import pandas as pd
import customtkinter as ctk
from tkinter import ttk, filedialog, messagebox
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from config.settings import (
    CAMINHO_BASE,
    CAMINHO_COFRE,
    BASE_DIR,
    DATA_DIR,
    MAX_LINHAS_TABELA,
    USAR_REDE,
    VIGIA_INTERVALO_MS,
)
from config.version import APP_NAME, APP_VERSION
from base_loader import sincronizar_cofre_da_base, sincronizar_cofre_se_necessario
from ui.branding import (
    carregar_logo_sidebar,
    configurar_app_windows,
    vincular_icone_em_toplevels,
)
from ui.cadastro_atestado import CadastroAtestadoDialog
from ui.seletor_obra import SeletorObra
from ui.tema import *
from utils.busca import aplicar_filtro_data, aplicar_filtros, resumo_obra
from utils.datas import COL_VIEW_INICIO, COL_VIEW_TRP, rotulo_campo, texto_celula_data
from ui.dialogo_filtro_data import DialogoFiltroData
from utils.cofre_df import preparar_cofre, linhas_com_codigo_valido
from utils.texto import normalizar_busca, vincular_maiusculas
from utils.tipos import eh_acumulado, eh_quantitativa, tag_e_rotulo_tabela
from utils.rede_setup import garantir_base_na_rede
from utils.vigia_dados import VigiaDadosRede


# ---------------------------------------------------------------------------
# Janela principal
# ---------------------------------------------------------------------------

class CofreBrasul(ctk.CTk):

    # ──────────────────────────────────────────────────────────────────────────
    # CONSTRUTOR - Inicializa a janela e carrega os dados
    # ──────────────────────────────────────────────────────────────────────────
    def __init__(self):
        super().__init__()

        self.caminho_base = Path(CAMINHO_BASE)
        self.caminho_xls = str(CAMINHO_COFRE)
        self.pasta_output = str(CAMINHO_COFRE.parent)

        self.title(f"BRASUL — {APP_NAME} v{APP_VERSION}")
        self.geometry("1680x920")
        self.minsize(1280, 780)
        self.configure(fg_color=FUNDO)

        configurar_app_windows()
        vincular_icone_em_toplevels(self)

        self.df_completo = pd.DataFrame()
        self.df_filtro = pd.DataFrame()
        self._tipo_ativo = "TODOS"
        self._obra_ativa = "Todas as obras"
        self._sort_col = None
        self._sort_asc = True
        self._filtro_data = None
        self._timer_busca = None
        self._vigia = None
        self._atualizando_vigia = False

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main()
        self._atualizar_kpis()

        self.bind("<Escape>", lambda _e: self._limpar())
        self.lbl_contagem.configure(text="Carregando dados...")
        self.after(200, self._verificar_pasta_dados)
        threading.Thread(target=self._carregar_em_fundo, daemon=True).start()

    # ──────────────────────────────────────────────────────────────────────────
    # CARREGAMENTO DOS DADOS
    # ──────────────────────────────────────────────────────────────────────────
    def _carregar_em_fundo(self):
        try:
            sincronizar_cofre_se_necessario(self.caminho_base, CAMINHO_COFRE)
        except Exception as e:
            print(f"Aviso ao sincronizar cofre: {e}")
        self.after(0, self._finalizar_carga_inicial)

    def _finalizar_carga_inicial(self):
        self._carregar_dados()
        self._atualizar_kpis()
        self._pesquisar()
        self.entry_busca.focus()
        self._iniciar_vigia_tempo_real()

    def _verificar_pasta_dados(self):
        if garantir_base_na_rede(BASE_DIR):
            self._status_tempo_real("Base copiada para Z:\\")
        if not DATA_DIR.exists():
            messagebox.showwarning(
                "Pasta de dados inacessível",
                f"Não foi possível acessar:\n\n  {DATA_DIR}\n\n"
                "Confirme se a unidade Z: está conectada na rede.",
            )
            return
        if not Path(CAMINHO_BASE).exists():
            messagebox.showwarning(
                "Planilha de atestados",
                f"Arquivo não encontrado. Coloque o arquivo em:\n\n  {CAMINHO_BASE}",
            )

    def _iniciar_vigia_tempo_real(self):
        """Recarrega a tela quando outro usuário altera a base na rede."""
        self._vigia = VigiaDadosRede(
            [Path(CAMINHO_BASE), Path(CAMINHO_COFRE)],
            VIGIA_INTERVALO_MS,
            self._ao_mudanca_na_rede,
        )
        self._vigia.iniciar(self)

    def _ao_mudanca_na_rede(self):
        if self._atualizando_vigia:
            return
        self._atualizando_vigia = True
        try:
            sincronizar_cofre_se_necessario(self.caminho_base, CAMINHO_COFRE)
            self._carregar_dados()
            self._atualizar_kpis()
            self._pesquisar()
            self._status_tempo_real("Atualizado em tempo real")
        except Exception as e:
            print(f"Atualização automática: {e}")
        finally:
            self._atualizando_vigia = False

    def _status_tempo_real(self, texto: str):
        if hasattr(self, "lbl_status_vivo"):
            self.lbl_status_vivo.configure(text=texto, text_color=VERDE)
            self.after(3500, lambda: self.lbl_status_vivo.configure(
                text="Monitorando alterações na rede…",
                text_color=CINZA_TXT,
            ))

    def _carregar_dados(self):
        """Carrega o cofre e padroniza colunas/tipos para a tela."""
        self.df_completo = pd.DataFrame()
        if os.path.exists(self.caminho_xls):
            try:
                self.df_completo = preparar_cofre(pd.read_excel(self.caminho_xls))
            except Exception as e:
                print(f"Erro ao carregar dados: {e}")
        self._atualizar_combo_obras()

    def _atualizar_combo_obras(self):
        if not hasattr(self, "seletor_obra"):
            return
        if self.df_completo.empty:
            self.seletor_obra.set_obras([])
        else:
            self.seletor_obra.set_obras(self.df_completo["Obra"].astype(str).tolist())
        self.seletor_obra.set(self._obra_ativa)

    def _ao_mudar_obra(self, escolha):
        self._obra_ativa = escolha
        self._pesquisar()

    def _abrir_cadastro(self):
        cores = {
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
        if self._vigia:
            self._vigia.pausar()
        CadastroAtestadoDialog(
            self,
            self.caminho_base,
            CAMINHO_COFRE,
            cores,
            on_salvo=self._apos_cadastro,
            on_fechar=self._retomar_vigia,
        )

    def _apos_cadastro(self):
        try:
            sincronizar_cofre_da_base(self.caminho_base, CAMINHO_COFRE)
        except Exception:
            pass
        self._carregar_dados()
        self._atualizar_kpis()
        self._pesquisar()
        self._status_tempo_real("Cadastro salvo na rede")

    def _retomar_vigia(self):
        if self._vigia:
            self._vigia.retomar()

    def _norm(self, txt: str) -> str:
        return normalizar_busca(txt)

    # ══════════════════════════════════════════════════════════════════════════
    # BARRA LATERAL (SIDEBAR)
    # ══════════════════════════════════════════════════════════════════════════
    # Contém o logotipo, os KPIs (indicadores) e os botões de ação.
    # ══════════════════════════════════════════════════════════════════════════

    def _build_sidebar(self):
        """Monta a barra lateral esquerda com todos os elementos."""
        self.sidebar = ctk.CTkFrame(self, width=300, fg_color=BRANCO, corner_radius=0,
                                    border_width=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_columnconfigure(0, weight=1)

        # Barra amarela no topo (detalhe visual)
        topo = ctk.CTkFrame(self.sidebar, height=6, fg_color=AMARELO, corner_radius=0)
        topo.pack(fill="x")

        # Logotipo principal (grande, margens reduzidas)
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(padx=10, pady=(10, 6), fill="x")

        self._logo_sidebar = carregar_logo_sidebar()
        if self._logo_sidebar:
            ctk.CTkLabel(logo_frame, image=self._logo_sidebar, text="").pack(anchor="center")
        else:
            ctk.CTkLabel(logo_frame, text="BRASUL", font=("Segoe UI", 28, "bold"),
                         text_color=PRETO).pack(anchor="center")

        # Separador
        ctk.CTkFrame(self.sidebar, height=1, fg_color=BORDA).pack(fill="x", padx=0)

        # ── KPIs (Cards com números) ──
        kpi_container = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        kpi_container.pack(fill="x", padx=18, pady=20)
        kpi_container.grid_columnconfigure((0, 1), weight=1)

        self.kpi_obras = self._kpi(kpi_container, "OBRAS", 0, 0, AZUL, "🏢")
        self.kpi_itens = self._kpi(kpi_container, "ITENS", 1, 0, VERDE, "📦")
        self.kpi_acum = self._kpi(kpi_container, "ACUMULADO", 0, 1, AZUL, "📊")
        self.kpi_quant = self._kpi(kpi_container, "QUANTITATIVA", 1, 1, VERDE, "📋")

        # Separador
        ctk.CTkFrame(self.sidebar, height=1, fg_color=BORDA).pack(fill="x", padx=0)

        # ── Botões de ação ──
        btn_area = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        btn_area.pack(fill="x", padx=18, pady=20)

        ctk.CTkButton(
            btn_area,
            text="NOVO ATESTADO",
            fg_color=AMARELO,
            text_color=PRETO,
            hover_color=AMARELO_ESC,
            height=56,
            corner_radius=12,
            font=F_BTN,
            command=self._abrir_cadastro,
        ).pack(fill="x", pady=(0, 10))

        ctk.CTkButton(
            btn_area, text="⬆  EXPORTAR BUSCA",
            fg_color=VERDE, text_color=BRANCO,
            hover_color="#16A34A", height=52, corner_radius=12,
            font=F_BTN, command=self._exportar).pack(fill="x", pady=(0, 10))

        ctk.CTkButton(
            btn_area, text="↺  RECARREGAR DADOS",
            fg_color=FUNDO, text_color=PRETO,
            hover_color=BORDA, border_width=1, border_color=BORDA,
            height=48, corner_radius=12,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            command=self._recarregar).pack(fill="x")

        # ── Rodapé (pasta na rede + monitoramento) ──
        ctk.CTkFrame(self.sidebar, height=1, fg_color=BORDA).pack(side="bottom", fill="x")
        pasta_txt = str(DATA_DIR)
        if len(pasta_txt) > 42:
            pasta_txt = "…" + pasta_txt[-39:]
        rede_tag = "Z: rede" if USAR_REDE else "local"
        ctk.CTkLabel(
            self.sidebar,
            text=f"Dados: {pasta_txt}\n({rede_tag})",
            font=ctk.CTkFont(family="Segoe UI", size=9),
            text_color="#888888",
            wraplength=SIDEBAR_W - 24,
        ).pack(side="bottom", pady=(8, 2))
        self.lbl_status_vivo = ctk.CTkLabel(
            self.sidebar,
            text="Monitorando alterações na rede…",
            font=ctk.CTkFont(family="Segoe UI", size=9, slant="italic"),
            text_color=CINZA_TXT,
            wraplength=SIDEBAR_W - 24,
        )
        self.lbl_status_vivo.pack(side="bottom", pady=(0, 4))
        ctk.CTkLabel(self.sidebar, text=f"Brasul Construtora  ·  v{APP_VERSION}",
                     font=ctk.CTkFont(family="Segoe UI", size=10),
                     text_color="#AAAAAA").pack(side="bottom", pady=10)

    def _kpi(self, parent, label, col, row, cor, icone=""):
        """Cria um card de KPI com ícone e número."""
        frame = ctk.CTkFrame(parent, fg_color=FUNDO, corner_radius=12, height=95)
        frame.grid(row=row, column=col, padx=6, pady=6, sticky="ew")
        frame.grid_propagate(False)

        inner = ctk.CTkFrame(frame, fg_color="transparent")
        inner.pack(expand=True, fill="both", padx=12, pady=10)

        # Linha superior com ícone e número
        top_row = ctk.CTkFrame(inner, fg_color="transparent")
        top_row.pack(fill="x", expand=True)

        if icone:
            ctk.CTkLabel(top_row, text=icone, font=ctk.CTkFont(size=20),
                         text_color=cor).pack(side="left")

        lbl_n = ctk.CTkLabel(top_row, text="0", font=F_KPI_N, text_color=cor)
        lbl_n.pack(side="right")

        ctk.CTkLabel(inner, text=label, font=F_KPI_L,
                     text_color=CINZA_TXT).pack(pady=(5, 0))

        setattr(self, f"_kn_{label.lower().split()[0]}", lbl_n)
        return lbl_n

    # ══════════════════════════════════════════════════════════════════════════
    # ÁREA PRINCIPAL
    # ══════════════════════════════════════════════════════════════════════════
    # Contém o cabeçalho, o campo de busca, os botões de filtro e a tabela
    # com os resultados.
    # ══════════════════════════════════════════════════════════════════════════

    def _build_main(self):
        """Monta a área principal da interface (busca e tabela)."""
        self.main = ctk.CTkFrame(self, fg_color="transparent")
        self.main.grid(row=0, column=1, padx=28, pady=24, sticky="nsew")
        self.main.grid_rowconfigure(2, weight=1)
        self.main.grid_columnconfigure(0, weight=1)

        # ── Cabeçalho com título e data ──
        topo = ctk.CTkFrame(self.main, fg_color="transparent")
        topo.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        topo.grid_columnconfigure(0, weight=1)

        left = ctk.CTkFrame(topo, fg_color="transparent")
        left.pack(side="left")

        ctk.CTkLabel(left, text="Busca de atestados",
                     font=F_TITULO, text_color=PRETO).pack(anchor="w")
        subt = "Consulta Cofre_atestados_brasul — busque por obra, código ou descrição"
        ctk.CTkLabel(left, text=subt, font=F_LABEL, text_color=CINZA_TXT).pack(anchor="w")

        # Data atual formatada
        from datetime import date
        meses = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                 "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
        d = date.today()
        ctk.CTkLabel(topo,
                     text=f"{d.day} de {meses[d.month]} de {d.year}",
                     font=F_LABEL, text_color=CINZA_TXT).pack(side="right")

        # ── Card de busca ──
        busca_card = ctk.CTkFrame(self.main, fg_color=CARD_BG, corner_radius=16,
                                  border_width=1, border_color=BORDA)
        busca_card.grid(row=1, column=0, sticky="ew", pady=(0, 16))

        # Linha do campo de busca
        linha1 = ctk.CTkFrame(busca_card, fg_color="transparent")
        linha1.pack(fill="x", padx=20, pady=(18, 12))

        ctk.CTkLabel(linha1, text="🔍",
                     font=ctk.CTkFont(size=22)).pack(side="left", padx=(0, 12))

        self.entry_busca = ctk.CTkEntry(
            linha1,
            placeholder_text="Busque por código (ex: 02.01.001) ou descrição (ex: ESCAVAÇÃO, AÇO, CONCRETO, PINTURA)...",
            height=56, border_width=0,
            fg_color="#F8F9FB",
            font=F_BUSCA,
            text_color=PRETO,
            corner_radius=12)
        self.entry_busca.pack(side="left", fill="x", expand=True, padx=(0, 12))
        vincular_maiusculas(self.entry_busca)
        self.entry_busca.bind("<Return>", lambda _e: self._pesquisar())
        self.entry_busca.bind("<Escape>", lambda _e: self._limpar())
        self.entry_busca.bind("<KeyRelease>", self._debounce_busca)

        ctk.CTkButton(
            linha1, text="BUSCAR",
            fg_color=AMARELO, text_color=PRETO,
            hover_color=AMARELO_ESC,
            width=130, height=56, corner_radius=12, font=F_BTN,
            command=self._pesquisar).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            linha1, text="✕",
            fg_color="#F0F0F0", text_color=PRETO,
            hover_color=BORDA,
            width=54, height=56, corner_radius=12, font=F_BTN,
            command=self._limpar).pack(side="left")

        # ── Filtros por tipo (apenas 3: Todos, Acumulado, Quantitativa) ──
        linha2 = ctk.CTkFrame(busca_card, fg_color="transparent")
        linha2.pack(fill="x", padx=20, pady=(0, 16))

        ctk.CTkLabel(linha2, text="Filtrar por tipo:",
                     font=F_LABEL, text_color=CINZA_TXT).pack(side="left", padx=(0, 12))

        self._chips = {}
        cores_botoes = {
            "TODOS": (PRETO, BRANCO),
            "ACUMULADO": (AZUL, BRANCO),
            "QUANTITATIVA": (VERDE, BRANCO),
        }

        for nome, val in [("Todos", "TODOS"),
                          ("Acumulado", "ACUMULADO"),
                          ("Quantitativa", "QUANTITATIVA")]:
            cor_fundo, cor_texto = cores_botoes[val]
            btn = ctk.CTkButton(
                linha2, text=nome, width=130, height=36,
                corner_radius=18,
                fg_color=cor_fundo if val == "TODOS" else "#EFEFEF",
                text_color=cor_texto if val == "TODOS" else CINZA_TXT,
                hover_color=cor_fundo,
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                command=lambda v=val, ca=cor_fundo, ct=cor_texto: self._set_tipo(v, ca, ct))
            btn.pack(side="left", padx=5)
            self._chips[val] = (btn, cor_fundo, cor_texto)

        linha3 = ctk.CTkFrame(busca_card, fg_color="transparent")
        linha3.pack(fill="x", padx=20, pady=(0, 8))

        ctk.CTkLabel(linha3, text="Obra:", font=F_LABEL, text_color=CINZA_TXT).pack(
            side="left", padx=(0, 8)
        )
        cores_sel = {
            "AMARELO": AMARELO,
            "AMARELO_ESC": AMARELO_ESC,
            "PRETO": PRETO,
            "BRANCO": BRANCO,
            "FUNDO": FUNDO,
            "BORDA": BORDA,
        }
        self.seletor_obra = SeletorObra(
            linha3, on_selecao=self._ao_mudar_obra, cores=cores_sel, largura=340,
        )
        self.seletor_obra.pack(side="left", padx=(0, 12))

        self.btn_filtro_data = ctk.CTkButton(
            linha3,
            text="📅  Filtrar por data",
            width=170,
            height=36,
            corner_radius=10,
            fg_color="#EFF6FF",
            text_color=AZUL,
            hover_color=AZUL_LITE,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            command=self._abrir_filtro_data,
        )
        self.btn_filtro_data.pack(side="left", padx=(0, 12))

        self.lbl_resumo_obra = ctk.CTkLabel(
            busca_card, text="",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=AZUL,
        )
        self.lbl_resumo_obra.pack(anchor="w", padx=20, pady=(0, 12))

        # ── Tabela de resultados ──
        tab_card = ctk.CTkFrame(self.main, fg_color=CARD_BG, corner_radius=16,
                                border_width=1, border_color=BORDA)
        tab_card.grid(row=2, column=0, sticky="nsew")
        tab_card.grid_rowconfigure(1, weight=1)
        tab_card.grid_columnconfigure(0, weight=1)

        # Cabeçalho da tabela (título e contagem)
        cab = ctk.CTkFrame(tab_card, fg_color="transparent")
        cab.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(16, 10))

        self.lbl_titulo_res = ctk.CTkLabel(
            cab, text="Aguardando pesquisa…",
            font=F_SECAO, text_color=PRETO)
        self.lbl_titulo_res.pack(side="left")

        self.lbl_contagem = ctk.CTkLabel(cab, text="",
                                         font=F_LABEL, text_color=CINZA_TXT)
        self.lbl_contagem.pack(side="right")

        # Configuração da Treeview (tabela)
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Brasul.Treeview",
                        background=BRANCO,
                        fieldbackground=BRANCO,
                        rowheight=46,
                        font=('Segoe UI', 10),
                        borderwidth=0, relief="flat")
        style.configure("Brasul.Treeview.Heading",
                        font=('Segoe UI', 10, 'bold'),
                        background="#F8FAFC",
                        foreground=PRETO,
                        relief="flat",
                        borderwidth=0, padding=12)
        style.map("Brasul.Treeview",
                  background=[('selected', AMARELO_LITE)],
                  foreground=[('selected', PRETO)])

        # Datas antes da descrição (fixas); descrição por último e estica — cabeçalhos não cortam
        colunas = ("tipo", "obra", "cod", "un", "data_ini", "data_trp", "desc")
        self.tabela = ttk.Treeview(tab_card, columns=colunas,
                                   show="headings",
                                   style="Brasul.Treeview",
                                   selectmode="extended")

        headers_cfg = {
            "tipo": ("TIPO", 96, "center"),
            "obra": ("ESCOLA / OBRA", 260, "w"),
            "cod": ("CÓDIGO", 112, "center"),
            "un": ("UN", 52, "center"),
            "data_ini": ("DATA INÍCIO", 108, "center"),
            "data_trp": ("DATA EMISSÃO TPR", 158, "center"),
            "desc": ("DESCRIÇÃO DO SERVIÇO", 320, "w"),
        }
        for col, (h, w, anc) in headers_cfg.items():
            self.tabela.heading(col, text=h,
                                command=lambda c=col: self._ordenar(c))
            estica = col == "desc"
            self.tabela.column(
                col,
                width=w,
                anchor=anc,
                minwidth=140 if estica else w,
                stretch=estica,
            )

        # Cores para diferentes tipos de itens
        self.tabela.tag_configure("ACUMULADO", background=AZUL_LITE, foreground=AZUL)
        self.tabela.tag_configure("QUANTITATIVA", background=VERDE_LITE, foreground=VERDE)
        self.tabela.tag_configure("AMBOS", background=LILAS_LITE, foreground=LILAS)
        self.tabela.tag_configure("PAR", background=BRANCO, foreground=PRETO)
        self.tabela.tag_configure("IMPAR", background=CINZA_LINHA, foreground=PRETO)

        # Barras de rolagem
        vsb = ttk.Scrollbar(tab_card, orient="vertical", command=self.tabela.yview)
        hsb = ttk.Scrollbar(tab_card, orient="horizontal", command=self.tabela.xview)
        self.tabela.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        tab_card.grid_columnconfigure(1, minsize=20)
        self.tabela.grid(row=1, column=0, sticky="nsew", padx=(16, 4), pady=(0, 8))
        vsb.grid(row=1, column=1, sticky="ns", padx=(0, 8), pady=(0, 8))
        hsb.grid(row=2, column=0, columnspan=2, sticky="ew", padx=(16, 16), pady=(0, 12))

    # ══════════════════════════════════════════════════════════════════════════
    # ATUALIZAÇÃO DOS KPIs
    # ══════════════════════════════════════════════════════════════════════════
    def _atualizar_kpis(self):
        """Atualiza os números dos cards (OBRAS, ITENS, ACUMULADO, QUANTITATIVA)."""
        if self.df_completo.empty:
            for attr in ['kpi_obras', 'kpi_itens', 'kpi_acum', 'kpi_quant']:
                getattr(self, attr).configure(text="0")
            return

        df = self.df_completo
        obras = df["Obra"].nunique()
        validos = linhas_com_codigo_valido(df)
        itens = len(validos)
        acum = int(validos["Tipo"].apply(eh_acumulado).sum())
        quant = int(validos["Tipo"].apply(eh_quantitativa).sum())

        self.kpi_obras.configure(text=str(obras))
        self.kpi_itens.configure(text=str(itens))
        self.kpi_acum.configure(text=str(acum))
        self.kpi_quant.configure(text=str(quant))

    # ══════════════════════════════════════════════════════════════════════════
    # BUSCA E FILTROS
    # ══════════════════════════════════════════════════════════════════════════
    def _debounce_busca(self, _=None):
        """Aguarda um pequeno intervalo antes de executar a busca.
        Isso evita processar a cada tecla digitada."""
        if self._timer_busca:
            self.after_cancel(self._timer_busca)
        self._timer_busca = self.after(260, self._pesquisar)

    def _pesquisar(self, _=None):
        """Filtra por texto, tipo e obra; atualiza resumo e histórico."""
        termo = self.entry_busca.get().strip()
        tipo = self._tipo_ativo
        obra = self._obra_ativa

        if self.df_completo.empty:
            self.lbl_titulo_res.configure(text="Nenhum dado carregado.")
            self.lbl_resumo_obra.configure(text="")
            return

        df = aplicar_filtros(self.df_completo, termo, tipo, obra, self._norm)
        if self._filtro_data:
            df = aplicar_filtro_data(
                df,
                self._filtro_data.get("campo"),
                self._filtro_data.get("de"),
                self._filtro_data.get("ate"),
            )
        self.df_filtro = df
        self._popular_tabela(df)

        txt_resumo = resumo_obra(self.df_completo, obra)
        if not txt_resumo and termo and not df.empty and df["Obra"].nunique() == 1:
            txt_resumo = resumo_obra(self.df_completo, df["Obra"].iloc[0])
        self.lbl_resumo_obra.configure(text=txt_resumo)

    def _abrir_filtro_data(self):
        cores = {
            "PRETO": PRETO,
            "CINZA_TXT": CINZA_TXT,
            "BORDA": BORDA,
            "AZUL": AZUL,
        }
        DialogoFiltroData(
            self,
            self._filtro_data,
            cores,
            on_aplicar=self._definir_filtro_data,
        )

    def _definir_filtro_data(self, filtro: dict | None):
        self._filtro_data = filtro
        self._atualizar_btn_filtro_data()
        self._pesquisar()

    def _atualizar_btn_filtro_data(self):
        if not hasattr(self, "btn_filtro_data"):
            return
        if not self._filtro_data:
            self.btn_filtro_data.configure(
                text="📅  Filtrar por data",
                fg_color="#EFF6FF",
                text_color=AZUL,
            )
            return
        f = self._filtro_data
        campo = rotulo_campo(f.get("campo", "inicio"))
        de = f.get("de")
        ate = f.get("ate")
        if de and ate:
            periodo = f"{de.strftime('%d/%m/%Y')} — {ate.strftime('%d/%m/%Y')}"
        elif de:
            periodo = f"a partir de {de.strftime('%d/%m/%Y')}"
        elif ate:
            periodo = f"até {ate.strftime('%d/%m/%Y')}"
        else:
            periodo = ""
        self.btn_filtro_data.configure(
            text=f"📅  {campo}: {periodo}",
            fg_color=AZUL,
            text_color=BRANCO,
        )

    def _set_tipo(self, val, cor_ativa, cor_txt):
        """Altera o filtro ativo e atualiza a aparência dos botões."""
        self._tipo_ativo = val
        for v, (btn, ca, ct) in self._chips.items():
            if v == val:
                btn.configure(fg_color=ca, text_color=ct)
            else:
                btn.configure(fg_color="#EFEFEF", text_color=CINZA_TXT)
        self._pesquisar()

    # ══════════════════════════════════════════════════════════════════════════
    # POPULAÇÃO DA TABELA
    # ══════════════════════════════════════════════════════════════════════════
    def _popular_tabela(self, df: pd.DataFrame):
        """Preenche a tabela com os dados filtrados."""
        self.tabela.delete(*self.tabela.get_children())

        MAX = MAX_LINHAS_TABELA
        for i, (_, row) in enumerate(df.head(MAX).iterrows()):
            label, tag = tag_e_rotulo_tabela(row.get("Tipo", ""))
            if tag == "PAR":
                tag = "PAR" if i % 2 == 0 else "IMPAR"
            prefixo = {"ACUMULADO": "📊  ", "QUANTITATIVA": "📋  ", "AMBOS": "🔄  "}
            if tag in prefixo:
                label = prefixo[tag] + label

            self.tabela.insert("", "end", tags=(tag,), values=(
                label,
                str(row.get('Obra', '')),
                str(row.get('Cod', '')),
                str(row.get('UN', '')),
                texto_celula_data(row.get(COL_VIEW_INICIO, '')),
                texto_celula_data(row.get(COL_VIEW_TRP, '')),
                str(row.get('Desc', '')),
            ))

        total = len(df)
        exib = min(total, MAX)
        suf = f"  (exibindo {exib} de {total})" if total > MAX else ""

        self.lbl_titulo_res.configure(text="Resultados")
        self.lbl_contagem.configure(
            text=f"🔎  {total} item{'ns' if total != 1 else ''} encontrado{'s' if total != 1 else ''}{suf}")

    def _limpar_tabela(self):
        """Limpa a tabela e reseta o estado do filtro."""
        self.tabela.delete(*self.tabela.get_children())
        self.df_filtro = pd.DataFrame()
        self.lbl_titulo_res.configure(text="Aguardando pesquisa…")
        self.lbl_contagem.configure(text="")

    def _limpar(self):
        """Limpa busca, obra e filtros (atalho Esc)."""
        self.entry_busca.delete(0, "end")
        self._obra_ativa = "Todas as obras"
        if hasattr(self, "seletor_obra"):
            self.seletor_obra.set("Todas as obras")
        self._tipo_ativo = "TODOS"
        self._filtro_data = None
        self._atualizar_btn_filtro_data()
        for val, (btn, ca, ct) in self._chips.items():
            if val == "TODOS":
                btn.configure(fg_color=ca, text_color=ct)
            else:
                btn.configure(fg_color="#EFEFEF", text_color=CINZA_TXT)
        self.lbl_resumo_obra.configure(text="")
        self._pesquisar()
        self.entry_busca.focus()

    # ══════════════════════════════════════════════════════════════════════════
    # ORDENAÇÃO
    # ══════════════════════════════════════════════════════════════════════════
    def _ordenar(self, col):
        """Ordena a tabela pela coluna clicada (alterna ascendente/descendente)."""
        if self._sort_col == col:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col
            self._sort_asc = True

        mapa = {
            "tipo": "Tipo",
            "obra": "Obra",
            "cod": "Cod",
            "desc": "Desc",
            "un": "UN",
            "data_ini": COL_VIEW_INICIO,
            "data_trp": COL_VIEW_TRP,
        }
        col_df = mapa.get(col, col)

        if not self.df_filtro.empty and col_df in self.df_filtro.columns:
            serie = self.df_filtro[col_df]
            if col in ("data_ini", "data_trp"):
                from utils.datas import COL_DT_INICIO, COL_DT_TRP
                col_ord = COL_DT_INICIO if col == "data_ini" else COL_DT_TRP
                if col_ord in self.df_filtro.columns:
                    serie = self.df_filtro[col_ord]
            self._popular_tabela(
                self.df_filtro.iloc[serie.sort_values(
                    ascending=self._sort_asc, na_position="last"
                ).index]
            )

    # ---------------------------------------------------------------------------
    # Exportar e recarregar
    # ---------------------------------------------------------------------------
    def _exportar(self):
        """Exporta os dados filtrados para um arquivo Excel."""
        if self.df_filtro.empty:
            messagebox.showwarning(
                "Sem dados para exportar",
                "Realize uma busca primeiro para exportar os resultados.")
            return

        path = filedialog.asksaveasfilename(
            title="Salvar resultado",
            defaultextension=".xlsx",
            initialfile="Relatorio_Busca_Atestados_Brasul.xlsx",
            filetypes=[("Planilha Excel", "*.xlsx")])
        if not path:
            return

        try:
            self.df_filtro.to_excel(path, index=False)
            messagebox.showinfo(
                "✅  Exportado",
                f"Planilha salva com {len(self.df_filtro)} registros!")
        except Exception as e:
            messagebox.showerror("Erro ao exportar", str(e))

    def _recarregar(self):
        """Recarrega os dados do Excel e atualiza a interface."""
        try:
            stats = sincronizar_cofre_da_base(
                self.caminho_base, CAMINHO_COFRE)
            extra = (
                f"\n\n{stats['linhas']} itens | {stats['obras']} obras | "
                f"{stats['pdfs']} arquivos"
            )
        except Exception as e:
            messagebox.showerror("Erro ao sincronizar", str(e))
            return

        self._carregar_dados()
        self._atualizar_kpis()
        self._limpar()
        total = len(self.df_completo)
        messagebox.showinfo(
            "Dados atualizados",
            f"Banco recarregado com {total} registros.{extra}")


# ═══════════════════════════════════════════════════════════════════════════════
# PONTO DE ENTRADA
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = CofreBrasul()
    app.mainloop()