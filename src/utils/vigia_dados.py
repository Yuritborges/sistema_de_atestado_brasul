"""
Monitora alterações na base/cofre na rede e dispara atualização da tela.
"""

from __future__ import annotations

from pathlib import Path


class VigiaDadosRede:
    """Verifica mtime dos arquivos a cada intervalo (via after do Tk)."""

    def __init__(self, caminhos: list[Path], intervalo_ms: int, ao_mudar):
        self._caminhos = [Path(p) for p in caminhos]
        self._intervalo_ms = intervalo_ms
        self._ao_mudar = ao_mudar
        self._widget = None
        self._ativo = False
        self._mtimes: dict[str, float | None] = {}
        self._pausado = False

    def _ler_mtimes(self) -> dict[str, float | None]:
        out = {}
        for p in self._caminhos:
            key = str(p)
            if p.exists():
                out[key] = p.stat().st_mtime
            else:
                out[key] = None
        return out

    def iniciar(self, widget) -> None:
        self._widget = widget
        self._ativo = True
        self._pausado = False
        self._mtimes = self._ler_mtimes()
        self._agendar()

    def pausar(self) -> None:
        self._pausado = True

    def retomar(self) -> None:
        self._pausado = False
        self._mtimes = self._ler_mtimes()

    def parar(self) -> None:
        self._ativo = False

    def _agendar(self) -> None:
        if self._ativo and self._widget:
            self._widget.after(self._intervalo_ms, self._tick)

    def _tick(self) -> None:
        if not self._ativo or not self._widget:
            return

        if not self._pausado:
            atual = self._ler_mtimes()
            if atual != self._mtimes:
                self._mtimes = atual
                try:
                    self._ao_mudar()
                except Exception as e:
                    print(f"Vigia dados: {e}")

        self._agendar()
