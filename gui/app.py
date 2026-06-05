import os
from tkinter import filedialog

import customtkinter as ctk

from gui.backend.ai_analyzer import AI_AVAILABLE, AIAnalyzer
from gui.backend.compiler import CompilerBackend
from gui.backend.tts import TTSEngine, tts_engine_name, tts_missing_dependency_message
from gui.config import get_groq_api_key
from gui.theme import COLORS as C
from gui.widgets.editor_panel import EditorPanel
from gui.widgets.output_panel import OutputPanel
from gui.widgets.statusbar import StatusBar
from gui.widgets.toolbar import Toolbar
from gui.widgets.voice_panel import VoicePanel

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Compilador Accesible  ·  v0.4")
        self.geometry("1400x900")
        self.minsize(1000, 680)
        self.configure(fg_color=C["bg_app"])

        self._current_file: str | None = None
        self._api_key: str = get_groq_api_key()
        self._ai_text: str = ""
        self._explore_mode = True
        self._editor_mode = "NORMAL"
        self._last_navigation_text = ""
        self._last_cursor_line = 0
        self._pending_line_announcement = None
        self._line_announce_delay_ms = 850
        self._navigation_ready = False

        self._compiler = CompilerBackend()
        self._analyzer = AIAnalyzer()
        self._tts      = TTSEngine()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_layout()
        self._bind_shortcuts()
        self.after(1000, self._speak_startup_help)

    # ── layout ────────────────────────────────────────────────────────────────

    def _build_layout(self):
        self._toolbar = Toolbar(
            self,
            on_open=self._open, on_save=self._save, on_clear=self._clear,
            on_ai=self._analyze_ai, on_compile=self._compile, on_execute=self._execute,
        )
        self._toolbar.grid(row=0, column=0, sticky="ew")

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew", padx=10, pady=(8, 4))
        content.grid_columnconfigure(0, weight=42)
        content.grid_columnconfigure(1, weight=58)
        content.grid_rowconfigure(0, weight=1)

        editor_col = ctk.CTkFrame(content, fg_color="transparent")
        editor_col.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        editor_col.grid_rowconfigure(0, weight=1)
        editor_col.grid_columnconfigure(0, weight=1)

        self._editor = EditorPanel(editor_col, on_cursor_change=self._on_editor_cursor_change)
        self._editor.grid(row=0, column=0, sticky="nsew")
        self._editor.set_mode(self._editor_mode)
        self._bind_editor_mode_keys()

        self._voice = VoicePanel(
            editor_col,
            on_insert  =self._editor.insert_text,
            on_compile =self._compile,
            on_clear   =self._editor.clear,
            on_undo    =self._editor.undo_last_line,
            on_status  =self._set_status,
        )
        self._voice.grid(row=1, column=0, sticky="ew", pady=(4, 0))

        self._output = OutputPanel(
            content,
            on_read_aloud=self._read_aloud,
            on_stop_tts  =self._stop_tts,
        )
        self._output.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        self._statusbar = StatusBar(self, has_binary=self._compiler.available())
        self._statusbar.grid(row=2, column=0, sticky="ew")

    def _bind_shortcuts(self):
        self.bind("<Control-o>",      lambda _: self._open())
        self.bind("<Control-s>",      lambda _: self._save())
        self.bind("<Control-Return>", lambda _: self._compile())
        self.bind("<Control-e>",      lambda _: self._execute())
        self.bind("<Alt-Up>",         lambda _: self._navigate_line(-1))
        self.bind("<Alt-Down>",       lambda _: self._navigate_line(1))
        self.bind("<Alt-l>",          lambda _: self._repeat_current_line())
        self.bind("<Alt-L>",          lambda _: self._repeat_current_line())
        self.bind("<Alt-i>",          lambda _: self._analyze_current_line())
        self.bind("<Alt-I>",          lambda _: self._analyze_ai())
        self.bind("<Alt-g>",          lambda _: self._prompt_go_to_line())
        self.bind("<Alt-G>",          lambda _: self._prompt_go_to_line())
        self.bind("<Alt-m>",          lambda _: self._toggle_explore_mode())
        self.bind("<Alt-M>",          lambda _: self._toggle_explore_mode())
        self.bind("<Alt-r>",          lambda _: self._repeat_last_local())
        self.bind("<Alt-R>",          lambda _: self._repeat_last_local())
        self.bind("<Escape>",         lambda _: self._escape())

    def _bind_editor_mode_keys(self):
        self._editor.bind_editor_key("<Key>", self._on_editor_key)

    # ── file operations ───────────────────────────────────────────────────────

    def _open(self):
        path = filedialog.askopenfilename(
            title="Abrir archivo .acc",
            filetypes=[("Lenguaje Accesible", "*.acc"), ("Todos", "*.*")],
        )
        if not path:
            return
        with open(path, encoding="utf-8") as f:
            self._editor.set_code(f.read())
        self._current_file = path
        self._editor.set_filename(os.path.basename(path))
        self._set_status("idle", f"Abierto: {os.path.basename(path)}")

    def _save(self):
        path = self._current_file or filedialog.asksaveasfilename(
            title="Guardar archivo .acc",
            defaultextension=".acc",
            filetypes=[("Lenguaje Accesible", "*.acc"), ("Todos", "*.*")],
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write(self._editor.get_code())
        self._current_file = path
        self._editor.set_filename(os.path.basename(path))
        self._set_status("ok", f"Guardado: {os.path.basename(path)}")

    def _clear(self):
        self._editor.clear()
        for tab in ("Tokens", "AST", "TAC", "Python", "Reporte", "Resultado"):
            self._output.write(tab, "")
        self._output.write_ai("")
        self._output.set_tts_buttons(read_enabled=False, stop_enabled=False)
        self._ai_text      = ""
        self._current_file = None
        self._editor.set_filename("nuevo archivo")
        self._set_status("idle", "Listo")
        self._set_editor_mode("NORMAL", announce=False)

    # ── compile / execute ─────────────────────────────────────────────────────

    def _compile(self):
        if not self._compiler.available():
            self._set_status("err", "Compilador no encontrado — ejecuta 'make' primero")
            return
        self._toolbar.set_compiling(True)
        self._set_status("idle", "Compilando…")
        self._compiler.compile(
            self._editor.get_code(),
            on_done=lambda outputs, ok: self.after(0, self._on_compile_done, outputs, ok),
        )

    def _on_compile_done(self, outputs: dict, success: bool):
        for name, text in outputs.items():
            self._output.write(name, text)
        if success:
            self._set_status("ok", "Compilación exitosa  ✓")
        else:
            self._set_status("err", "Compilación fallida — revisa el Reporte")
            self._output.show("Reporte")
        self._toolbar.set_compiling(False)

    def _execute(self):
        if not self._compiler.available():
            self._set_status("err", "Compilador no encontrado — ejecuta 'make' primero")
            return
        if not self._editor.get_code().strip():
            self._set_status("warn", "El editor está vacío")
            return
        self._toolbar.set_executing(True)
        self._set_status("idle", "Compilando y ejecutando…")
        self._compiler.execute(
            self._editor.get_code(),
            on_done=lambda output, ok: self.after(0, self._on_execute_done, output, ok),
        )

    def _on_execute_done(self, output: str, success: bool):
        self._output.write("Resultado", output)
        self._output.show("Resultado")
        if success:
            self._set_status("ok", "Ejecución completada  ✓")
        else:
            self._set_status("err", "El programa terminó con errores")
        self._toolbar.set_executing(False)

    # ── AI analysis ───────────────────────────────────────────────────────────

    def _analyze_ai(self):
        if not AI_AVAILABLE:
            self._output.write_ai(
                "  ✦ Análisis con IA no disponible.\n\n"
                "  Instala la dependencia:\n    pip install groq\n"
            )
            self._output.show("IA")
            return

        code = self._editor.get_code().strip()
        if not code:
            self._output.write_ai("  El editor está vacío. Escribe o carga código .acc primero.\n")
            self._output.show("IA")
            return

        api_key = self._api_key or self._prompt_api_key()
        if not api_key:
            return
        self._api_key = api_key

        self._toolbar.set_ai_busy(True)
        self._output.set_tts_buttons(read_enabled=False, stop_enabled=False)
        self._output.set_ai_status("Consultando a la IA…", C["ia"])
        self._output.write_ai("  Analizando el código con IA…\n")
        self._output.show("IA")
        self._set_status("idle", "Analizando código con IA…")

        self._analyzer.analyze(
            code, api_key,
            on_success=lambda text: self.after(0, self._on_ai_success, text),
            on_error  =lambda msg:  self.after(0, self._on_ai_error,   msg),
        )

    def _on_ai_success(self, text: str):
        self._ai_text = text
        self._output.write_ai(text)
        self._output.set_tts_buttons(read_enabled=True, stop_enabled=False)
        missing_tts = tts_missing_dependency_message()
        if missing_tts:
            self._output.set_ai_status(missing_tts, C["warn"])
        else:
            self._output.set_ai_status(
                f"Análisis listo  ·  leyendo con {tts_engine_name()}…", C["ok"])
        self._toolbar.set_ai_busy(False)
        self._set_status("ok", "Análisis IA completado  ✓")
        if not missing_tts:
            self._read_aloud()

    def _on_ai_error(self, msg: str):
        self._output.write_ai(f"  ✦ Error al analizar:\n\n  {msg}\n")
        self._output.set_ai_status("Error en el análisis", C["err"])
        self._toolbar.set_ai_busy(False)
        self._set_status("err", f"Error IA: {msg[:60]}")

    def _analyze_current_line(self):
        if not AI_AVAILABLE:
            self._speak_local("Análisis con inteligencia artificial no disponible.")
            self._set_status("err", "Análisis IA no disponible")
            return

        api_key = self._api_key or self._prompt_api_key()
        if not api_key:
            return
        self._api_key = api_key

        line = self._editor.get_current_line_number()
        text = self._editor.get_line_text(line)
        self._stop_all_speech()
        self._toolbar.set_ai_busy(True)
        self._output.set_tts_buttons(read_enabled=False, stop_enabled=False)
        self._output.set_ai_status(f"Explicando línea {line}…", C["ia"])
        self._output.write_ai(f"  Explicando línea {line}…\n")
        self._output.show("IA")
        self._set_status("idle", f"Analizando línea {line} con IA…")
        self._analyzer.analyze_line(
            self._editor.get_code(),
            line,
            text,
            api_key,
            on_success=lambda result: self.after(0, self._on_line_ai_success, line, result),
            on_error  =lambda msg:    self.after(0, self._on_ai_error, msg),
        )

    def _on_line_ai_success(self, line: int, text: str):
        self._ai_text = text
        self._output.write_ai(text)
        self._output.set_tts_buttons(read_enabled=True, stop_enabled=False)
        missing_tts = tts_missing_dependency_message()
        if missing_tts:
            self._output.set_ai_status(missing_tts, C["warn"])
        else:
            self._output.set_ai_status(
                f"Línea {line} explicada  ·  leyendo con {tts_engine_name()}…", C["ok"])
        self._toolbar.set_ai_busy(False)
        self._set_status("ok", f"Explicación lista para línea {line}")
        if not missing_tts:
            self._read_aloud()

    def _prompt_api_key(self) -> str:
        dialog = ctk.CTkInputDialog(
            title="API Key requerida",
            text=(
                "Ingresa tu API Key de Groq.\n"
                "Para no pedirla cada vez, crea un archivo .env\n"
                "con GROQ_API_KEY=tu_clave"
            ),
        )
        return (dialog.get_input() or "").strip()

    # ── TTS ───────────────────────────────────────────────────────────────────

    def _read_aloud(self):
        if not self._ai_text or self._tts.active:
            return
        self._output.set_tts_buttons(read_enabled=False, stop_enabled=True)
        self._output.set_ai_status("🔊 Leyendo en voz alta…", C["accent"])
        self._set_status("idle", "Leyendo análisis en voz alta…")
        self._tts.speak(
            self._ai_text,
            on_done=lambda error=None: self.after(0, self._on_tts_done, error),
        )

    def _stop_tts(self):
        self._tts.stop()

    def _on_tts_done(self, error: str | None):
        self._output.set_tts_buttons(read_enabled=True, stop_enabled=False)
        if error:
            self._output.set_ai_status("Error al leer", C["err"])
            self._set_status("err", f"Error TTS: {error}")
        else:
            self._output.set_ai_status(
                "Análisis listo  ·  🔊 haz clic en Leer para escucharlo", C["ok"])
            self._set_status("idle", "Listo")

    # ── helpers ───────────────────────────────────────────────────────────────

    def _set_status(self, level: str, message: str) -> None:
        self._statusbar.set(level, message)

    # ── accessible editor navigation ─────────────────────────────────────────

    def _on_editor_cursor_change(self, line: int, total: int, text: str) -> None:
        if hasattr(self, "_statusbar"):
            summary = f"{self._editor_mode}  ·  {self._line_summary(line, total, text, include_text=False)}"
            self._set_status("idle", summary)
        if line != self._last_cursor_line:
            self._last_cursor_line = line
            if self._navigation_ready and self._explore_mode:
                self._schedule_line_announcement(line, total)

    def _schedule_line_announcement(self, line: int, total: int) -> None:
        if self._pending_line_announcement is not None:
            try:
                self.after_cancel(self._pending_line_announcement)
            except Exception:
                pass
        self._pending_line_announcement = self.after(
            self._line_announce_delay_ms,
            lambda l=line, t=total: self._run_line_announcement(l, t),
        )

    def _run_line_announcement(self, line: int, total: int):
        self._pending_line_announcement = None
        self._speak_navigation(f"Línea {line} de {total}")

    def _navigate_line(self, delta: int):
        current = self._editor.get_current_line_number()
        total = self._editor.get_total_lines()
        at_start = delta < 0 and current <= 1
        at_end = delta > 0 and current >= total
        if at_start:
            line, total, text = self._editor.go_to_line(1)
            message = f"Inicio del archivo. Línea {line} de {total}"
        elif at_end:
            line, total, text = self._editor.go_to_line(total)
            message = f"Fin del archivo. Línea {line} de {total}"
        elif delta > 0:
            line, total, text = self._editor.go_next_line()
            message = f"Línea {line} de {total}"
        else:
            line, total, text = self._editor.go_previous_line()
            message = f"Línea {line} de {total}"

        self._set_status("idle", self._line_summary(line, total, text, include_text=False))
        if self._explore_mode:
            self._schedule_line_announcement(line, total)

    def _repeat_current_line(self):
        line = self._editor.get_current_line_number()
        total = self._editor.get_total_lines()
        text = self._editor.get_line_text(line)
        self._speak_navigation(self._line_summary(line, total, text))

    def _repeat_last_local(self):
        if self._last_navigation_text:
            self._speak_navigation(self._last_navigation_text)
        else:
            self._repeat_current_line()

    def _prompt_go_to_line(self):
        dialog = ctk.CTkInputDialog(
            title="Ir a línea",
            text=f"Número de línea entre 1 y {self._editor.get_total_lines()}",
        )
        raw = (dialog.get_input() or "").strip()
        if not raw:
            return
        try:
            target = int(raw)
        except ValueError:
            self._speak_navigation("Número de línea inválido.")
            self._set_status("err", "Número de línea inválido")
            return
        line, total, text = self._editor.go_to_line(target)
        self._speak_navigation(self._line_summary(line, total, text))

    def _toggle_explore_mode(self):
        self._explore_mode = not self._explore_mode
        state = "activado" if self._explore_mode else "desactivado"
        self._speak_navigation(f"Modo exploración {state}.")
        self._set_status("ok", f"Modo exploración {state}")

    def _line_summary(self, line: int, total: int, text: str, include_text: bool = True) -> str:
        clean = " ".join(text.strip().split())
        if not include_text:
            return f"Línea {line} de {total}"
        if clean:
            return f"Línea {line} de {total}: {clean}"
        return f"Línea {line} de {total}: línea vacía"

    def _speak_local(self, text: str):
        self._speak_navigation(text)

    def _speak_navigation(self, text: str):
        missing_tts = tts_missing_dependency_message()
        if missing_tts:
            self._set_status("warn", missing_tts)
            return
        self._cancel_pending_line_announcement()
        self._tts.stop()
        self._last_navigation_text = text
        self._tts.speak(
            text,
            on_done=lambda error=None: self.after(0, self._on_navigation_tts_done, error),
        )

    def _cancel_pending_line_announcement(self):
        if self._pending_line_announcement is not None:
            try:
                self.after_cancel(self._pending_line_announcement)
            except Exception:
                pass
            self._pending_line_announcement = None

    def _on_navigation_tts_done(self, error: str | None):
        if error:
            self._set_status("err", f"Error de voz: {error[:80]}")

    def _stop_all_speech(self):
        self._cancel_pending_line_announcement()
        self._tts.stop()
        self._set_status("idle", "Voz detenida")

    # ── modal editor controls ────────────────────────────────────────────────

    def _on_editor_key(self, event):
        key = event.keysym
        if event.state & 0x4:
            return None
        if event.state & 0x8:
            return None

        if self._editor_mode == "INSERT":
            if key == "Escape":
                self._set_editor_mode("NORMAL")
                return "break"
            return None

        if key == "Escape":
            self._escape()
            return "break"
        if key == "i":
            self._set_editor_mode("INSERT")
            return "break"
        if key == "v":
            self._set_editor_mode("VISUAL")
            return "break"
        if key in ("j", "Down"):
            self._navigate_line(1)
            return "break"
        if key in ("k", "Up"):
            self._navigate_line(-1)
            return "break"
        if key == "g":
            self._prompt_go_to_line()
            return "break"
        if key == "I":
            self._analyze_ai()
            return "break"
        if key == "Return":
            self._analyze_current_line()
            return "break"
        if len(getattr(event, "char", "") or "") == 1:
            return "break"
        return None

    def _set_editor_mode(self, mode: str, announce: bool = True):
        if mode == "VISUAL":
            self._editor.start_visual_selection()
        else:
            self._editor.set_mode(mode)
        self._editor_mode = mode
        if announce:
            spoken = {"NORMAL": "Modo normal", "INSERT": "Modo inserción", "VISUAL": "Modo visual"}[mode]
            self._speak_navigation(spoken)
        line = self._editor.get_current_line_number()
        total = self._editor.get_total_lines()
        self._set_status("idle", f"{mode}  ·  Línea {line} de {total}")

    def _escape(self):
        if self._editor_mode != "NORMAL":
            self._set_editor_mode("NORMAL")
        else:
            self._stop_all_speech()

    def _speak_startup_help(self):
        if tts_missing_dependency_message():
            self._navigation_ready = True
            return
        message = (
            "Compilador accesible listo. Estás en modo normal. "
            "Usa jota para bajar una línea, ka para subir, i para insertar, "
            "v para modo visual, Enter para explicar la línea con inteligencia artificial, "
            "Shift i para analizar todo el código, y Escape para volver a normal o detener la voz."
        )
        self._speak_navigation(message)
        self._navigation_ready = True
