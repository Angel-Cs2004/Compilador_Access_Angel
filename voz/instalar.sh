#!/bin/bash
# Instala las dependencias necesarias para el modo voz
# Ejecutar desde la raíz del proyecto: bash voz/instalar.sh

set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo ""
echo "=== Instalando dependencias del modo voz ==="
echo ""

echo "[1/3] Instalando python-pyaudio (micrófono)..."
sudo pacman -S --noconfirm python-pyaudio

echo ""
echo "[2/3] Creando entorno virtual Python en ./venv/ ..."
python3 -m venv --system-site-packages venv

echo ""
echo "[3/3] Instalando SpeechRecognition en el entorno virtual..."
venv/bin/pip install --quiet SpeechRecognition

echo ""
echo "=== Instalación completada ==="
echo ""
echo "Para usar el modo voz:"
echo "  bash voz/ejecutar.sh"
echo ""
