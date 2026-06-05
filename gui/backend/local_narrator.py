import shutil
import subprocess


class LocalNarrator:
    def __init__(self):
        self._process: subprocess.Popen | None = None
        self.available = shutil.which("espeak-ng") is not None

    def speak(self, text: str) -> None:
        if not text or not self.available:
            return
        self.stop()
        self._process = subprocess.Popen(
            ["espeak-ng", "-v", "es", "-s", "175", text],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def stop(self) -> None:
        if self._process and self._process.poll() is None:
            try:
                self._process.terminate()
            except Exception:
                pass
        self._process = None
