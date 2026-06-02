#!/bin/bash
# Lanza el compilador en modo voz

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

# Compilar si el binario no existe
if [ ! -f "build/compilador" ]; then
    echo "Compilando el proyecto..."
    make
fi

# Usar Python del entorno virtual si existe, si no el del sistema
if [ -f "venv/bin/python3" ]; then
    PYTHON="venv/bin/python3"
else
    PYTHON="python3"
fi

# Apuntar al micrófono real (evita que PipeWire use el loopback por defecto)
pactl set-default-source alsa_input.pci-0000_00_1f.3.analog-stereo 2>/dev/null || true
pactl set-source-volume  alsa_input.pci-0000_00_1f.3.analog-stereo 80%        2>/dev/null || true

# Lanzar voz.py filtrando warnings de ALSA
$PYTHON voz/voz.py 2> >(grep -v "^ALSA\|snd_\|pcm\." >&2)
