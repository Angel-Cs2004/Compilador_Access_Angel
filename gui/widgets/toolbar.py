from typing import Callable

import customtkinter as ctk

from gui.theme import COLORS as C


class Toolbar(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        on_open:    Callable,
        on_save:    Callable,
        on_clear:   Callable,
        on_ai:      Callable,
        on_compile: Callable,
        on_execute: Callable,
        **kwargs,
    ):
        super().__init__(parent, corner_radius=0, height=58, fg_color=C["bg_bar"], **kwargs)
        self.grid_propagate(False)
        self.grid_columnconfigure(10, weight=1)

        self._build(on_open, on_save, on_clear, on_ai, on_compile, on_execute)

    def _build(self, on_open, on_save, on_clear, on_ai, on_compile, on_execute):
        ctk.CTkLabel(
            self, text="  ◈  Compilador Accesible",
            font=ctk.CTkFont(size=17, weight="bold"), text_color=C["accent"],
        ).grid(row=0, column=0, padx=18, pady=14, sticky="w")

        self._sep(1)

        for col, (label, cmd) in enumerate(
            [("  Abrir", on_open), ("  Guardar", on_save), ("  Limpiar", on_clear)],
            start=2,
        ):
            ctk.CTkButton(
                self, text=label, command=cmd,
                width=100, height=36, corner_radius=8,
                fg_color="transparent", border_width=1,
                border_color=C["border"], text_color=C["txt"],
                hover_color="#1e293b", font=ctk.CTkFont(size=12),
            ).grid(row=0, column=col, padx=4, pady=11)

        self._sep(5)

        self._btn_ai = ctk.CTkButton(
            self, text="✦  Analizar con IA", command=on_ai,
            width=160, height=36, corner_radius=8,
            fg_color="#3b0764", hover_color="#4c1d95",
            text_color=C["ia"], font=ctk.CTkFont(size=12, weight="bold"),
            border_width=1, border_color="#7c3aed",
        )
        self._btn_ai.grid(row=0, column=6, padx=4, pady=11)

        self._sep(7)

        self._btn_compile = ctk.CTkButton(
            self, text="▶  Compilar   Ctrl+↵", command=on_compile,
            width=190, height=36, corner_radius=8,
            fg_color="#166534", hover_color="#15803d",
            text_color=C["ok"], font=ctk.CTkFont(size=13, weight="bold"),
            border_width=1, border_color=C["ok"],
        )
        self._btn_compile.grid(row=0, column=8, padx=(16, 4), pady=11)

        self._sep(9)

        self._btn_execute = ctk.CTkButton(
            self, text="▶▶  Ejecutar   Ctrl+E", command=on_execute,
            width=190, height=36, corner_radius=8,
            fg_color="#7c2d12", hover_color="#9a3412",
            text_color="#fb923c", font=ctk.CTkFont(size=13, weight="bold"),
            border_width=1, border_color="#fb923c",
        )
        self._btn_execute.grid(row=0, column=10, padx=(4, 16), pady=11)

    def _sep(self, col: int):
        ctk.CTkLabel(self, text="│", text_color=C["border"]).grid(row=0, column=col, padx=4)

    # ── state helpers ────────────────────────────────────────────────────────

    def set_compiling(self, busy: bool) -> None:
        if busy:
            self._btn_compile.configure(state="disabled", text="⏳  Compilando…")
            self._btn_execute.configure(state="disabled")
        else:
            self._btn_compile.configure(state="normal", text="▶  Compilar   Ctrl+↵")
            self._btn_execute.configure(state="normal")

    def set_executing(self, busy: bool) -> None:
        if busy:
            self._btn_execute.configure(state="disabled", text="⏳  Ejecutando…")
            self._btn_compile.configure(state="disabled")
        else:
            self._btn_execute.configure(state="normal", text="▶▶  Ejecutar   Ctrl+E")
            self._btn_compile.configure(state="normal")

    def set_ai_busy(self, busy: bool) -> None:
        if busy:
            self._btn_ai.configure(state="disabled", text="✦  Analizando…")
        else:
            self._btn_ai.configure(state="normal", text="✦  Analizar con IA")
