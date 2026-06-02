#!/usr/bin/env python3
"""
Capa de voz para el Compilador Accesible
Motor: Vosk (offline, streaming) — el texto aparece mientras hablas,
sin esperar a Google ni depender de internet.
"""

import os
import sys
import json
import unicodedata
import subprocess
import tempfile

import pyaudio
from vosk import Model, KaldiRecognizer, SetLogLevel

SetLogLevel(-1)  # silencia logs internos de Vosk

# ── Colores ANSI ──────────────────────────────────────────────────────────────
R  = "\033[0m"
B  = "\033[1m"
RD = "\033[31m"
GN = "\033[32m"
YL = "\033[33m"
CY = "\033[36m"
BL = "\033[34m"
DM = "\033[2m"

# ── Rutas ─────────────────────────────────────────────────────────────────────
_DIR       = os.path.dirname(os.path.abspath(__file__))
COMPILADOR = os.path.join(_DIR, "..", "build", "compilador")
MODEL_DIR  = os.path.join(_DIR, "models", "vosk-model-small-es-0.42")

# ── Comandos de voz reconocidos ───────────────────────────────────────────────
CMDS_EJECUTAR   = {"ejecutar", "compilar", "correr", "procesar"}
CMDS_NUEVA_LINE = {"nueva linea", "enter", "siguiente linea", "salto"}
CMDS_MOSTRAR    = {"mostrar codigo", "ver codigo", "que tengo"}
CMDS_LIMPIAR    = {"limpiar", "borrar todo", "reset"}
CMDS_DESHACER   = {"deshacer", "borrar linea", "undo"}
CMDS_SALIR      = {"salir", "terminar", "cerrar", "exit"}

# ── Configuración de audio ────────────────────────────────────────────────────
SAMPLE_RATE = 16000   # Vosk requiere 16kHz mono
CHUNK       = 4000    # 250ms de audio por lectura

# ── Traducción fonética → símbolo ────────────────────────────────────────────
# Vosk transcribe lo que escucha: "x" → "equis", 6 → "seis".
# Estas tablas convierten el habla al símbolo real antes de meter al buffer.

LETRAS_ES = {
    "equis":  "x",  "jota":  "j",  "ka":    "k",  "ele":   "l",
    "eme":    "m",  "ene":   "n",  "eñe":   "ñ",  "pe":    "p",
    "erre":   "r",  "ese":   "s",  "te":    "t",  "uve":   "v",
    "ye":     "y",  "zeta":  "z",  "hache": "h",  "efe":   "f",
    "ce":     "c",  "ge":    "g",
}

NUMEROS_ES = {
    "cero":      "0",
    "uno":       "1",   "una":      "1",
    "dos":       "2",
    "tres":      "3",
    "cuatro":    "4",
    "cinco":     "5",
    "seis":      "6",
    "siete":     "7",
    "ocho":      "8",
    "nueve":     "9",
    "diez":      "10",
    "once":      "11",
    "doce":      "12",
    "trece":     "13",
    "catorce":   "14",
    "quince":    "15",
    "veinte":    "20",
    "treinta":   "30",
    "cuarenta":  "40",
    "cincuenta": "50",
    "cien":      "100",
}


# ── Utilidades de texto ───────────────────────────────────────────────────────

def quitar_tildes(texto: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )

def normalizar(texto: str) -> str:
    return quitar_tildes(texto.lower().strip(" .,!¿?¡"))

def traducir_a_codigo(texto: str) -> str:
    """Convierte palabras habladas a símbolos de código: 'equis' → 'x', 'seis' → '6'."""
    t = (texto
         .replace("doble uve", "w")
         .replace("doble ve",  "w")
         .replace("i griega",  "y")
         .replace("punto",     "."))
    palabras = t.split()
    return " ".join(
        LETRAS_ES.get(p, NUMEROS_ES.get(p, p))
        for p in palabras
    )


# ── UI ────────────────────────────────────────────────────────────────────────

def banner():
    print(f"\n{BL}{B}  ╔══════════════════════════════════════╗")
    print(f"  ║   COMPILADOR ACCESIBLE — MODO VOZ    ║")
    print(f"  ║   Motor offline  •  Sin internet     ║")
    print(f"  ╚══════════════════════════════════════╝{R}\n")
    print(f"{B}Comandos disponibles:{R}")
    print(f"  {CY}\"nueva linea\"{R}    → inserta salto de línea")
    print(f"  {CY}\"ejecutar\"{R}       → compila y muestra el AST")
    print(f"  {CY}\"mostrar codigo\"{R} → imprime el buffer actual")
    print(f"  {CY}\"deshacer\"{R}       → elimina la última línea")
    print(f"  {CY}\"limpiar\"{R}        → vacía el buffer")
    print(f"  {CY}\"salir\"{R}          → cierra el programa\n")

