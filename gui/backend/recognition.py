import importlib.util
import json
import threading
import unicodedata

VOICE_AVAILABLE: bool = (
    importlib.util.find_spec("vosk") is not None
    and importlib.util.find_spec("pyaudio") is not None
)

_LETRAS: dict[str, str] = {
    "equis": "x", "jota": "j", "ka": "k",   "ele": "l",  "eme": "m",
    "ene":   "n", "eñe":  "ñ", "pe":  "p",  "erre": "r", "ese": "s",
    "te":    "t", "uve":  "v", "ye":  "y",  "zeta": "z", "hache": "h",
    "efe":   "f", "ce":   "c", "ge":  "g",
}
_NUMEROS: dict[str, str] = {
    "cero": "0",  "uno": "1",    "una": "1",   "dos": "2",      "tres": "3",
    "cuatro": "4","cinco": "5",  "seis": "6",  "siete": "7",    "ocho": "8",
    "nueve": "9", "diez": "10",  "once": "11", "doce": "12",    "trece": "13",
    "catorce": "14", "quince": "15", "veinte": "20", "treinta": "30",
    "cuarenta": "40", "cincuenta": "50", "cien": "100",
}

CMDS_NEWLINE : frozenset[str] = frozenset({"nueva linea", "enter", "siguiente linea", "salto de linea"})
CMDS_COMPILE : frozenset[str] = frozenset({"compilar", "ejecutar", "correr", "procesar"})
CMDS_CLEAR   : frozenset[str] = frozenset({"limpiar", "borrar todo", "reset"})
CMDS_UNDO    : frozenset[str] = frozenset({"deshacer", "borrar linea", "undo"})


def normalize(text: str) -> str:
    without_accents = "".join(
        ch for ch in unicodedata.normalize("NFD", text)
        if unicodedata.category(ch) != "Mn"
    )
    return without_accents.lower().strip(" .,!¿?¡")


def to_code(text: str) -> str:
    t = (text
         .replace("doble uve", "w").replace("doble ve", "w")
         .replace("i griega", "y").replace("punto", "."))
    return " ".join(_LETRAS.get(word, _NUMEROS.get(word, word)) for word in t.split())


class VoiceRecognizer(threading.Thread):
    def __init__(self, model_path: str, on_ready, on_final, on_partial, on_error):
        super().__init__(daemon=True)
        self._model_path = model_path
        self._running    = True
        self.on_ready    = on_ready
        self.on_final    = on_final
        self.on_partial  = on_partial
        self.on_error    = on_error

    def stop(self) -> None:
        self._running = False

    def run(self) -> None:
        try:
            import pyaudio
            from vosk import KaldiRecognizer, Model, SetLogLevel

            SetLogLevel(-1)
            model  = Model(self._model_path)
            rec    = KaldiRecognizer(model, 16000)
            pa     = pyaudio.PyAudio()
            stream = pa.open(
                format=pyaudio.paInt16, channels=1,
                rate=16000, input=True, frames_per_buffer=4000,
            )
            self.on_ready()
            while self._running:
                data = stream.read(4000, exception_on_overflow=False)
                if rec.AcceptWaveform(data):
                    text = json.loads(rec.Result()).get("text", "").strip()
                    if text:
                        self.on_final(text)
                else:
                    partial = json.loads(rec.PartialResult()).get("partial", "")
                    self.on_partial(partial)
            stream.stop_stream()
            stream.close()
            pa.terminate()
        except Exception as exc:
            self.on_error(str(exc))
