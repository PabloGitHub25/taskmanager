#!/bin/bash

PASS=0
FAIL=0
START_TIME=$(date +%s)
ROOT="/workspaces/taskmanager"

print_ok()   { echo "  ✓ $1"; PASS=$((PASS+1)); }
print_fail() { echo "  ✗ $1"; FAIL=$((FAIL+1)); }

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║  PIPELINE CI - TASK MANAGER"
echo "╚══════════════════════════════════════════╝"
echo "  Inicio: $(date '+%Y-%m-%d %H:%M:%S')"
echo "  Rama: main | Commit: $(git rev-parse --short HEAD 2>/dev/null || echo 'N/A')"

echo ""
echo "──────────────────────────────────────────"
echo "  STAGE: 1/4 - BUILD"
echo "──────────────────────────────────────────"

[ -f "$ROOT/app/app.py" ]           && print_ok "app.py encontrado"           || print_fail "app.py no encontrado"
[ -f "$ROOT/app/requirements.txt" ] && print_ok "requirements.txt encontrado"  || print_fail "requirements.txt no encontrado"

python3 -m py_compile "$ROOT/app/app.py" 2>/dev/null \
  && print_ok "Sintaxis Python válida" || print_fail "Error de sintaxis"

pip install -r "$ROOT/app/requirements.txt" -q \
  && print_ok "Dependencias instaladas" || print_fail "Error instalando dependencias"

echo ""
echo "──────────────────────────────────────────"
echo "  STAGE: 2/4 - TEST"
echo "──────────────────────────────────────────"

cd "$ROOT"
python3 -m pytest tests/test_tasks.py -v --tb=short
TEST_EXIT=$?
if [ $TEST_EXIT -eq 0 ]; then
    print_ok "Todas las pruebas pasaron"
else
    print_fail "Pruebas fallaron"
fi

echo ""
echo "──────────────────────────────────────────"
echo "  STAGE: 3/4 - VALIDACIONES"
echo "──────────────────────────────────────────"

pkill -f "python3 app/app.py" 2>/dev/null || true
sleep 1
python3 "$ROOT/app/app.py" &
APP_PID=$!
sleep 3

if kill -0 $APP_PID 2>/dev/null; then
    print_ok "Servidor inició (PID: $APP_PID)"

    HEALTH=$(curl -s http://localhost:5000/health 2>/dev/null)
    if echo "$HEALTH" | grep -q "healthy"; then
        print_ok "Health check OK"
    else
        print_fail "Health check falló"
    fi

    CREATE=$(curl -s -X POST http://localhost:5000/tasks \
      -H "Content-Type: application/json" \
      -d '{"titulo":"Smoke Test"}' 2>/dev/null)
    if echo "$CREATE" | grep -q "Smoke Test"; then
        print_ok "POST /tasks funcional"
    else
        print_fail "POST /tasks falló"
    fi

    LIST=$(curl -s http://localhost:5000/tasks 2>/dev/null)
    if echo "$LIST" | grep -q "\["; then
        print_ok "GET /tasks funcional"
    else
        print_fail "GET /tasks falló"
    fi

    kill $APP_PID 2>/dev/null || true
else
    print_fail "Servidor no inició"
fi

echo ""
echo "──────────────────────────────────────────"
echo "  STAGE: 4/4 - REPORTE FINAL"
echo "──────────────────────────────────────────"

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
echo "  ┌──────────────────────────────────┐"
echo "  │  RESUMEN DEL PIPELINE            │"
echo "  │  Duración: ${DURATION}s                   │"
echo "  │  ✓ Verificaciones OK: $PASS             │"
echo "  │  ✗ Fallos:            $FAIL             │"
echo "  └──────────────────────────────────┘"

if [ $FAIL -gt 0 ]; then
    echo "  ❌ PIPELINE FALLÓ"
    exit 1
else
    echo "  ✅ PIPELINE EXITOSO - Listo para despliegue"
    exit 0
fi
