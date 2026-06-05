import os
import subprocess
import sys
import tempfile
import threading

from gui.theme import strip_ansi
from gui.config import ROOT_DIR

OUTPUT_TABS = ("Tokens", "AST", "TAC", "Python", "Reporte")


class CompilerBackend:
    def __init__(self):
        self.binary = self._find_binary()

    def available(self) -> bool:
        return self.binary is not None

    def compile(self, source: str, on_done) -> None:
        """Run compilation in a background thread.

        on_done(outputs: dict[str, str], success: bool) is called from that thread.
        """
        threading.Thread(target=self._compile_task, args=(source, on_done), daemon=True).start()

    def execute(self, source: str, on_done) -> None:
        """Compile then execute the generated Python.

        on_done(output: str, success: bool) is called from that thread.
        """
        threading.Thread(target=self._execute_task, args=(source, on_done), daemon=True).start()

    # ── private ──────────────────────────────────────────────────────────────

    def _find_binary(self) -> str | None:
        for name in ("compilador", "compilador.exe"):
            path = ROOT_DIR / "build" / name
            if os.path.isfile(path):
                return str(path)
        return None

    def _invoke(self, args: list[str]) -> str:
        try:
            result = subprocess.run(
                [self.binary, *args],
                capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=20,
            )
            return strip_ansi(result.stdout + result.stderr)
        except subprocess.TimeoutExpired:
            return "⚠  Tiempo de espera agotado (>20 s)."
        except Exception as exc:
            return f"⚠  Error al invocar el compilador:\n{exc}"

    def _compile_task(self, source: str, on_done) -> None:
        fd, tmp = tempfile.mkstemp(suffix=".acc")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(source)
            outputs = {
                "Tokens":  self._invoke(["--tokens", tmp]),
                "AST":     self._invoke(["--ast",    tmp]),
                "TAC":     self._invoke(["--ir",     tmp]),
                "Python":  self._invoke(["--gen",    tmp]),
                "Reporte": self._invoke([tmp]),
            }
            success = "COMPILACION EXITOSA" in outputs["Reporte"]
        finally:
            try:
                os.unlink(tmp)
            except OSError:
                pass
        on_done(outputs, success)

    def _execute_task(self, source: str, on_done) -> None:
        fd_acc, tmp_acc = tempfile.mkstemp(suffix=".acc")
        fd_py,  tmp_py  = tempfile.mkstemp(suffix=".py")
        os.close(fd_py)
        try:
            with os.fdopen(fd_acc, "w", encoding="utf-8") as f:
                f.write(source)

            comp = subprocess.run(
                [self.binary, "--salida", tmp_py, tmp_acc],
                capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=20,
            )
            if comp.returncode != 0:
                output = "✗ Error de compilación — el programa no pudo ejecutarse:\n\n"
                output += strip_ansi(comp.stdout + comp.stderr)
                on_done(output, False)
                return

            run = subprocess.run(
                [sys.executable, tmp_py],
                capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=10,
            )
            output = run.stdout
            if run.stderr:
                output += "\n── Errores de ejecución ──\n" + run.stderr
            if not output.strip():
                output = "(El programa ejecutó sin producir salida)"
            on_done(output, run.returncode == 0)

        except subprocess.TimeoutExpired:
            on_done(
                "⚠  Tiempo agotado (>10 s).\nEl programa puede tener un bucle infinito.",
                False,
            )
        except Exception as exc:
            on_done(f"⚠  Error inesperado:\n{exc}", False)
        finally:
            for path in (tmp_acc, tmp_py):
                try:
                    os.unlink(path)
                except OSError:
                    pass
