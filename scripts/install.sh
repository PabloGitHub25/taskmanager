#!/bin/bash
# ================================================
# Script: install.sh
# Entorno: DEV / TEST / PROD
# Descripción: Instala dependencias del Task Manager
# ================================================

set -e  # Salir si cualquier comando falla

ENV=${1:-dev}  # Default: dev

echo "============================================="
echo "  TASK MANAGER - Instalación de dependencias"
echo "  Entorno: $ENV"
echo "============================================="

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 no encontrado. Instalando..."
    apt-get update -qq && apt-get install -y python3 python3-pip
fi

echo "[INFO] Python version: $(python3 --version)"

# Instalar dependencias
echo "[INFO] Instalando dependencias Python..."
pip install --break-system-packages -r /home/claude/taskmanager/app/requirements.txt -q

echo "[OK] Dependencias instaladas correctamente"

# Verificar instalación
python3 -c "import flask; print(f'[OK] Flask {flask.__version__}')"
python3 -c "import pytest; print(f'[OK] Pytest {pytest.__version__}')"

echo "============================================="
echo "  Instalación completada para entorno: $ENV"
echo "============================================="
