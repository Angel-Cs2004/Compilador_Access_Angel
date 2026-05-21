#!/usr/bin/env python3
"""
Capa de voz para el Compilador Accesible
Captura voz por micrófono → texto → ./compilador

Comandos de voz especiales:
  "nueva linea"         → inserta salto de línea en el buffer
  "ejecutar/compilar"   → envía el buffer al compilador
  "mostrar"             → muestra el código acumulado hasta ahora
  "deshacer"            → elimina la última línea del buffer
  "limpiar/borrar todo" → limpia el buffer
  "salir/terminar"      → cierra el programa
"""

import os
import sys
import speech_recognition as sr
import subprocess
import tempfile

# ── Colores ANSI ────────────────────────────────────────────────────────────
R  = "\033[0m"
B  = "\033[1m"
RD = "\033[31m"
GN = "\033[32m"
YL = "\033[33m"
CY = "\033[36m"
BL = "\033[34m"

# ── Ruta al compilador (relativa al script: voz/ → build/compilador) ─────────
DIR_BASE   = os.path.dirname(os.path.abspath(__file__))
COMPILADOR = os.path.join(DIR_BASE, "..", "build", "compilador")

# ── Comandos de voz reconocidos ──────────────────────────────────────────────
CMDS_EJECUTAR   = {"ejecutar", "compilar", "correr", "procesar"}
CMDS_NUEVA_LINE = {"nueva linea", "nueva línea", "enter", "siguiente linea"}
CMDS_MOSTRAR    = {"mostrar", "mostrar código", "ver código", "ver codigo"}
CMDS_LIMPIAR    = {"limpiar", "borrar", "borrar todo", "limpiar todo", "reset"}
CMDS_DESHACER   = {"deshacer", "borrar linea", "quitar última linea"}
CMDS_SALIR      = {"salir", "terminar", "cerrar", "exit", "quitar"}


def banner():
    print(f"\n{BL}{B}  ╔══════════════════════════════════════╗")
    print(f"  ║   COMPILADOR ACCESIBLE — MODO VOZ    ║")
    print(f"  ║   Habla tu código en español         ║")
    print(f"  ╚══════════════════════════════════════╝{R}\n")
    print(f"{B}Comandos de voz disponibles:{R}")
    print(f"  {CY}\"nueva linea\"{R}   → salto de línea en el código")
    print(f"  {CY}\"ejecutar\"{R}      → envía el código al compilador")
    print(f"  {CY}\"mostrar\"{R}       → muestra el código acumulado")
    print(f"  {CY}\"deshacer\"{R}      → elimina la última línea")
    print(f"  {CY}\"limpiar\"{R}       → borra todo el buffer")
    print(f"  {CY}\"salir\"{R}         → cierra el programa\n")


def mostrar_buffer(buffer: list[str]):
    if not buffer:
        print(f"{YL}(buffer vacío){R}")
        return
    print(f"\n{B}── Código capturado ──────────────────────{R}")
    for i, linea in enumerate(buffer, 1):
        print(f"  {BL}{i:2}.{R} {linea}")
    print(f"{B}─────────────────────────────────────────{R}\n")


def ejecutar_compilador(codigo: str) -> str:
    """Escribe el código en un archivo temporal y llama al compilador."""
    if not os.path.isfile(COMPILADOR):
        return f"{RD}Error: no se encontró el compilador en '{COMPILADOR}'{R}"

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".acc", delete=False, encoding="utf-8"
    ) as f:
        f.write(codigo)
        ruta = f.name

    try:
        result = subprocess.run(
            [COMPILADOR, ruta],
            capture_output=True, text=True, timeout=10
        )
        salida = result.stdout
        if result.returncode != 0 and result.stderr:
            salida += result.stderr
        return salida
    except subprocess.TimeoutExpired:
        return f"{RD}Error: el compilador tardó demasiado{R}"
    finally:
        os.unlink(ruta)


def normalizar(texto: str) -> str:
    """Minúsculas y elimina puntuación final."""
    return texto.lower().strip(" .,!¿?")


def escuchar(rec: sr.Recognizer, mic: sr.Microphone) -> str | None:
    """Captura un fragmento de voz y lo convierte a texto."""
    print(f"{GN}🎙  Escuchando...{R}", end=" ", flush=True)
    try:
        with mic as source:
            audio = rec.listen(source, timeout=6, phrase_time_limit=8)
        texto = rec.recognize_google(audio, language="es-ES")
        print(f"{B}{texto}{R}")
        return texto
    except sr.WaitTimeoutError:
        print(f"{YL}(silencio){R}")
        return None
    except sr.UnknownValueError:
        print(f"{YL}(no se entendió){R}")
        return None
    except sr.RequestError as e:
        print(f"{RD}Error de red: {e}{R}")
        return None


def main():
    # Verificar que el compilador exista
    if not os.path.isfile(COMPILADOR):
        print(f"{RD}Error: primero ejecuta 'make' para compilar el proyecto.{R}")
        sys.exit(1)

    banner()

    rec = sr.Recognizer()
    rec.pause_threshold   = 0.8   # segundos de silencio antes de cortar
    rec.energy_threshold  = 300   # sensibilidad del micrófono
    rec.dynamic_energy_threshold = True

    # Calibración inicial del ruido ambiente
    print(f"{YL}Calibrando micrófono (1 segundo de silencio)...{R}")
    with sr.Microphone() as source:
        rec.adjust_for_ambient_noise(source, duration=1)
    print(f"{GN}Micrófono listo.{R}\n")

    mic    = sr.Microphone()
    buffer = []   # líneas de código acumuladas

    while True:
        texto = escuchar(rec, mic)
        if texto is None:
            continue

        norm = normalizar(texto)

        # ── Comandos especiales ─────────────────────────────────────────────
        if norm in CMDS_SALIR:
            print(f"\n{BL}Cerrando el compilador de voz. ¡Hasta luego!{R}\n")
            break

        if norm in CMDS_NUEVA_LINE:
            buffer.append("")
            print(f"  {YL}↵ Nueva línea insertada{R}")
            continue

        if norm in CMDS_MOSTRAR:
            mostrar_buffer(buffer)
            continue

        if norm in CMDS_LIMPIAR:
            buffer.clear()
            print(f"  {YL}Buffer limpiado.{R}")
            continue

        if norm in CMDS_DESHACER:
            if buffer:
                eliminada = buffer.pop()
                print(f"  {YL}Línea eliminada: '{eliminada}'{R}")
            else:
                print(f"  {YL}El buffer ya está vacío.{R}")
            continue

        if norm in CMDS_EJECUTAR:
            if not buffer:
                print(f"  {YL}No hay código que compilar. Habla primero.{R}")
                continue
            codigo = "\n".join(buffer)
            print(f"\n{B}── Enviando al compilador ─────────────────{R}")
            mostrar_buffer(buffer)
            resultado = ejecutar_compilador(codigo)
            print(resultado)
            buffer.clear()
            continue

        # ── Línea de código normal ──────────────────────────────────────────
        # Google puede devolver la línea con mayúscula inicial, la normalizamos
        linea = texto.strip().lower()
        buffer.append(linea)
        print(f"  {CY}+{R} '{linea}' {YL}(línea {len(buffer)}){R}")


if __name__ == "__main__":
    main()
