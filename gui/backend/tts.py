import importlib.util
import os
import shutil
import subprocess
import tempfile
import threading
import asyncio
import time

EDGE_TTS_AVAILABLE: bool = importlib.util.find_spec("edge_tts") is not None
PYTTSX3_AVAILABLE: bool = importlib.util.find_spec("pyttsx3") is not None
TTS_AVAILABLE: bool = EDGE_TTS_AVAILABLE or PYTTSX3_AVAILABLE

_SPANISH_VOICE_HINTS = ("helena", "spanish", "español", "es-", "sabina", "jorge")
_EDGE_VOICE = "es-PE-CamilaNeural"


def tts_missing_dependency_message() -> str | None:
    if EDGE_TTS_AVAILABLE:
        if _find_audio_player() is None:
            return "Falta reproductor de audio. Instala ffmpeg o mpg123."
        return None
    if PYTTSX3_AVAILABLE:
        if shutil.which("espeak-ng") is None and shutil.which("espeak") is None:
            return "Falta espeak-ng. Instálalo con: sudo pacman -S espeak-ng"
        if shutil.which("aplay") is None:
            return "Falta aplay. Instálalo con: sudo pacman -S alsa-utils"
        return None
    return "Falta TTS. Instala: venv/bin/pip install edge-tts pyttsx3"


def tts_engine_name() -> str:
    if EDGE_TTS_AVAILABLE:
        return "voz neuronal"
    if PYTTSX3_AVAILABLE:
        return "voz offline"
    return "voz no disponible"


def _find_audio_player() -> list[str] | None:
    if shutil.which("ffplay"):
        return ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"]
    if shutil.which("mpg123"):
        return ["mpg123", "-q"]
    return None


class TTSEngine:
    def __init__(self):
        self._engine  = None
        self._player  = None
        self._active  = False
        self._lock    = threading.Lock()
        self._generation = 0

    @property
    def active(self) -> bool:
        return self._active

    def speak(self, text: str, on_done) -> None:
        """Start speaking in a background thread.

        on_done(error: str | None) is called when finished or stopped.
        """
        missing = tts_missing_dependency_message()
        if missing:
            on_done(error=missing)
            return
        if not text:
            return
        self.stop()
        with self._lock:
            self._generation += 1
            generation = self._generation
            self._active = True
        threading.Thread(
            target=self._speak_task,
            args=(text, generation, on_done),
            daemon=True,
        ).start()

    def stop(self) -> None:
        with self._lock:
            self._generation += 1
            self._active = False
        player = self._player
        if player and player.poll() is None:
            try:
                player.terminate()
            except Exception:
                pass
        engine = self._engine
        if engine:
            try:
                engine.stop()
            except Exception:
                pass

    def _is_current(self, generation: int) -> bool:
        return self._active and generation == self._generation

    def _speak_task(self, text: str, generation: int, on_done) -> None:
        error = None
        try:
            if EDGE_TTS_AVAILABLE:
                self._speak_edge(text, generation)
            else:
                self._speak_pyttsx3(text, generation)
        except Exception as exc:
            error = str(exc)
        finally:
            if generation == self._generation:
                self._engine = None
                self._player = None
                self._active = False
        if generation == self._generation:
            on_done(error=error)

    def _speak_edge(self, text: str, generation: int) -> None:
        import edge_tts

        player_cmd = _find_audio_player()
        if player_cmd is None:
            raise RuntimeError("No hay reproductor de audio disponible.")

        fd, path = tempfile.mkstemp(suffix=".mp3")
        os.close(fd)
        try:
            communicate = edge_tts.Communicate(
                text,
                voice=_EDGE_VOICE,
                rate="-6%",
                volume="+0%",
            )
            asyncio.run(communicate.save(path))
            if not self._is_current(generation):
                return
            self._player = subprocess.Popen(
                [*player_cmd, path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            while self._player.poll() is None:
                if not self._is_current(generation):
                    try:
                        self._player.terminate()
                    except Exception:
                        pass
                    return
                time.sleep(0.1)
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass

    def _speak_pyttsx3(self, text: str, generation: int) -> None:
        import pyttsx3

        if not self._is_current(generation):
            return
        engine = pyttsx3.init()
        self._engine = engine
        for voice in engine.getProperty("voices"):
            name = (voice.name or "").lower()
            vid  = (voice.id   or "").lower()
            if any(hint in name or hint in vid for hint in _SPANISH_VOICE_HINTS):
                engine.setProperty("voice", voice.id)
                break
        engine.setProperty("rate", 150)
        engine.setProperty("volume", 1.0)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
