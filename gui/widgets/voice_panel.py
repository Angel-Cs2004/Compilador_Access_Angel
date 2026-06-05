import os
import threading
import urllib.request
import zipfile
from typing import Callable

import customtkinter as ctk

from gui.backend.recognition import (
    CMDS_CLEAR, CMDS_COMPILE, CMDS_NEWLINE, CMDS_UNDO,
    VOICE_AVAILABLE, VoiceRecognizer, normalize, to_code,
)
from gui.theme import COLORS as C

_MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "voz", "models", "vosk-model-small-es-0.42",
)
_MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip"


class VoicePanel(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        on_insert:  Callable[[str], None],
        on_compile: Callable[[], None],
        on_clear:   Callable[[], None],
        on_undo:    Callable[[], None],
        on_status:  Callable[[str, str], None],
        **kwargs,
    ):
        super().__init__(
            parent, corner_radius=8,
            fg_color=C["bg_bar"], border_width=1, border_color=C["border"],
            **kwargs,
        )
        self._on_insert  = on_insert
        self._on_compile = on_compile
        self._on_clear   = on_clear
        self._on_undo    = on_undo
        self._on_status  = on_status
        self._active     = False
        self._recognizer: VoiceRecognizer | None = None

        self.grid_columnconfigure(1, weight=1)
        self._build()
        self._refresh()

    # ── build ────────────────────────────────────────────────────────────────

    def _build(self):
        ctk.CTkLabel(self, text="🎙", font=ctk.CTkFont(size=15)).grid(
            row=0, column=0, padx=(12, 4), pady=(10, 2), sticky="w")

        ctk.CTkLabel(self, text="Entrada por voz",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=C["mic"]).grid(
            row=0, column=1, pady=(10, 2), sticky="w")

        self._dot = ctk.CTkLabel(self, text="●", font=ctk.CTkFont(size=12),
                                 text_color=C["txt_dim"])
        self._dot.grid(row=0, column=2, padx=(4, 2), pady=(10, 2))

        self._lbl_state = ctk.CTkLabel(self, text="Inactiva",
                                       font=ctk.CTkFont(size=11),
                                       text_color=C["txt_dim"])
        self._lbl_state.grid(row=0, column=3, padx=(0, 12), pady=(10, 2), sticky="e")

        self._btn = ctk.CTkButton(self, text="", width=210, height=30,
                                  corner_radius=7, font=ctk.CTkFont(size=11))
        self._btn.grid(row=1, column=0, columnspan=2, padx=12, pady=(2, 4), sticky="w")

        self._lbl_partial = ctk.CTkLabel(self, text="",
                                         font=ctk.CTkFont(family="Consolas", size=11),
                                         text_color=C["txt_dim"], anchor="w")
        self._lbl_partial.grid(row=1, column=2, columnspan=2,
                               padx=(4, 12), pady=(2, 4), sticky="ew")

        ctk.CTkLabel(
            self,
            text='  Comandos: "nueva linea"  ·  "compilar"  ·  "limpiar"  ·  "deshacer"',
            font=ctk.CTkFont(size=10), text_color=C["txt_dim"],
        ).grid(row=2, column=0, columnspan=4, padx=12, pady=(0, 8), sticky="w")

    # ── button state machine ─────────────────────────────────────────────────

    def _refresh(self):
        if not VOICE_AVAILABLE:
            self._btn.configure(
                text="  pip install vosk pyaudio",
                fg_color="#7c3aed", hover_color="#6d28d9",
                text_color="white", state="disabled", command=lambda: None,
            )
            self._lbl_state.configure(text="Libs no instaladas", text_color=C["warn"])
            self._dot.configure(text_color=C["warn"])
        elif not os.path.isdir(_MODEL_PATH):
            self._btn.configure(
                text="⬇  Descargar modelo de voz (~39 MB)",
                fg_color="#7c3aed", hover_color="#6d28d9",
                text_color="white", state="normal", command=self._download,
            )
            self._lbl_state.configure(text="Modelo no instalado", text_color=C["warn"])
            self._dot.configure(text_color=C["warn"])
        elif self._active:
            self._btn.configure(
                text="⏹  Detener voz",
                fg_color="#7f1d1d", hover_color="#991b1b",
                text_color=C["err"], state="normal", command=self._deactivate,
            )
            self._lbl_state.configure(text="Escuchando…", text_color=C["mic"])
            self._dot.configure(text_color=C["mic"])
        else:
            self._btn.configure(
                text="🎙  Activar voz",
                fg_color="#4c1d95", hover_color="#5b21b6",
                text_color=C["mic"], state="normal", command=self._activate,
            )
            self._lbl_state.configure(text="Inactiva", text_color=C["txt_dim"])
            self._dot.configure(text_color=C["txt_dim"])

    # ── voice lifecycle ──────────────────────────────────────────────────────

    def _activate(self):
        self._active = True
        self._btn.configure(state="disabled", text="Cargando modelo…")
        self._lbl_state.configure(text="Cargando…", text_color=C["warn"])
        self._dot.configure(text_color=C["warn"])
        self._recognizer = VoiceRecognizer(
            model_path=_MODEL_PATH,
            on_ready  =lambda: self.after(0, self._on_ready),
            on_final  =lambda t: self.after(0, self._on_final, t),
            on_partial=lambda t: self.after(0, lambda: self._lbl_partial.configure(
                text=f"  {t}…" if t else "")),
            on_error  =lambda e: self.after(0, self._on_error, e),
        )
        self._recognizer.start()

    def _deactivate(self):
        self._active = False
        if self._recognizer:
            self._recognizer.stop()
            self._recognizer = None
        self._lbl_partial.configure(text="")
        self._refresh()
        self._on_status("idle", "Voz desactivada")

    def _on_ready(self):
        self._refresh()
        self._on_status("idle", "🎙 Micrófono activo — habla cuando quieras")

    def _on_error(self, msg: str):
        self._active     = False
        self._recognizer = None
        self._lbl_partial.configure(text="")
        self._refresh()
        self._on_status("err", f"Error de voz: {msg}")

    # ── text processing ──────────────────────────────────────────────────────

    def _on_final(self, text: str):
        self._lbl_partial.configure(text="")
        norm = normalize(text)
        if norm in CMDS_NEWLINE:
            self._on_insert("\n")
            self._on_status("idle", "🎙  ↵ Nueva línea insertada")
        elif norm in CMDS_COMPILE:
            self._on_status("idle", "🎙  Compilando por voz…")
            self._on_compile()
        elif norm in CMDS_CLEAR:
            self._on_clear()
            self._on_status("idle", "🎙  Editor limpiado")
        elif norm in CMDS_UNDO:
            self._on_undo()
            self._on_status("idle", "🎙  Última línea eliminada")
        else:
            line = to_code(normalize(text))
            self._on_insert(line + "\n")
            self._on_status("idle", f'🎙  Insertado: "{line}"')

    # ── model download ───────────────────────────────────────────────────────

    def _download(self):
        self._btn.configure(state="disabled", text="Descargando…  0%")
        self._on_status("warn", "Descargando modelo de voz (~39 MB)…")
        threading.Thread(target=self._download_task, daemon=True).start()

    def _download_task(self):
        try:
            os.makedirs(os.path.dirname(_MODEL_PATH), exist_ok=True)
            zip_path = _MODEL_PATH + ".zip"

            def _progress(count, block, total):
                if total > 0:
                    pct = min(int(count * block * 100 / total), 100)
                    self.after(0, lambda p=pct: self._btn.configure(
                        text=f"Descargando…  {p}%"))

            urllib.request.urlretrieve(_MODEL_URL, zip_path, _progress)
            self.after(0, lambda: self._btn.configure(text="Extrayendo…"))
            with zipfile.ZipFile(zip_path, "r") as z:
                z.extractall(os.path.dirname(_MODEL_PATH))
            os.remove(zip_path)
            self.after(0, self._download_done)
        except Exception as exc:
            self.after(0, lambda e=str(exc): self._download_error(e))

    def _download_done(self):
        self._on_status("ok", "Modelo de voz instalado correctamente")
        self._refresh()

    def _download_error(self, msg: str):
        self._on_status("err", f"Error al descargar el modelo: {msg}")
        self._btn.configure(state="normal", text="⬇  Reintentar descarga",
                            command=self._download)
