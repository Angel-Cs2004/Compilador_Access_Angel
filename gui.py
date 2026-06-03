#!/usr/bin/env python3
"""
Interfaz gráfica del Compilador Accesible
Requiere: pip install customtkinter vosk pyaudio groq pyttsx3
"""
import os
import re
import sys
import json
import threading
import tempfile
import subprocess
import unicodedata
import urllib.request
import zipfile
import importlib.util
from tkinter import filedialog

try:
    import customtkinter as ctk
except ModuleNotFoundError:
    sys.exit("Instala las dependencias:\n  pip install customtkinter vosk pyaudio groq pyttsx3\n")

# ── Detección de dependencias opcionales ──────────────────────────────────────
_VOZ_LIBS = (
    importlib.util.find_spec("vosk") is not None and
    importlib.util.find_spec("pyaudio") is not None
)
_AI_LIBS  = importlib.util.find_spec("groq") is not None
_TTS_LIBS = importlib.util.find_spec("pyttsx3") is not None

# ── Tema ──────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ── Paleta ────────────────────────────────────────────────────────────────────
C = {
    "bg_app":   "#0f172a",
    "bg_panel": "#1e293b",
    "bg_code":  "#0d1117",
    "bg_bar":   "#020617",
    "txt":      "#e2e8f0",
    "txt_dim":  "#475569",
    "accent":   "#60a5fa",
    "ok":       "#4ade80",
    "err":      "#f87171",
    "warn":     "#fbbf24",
    "mic":      "#c084fc",
    "ia":       "#f0abfc",   # rosa/lila para IA
    "border":   "#1e3a5f",
}

_ANSI = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
def _strip_ansi(s: str) -> str:
    return _ANSI.sub("", s)

# ── Ruta del modelo Vosk ──────────────────────────────────────────────────────
_MODEL_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "voz", "models", "vosk-model-small-es-0.42",
)
_MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip"

# ── Vocabulario de voz ────────────────────────────────────────────────────────
_LETRAS = {
    "equis":"x","jota":"j","ka":"k","ele":"l","eme":"m","ene":"n",
    "eñe":"ñ","pe":"p","erre":"r","ese":"s","te":"t","uve":"v",
    "ye":"y","zeta":"z","hache":"h","efe":"f","ce":"c","ge":"g",
}
_NUMEROS = {
    "cero":"0","uno":"1","una":"1","dos":"2","tres":"3","cuatro":"4",
    "cinco":"5","seis":"6","siete":"7","ocho":"8","nueve":"9",
    "diez":"10","once":"11","doce":"12","trece":"13","catorce":"14",
    "quince":"15","veinte":"20","treinta":"30","cuarenta":"40",
    "cincuenta":"50","cien":"100",
}
_CMDS_NEWLINE  = {"nueva linea","enter","siguiente linea","salto de linea"}
_CMDS_COMPILAR = {"compilar","ejecutar","correr","procesar"}
_CMDS_LIMPIAR  = {"limpiar","borrar todo","reset"}
_CMDS_DESHACER = {"deshacer","borrar linea","undo"}

def _normalizar(texto: str) -> str:
    sin_tildes = "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )
    return sin_tildes.lower().strip(" .,!¿?¡")

def _a_codigo(texto: str) -> str:
    t = (texto
         .replace("doble uve","w").replace("doble ve","w")
         .replace("i griega","y").replace("punto","."))
    return " ".join(_LETRAS.get(p, _NUMEROS.get(p, p)) for p in t.split())

# ── Prompt para Claude ────────────────────────────────────────────────────────
_PROMPT_SISTEMA = """\
Eres un asistente para el lenguaje ".acc", un lenguaje con sintaxis en español.

Analiza el código y responde SOLO con estas 3 secciones, de forma breve:

¿QUÉ HACE?
(1 oración)

VARIABLES Y ESTRUCTURAS
(lista corta: cada variable con su valor, y qué bucles/condiciones usa)

RESULTADO
(qué imprime al ejecutarse)

Sé conciso. Sin explicaciones adicionales. Responde en español.
"""

# ── Código de ejemplo ─────────────────────────────────────────────────────────
_EJEMPLO = """\
# Ejemplo completo del lenguaje .acc
definir base como 5
definir altura como 10
definir area como base por altura

mostrar "Resultado del calculo:"
mostrar area

si area es mayor que 40 entonces
    mostrar "El area es grande"
sino
    mostrar "El area es pequena"
fin si

definir contador como 0
repetir 4 veces
    definir contador como contador mas 1
    mostrar contador
fin repetir

definir x como 20
mientras x es mayor que 0
    definir x como x menos 7
fin mientras
mostrar x
"""


