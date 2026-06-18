#!/bin/bash
# ================================================
# Script: pipeline_ci.sh
# Descripción: Pipeline CI - Build → Test → Validate
# Simula GitHub Actions / Jenkins localmente
# ================================================

set -e

PASS=0
FAIL=0
WARNINGS=0
START_TIME=$(date +%s)

print_header() {
    echo ""
    echo "╔══════════════════════════════════════════╗"
    echo "║  $1"
    echo "╚══════════════════════════════════════════╝"
}

print_step() {
    echo ""
    echo "──────────────────────────────────────────"
    echo "  STAGE: $1"
    echo "──────────────────────────────────────────"
}

print_ok()   { echo "  ✓ $1"; ((PASS++)); }
print_fail() { echo "  ✗ $1"; ((FAIL++)); }
print_warn() { echo "  ⚠ $1"; ((WARNINGS++)); }

print_header "PIPELINE CI - TASK MANAGER"
echo "  Inicio: $(date '+%Y-%m-%d %H:%M:%S')"
echo "  Rama: main | Commit: $(git rev-parse --short HEAD 2>/dev/null || echo 'N/A')"


# ─── STAGE 1: BUILD ──────────────────────────────
print_step "1/4 - BUILD"

echo "  Verificando estructura del proyecto..."
if [ -f "/home/claude/taskmanager/app/app.py" ]; then
    print_ok "app.py encontrado"
else
    print_fail "app.py no encontrado"
fi

if [ -f "/home/claude/taskmanager/app/requirements.txt" ]; then
    print_ok "requirements.txt encontrado"
else
    print_fail "requirements.txt no encontrado"
fi

echo "  Verificando sintaxis Python..."
if python3 -m py_compile /home/claude/taskmanager/app/app.py 2>/dev/null; then
    print_ok "Sintaxis Python válida"
else
    print_fail "Error de sintaxis en app.py"
fi

echo "  Instalando dependencias..."
pip install --break-system-packages -r /home/claude/taskmanager/app/requirements.txt -q
print_ok "Dependencias instaladas"


# ─── STAGE 2: TEST ───────────────────────────────
print_step "2/4 - TEST"

echo "  Ejecutando suite de pruebas..."
cd /home/claude/taskmanager

TEST_OUTPUT=$(python3 -m pytest tests/test_tasks.py -v --tb=short 2>&1)
TEST_EXIT=$?

echo "$TEST_OUTPUT"

if [ $TEST_EXIT -eq 0 ]; then
    # Contar tests pasados
    PASSED=$(echo "$TEST_OUTPUT" | grep -c " PASSED" || true)
    FAILED=$(echo "$TEST_OUTPUT" | grep -c " FAILED" || true)
    print_ok "Tests ejecutados: $PASSED pasaron, $FAILED fallaron"
else
    print_fail "Suite de pruebas falló"
    FAIL=$((FAIL+1))
fi


# ─── STAGE 3: VALIDACIONES ───────────────────────
print_step "3/4 - VALIDACIONES"

echo "  Verificando endpoints de la API..."
# Iniciar servidor en background para smoke test
python3 /home/claude/taskmanager/app/app.py &
APP_PID=$!
sleep 2

if kill -0 $APP_PID 2>/dev/null; then
    print_ok "Servidor inició correctamente (PID: $APP_PID)"
    
    # Health check
    HEALTH=$(curl -s http://localhost:5000/health 2>/dev/null)
    if echo "$HEALTH" | grep -q "healthy"; then
        print_ok "Health check OK"
    else
        print_fail "Health check falló"
    fi
    
    # Smoke test: crear tarea
    CREATE=$(curl -s -X POST http://localhost:5000/tasks \
        -H "Content-Type: application/json" \
        -d '{"titulo":"Smoke Test Task"}' 2>/dev/null)
    if echo "$CREATE" | grep -q "Smoke Test Task"; then
        print_ok "Endpoint POST /tasks funcional"
    else
        print_fail "Endpoint POST /tasks falló"
    fi
    
    # Smoke test: listar tareas
    LIST=$(curl -s http://localhost:5000/tasks 2>/dev/null)
    if echo "$LIST" | grep -q "\["; then
        print_ok "Endpoint GET /tasks funcional"
    else
        print_fail "Endpoint GET /tasks falló"
    fi
    
    kill $APP_PID 2>/dev/null
else
    print_fail "Servidor no inició"
fi


# ─── STAGE 4: REPORTE ────────────────────────────
print_step "4/4 - REPORTE FINAL"

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
echo "  ┌─────────────────────────────────┐"
echo "  │  RESUMEN DEL PIPELINE           │"
echo "  │  Duración: ${DURATION}s               │"
echo "  │  ✓ Verificaciones OK: $PASS         │"
echo "  │  ✗ Fallos: $FAIL                    │"
echo "  │  ⚠ Advertencias: $WARNINGS          │"
echo "  └─────────────────────────────────┘"

if [ $FAIL -gt 0 ]; then
    echo ""
    echo "  ❌ PIPELINE FALLÓ - No apto para despliegue"
    exit 1
else
    echo ""
    echo "  ✅ PIPELINE EXITOSO - Listo para despliegue"
    exit 0
fi
