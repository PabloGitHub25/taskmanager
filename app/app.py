from flask import Flask, jsonify, request, abort, render_template_string
from datetime import datetime, timezone
import uuid, os

app = Flask(__name__)
tasks = {}
VALID_STATES = ["pendiente", "en_progreso", "completado"]

HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Task Manager</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg:       #0f1117;
    --surface:  #1a1d27;
    --card:     #212435;
    --border:   #2e3249;
    --accent:   #6c63ff;
    --accent2:  #a78bfa;
    --text:     #e8eaf6;
    --muted:    #7b82a8;
    --pend:     #f59e0b;
    --prog:     #3b82f6;
    --done:     #10b981;
    --danger:   #ef4444;
    --radius:   12px;
  }

  body {
    font-family: 'Inter', sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
  }

  /* ── HEADER ── */
  header {
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 0 32px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 64px;
    position: sticky; top: 0; z-index: 100;
  }
  .logo { display: flex; align-items: center; gap: 10px; }
  .logo-icon {
    width: 32px; height: 32px; border-radius: 8px;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    display: flex; align-items: center; justify-content: center;
    font-size: 16px;
  }
  .logo-text { font-weight: 700; font-size: 18px; }
  .logo-text span { color: var(--accent2); }
  .header-stats { display: flex; gap: 24px; }
  .stat { text-align: center; }
  .stat-n { font-size: 20px; font-weight: 700; color: var(--accent2); }
  .stat-l { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: .05em; }

  /* ── LAYOUT ── */
  main { max-width: 1100px; margin: 0 auto; padding: 40px 24px; }

  /* ── FORM CARD ── */
  .form-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 28px;
    margin-bottom: 36px;
  }
  .form-card h2 { font-size: 15px; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: .08em; margin-bottom: 20px; }
  .form-row { display: grid; grid-template-columns: 1fr 1fr 180px auto; gap: 12px; align-items: end; }
  label { display: block; font-size: 12px; color: var(--muted); margin-bottom: 6px; font-weight: 500; }
  input, select, textarea {
    width: 100%; padding: 10px 14px;
    background: var(--card); border: 1px solid var(--border);
    border-radius: 8px; color: var(--text); font-family: inherit; font-size: 14px;
    transition: border-color .2s;
    outline: none;
  }
  input:focus, select:focus, textarea:focus { border-color: var(--accent); }
  select option { background: var(--card); }

  /* ── BUTTONS ── */
  .btn {
    padding: 10px 20px; border-radius: 8px; border: none;
    font-family: inherit; font-size: 14px; font-weight: 600;
    cursor: pointer; transition: all .15s; white-space: nowrap;
  }
  .btn-primary { background: var(--accent); color: #fff; }
  .btn-primary:hover { background: #5a52e0; transform: translateY(-1px); }
  .btn-ghost { background: transparent; color: var(--muted); border: 1px solid var(--border); }
  .btn-ghost:hover { color: var(--text); border-color: var(--accent); }
  .btn-danger { background: transparent; color: var(--danger); border: 1px solid transparent; padding: 6px 10px; font-size: 13px; }
  .btn-danger:hover { background: rgba(239,68,68,.1); border-color: var(--danger); }
  .btn-edit { background: transparent; color: var(--accent2); border: 1px solid transparent; padding: 6px 10px; font-size: 13px; }
  .btn-edit:hover { background: rgba(167,139,250,.1); border-color: var(--accent2); }

  /* ── FILTERS ── */
  .filters { display: flex; gap: 10px; margin-bottom: 24px; flex-wrap: wrap; }
  .filter-btn {
    padding: 7px 18px; border-radius: 20px; border: 1px solid var(--border);
    background: transparent; color: var(--muted); font-family: inherit; font-size: 13px;
    cursor: pointer; transition: all .15s;
  }
  .filter-btn.active, .filter-btn:hover { background: var(--accent); color: #fff; border-color: var(--accent); }

  /* ── KANBAN COLUMNS ── */
  .kanban { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
  .column {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 20px;
    min-height: 200px;
  }
  .col-header {
    display: flex; align-items: center; gap: 10px;
    margin-bottom: 18px; padding-bottom: 14px;
    border-bottom: 1px solid var(--border);
  }
  .col-dot { width: 10px; height: 10px; border-radius: 50%; }
  .col-title { font-weight: 600; font-size: 14px; }
  .col-count {
    margin-left: auto; background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px; padding: 2px 10px;
    font-size: 12px; color: var(--muted);
  }

  /* ── TASK CARD ── */
  .task-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 14px;
    margin-bottom: 10px;
    transition: border-color .2s, transform .15s;
    animation: slideIn .2s ease;
  }
  .task-card:hover { border-color: var(--accent); transform: translateY(-2px); }
  @keyframes slideIn { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:none; } }
  .task-title { font-size: 14px; font-weight: 500; margin-bottom: 6px; word-break: break-word; }
  .task-desc { font-size: 12px; color: var(--muted); margin-bottom: 12px; line-height: 1.5; }
  .task-footer { display: flex; align-items: center; justify-content: space-between; }
  .task-date { font-size: 11px; color: var(--muted); }
  .task-actions { display: flex; gap: 4px; }

  /* ── STATUS BADGE ── */
  .badge {
    display: inline-block; padding: 3px 10px; border-radius: 12px;
    font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: .04em;
  }
  .badge-pendiente   { background: rgba(245,158,11,.15); color: var(--pend); }
  .badge-en_progreso { background: rgba(59,130,246,.15); color: var(--prog); }
  .badge-completado  { background: rgba(16,185,129,.15); color: var(--done); }

  /* ── MODAL ── */
  .modal-bg {
    display: none; position: fixed; inset: 0;
    background: rgba(0,0,0,.6); backdrop-filter: blur(4px);
    z-index: 200; align-items: center; justify-content: center;
  }
  .modal-bg.open { display: flex; }
  .modal {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 28px; width: 480px; max-width: 95vw;
    animation: popIn .2s ease;
  }
  @keyframes popIn { from { transform: scale(.95); opacity:0; } to { transform: scale(1); opacity:1; } }
  .modal h3 { font-size: 18px; margin-bottom: 20px; }
  .modal .form-group { margin-bottom: 16px; }
  .modal-footer { display: flex; justify-content: flex-end; gap: 10px; margin-top: 24px; }

  /* ── TOAST ── */
  .toast {
    position: fixed; bottom: 28px; right: 28px;
    background: var(--card); border: 1px solid var(--done);
    color: var(--done); padding: 12px 20px; border-radius: 10px;
    font-size: 14px; font-weight: 500; z-index: 300;
    transform: translateY(80px); opacity: 0; transition: all .3s;
  }
  .toast.show { transform: none; opacity: 1; }
  .toast.error { border-color: var(--danger); color: var(--danger); }

  /* ── EMPTY STATE ── */
  .empty {
    text-align: center; padding: 40px 20px;
    color: var(--muted); font-size: 13px;
  }
  .empty-icon { font-size: 32px; margin-bottom: 10px; }

  @media (max-width: 768px) {
    .kanban { grid-template-columns: 1fr; }
    .form-row { grid-template-columns: 1fr; }
    .header-stats { display: none; }
  }
</style>
</head>
<body>

<header>
  <div class="logo">
    <div class="logo-icon">✓</div>
    <div class="logo-text">Task<span>Manager</span></div>
  </div>
  <div class="header-stats">
    <div class="stat"><div class="stat-n" id="cnt-total">0</div><div class="stat-l">Total</div></div>
    <div class="stat"><div class="stat-n" id="cnt-pend" style="color:var(--pend)">0</div><div class="stat-l">Pendiente</div></div>
    <div class="stat"><div class="stat-n" id="cnt-prog" style="color:var(--prog)">0</div><div class="stat-l">En progreso</div></div>
    <div class="stat"><div class="stat-n" id="cnt-done" style="color:var(--done)">0</div><div class="stat-l">Completado</div></div>
  </div>
</header>

<main>
  <!-- Formulario nueva tarea -->
  <div class="form-card">
    <h2>Nueva Tarea</h2>
    <div class="form-row">
      <div>
        <label>Título *</label>
        <input id="new-title" type="text" placeholder="¿Qué hay que hacer?" />
      </div>
      <div>
        <label>Descripción</label>
        <input id="new-desc" type="text" placeholder="Detalles opcionales..." />
      </div>
      <div>
        <label>Estado</label>
        <select id="new-estado">
          <option value="pendiente">Pendiente</option>
          <option value="en_progreso">En progreso</option>
          <option value="completado">Completado</option>
        </select>
      </div>
      <div>
        <label>&nbsp;</label>
        <button class="btn btn-primary" onclick="createTask()">+ Agregar</button>
      </div>
    </div>
  </div>

  <!-- Vista Kanban -->
  <div class="kanban">
    <div class="column">
      <div class="col-header">
        <div class="col-dot" style="background:var(--pend)"></div>
        <span class="col-title">Pendiente</span>
        <span class="col-count" id="col-cnt-pendiente">0</span>
      </div>
      <div id="col-pendiente"></div>
    </div>
    <div class="column">
      <div class="col-header">
        <div class="col-dot" style="background:var(--prog)"></div>
        <span class="col-title">En progreso</span>
        <span class="col-count" id="col-cnt-en_progreso">0</span>
      </div>
      <div id="col-en_progreso"></div>
    </div>
    <div class="column">
      <div class="col-header">
        <div class="col-dot" style="background:var(--done)"></div>
        <span class="col-title">Completado</span>
        <span class="col-count" id="col-cnt-completado">0</span>
      </div>
      <div id="col-completado"></div>
    </div>
  </div>
</main>

<!-- Modal edición -->
<div class="modal-bg" id="edit-modal">
  <div class="modal">
    <h3>✏️ Editar Tarea</h3>
    <input type="hidden" id="edit-id" />
    <div class="form-group">
      <label>Título</label>
      <input id="edit-title" type="text" />
    </div>
    <div class="form-group">
      <label>Descripción</label>
      <input id="edit-desc" type="text" />
    </div>
    <div class="form-group">
      <label>Estado</label>
      <select id="edit-estado">
        <option value="pendiente">Pendiente</option>
        <option value="en_progreso">En progreso</option>
        <option value="completado">Completado</option>
      </select>
    </div>
    <div class="modal-footer">
      <button class="btn btn-ghost" onclick="closeModal()">Cancelar</button>
      <button class="btn btn-primary" onclick="saveEdit()">Guardar cambios</button>
    </div>
  </div>
</div>

<div class="toast" id="toast"></div>

<script>
  async function api(method, path, body) {
    const r = await fetch(path, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: body ? JSON.stringify(body) : undefined
    });
    return r.json();
  }

  async function loadTasks() {
    const tasks = await api('GET', '/tasks');
    const cols = { pendiente: [], en_progreso: [], completado: [] };
    tasks.forEach(t => { if (cols[t.estado]) cols[t.estado].push(t); });

    ['pendiente','en_progreso','completado'].forEach(s => {
      const el = document.getElementById('col-' + s);
      const cnt = document.getElementById('col-cnt-' + s);
      cnt.textContent = cols[s].length;
      if (!cols[s].length) {
        el.innerHTML = '<div class="empty"><div class="empty-icon">📭</div>Sin tareas aquí</div>';
        return;
      }
      el.innerHTML = cols[s].map(t => `
        <div class="task-card">
          <div class="task-title">${esc(t.titulo)}</div>
          ${t.descripcion ? `<div class="task-desc">${esc(t.descripcion)}</div>` : ''}
          <div class="task-footer">
            <span class="task-date">${new Date(t.creado_en).toLocaleDateString('es-EC')}</span>
            <div class="task-actions">
              <button class="btn btn-edit" onclick="openEdit('${t.id}','${esc(t.titulo)}','${esc(t.descripcion||'')}','${t.estado}')">✏️</button>
              <button class="btn btn-danger" onclick="deleteTask('${t.id}')">🗑️</button>
            </div>
          </div>
        </div>`).join('');
    });

    // header stats
    document.getElementById('cnt-total').textContent = tasks.length;
    document.getElementById('cnt-pend').textContent  = cols.pendiente.length;
    document.getElementById('cnt-prog').textContent  = cols.en_progreso.length;
    document.getElementById('cnt-done').textContent  = cols.completado.length;
  }

  async function createTask() {
    const titulo = document.getElementById('new-title').value.trim();
    if (!titulo) { toast('El título es obligatorio', true); return; }
    await api('POST', '/tasks', {
      titulo,
      descripcion: document.getElementById('new-desc').value,
      estado: document.getElementById('new-estado').value
    });
    document.getElementById('new-title').value = '';
    document.getElementById('new-desc').value  = '';
    await loadTasks();
    toast('Tarea creada ✓');
  }

  async function deleteTask(id) {
    if (!confirm('¿Eliminar esta tarea?')) return;
    await api('DELETE', '/tasks/' + id);
    await loadTasks();
    toast('Tarea eliminada');
  }

  function openEdit(id, titulo, desc, estado) {
    document.getElementById('edit-id').value     = id;
    document.getElementById('edit-title').value  = titulo;
    document.getElementById('edit-desc').value   = desc;
    document.getElementById('edit-estado').value = estado;
    document.getElementById('edit-modal').classList.add('open');
  }

  function closeModal() {
    document.getElementById('edit-modal').classList.remove('open');
  }

  async function saveEdit() {
    const id = document.getElementById('edit-id').value;
    await api('PUT', '/tasks/' + id, {
      titulo:      document.getElementById('edit-title').value,
      descripcion: document.getElementById('edit-desc').value,
      estado:      document.getElementById('edit-estado').value
    });
    closeModal();
    await loadTasks();
    toast('Tarea actualizada ✓');
  }

  function toast(msg, err=false) {
    const el = document.getElementById('toast');
    el.textContent = msg;
    el.className = 'toast show' + (err ? ' error' : '');
    setTimeout(() => el.className = 'toast', 3000);
  }

  function esc(s) {
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
  }

  // Enter para crear
  document.getElementById('new-title').addEventListener('keydown', e => { if(e.key==='Enter') createTask(); });
  // Cerrar modal con Escape
  document.addEventListener('keydown', e => { if(e.key==='Escape') closeModal(); });

  loadTasks();
</script>
</body>
</html>
"""

def task_to_dict(t):
    return { k: t[k] for k in ["id","titulo","descripcion","estado","creado_en"] }

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/health")
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()})

@app.route("/tasks", methods=["GET"])
def get_tasks():
    estado = request.args.get("estado")
    result = list(tasks.values())
    if estado:
        result = [t for t in result if t["estado"] == estado]
    return jsonify(result)

@app.route("/tasks/<task_id>", methods=["GET"])
def get_task(task_id):
    task = tasks.get(task_id)
    if not task: abort(404, description="Tarea no encontrada")
    return jsonify(task_to_dict(task))

@app.route("/tasks", methods=["POST"])
def create_task():
    data = request.get_json(silent=True)
    if not data or not data.get("titulo"):
        abort(400, description="El campo 'titulo' es requerido")
    estado = data.get("estado", "pendiente")
    if estado not in VALID_STATES:
        abort(400, description=f"Estado inválido. Use: {VALID_STATES}")
    task = {
        "id": str(uuid.uuid4()),
        "titulo": data["titulo"],
        "descripcion": data.get("descripcion", ""),
        "estado": estado,
        "creado_en": datetime.now(timezone.utc).isoformat()
    }
    tasks[task["id"]] = task
    return jsonify(task_to_dict(task)), 201

@app.route("/tasks/<task_id>", methods=["PUT"])
def update_task(task_id):
    task = tasks.get(task_id)
    if not task: abort(404, description="Tarea no encontrada")
    data = request.get_json(silent=True)
    if not data: abort(400, description="Body JSON requerido")
    if "titulo"      in data: task["titulo"] = data["titulo"]
    if "descripcion" in data: task["descripcion"] = data["descripcion"]
    if "estado"      in data:
        if data["estado"] not in VALID_STATES:
            abort(400, description=f"Estado inválido.")
        task["estado"] = data["estado"]
    return jsonify(task_to_dict(task))

@app.route("/tasks/<task_id>", methods=["DELETE"])
def delete_task(task_id):
    task = tasks.pop(task_id, None)
    if not task: abort(404, description="Tarea no encontrada")
    return jsonify({"mensaje": "Tarea eliminada", "id": task_id})

@app.errorhandler(400)
def bad_request(e): return jsonify({"error": str(e.description)}), 400
@app.errorhandler(404)
def not_found(e):   return jsonify({"error": str(e.description)}), 404

if __name__ == "__main__":
    port  = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("ENV", "dev") == "dev"
    app.run(host="0.0.0.0", port=port, debug=debug)