def mostrar_buffer(buffer: list[str]):
    if not buffer:
        print(f"\r{YL}  (buffer vacío){R}                              ")
        return
    print(f"\n{B}── Código acumulado ──────────────────────{R}")
    for i, linea in enumerate(buffer, 1):
        print(f"  {BL}{i:2}.{R} {linea if linea else '(línea vacía)'}")
    print(f"{B}─────────────────────────────────────────{R}\n")


# ── Compilador ────────────────────────────────────────────────────────────────

def ejecutar_compilador(codigo: str) -> str:
    if not os.path.isfile(COMPILADOR):
        return f"{RD}Error: ejecuta 'make' primero{R}"
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".acc", delete=False, encoding="utf-8"
    ) as f:
        f.write(codigo)
        ruta = f.name
    try:
        r = subprocess.run(
            [COMPILADOR, ruta], capture_output=True, text=True, timeout=10
        )
        return r.stdout + (r.stderr if r.returncode != 0 else "")
    except subprocess.TimeoutExpired:
        return f"{RD}Timeout del compilador{R}"
    finally:
        os.unlink(ruta)


# ── Comandos ──────────────────────────────────────────────────────────────────

def procesar_comando(norm: str, buffer: list[str]) -> bool:
    if norm in CMDS_SALIR:
        print(f"\n{BL}Cerrando. ¡Hasta luego!{R}\n")
        sys.exit(0)
    if norm in CMDS_NUEVA_LINE:
        buffer.append("")
        print(f"\r  {YL}↵ Nueva línea insertada{R}                         ")
        return True
    if norm in CMDS_MOSTRAR:
        mostrar_buffer(buffer)
        return True
    if norm in CMDS_LIMPIAR:
        buffer.clear()
        print(f"\r  {YL}Buffer limpiado.{R}                                ")
        return True
    if norm in CMDS_DESHACER:
        if buffer:
            print(f"\r  {YL}Eliminada: '{buffer.pop()}'{R}                     ")
        else:
            print(f"\r  {YL}Buffer ya vacío.{R}                               ")
        return True
    if norm in CMDS_EJECUTAR:
        if not buffer:
            print(f"\r  {YL}No hay código aún. Habla primero.{R}              ")
            return True
        mostrar_buffer(buffer)
        print(f"{B}── Compilando... ─────────────────────────{R}")
        print(ejecutar_compilador("\n".join(buffer)))
        buffer.clear()
        return True
    return False


# ── Bucle principal ───────────────────────────────────────────────────────────

def main():
    if not os.path.isfile(COMPILADOR):
        print(f"{RD}Error: ejecuta 'make' primero para compilar el proyecto.{R}")
        sys.exit(1)

    if not os.path.isdir(MODEL_DIR):
        print(f"{RD}Modelo de voz no encontrado.")
        print(f"Ejecuta:  bash voz/instalar.sh{R}")
        sys.exit(1)

    banner()

    print(f"{YL}Cargando modelo de voz...{R}", end=" ", flush=True)
    model = Model(MODEL_DIR)
    rec   = KaldiRecognizer(model, SAMPLE_RATE)
    print(f"{GN}listo{R}\n")

    p      = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=CHUNK,
    )

    print(f"{GN}🎙 Micrófono activo — habla cuando quieras.{R}\n")

    buffer: list[str] = []

    try:
        while True:
            data = stream.read(CHUNK, exception_on_overflow=False)

            if rec.AcceptWaveform(data):
                # Frase completa → procesar
                texto = json.loads(rec.Result()).get("text", "").strip()

                if not texto:
                    print(f"\r{GN}🎙{R} {DM}●{R}                                        ",
                          end="", flush=True)
                    continue

                norm = normalizar(texto)
                print(f"\r{GN}🎙{R}  {B}{texto}{R}                                   ")

                if procesar_comando(norm, buffer):
                    continue

                linea = traducir_a_codigo(quitar_tildes(texto.strip().lower()))
                buffer.append(linea)
                print(f"  {CY}+{R} {B}'{linea}'{R}  {YL}← línea {len(buffer)}{R}")

            else:
                # Resultado parcial — aparece mientras hablas (como el celular)
                parcial = json.loads(rec.PartialResult()).get("partial", "")
                if parcial:
                    print(f"\r{GN}🎙{R}  {DM}{parcial}...{R}                               ",
                          end="", flush=True)
                else:
                    print(f"\r{GN}🎙 ● Escuchando...{R}                               ",
                          end="", flush=True)

    except KeyboardInterrupt:
        pass
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
        print(f"\n{BL}Cerrando. ¡Hasta luego!{R}\n")


if __name__ == "__main__":
    main()
