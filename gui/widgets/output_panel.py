from typing import Callable

import customtkinter as ctk

from gui.backend.tts import TTS_AVAILABLE, tts_missing_dependency_message
from gui.theme import COLORS as C

_TABS = (
    ("Tokens", "Tokens"),
    ("AST", "Árbol"),
    ("TAC", "Intermedio"),
    ("Python", "Python"),
    ("Reporte", "Reporte"),
    ("Resultado", "Salida"),
)
_TAB_LABELS = {key: label for key, label in _TABS}
_TAB_KEYS = tuple(key for key, _label in _TABS)
_WELCOME = (
    "  Escribe código .acc y presiona  ▶ Compilar  (Ctrl+Enter)\n\n"
    "  Qué muestra cada pestaña:\n\n"
    "    Tokens      →  cómo el compilador separa tu código en palabras y símbolos.\n"
    "    Árbol       →  la estructura lógica del programa ya entendida por el parser.\n"
    "    Intermedio  →  pasos internos antes de generar código final.\n"
    "    Python      →  el programa equivalente generado en Python.\n"
    "    Reporte     →  errores, advertencias y resumen de compilación.\n"
    "    Salida      →  lo que imprime tu programa al ejecutarse.\n"
    "    IA          →  explicación natural del código o de la línea actual.\n"
)


class OutputPanel(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        on_read_aloud: Callable[[], None],
        on_stop_tts:   Callable[[], None],
        **kwargs,
    ):
        super().__init__(
            parent, corner_radius=10,
            fg_color=C["bg_panel"], border_width=1, border_color=C["border"],
            **kwargs,
        )
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._on_read_aloud = on_read_aloud
        self._on_stop_tts   = on_stop_tts

        self._build_tabs()
        self.write("Reporte", _WELCOME)

    # ── build ────────────────────────────────────────────────────────────────

    def _build_tabs(self):
        self._tabs = ctk.CTkTabview(
            self, corner_radius=8, fg_color=C["bg_panel"],
            segmented_button_fg_color=C["bg_bar"],
            segmented_button_selected_color=C["bg_panel"],
            segmented_button_selected_hover_color=C["bg_panel"],
            segmented_button_unselected_hover_color="#1e293b",
        )
        self._tabs.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        self._boxes: dict[str, ctk.CTkTextbox] = {}
        self._tab_names: dict[str, str] = {}
        for key, label in _TABS:
            tab = self._tabs.add(label)
            self._tab_names[key] = label
            tab.grid_rowconfigure(0, weight=1)
            tab.grid_columnconfigure(0, weight=1)
            box = ctk.CTkTextbox(
                tab,
                font=ctk.CTkFont(family="Consolas", size=12),
                wrap="none", corner_radius=8, state="disabled",
                fg_color=C["bg_code"], text_color=C["txt"],
                border_width=1, border_color=C["border"],
                scrollbar_button_color=C["border"],
            )
            box.grid(row=0, column=0, sticky="nsew")
            self._boxes[key] = box

        self._build_ai_tab()

    def _build_ai_tab(self):
        tab = self._tabs.add("IA")
        tab.grid_rowconfigure(1, weight=1)
        tab.grid_columnconfigure(0, weight=1)

        # Controls bar
        ctrl = ctk.CTkFrame(tab, corner_radius=8, fg_color=C["bg_bar"], height=44)
        ctrl.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        ctrl.grid_propagate(False)
        ctrl.grid_columnconfigure(3, weight=1)

        self._btn_read = ctk.CTkButton(
            ctrl, text="🔊  Leer en voz alta", command=self._on_read_aloud,
            width=155, height=30, corner_radius=7,
            fg_color="#1e3a5f", hover_color="#1e40af",
            text_color=C["accent"], font=ctk.CTkFont(size=11),
            state="disabled",
        )
        self._btn_read.grid(row=0, column=0, padx=(10, 4), pady=7)

        self._btn_stop = ctk.CTkButton(
            ctrl, text="⏹  Detener", command=self._on_stop_tts,
            width=95, height=30, corner_radius=7,
            fg_color="transparent", border_width=1,
            border_color=C["border"], text_color=C["txt_dim"],
            font=ctk.CTkFont(size=11), state="disabled",
        )
        self._btn_stop.grid(row=0, column=1, padx=4, pady=7)

        ctk.CTkLabel(ctrl, text="│", text_color=C["border"]).grid(row=0, column=2, padx=6)

        self._lbl_ai_status = ctk.CTkLabel(
            ctrl, text="Esperando análisis…",
            font=ctk.CTkFont(size=11), text_color=C["txt_dim"],
        )
        self._lbl_ai_status.grid(row=0, column=3, padx=8, sticky="w")

        # Text area
        self._ai_box = ctk.CTkTextbox(
            tab, font=ctk.CTkFont(size=12),
            wrap="word", corner_radius=8, state="disabled",
            fg_color=C["bg_code"], text_color=C["txt"],
            border_width=1, border_color=C["border"],
            scrollbar_button_color=C["border"],
        )
        self._ai_box.grid(row=1, column=0, sticky="nsew")

    # ── public API ───────────────────────────────────────────────────────────

    def write(self, tab: str, text: str) -> None:
        box = self._boxes[tab]
        box.configure(state="normal")
        box.delete("1.0", "end")
        box.insert("1.0", text)
        box.configure(state="disabled")

    def show(self, tab: str) -> None:
        self._tabs.set(self._tab_names.get(tab, tab))

    def write_ai(self, text: str) -> None:
        self._ai_box.configure(state="normal")
        self._ai_box.delete("1.0", "end")
        self._ai_box.insert("1.0", text)
        self._ai_box.configure(state="disabled")

    def set_ai_status(self, text: str, color: str) -> None:
        self._lbl_ai_status.configure(text=text, text_color=color)

    def set_tts_buttons(self, read_enabled: bool, stop_enabled: bool) -> None:
        missing = tts_missing_dependency_message()
        tts_ok = TTS_AVAILABLE and read_enabled and missing is None
        self._btn_read.configure(state="normal" if tts_ok   else "disabled")
        self._btn_stop.configure(state="normal" if stop_enabled else "disabled")

        if missing and read_enabled:
            self._lbl_ai_status.configure(text=missing, text_color=C["warn"])
