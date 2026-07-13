#!/bin/bash

# Script para iniciar el simulador de escritorio en tiempo real (PyQt6 + pyqtgraph)
# TFI Teoría de Control K-4011 · UTN FRBA

echo "--------------------------------------------------------"
echo "🖥️  Iniciando Simulador de Escritorio (Tiempo Real) - PyQt6"
echo "--------------------------------------------------------"

# 1. Asegurar que estamos en el directorio del script
cd "$(dirname "$0")"

# 2. Verificar que Python 3 está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 no está instalado en el sistema."
    echo "Por favor, instale Python 3 antes de ejecutar la simulación."
    exit 1
fi

# 3. Verificar o crear el entorno virtual
if [ ! -d ".venv" ]; then
    echo "⚠️  No se encontró el entorno virtual (.venv). Creándolo..."
    if command -v uv &> /dev/null; then
        echo "✨ Detectado 'uv'. Creando entorno virtual rápido..."
        uv venv
    else
        echo "🐍 'uv' no detectado. Creando entorno virtual con python3 -m venv..."
        python3 -m venv .venv
    fi
fi

# 4. Activar el entorno virtual
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
else
    echo "❌ Error: No se pudo activar el entorno virtual."
    exit 1
fi

# 5. Instalar/Actualizar dependencias
echo "📦 Verificando e instalando dependencias (incluye PyQt6 y pyqtgraph)..."
if command -v uv &> /dev/null; then
    uv pip install -r requirements.txt --quiet
else
    pip install --upgrade pip --quiet
    pip install -r requirements.txt --quiet
fi

# 6. Ejecutar el simulador de escritorio
echo "🚀 Lanzando aplicación PyQt6..."
echo "--------------------------------------------------------"
.venv/bin/python src/app_escritorio.py

