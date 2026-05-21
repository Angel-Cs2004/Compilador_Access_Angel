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

# Lanzar voz.py filtrando warnings de ALSA
$PYTHON voz/voz.py 2> >(grep -v "^ALSA\|snd_\|pcm\." >&2)