# ── Hilo de reconocimiento de voz ─────────────────────────────────────────────
class _VozThread(threading.Thread):
    def __init__(self, model_path, on_ready, on_final, on_partial, on_error):
        super().__init__(daemon=True)
        self._model_path = model_path
        self._activo = True
        self.on_ready   = on_ready
        self.on_final   = on_final
        self.on_partial = on_partial
        self.on_error   = on_error

    def detener(self):
        self._activo = False

    def run(self):
        try:
            import pyaudio
            from vosk import Model, KaldiRecognizer, SetLogLevel
            SetLogLevel(-1)

            model  = Model(self._model_path)
            rec    = KaldiRecognizer(model, 16000)
            pa     = pyaudio.PyAudio()
            stream = pa.open(
                format=pyaudio.paInt16, channels=1,
                rate=16000, input=True, frames_per_buffer=4000,
            )
            self.on_ready()
            while self._activo:
                data = stream.read(4000, exception_on_overflow=False)
                if rec.AcceptWaveform(data):
                    texto = json.loads(rec.Result()).get("text", "").strip()
                    if texto:
                        self.on_final(texto)
                else:
                    parcial = json.loads(rec.PartialResult()).get("partial", "")
                    self.on_partial(parcial)
            stream.stop_stream()
            stream.close()
            pa.terminate()
        except Exception as exc:
            self.on_error(str(exc))


