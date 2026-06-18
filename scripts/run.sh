#!/bin/bash
# ================================================
# Script: run.sh
# Descripción: Ejecuta el Task Manager según entorno
# Uso: ./run.sh [dev|test|prod]
# ================================================

set -e

ENV=${1:-dev}
APP_DIR="/home/claude/taskmanager/app"

echo "============================================="
echo "  TASK MANAGER - Inicio del servidor"
echo "  Entorno: $ENV"
echo "============================================="

case $ENV in
  dev)
    export PORT=5000
    export ENV=dev
    echo "[INFO] Modo desarrollo - debug activado, puerto $PORT"
    ;;
  test)
    export PORT=5001
    export ENV=test
    echo "[INFO] Modo test - puerto $PORT"
    ;;
  prod)
    export PORT=8080
    export ENV=prod
    echo "[INFO] Modo producción - puerto $PORT"
    ;;
  *)
    echo "[ERROR] Entorno desconocido: $ENV"
    exit 1
    ;;
esac

echo "[INFO] Iniciando aplicación..."
python3 "$APP_DIR/app.py"
