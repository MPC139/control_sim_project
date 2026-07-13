#!/bin/bash

# Instrucciones para iniciar el simulador de Control de Temperatura

echo "--------------------------------------------------------"
echo "🚀 Iniciando Entorno de Simulación de Teoría de Control"
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
echo "📦 Verificando e instalando dependencias..."
if command -v uv &> /dev/null; then
    uv pip install -r requirements.txt --quiet
else
    pip install --upgrade pip --quiet
    pip install -r requirements.txt --quiet
fi

# 6. Ejecutar la aplicación de Streamlit
echo "🌐 Iniciando servidor web de Streamlit..."
echo "ℹ️  La aplicación debería abrirse automáticamente en su navegador."
echo "   Si no abre, acceda a: http://localhost:8501"
echo "--------------------------------------------------------"
.venv/bin/python -m streamlit run src/app.py