# ── Aplicación principal ───────────────────────────────────────────────────────
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Compilador Accesible  ·  v0.4")
        self.geometry("1400x900")
        self.minsize(1000, 680)
        self.configure(fg_color=C["bg_app"])

        self._archivo      = None
        self._bin          = self._buscar_binario()
        self._voz_hilo     = None
        self._voz_encendida = False
        self._tts_activo   = False
        self._tts_hilo     = None
        self._tts_engine   = None
        self._ia_texto     = ""
        self._api_key      = os.getenv("GROQ_API_KEY", "")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._hacer_toolbar()
        self._hacer_contenido()
        self._hacer_statusbar()

        self.bind("<Control-o>",      lambda _: self._abrir())
        self.bind("<Control-s>",      lambda _: self._guardar())
        self.bind("<Control-l>",      lambda _: self._limpiar())
        self.bind("<Control-Return>", lambda _: self._compilar())
        self.bind("<Control-e>",      lambda _: self._ejecutar())

    # ── binario ───────────────────────────────────────────────────────────
    def _buscar_binario(self):
        base = os.path.dirname(os.path.abspath(__file__))
        for n in ("compilador", "compilador.exe"):
            r = os.path.join(base, "build", n)
            if os.path.isfile(r):
                return r
        return None

    # ── toolbar ──────────────────────────────────────────────────────────
    def _hacer_toolbar(self):
        bar = ctk.CTkFrame(self, corner_radius=0, height=58, fg_color=C["bg_bar"])
        bar.grid(row=0, column=0, sticky="ew")
        bar.grid_propagate(False)
        bar.grid_columnconfigure(10, weight=1)

        ctk.CTkLabel(
            bar, text="  ◈  Compilador Accesible",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color=C["accent"],
        ).grid(row=0, column=0, padx=18, pady=14, sticky="w")

        ctk.CTkLabel(bar, text="│", text_color=C["border"]).grid(row=0, column=1, padx=4)

        for idx, (lbl, cmd) in enumerate(
            [("  Abrir", self._abrir),
             ("  Guardar", self._guardar),
             ("  Limpiar", self._limpiar)],
            start=2,
        ):
            ctk.CTkButton(
                bar, text=lbl, command=cmd,
                width=100, height=36, corner_radius=8,
                fg_color="transparent", border_width=1,
                border_color=C["border"], text_color=C["txt"],
                hover_color="#1e293b", font=ctk.CTkFont(size=12),
            ).grid(row=0, column=idx, padx=4, pady=11)

        ctk.CTkLabel(bar, text="│", text_color=C["border"]).grid(row=0, column=5, padx=4)

        # Botón IA
        self._btn_ia = ctk.CTkButton(
            bar, text="✦  Analizar con IA", command=self._analizar_ia,
            width=160, height=36, corner_radius=8,
            fg_color="#3b0764", hover_color="#4c1d95",
            text_color=C["ia"], font=ctk.CTkFont(size=12, weight="bold"),
            border_width=1, border_color="#7c3aed",
        )
        self._btn_ia.grid(row=0, column=6, padx=4, pady=11)

        ctk.CTkLabel(bar, text="│", text_color=C["border"]).grid(row=0, column=7, padx=4)

        # Botón compilar
        self._btn_compilar = ctk.CTkButton(
            bar, text="▶  Compilar   Ctrl+↵", command=self._compilar,
            width=190, height=36, corner_radius=8,
            fg_color="#166534", hover_color="#15803d",
            text_color=C["ok"], font=ctk.CTkFont(size=13, weight="bold"),
            border_width=1, border_color=C["ok"],
        )
        self._btn_compilar.grid(row=0, column=8, padx=(16, 4), pady=11)

        ctk.CTkLabel(bar, text="│", text_color=C["border"]).grid(row=0, column=9, padx=4)

        # Botón ejecutar
        self._btn_ejecutar = ctk.CTkButton(
            bar, text="▶▶  Ejecutar   Ctrl+E", command=self._ejecutar,
            width=190, height=36, corner_radius=8,
            fg_color="#7c2d12", hover_color="#9a3412",
            text_color="#fb923c", font=ctk.CTkFont(size=13, weight="bold"),
            border_width=1, border_color="#fb923c",
        )
        self._btn_ejecutar.grid(row=0, column=10, padx=(4, 16), pady=11)

    # ── contenido central ────────────────────────────────────────────────
    def _hacer_contenido(self):
        wrap = ctk.CTkFrame(self, fg_color="transparent")
        wrap.grid(row=1, column=0, sticky="nsew", padx=10, pady=(8, 4))
        wrap.grid_columnconfigure(0, weight=42)
        wrap.grid_columnconfigure(1, weight=58)
        wrap.grid_rowconfigure(0, weight=1)

        self._hacer_panel_editor(wrap)
        self._hacer_panel_salida(wrap)

    # ── panel editor ─────────────────────────────────────────────────────
    def _hacer_panel_editor(self, parent):
        panel = ctk.CTkFrame(parent, corner_radius=10,
                             fg_color=C["bg_panel"],
                             border_width=1, border_color=C["border"])
        panel.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        panel.grid_rowconfigure(1, weight=1)
        panel.grid_columnconfigure(0, weight=1)

        cab = ctk.CTkFrame(panel, corner_radius=8, fg_color=C["bg_bar"], height=38)
        cab.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))
        cab.grid_propagate(False)
        cab.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            cab, text="  ✦ Código fuente  (.acc)",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=C["accent"],
        ).grid(row=0, column=0, padx=12, pady=10, sticky="w")

        self._lbl_arch = ctk.CTkLabel(
            cab, text="nuevo archivo",
            font=ctk.CTkFont(size=11), text_color=C["txt_dim"],
        )
        self._lbl_arch.grid(row=0, column=1, padx=12, pady=10, sticky="e")

        self._editor = ctk.CTkTextbox(
            panel,
            font=ctk.CTkFont(family="Consolas", size=13),
            wrap="none", corner_radius=8,
            fg_color=C["bg_code"], text_color=C["txt"],
            border_width=1, border_color=C["border"],
            scrollbar_button_color=C["border"],
        )
        self._editor.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 4))
        self._editor.insert("1.0", _EJEMPLO)

        self._hacer_panel_voz(panel)

    # ── panel de voz ─────────────────────────────────────────────────────
    def _hacer_panel_voz(self, parent):
        vframe = ctk.CTkFrame(parent, corner_radius=8,
                              fg_color=C["bg_bar"],
                              border_width=1, border_color=C["border"])
        vframe.grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 8))
        vframe.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(vframe, text="🎙", font=ctk.CTkFont(size=15)
                     ).grid(row=0, column=0, padx=(12, 4), pady=(10, 2), sticky="w")

        ctk.CTkLabel(vframe, text="Entrada por voz",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=C["mic"],
                     ).grid(row=0, column=1, pady=(10, 2), sticky="w")

        self._voz_dot = ctk.CTkLabel(vframe, text="●",
                                     font=ctk.CTkFont(size=12),
                                     text_color=C["txt_dim"])
        self._voz_dot.grid(row=0, column=2, padx=(4, 2), pady=(10, 2))

        self._voz_estado_lbl = ctk.CTkLabel(vframe, text="Inactiva",
                                            font=ctk.CTkFont(size=11),
                                            text_color=C["txt_dim"])
        self._voz_estado_lbl.grid(row=0, column=3, padx=(0, 12), pady=(10, 2), sticky="e")

        self._btn_voz = ctk.CTkButton(vframe, text="", command=self._accion_voz,
                                      width=210, height=30, corner_radius=7,
                                      font=ctk.CTkFont(size=11))
        self._btn_voz.grid(row=1, column=0, columnspan=2, padx=12, pady=(2, 4), sticky="w")

        self._lbl_parcial = ctk.CTkLabel(vframe, text="",
                                         font=ctk.CTkFont(family="Consolas", size=11),
                                         text_color=C["txt_dim"], anchor="w")
        self._lbl_parcial.grid(row=1, column=2, columnspan=2,
                               padx=(4, 12), pady=(2, 4), sticky="ew")

        ctk.CTkLabel(
            vframe,
            text='  Comandos: "nueva linea"  ·  "compilar"  ·  "limpiar"  ·  "deshacer"',
            font=ctk.CTkFont(size=10), text_color=C["txt_dim"],
        ).grid(row=2, column=0, columnspan=4, padx=12, pady=(0, 8), sticky="w")

        self._actualizar_btn_voz()

    # ── panel de salida (pestañas) ────────────────────────────────────────
    def _hacer_panel_salida(self, parent):
        panel = ctk.CTkFrame(parent, corner_radius=10,
                             fg_color=C["bg_panel"],
                             border_width=1, border_color=C["border"])
        panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        panel.grid_rowconfigure(0, weight=1)
        panel.grid_columnconfigure(0, weight=1)

        self._tabs = ctk.CTkTabview(
            panel, corner_radius=8, fg_color=C["bg_panel"],
            segmented_button_fg_color=C["bg_bar"],
            segmented_button_selected_color=C["bg_panel"],
            segmented_button_selected_hover_color=C["bg_panel"],
            segmented_button_unselected_hover_color="#1e293b",
        )
        self._tabs.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        self._caja: dict[str, ctk.CTkTextbox] = {}

        for nombre in ("Tokens", "AST", "TAC", "Python", "Reporte", "Resultado"):
            tab = self._tabs.add(nombre)
            tab.grid_rowconfigure(0, weight=1)
            tab.grid_columnconfigure(0, weight=1)
            txt = ctk.CTkTextbox(
                tab,
                font=ctk.CTkFont(family="Consolas", size=12),
                wrap="none", corner_radius=8, state="disabled",
                fg_color=C["bg_code"], text_color=C["txt"],
                border_width=1, border_color=C["border"],
                scrollbar_button_color=C["border"],
            )
            txt.grid(row=0, column=0, sticky="nsew")
            self._caja[nombre] = txt

        # Pestaña IA con layout especial
        self._hacer_tab_ia()

        self._escribir("Reporte",
            "  Escribe código .acc y presiona  ▶ Compilar  (Ctrl+Enter)\n\n"
            "  Pestañas:\n\n"
            "    Tokens  →  tabla de tokens (Fase 1)\n"
            "    AST     →  árbol sintáctico + semántico (Fases 2-3)\n"
            "    TAC     →  código intermedio antes/después de optimizar (Fases 4-5)\n"
            "    Python  →  código Python 3 generado (Fase 6)\n"
            "    Reporte →  estadísticas completas\n"
            "    IA      →  análisis inteligente del código con explicación en voz\n"
        )

    # ── pestaña IA ────────────────────────────────────────────────────────
    def _hacer_tab_ia(self):
        tab = self._tabs.add("IA")
        tab.grid_rowconfigure(1, weight=1)
        tab.grid_columnconfigure(0, weight=1)

        # Barra de controles IA
        ctrl = ctk.CTkFrame(tab, corner_radius=8,
                            fg_color=C["bg_bar"], height=44)
        ctrl.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        ctrl.grid_propagate(False)
        ctrl.grid_columnconfigure(3, weight=1)

        self._btn_leer = ctk.CTkButton(
            ctrl, text="🔊  Leer en voz alta",
            command=self._hablar_ia,
            width=155, height=30, corner_radius=7,
            fg_color="#1e3a5f", hover_color="#1e40af",
            text_color=C["accent"], font=ctk.CTkFont(size=11),
            state="disabled",
        )
        self._btn_leer.grid(row=0, column=0, padx=(10, 4), pady=7)

        self._btn_stop_tts = ctk.CTkButton(
            ctrl, text="⏹  Detener",
            command=self._detener_tts,
            width=95, height=30, corner_radius=7,
            fg_color="transparent", border_width=1,
            border_color=C["border"], text_color=C["txt_dim"],
            font=ctk.CTkFont(size=11), state="disabled",
        )
        self._btn_stop_tts.grid(row=0, column=1, padx=4, pady=7)

        ctk.CTkLabel(ctrl, text="│", text_color=C["border"]
                     ).grid(row=0, column=2, padx=6)

        self._lbl_ia_status = ctk.CTkLabel(
            ctrl, text="Esperando análisis…",
            font=ctk.CTkFont(size=11), text_color=C["txt_dim"],
        )
        self._lbl_ia_status.grid(row=0, column=3, padx=8, sticky="w")

        # Área de texto del análisis
        self._ia_txt = ctk.CTkTextbox(
            tab,
            font=ctk.CTkFont(size=12),
            wrap="word", corner_radius=8, state="disabled",
            fg_color=C["bg_code"], text_color=C["txt"],
            border_width=1, border_color=C["border"],
            scrollbar_button_color=C["border"],
        )
        self._ia_txt.grid(row=1, column=0, sticky="nsew")

    # ── barra de estado ──────────────────────────────────────────────────
    def _hacer_statusbar(self):
        bar = ctk.CTkFrame(self, corner_radius=0, height=30, fg_color=C["bg_bar"])
        bar.grid(row=2, column=0, sticky="ew")
        bar.grid_propagate(False)
        bar.grid_columnconfigure(2, weight=1)

        self._dot = ctk.CTkLabel(
            bar, text="●", font=ctk.CTkFont(size=13),
            text_color=C["warn"] if not self._bin else C["txt_dim"],
        )
        self._dot.grid(row=0, column=0, padx=(14, 4), pady=5, sticky="w")

        msg = ("Compilador no encontrado — ejecuta 'make'" if not self._bin else "Listo")
        self._lbl_estado = ctk.CTkLabel(
            bar, text=msg, font=ctk.CTkFont(size=11),
            text_color=C["warn"] if not self._bin else C["txt_dim"],
        )
        self._lbl_estado.grid(row=0, column=1, pady=5, sticky="w")

        ctk.CTkLabel(
            bar,
            text="Ctrl+O  Abrir    Ctrl+S  Guardar    Ctrl+L  Limpiar    Ctrl+↵  Compilar  ",
            font=ctk.CTkFont(size=10), text_color=C["txt_dim"],
        ).grid(row=0, column=2, pady=5, sticky="e")

    # ── helpers UI ───────────────────────────────────────────────────────
    def _escribir(self, tab: str, texto: str):
        w = self._caja[tab]
        w.configure(state="normal")
        w.delete("1.0", "end")
        w.insert("1.0", texto)
        w.configure(state="disabled")

    def _escribir_ia(self, texto: str):
        self._ia_txt.configure(state="normal")
        self._ia_txt.delete("1.0", "end")
        self._ia_txt.insert("1.0", texto)
        self._ia_txt.configure(state="disabled")

    def _estado(self, nivel: str, msg: str):
        color = {"ok": C["ok"], "err": C["err"],
                 "warn": C["warn"], "idle": C["txt_dim"]}.get(nivel, C["txt_dim"])
        self._dot.configure(text_color=color)
        self._lbl_estado.configure(text=f"  {msg}", text_color=color)

    # ── archivo ───────────────────────────────────────────────────────────
    def _abrir(self):
        ruta = filedialog.askopenfilename(
            title="Abrir archivo .acc",
            filetypes=[("Lenguaje Accesible", "*.acc"), ("Todos", "*.*")],
        )
        if not ruta:
            return
        with open(ruta, encoding="utf-8") as f:
            self._editor.delete("1.0", "end")
            self._editor.insert("1.0", f.read())
        self._archivo = ruta
        self._lbl_arch.configure(text=os.path.basename(ruta))
        self._estado("idle", f"Abierto: {os.path.basename(ruta)}")

    def _guardar(self):
        ruta = self._archivo or filedialog.asksaveasfilename(
            title="Guardar archivo .acc",
            defaultextension=".acc",
            filetypes=[("Lenguaje Accesible", "*.acc"), ("Todos", "*.*")],
        )
        if not ruta:
            return
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(self._editor.get("1.0", "end-1c"))
        self._archivo = ruta
        self._lbl_arch.configure(text=os.path.basename(ruta))
        self._estado("ok", f"Guardado: {os.path.basename(ruta)}")

    def _limpiar(self):
        self._editor.delete("1.0", "end")
        for n in self._caja:
            self._escribir(n, "")
        self._escribir_ia("")
        self._ia_texto = ""
        self._btn_leer.configure(state="disabled")
        self._archivo = None
        self._lbl_arch.configure(text="nuevo archivo")
        self._estado("idle", "Listo")

    # ── compilación ───────────────────────────────────────────────────────
    def _compilar(self):
        if not self._bin:
            self._estado("err", "Compilador no encontrado — ejecuta 'make' primero")
            return
        self._btn_compilar.configure(state="disabled", text="⏳  Compilando…")
        self._estado("idle", "Compilando…")
        threading.Thread(target=self._tarea_compilar, daemon=True).start()

    def _tarea_compilar(self):
        codigo = self._editor.get("1.0", "end-1c")
        fd, tmp = tempfile.mkstemp(suffix=".acc")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(codigo)
            salidas = {
                "Tokens":  self._invocar(["--tokens", tmp]),
                "AST":     self._invocar(["--ast",    tmp]),
                "TAC":     self._invocar(["--ir",     tmp]),
                "Python":  self._invocar(["--gen",    tmp]),
                "Reporte": self._invocar([tmp]),
            }
            exito = "COMPILACION EXITOSA" in salidas["Reporte"]
        finally:
            try: os.unlink(tmp)
            except OSError: pass
        self.after(0, self._aplicar_resultados, salidas, exito)

    def _invocar(self, args: list) -> str:
        try:
            r = subprocess.run(
                [self._bin, *args], capture_output=True,
                text=True, encoding="utf-8", errors="replace", timeout=20,
            )
            return _strip_ansi(r.stdout + r.stderr)
        except subprocess.TimeoutExpired:
            return "⚠  Tiempo de espera agotado (>20 s)."
        except Exception as exc:
            return f"⚠  Error al invocar el compilador:\n{exc}"

    def _aplicar_resultados(self, salidas: dict, exito: bool):
        for nombre, texto in salidas.items():
            self._escribir(nombre, texto)
        if exito:
            self._estado("ok", "Compilación exitosa  ✓")
        else:
            self._estado("err", "Compilación fallida — revisa el Reporte")
            self._tabs.set("Reporte")
        self._btn_compilar.configure(state="normal", text="▶  Compilar   Ctrl+↵")

    # ══════════════════════════════════════════════════════════════════════
    #  EJECUCIÓN DEL PROGRAMA
    # ══════════════════════════════════════════════════════════════════════

    def _ejecutar(self):
        if not self._bin:
            self._estado("err", "Compilador no encontrado — ejecuta 'make' primero")
            return
        codigo = self._editor.get("1.0", "end-1c").strip()
        if not codigo:
            self._estado("warn", "El editor está vacío")
            return
        self._btn_ejecutar.configure(state="disabled", text="⏳  Ejecutando…")
        self._btn_compilar.configure(state="disabled")
        self._estado("idle", "Compilando y ejecutando…")
        threading.Thread(target=self._tarea_ejecutar, daemon=True).start()

    def _tarea_ejecutar(self):
        codigo = self._editor.get("1.0", "end-1c")
        fd_acc, tmp_acc = tempfile.mkstemp(suffix=".acc")
        fd_py,  tmp_py  = tempfile.mkstemp(suffix=".py")
        os.close(fd_py)
        try:
            with os.fdopen(fd_acc, "w", encoding="utf-8") as f:
                f.write(codigo)

            # Paso 1: compilar .acc → .py
            comp = subprocess.run(
                [self._bin, "--salida", tmp_py, tmp_acc],
                capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=20,
            )
            if comp.returncode != 0:
                salida = "✗ Error de compilación — el programa no pudo ejecutarse:\n\n"
                salida += _strip_ansi(comp.stdout + comp.stderr)
                self.after(0, self._mostrar_resultado, salida, False)
                return

            # Paso 2: ejecutar el Python generado
            run = subprocess.run(
                [sys.executable, tmp_py],
                capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=10,
            )
            salida = run.stdout
            if run.stderr:
                salida += "\n── Errores de ejecución ──\n" + run.stderr
            if not salida.strip():
                salida = "(El programa ejecutó sin producir salida)"

            self.after(0, self._mostrar_resultado, salida, run.returncode == 0)

        except subprocess.TimeoutExpired:
            self.after(0, self._mostrar_resultado,
                "⚠  Tiempo agotado (>10 s).\n"
                "El programa puede tener un bucle infinito.", False)
        except Exception as exc:
            self.after(0, self._mostrar_resultado, f"⚠  Error inesperado:\n{exc}", False)
        finally:
            try: os.unlink(tmp_acc)
            except OSError: pass
            try: os.unlink(tmp_py)
            except OSError: pass

    def _mostrar_resultado(self, texto: str, exito: bool):
        self._escribir("Resultado", texto)
        self._tabs.set("Resultado")
        if exito:
            self._estado("ok", "Ejecución completada  ✓")
        else:
            self._estado("err", "El programa terminó con errores")
        self._btn_ejecutar.configure(state="normal", text="▶▶  Ejecutar   Ctrl+E")
        self._btn_compilar.configure(state="normal", text="▶  Compilar   Ctrl+↵")

    # ══════════════════════════════════════════════════════════════════════
    #  ANÁLISIS CON IA
    # ══════════════════════════════════════════════════════════════════════

    def _analizar_ia(self):
        if not _AI_LIBS:
            self._escribir_ia(
                "  ✦ Análisis con IA no disponible.\n\n"
                "  Instala la dependencia:\n"
                "    pip install groq\n"
            )
            self._tabs.set("IA")
            return

        codigo = self._editor.get("1.0", "end-1c").strip()
        if not codigo:
            self._escribir_ia("  El editor está vacío. Escribe o carga código .acc primero.\n")
            self._tabs.set("IA")
            return

        # Obtener API key
        api_key = self._api_key or self._pedir_api_key()
        if not api_key:
            return
        self._api_key = api_key

        # Iniciar análisis
        self._btn_ia.configure(state="disabled", text="✦  Analizando…")
        self._btn_leer.configure(state="disabled")
        self._lbl_ia_status.configure(text="Consultando a la IA…", text_color=C["ia"])
        self._escribir_ia("  Analizando el código con IA…\n")
        self._tabs.set("IA")
        self._estado("idle", "Analizando código con IA…")

        threading.Thread(
            target=self._run_analizar,
            args=(codigo, api_key),
            daemon=True,
        ).start()

    def _pedir_api_key(self) -> str:
        dialogo = ctk.CTkInputDialog(
            title="API Key requerida",
            text=(
                "Ingresa tu API Key de Groq.\n"
                "(También puedes definir la variable\n"
                " de entorno GROQ_API_KEY)"
            ),
        )
        return (dialogo.get_input() or "").strip()

    def _run_analizar(self, codigo: str, api_key: str):
        try:
            from groq import Groq
            client = Groq(api_key=api_key)
            mensaje = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                max_tokens=500,
                messages=[
                    {"role": "system", "content": _PROMPT_SISTEMA},
                    {"role": "user",   "content": f"Analiza este código .acc:\n\n```\n{codigo}\n```"},
                ],
            )
            respuesta = mensaje.choices[0].message.content
            self.after(0, self._aplicar_analisis, respuesta)

        except Exception as exc:
            msg = str(exc)
            if "authentication" in msg.lower() or "api_key" in msg.lower():
                msg = "API Key inválida o expirada. Verifica tu clave de Groq."
            elif "rate" in msg.lower() or "quota" in msg.lower() or "429" in msg:
                msg = "Límite de peticiones alcanzado (cuota gratuita). Espera unos segundos e intenta de nuevo."
            self.after(0, self._error_analisis, msg)

    def _aplicar_analisis(self, texto: str):
        self._ia_texto = texto
        self._escribir_ia(texto)
        self._btn_ia.configure(state="normal", text="✦  Analizar con IA")
        self._btn_leer.configure(state="normal" if _TTS_LIBS else "disabled")
        self._lbl_ia_status.configure(
            text="Análisis listo  ·  🔊 haz clic en Leer para escucharlo",
            text_color=C["ok"],
        )
        self._estado("ok", "Análisis IA completado  ✓")

    def _error_analisis(self, msg: str):
        self._escribir_ia(f"  ✦ Error al analizar:\n\n  {msg}\n")
        self._btn_ia.configure(state="normal", text="✦  Analizar con IA")
        self._lbl_ia_status.configure(text="Error en el análisis", text_color=C["err"])
        self._estado("err", f"Error IA: {msg[:60]}")

    # ══════════════════════════════════════════════════════════════════════
    #  TTS — TEXTO A VOZ
    # ══════════════════════════════════════════════════════════════════════

    def _hablar_ia(self):
        if not _TTS_LIBS:
            self._estado("err", "TTS no disponible — instala:  pip install pyttsx3")
            return
        if not self._ia_texto:
            return
        if self._tts_activo:
            return

        self._tts_activo = True
        self._btn_leer.configure(state="disabled")
        self._btn_stop_tts.configure(state="normal")
        self._lbl_ia_status.configure(text="🔊 Leyendo en voz alta…", text_color=C["accent"])
        self._estado("idle", "Leyendo análisis en voz alta…")

        self._tts_hilo = threading.Thread(
            target=self._run_hablar, args=(self._ia_texto,), daemon=True
        )
        self._tts_hilo.start()

    def _detener_tts(self):
        self._tts_activo = False
        engine = getattr(self, "_tts_engine", None)
        if engine:
            try:
                engine.stop()
            except Exception:
                pass

    def _run_hablar(self, texto: str):
        try:
            import pyttsx3
            engine = pyttsx3.init()
            self._tts_engine = engine

            # Intentar voz en español
            for v in engine.getProperty("voices"):
                nombre = (v.name or "").lower()
                vid    = (v.id or "").lower()
                if any(x in nombre or x in vid for x in
                       ["helena", "spanish", "español", "es-", "sabina", "jorge"]):
                    engine.setProperty("voice", v.id)
                    break

            engine.setProperty("rate", 155)
            engine.setProperty("volume", 1.0)

            # Pasar todo el texto de una vez — múltiples runAndWait() rompen SAPI5 en Windows
            engine.say(texto)
            engine.runAndWait()
            engine.stop()
        except Exception as exc:
            self.after(0, lambda e=str(exc): self._estado("err", f"Error TTS: {e}"))
        finally:
            self._tts_engine = None
            self.after(0, self._tts_terminado)

    def _tts_terminado(self):
        self._tts_activo = False
        self._tts_hilo   = None
        self._btn_leer.configure(state="normal")
        self._btn_stop_tts.configure(state="disabled")
        self._lbl_ia_status.configure(
            text="Análisis listo  ·  🔊 haz clic en Leer para escucharlo",
            text_color=C["ok"],
        )
        self._estado("idle", "Listo")

    # ══════════════════════════════════════════════════════════════════════
    #  VOZ — ENTRADA POR MICRÓFONO
    # ══════════════════════════════════════════════════════════════════════

    def _actualizar_btn_voz(self):
        if not _VOZ_LIBS:
            self._btn_voz.configure(
                text="  pip install vosk pyaudio",
                fg_color="#7c3aed", hover_color="#6d28d9",
                text_color="white", state="disabled",
            )
            self._voz_estado_lbl.configure(text="Libs no instaladas", text_color=C["warn"])
            self._voz_dot.configure(text_color=C["warn"])
        elif not os.path.isdir(_MODEL_PATH):
            self._btn_voz.configure(
                text="⬇  Descargar modelo de voz (~39 MB)",
                fg_color="#7c3aed", hover_color="#6d28d9",
                text_color="white", state="normal",
                command=self._descargar_modelo,
            )
            self._voz_estado_lbl.configure(text="Modelo no instalado", text_color=C["warn"])
            self._voz_dot.configure(text_color=C["warn"])
        elif self._voz_encendida:
            self._btn_voz.configure(
                text="⏹  Detener voz",
                fg_color="#7f1d1d", hover_color="#991b1b",
                text_color=C["err"], state="normal",
                command=self._toggle_voz,
            )
            self._voz_estado_lbl.configure(text="Escuchando…", text_color=C["mic"])
            self._voz_dot.configure(text_color=C["mic"])
        else:
            self._btn_voz.configure(
                text="🎙  Activar voz",
                fg_color="#4c1d95", hover_color="#5b21b6",
                text_color=C["mic"], state="normal",
                command=self._toggle_voz,
            )
            self._voz_estado_lbl.configure(text="Inactiva", text_color=C["txt_dim"])
            self._voz_dot.configure(text_color=C["txt_dim"])

    def _accion_voz(self):
        pass  # reemplazado por _actualizar_btn_voz en init

    def _descargar_modelo(self):
        self._btn_voz.configure(state="disabled", text="Descargando…  0%")
        self._estado("warn", "Descargando modelo de voz (~39 MB)…")
        threading.Thread(target=self._run_descarga, daemon=True).start()

    def _run_descarga(self):
        try:
            os.makedirs(os.path.dirname(_MODEL_PATH), exist_ok=True)
            zip_path = _MODEL_PATH + ".zip"

            def progreso(count, block, total):
                if total > 0:
                    pct = min(int(count * block * 100 / total), 100)
                    self.after(0, lambda p=pct: self._btn_voz.configure(
                        text=f"Descargando…  {p}%"))

            urllib.request.urlretrieve(_MODEL_URL, zip_path, progreso)
            self.after(0, lambda: self._btn_voz.configure(text="Extrayendo…"))
            with zipfile.ZipFile(zip_path, "r") as z:
                z.extractall(os.path.dirname(_MODEL_PATH))
            os.remove(zip_path)
            self.after(0, self._descarga_completa)
        except Exception as exc:
            self.after(0, lambda e=str(exc): self._descarga_error(e))

    def _descarga_completa(self):
        self._estado("ok", "Modelo de voz instalado correctamente")
        self._actualizar_btn_voz()

    def _descarga_error(self, msg: str):
        self._estado("err", f"Error al descargar el modelo: {msg}")
        self._btn_voz.configure(state="normal", text="⬇  Reintentar descarga",
                                command=self._descargar_modelo)

    def _toggle_voz(self):
        if self._voz_encendida:
            self._apagar_voz()
        else:
            self._encender_voz()

    def _encender_voz(self):
        self._voz_encendida = True
        self._btn_voz.configure(state="disabled", text="Cargando modelo…")
        self._voz_estado_lbl.configure(text="Cargando…", text_color=C["warn"])
        self._voz_dot.configure(text_color=C["warn"])
        self._voz_hilo = _VozThread(
            model_path=_MODEL_PATH,
            on_ready=self._voz_lista,
            on_final=self._voz_final,
            on_partial=self._voz_parcial,
            on_error=self._voz_error,
        )
        self._voz_hilo.start()

    def _apagar_voz(self):
        self._voz_encendida = False
        if self._voz_hilo:
            self._voz_hilo.detener()
            self._voz_hilo = None
        self._lbl_parcial.configure(text="")
        self._actualizar_btn_voz()
        self._estado("idle", "Voz desactivada")

    def _voz_lista(self):
        self.after(0, self._on_voz_lista)

    def _on_voz_lista(self):
        self._actualizar_btn_voz()
        self._estado("idle", "🎙 Micrófono activo — habla cuando quieras")

    def _voz_parcial(self, texto: str):
        self.after(0, lambda t=texto: self._lbl_parcial.configure(
            text=f"  {t}…" if t else ""))

    def _voz_final(self, texto: str):
        self.after(0, lambda t=texto: self._procesar_frase(t))

    def _voz_error(self, msg: str):
        self.after(0, lambda m=msg: self._on_voz_error(m))

    def _on_voz_error(self, msg: str):
        self._voz_encendida = False
        self._voz_hilo = None
        self._lbl_parcial.configure(text="")
        self._actualizar_btn_voz()
        self._estado("err", f"Error de voz: {msg}")

    def _procesar_frase(self, texto: str):
        self._lbl_parcial.configure(text="")
        norm = _normalizar(texto)

        if norm in _CMDS_NEWLINE:
            self._editor.insert("end", "\n")
            self._estado("idle", "🎙  ↵ Nueva línea insertada")
        elif norm in _CMDS_COMPILAR:
            self._estado("idle", "🎙  Compilando por voz…")
            self._compilar()
        elif norm in _CMDS_LIMPIAR:
            self._editor.delete("1.0", "end")
            self._estado("idle", "🎙  Editor limpiado")
        elif norm in _CMDS_DESHACER:
            contenido = self._editor.get("1.0", "end-1c")
            lineas = contenido.split("\n")
            if lineas:
                lineas.pop()
                self._editor.delete("1.0", "end")
                self._editor.insert("1.0", "\n".join(lineas))
            self._estado("idle", "🎙  Última línea eliminada")
        else:
            linea = _a_codigo(_normalizar(texto))
            self._editor.insert("end", linea + "\n")
            self._estado("idle", f'🎙  Insertado: "{linea}"')


# ── punto de entrada ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    App().mainloop()
