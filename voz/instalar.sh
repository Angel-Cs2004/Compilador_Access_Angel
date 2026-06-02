#!/bin/bash
# Instala las dependencias necesarias para el modo voz
# Ejecutar desde la raíz del proyecto: bash voz/instalar.sh

set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo ""
echo "=== Instalando dependencias del modo voz ==="
echo ""

echo "[1/4] Instalando python-pyaudio (micrófono)..."
sudo pacman -S --noconfirm python-pyaudio

echo ""
echo "[2/4] Creando entorno virtual Python en ./venv/ ..."
python3 -m venv --system-site-packages venv

echo ""
echo "[3/4] Instalando Vosk (reconocimiento offline) en el entorno virtual..."
venv/bin/pip install --quiet vosk

echo ""
echo "[4/4] Descargando modelo de español (~39 MB)..."
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
echo "=== Instalación completada ==="
echo ""
echo "Para usar el modo voz:"
echo "  bash voz/ejecutar.sh"
echo ""
