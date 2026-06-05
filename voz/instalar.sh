#!/bin/bash
# Instala las dependencias necesarias para el modo voz
# Ejecutar desde la raíz del proyecto: bash voz/instalar.sh

set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo ""
echo "=== Instalando dependencias del modo voz ==="
echo ""

echo "[1/5] Instalando python-pyaudio, espeak-ng y alsa-utils..."
sudo pacman -S --noconfirm python-pyaudio espeak-ng alsa-utils

echo ""
echo "[2/5] Creando entorno virtual Python en ./venv/ ..."
python3 -m venv --system-site-packages venv

echo ""
echo "[3/5] Instalando dependencias Python de la GUI y voz..."
venv/bin/pip install --quiet vosk pyttsx3 edge-tts customtkinter groq

echo ""
echo "[4/5] Descargando modelo de español (~39 MB)..."
mkdir -p voz/models
cd voz/models

if [ ! -d "vosk-model-small-es-0.42" ]; then
    echo "  Descargando vosk-model-small-es-0.42.zip ..."
    curl -L -o modelo_es.zip \
        "https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip"
    echo "  Descomprimiendo..."
    unzip -q modelo_es.zip
    rm modelo_es.zip
    echo "  Modelo listo en voz/models/vosk-model-small-es-0.42/"
else
    echo "  Modelo ya descargado, omitiendo."
fi

cd "$ROOT_DIR"

echo ""
echo "[5/5] Compilando el proyecto si hace falta..."
make

echo ""
echo "=== Instalación completada ==="
echo ""
echo "Para usar la GUI:"
echo "  venv/bin/python3 gui.py"
echo ""
echo "Para usar el modo voz por terminal:"
echo "  bash voz/ejecutar.sh"
echo ""
