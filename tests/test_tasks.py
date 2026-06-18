"""
Suite de pruebas - Task Manager
Tipos: Funcionales, Negativos, Borde
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

import pytest
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        # Limpiar tareas entre tests
        from app import tasks
        tasks.clear()
        yield c


# ─── PRUEBAS FUNCIONALES ──────────────────────────────────────────────────────

class TestFuncionales:
    def test_health_check(self, client):
        """F-01: El sistema responde al health check"""
        r = client.get("/health")
        assert r.status_code == 200
        data = r.get_json()
        assert data["status"] == "healthy"

    def test_crear_tarea_basica(self, client):
        """F-02: Crear una tarea con datos mínimos"""
        r = client.post("/tasks", json={"titulo": "Revisar código"})
        assert r.status_code == 201
        data = r.get_json()
        assert data["titulo"] == "Revisar código"
        assert data["estado"] == "pendiente"
        assert "id" in data

    def test_crear_tarea_con_estado(self, client):
        """F-03: Crear tarea con estado específico"""
        r = client.post("/tasks", json={"titulo": "Deploy", "estado": "en_progreso"})
        assert r.status_code == 201
        assert r.get_json()["estado"] == "en_progreso"

    def test_listar_tareas_vacias(self, client):
        """F-04: Listar cuando no hay tareas"""
        r = client.get("/tasks")
        assert r.status_code == 200
        assert r.get_json() == []

    def test_listar_tareas_con_datos(self, client):
        """F-05: Listar tareas creadas"""
        client.post("/tasks", json={"titulo": "Tarea A"})
        client.post("/tasks", json={"titulo": "Tarea B"})
        r = client.get("/tasks")
        assert r.status_code == 200
        assert len(r.get_json()) == 2

    def test_obtener_tarea_por_id(self, client):
        """F-06: Obtener una tarea por su ID"""
        r_create = client.post("/tasks", json={"titulo": "Mi Tarea"})
        task_id = r_create.get_json()["id"]
        r = client.get(f"/tasks/{task_id}")
        assert r.status_code == 200
        assert r.get_json()["id"] == task_id

    def test_actualizar_titulo(self, client):
        """F-07: Actualizar título de una tarea"""
        task_id = client.post("/tasks", json={"titulo": "Original"}).get_json()["id"]
        r = client.put(f"/tasks/{task_id}", json={"titulo": "Actualizado"})
        assert r.status_code == 200
        assert r.get_json()["titulo"] == "Actualizado"

    def test_cambiar_estado(self, client):
        """F-08: Cambiar estado de pendiente a completado"""
        task_id = client.post("/tasks", json={"titulo": "T1"}).get_json()["id"]
        r = client.put(f"/tasks/{task_id}", json={"estado": "completado"})
        assert r.status_code == 200
        assert r.get_json()["estado"] == "completado"

    def test_eliminar_tarea(self, client):
        """F-09: Eliminar una tarea existente"""
        task_id = client.post("/tasks", json={"titulo": "Borrar"}).get_json()["id"]
        r = client.delete(f"/tasks/{task_id}")
        assert r.status_code == 200
        # Verificar que ya no existe
        r2 = client.get(f"/tasks/{task_id}")
        assert r2.status_code == 404

    def test_filtrar_por_estado(self, client):
        """F-10: Filtrar tareas por estado"""
        client.post("/tasks", json={"titulo": "T1", "estado": "pendiente"})
        client.post("/tasks", json={"titulo": "T2", "estado": "completado"})
        r = client.get("/tasks?estado=pendiente")
        tareas = r.get_json()
        assert all(t["estado"] == "pendiente" for t in tareas)
        assert len(tareas) == 1


# ─── PRUEBAS NEGATIVAS ────────────────────────────────────────────────────────

class TestNegativos:
    def test_crear_sin_titulo(self, client):
        """N-01: Crear tarea sin título debe fallar"""
        r = client.post("/tasks", json={"descripcion": "sin titulo"})
        assert r.status_code == 400

    def test_crear_con_body_vacio(self, client):
        """N-02: Crear tarea con body vacío debe fallar"""
        r = client.post("/tasks", json={})
        assert r.status_code == 400

    def test_crear_con_estado_invalido(self, client):
        """N-03: Estado inválido debe ser rechazado"""
        r = client.post("/tasks", json={"titulo": "T", "estado": "invalido"})
        assert r.status_code == 400

    def test_obtener_tarea_inexistente(self, client):
        """N-04: Obtener tarea con ID que no existe"""
        r = client.get("/tasks/id-que-no-existe")
        assert r.status_code == 404

    def test_actualizar_tarea_inexistente(self, client):
        """N-05: Actualizar tarea que no existe"""
        r = client.put("/tasks/fake-id", json={"titulo": "X"})
        assert r.status_code == 404

    def test_eliminar_tarea_inexistente(self, client):
        """N-06: Eliminar tarea que no existe"""
        r = client.delete("/tasks/fake-id")
        assert r.status_code == 404

    def test_actualizar_con_estado_invalido(self, client):
        """N-07: Actualizar estado con valor inválido"""
        task_id = client.post("/tasks", json={"titulo": "T"}).get_json()["id"]
        r = client.put(f"/tasks/{task_id}", json={"estado": "xyz"})
        assert r.status_code == 400

    def test_crear_sin_content_type_json(self, client):
        """N-08: POST sin Content-Type application/json"""
        r = client.post("/tasks", data="titulo=T", content_type="text/plain")
        assert r.status_code == 400


# ─── PRUEBAS DE BORDE ─────────────────────────────────────────────────────────

class TestBorde:
    def test_titulo_muy_largo(self, client):
        """B-01: Crear tarea con título de 500 caracteres"""
        titulo = "A" * 500
        r = client.post("/tasks", json={"titulo": titulo})
        assert r.status_code == 201
        assert len(r.get_json()["titulo"]) == 500

    def test_titulo_un_caracter(self, client):
        """B-02: Título de un solo carácter"""
        r = client.post("/tasks", json={"titulo": "X"})
        assert r.status_code == 201

    def test_crear_muchas_tareas(self, client):
        """B-03: Crear 50 tareas en secuencia"""
        for i in range(50):
            client.post("/tasks", json={"titulo": f"Tarea {i}"})
        r = client.get("/tasks")
        assert len(r.get_json()) == 50

    def test_descripcion_vacia(self, client):
        """B-04: Tarea con descripción vacía"""
        r = client.post("/tasks", json={"titulo": "T", "descripcion": ""})
        assert r.status_code == 201

    def test_descripcion_con_caracteres_especiales(self, client):
        """B-05: Descripción con caracteres especiales"""
        r = client.post("/tasks", json={"titulo": "T", "descripcion": "áéíóú <script> & \"quotes\""})
        assert r.status_code == 201

    def test_filtro_estado_sin_resultados(self, client):
        """B-06: Filtro por estado que no tiene tareas"""
        client.post("/tasks", json={"titulo": "T", "estado": "pendiente"})
        r = client.get("/tasks?estado=completado")
        assert r.status_code == 200
        assert r.get_json() == []

    def test_todos_los_estados_validos(self, client):
        """B-07: Crear tarea con cada uno de los estados válidos"""
        for estado in ["pendiente", "en_progreso", "completado"]:
            r = client.post("/tasks", json={"titulo": f"T-{estado}", "estado": estado})
            assert r.status_code == 201
            assert r.get_json()["estado"] == estado
