# main.py
from flask import Flask, request, jsonify, render_template_string
import time, json, os

app = Flask(__name__)

DATA_FILE = "data.json"

# Cargar persistencia
if os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE, "r") as f:
            data_buffer = json.load(f)
    except:
        data_buffer = []
else:
    data_buffer = []

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data_buffer, f)

# --- Dashboard HTML (industrial style) ---
dashboard_html = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Dashboard Ambiental - Gateway ESP32</title>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    :root{
      --bg:#0f1720;
      --panel:#0b1220;
      --accent:#00b894;
      --warn:#ffbe52;
      --danger:#ff5252;
      --muted:#98a8b9;
      --card:#0f1a24;
    }
    body{margin:0;font-family:Inter,Arial;background:linear-gradient(180deg,#071227 0%, #0a2230 100%);color:#e6eef6}
    header{padding:22px;text-align:center}
    h1{margin:0;color:var(--accent);font-weight:700}
    .container{max-width:1200px;margin:18px auto;padding:12px}
    .top-row{display:flex;gap:12px;align-items:center;justify-content:space-between;flex-wrap:wrap}
    .status-card{background:rgba(255,255,255,0.04);padding:14px;border-radius:10px;min-width:220px;box-shadow:0 6px 18px rgba(0,0,0,0.6);}
    .cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px;margin-top:18px}
    .node-card{background:linear-gradient(180deg,rgba(255,255,255,0.02),rgba(255,255,255,0.01));padding:16px;border-radius:12px;position:relative;box-shadow:0 8px 24px rgba(0,0,0,0.6)}
    .node-title{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
    .node-id{font-weight:700}
    .big-metric{font-size:28px;font-weight:700;margin-top:6px}
    .small{color:var(--muted);font-size:13px}
    .badge{padding:6px 10px;border-radius:8px;font-weight:700}
    .green{background:rgba(0,184,148,0.12);color:var(--accent);border:1px solid rgba(0,184,148,0.18)}
    .yellow{background:rgba(255,190,82,0.08);color:var(--warn);border:1px solid rgba(255,190,82,0.12)}
    .red{background:rgba(255,82,82,0.08);color:var(--danger);border:1px solid rgba(255,82,82,0.12)}
    /* blinking */
    .blink {animation:blink 1s step-start 0s infinite}
    @keyframes blink {50% {opacity:0.04}}
    .mini-chart {height:70px}
    .controls{display:flex;gap:8px;align-items:center}
    button{background:#1f6f8b;border:none;color:white;padding:10px 14px;border-radius:8px;cursor:pointer}
    button.danger{background:#b83232}
    footer{color:var(--muted);text-align:center;padding:22px 0 60px}
    /* alert overlay */
    .alert{position:absolute;left:8px;top:8px;padding:6px 10px;border-radius:8px;font-weight:700}
    .alert-crit{background:var(--danger);color:#fff}
    /* layout for large charts */
    .big-charts{display:grid;grid-template-columns:1fr;gap:14px;margin-top:18px}
    @media(min-width:900px){ .big-charts{grid-template-columns:1fr 1fr} }
  </style>
</head>
<body>
  <header>
    <h1>📡 Dashboard Ambiental - Gateway ESP32</h1>
    <div style="color:var(--muted);margin-top:8px">Monitoreo en tiempo real — Nodos: 2</div>
  </header>

  <div class="container">
    <div class="top-row">
      <div class="status-card">
        <div style="font-size:13px;color:var(--muted)">Última actualización</div>
        <div style="font-weight:800;margin-top:6px" id="lastUpdate">—</div>
      </div>

      <div style="display:flex;gap:8px">
        <button onclick="fetchAndRender()">Refrescar ahora</button>
        <button class="danger" onclick="limpiar()">Borrar datos</button>
      </div>
    </div>

    <div class="cards" id="nodesContainer">
      <!-- tarjetas de nodos se inyectan aquí -->
    </div>

    <div class="big-charts">
      <div style="background:#071826;padding:14px;border-radius:12px">
        <h3 style="color:#bfe8d3;text-align:center">Temperatura (historial)</h3>
        <canvas id="chartTemp" height="220"></canvas>
      </div>
      <div style="background:#071826;padding:14px;border-radius:12px">
        <h3 style="color:#bfe8d3;text-align:center">Humedad (historial)</h3>
        <canvas id="chartHum" height="220"></canvas>
      </div>
    </div>

  </div>

<script>
// CONFIG
const API_NODES = '/nodes';
const API_DATOS = '/datos';
const CRITICAL = { temperatura: 35.0, humedad: 85.0, gas: 400.0 };
const NODE_TIMEOUT_OK = 12;   // segundos -> conectado
const NODE_TIMEOUT_RETRY = 30; // segundos -> reconectando
// global charts
let globalTempChart, globalHumChart;

// helpers
function fmtTime(ts) {
  const d = new Date(ts * 1000);
  return d.toLocaleString();
}
function timeNow(){ return Math.floor(Date.now()/1000); }

// fetch nodes info
async function fetchNodes(){
  const r = await fetch(API_NODES);
  return await r.json();
}
async function fetchDatos(){
  const r = await fetch(API_DATOS);
  return await r.json();
}

function statusClass(status){
  if(status==='connected') return 'green';
  if(status==='reconnecting') return 'yellow blink';
  return 'red blink';
}

// create node card HTML
function makeNodeCard(node){
  // node: { id, last, temperatura, humedad, gas, status, history: [...] }
  const id = node.id;
  const status = node.status;
  const cls = statusClass(status);
  const critTemp = node.temperatura >= CRITICAL.temperatura;
  const critHum  = node.humedad >= CRITICAL.humedad;
  const critGas  = node.gas >= CRITICAL.gas;
  const crit = critTemp || critHum || critGas;
  const badge = `<div class="badge ${cls}">${status.toUpperCase()}</div>`;

  const html = `
    <div class="node-card" id="card-${id}">
      ${crit ? `<div class="alert alert-crit">CRÍTICO</div>` : ''}
      <div class="node-title">
        <div>
          <div class="node-id">${id}</div>
          <div class="small">Último: ${fmtTime(node.last)}</div>
        </div>
        <div style="text-align:right">${badge}</div>
      </div>

      <div style="display:flex;gap:12px;align-items:center">
        <div style="flex:0 0 160px">
          <div class="small">Temperatura</div>
          <div class="big-metric">${node.temperatura.toFixed(2)} °C</div>
          <div class="small">Humedad: ${node.humedad.toFixed(2)} %</div>
          <div class="small">Gas: ${node.gas.toFixed(0)} ppm</div>
        </div>
        <div style="flex:1">
          <canvas id="mini-${id}" class="mini-chart"></canvas>
        </div>
      </div>
    </div>
  `;
  return html;
}

// render all nodes
async function renderNodes(){
  const payload = await fetchNodes();
  const container = document.getElementById('nodesContainer');
  container.innerHTML = '';
  // payload is object keyed by node id
  for(const id in payload){
    const node = payload[id];
    container.insertAdjacentHTML('beforeend', makeNodeCard(node));
    // mini chart
    const ctx = document.getElementById('mini-'+id).getContext('2d');
    const labels = node.history.map(p => new Date(p.timestamp*1000).toLocaleTimeString());
    const dataT = node.history.map(p => p.temperatura);
    new Chart(ctx, { type:'line', data:{labels, datasets:[{label:'°C', data:dataT, borderWidth:1, pointRadius:2}] }, options:{responsive:true, maintainAspectRatio:false, plugins:{legend:{display:false}}}});
  }
}

// global charts
async function renderGlobalCharts(){
  const datos = await fetchDatos();
  const labels = datos.map(d => new Date(d.timestamp*1000).toLocaleTimeString());
  const temp = datos.map(d => d.temperatura);
  const hum  = datos.map(d => d.humedad);

  if(!globalTempChart){
    globalTempChart = new Chart(document.getElementById('chartTemp').getContext('2d'), {
      type:'line',
      data:{labels, datasets:[{label:'Temperatura °C', data:temp, borderColor:'#1ec1a6', backgroundColor:'rgba(30,193,166,0.06)', tension:0.3}]},
      options:{plugins:{legend:{display:false}}}
    });
  } else {
    globalTempChart.data.labels = labels;
    globalTempChart.data.datasets[0].data = temp;
    globalTempChart.update();
  }

  if(!globalHumChart){
    globalHumChart = new Chart(document.getElementById('chartHum').getContext('2d'), {
      type:'line',
      data:{labels, datasets:[{label:'Humedad %', data:hum, borderColor:'#58a6ff', backgroundColor:'rgba(88,166,255,0.04)', tension:0.3}]},
      options:{plugins:{legend:{display:false}}}
    });
  } else {
    globalHumChart.data.labels = labels;
    globalHumChart.data.datasets[0].data = hum;
    globalHumChart.update();
  }
}

// nodes endpoint returns object { id: { ... } }
async function fetchAndRender(){
  try{
    const nodes = await fetchNodes();
    document.getElementById('lastUpdate').innerText = new Date().toLocaleString();
    await renderNodes();
    await renderGlobalCharts();
  } catch(e){
    console.error(e);
  }
}

function limpiar(){
  fetch('/clear', {method:'POST'}).then(()=>{ alert('Datos borrados'); fetchAndRender(); });
}

setInterval(fetchAndRender, 3000);
window.onload = fetchAndRender;
</script>

</body>
</html>
"""

# ------------------------------
# RUTAS
# ------------------------------

@app.route("/")
def home():
    return render_template_string(dashboard_html)

# Recibir datos (lo hace el Gateway)
@app.route("/data", methods=["POST"])
def receive_data():
    content = request.get_json()
    if not content:
        return jsonify({"status":"error","reason":"payload vacío"}), 400

    # aseguramos que tenga id
    if "id" not in content:
        return jsonify({"status":"error","reason":"falta id"}), 400

    content["timestamp"] = time.time()
    data_buffer.append(content)
    if len(data_buffer) > 1000:
        data_buffer.pop(0)
    save_data()
    return jsonify({"status":"ok"}), 200

# devolver historial
@app.route("/datos", methods=["GET"])
def send_data():
    return jsonify(data_buffer)

# limpiar
@app.route("/clear", methods=["POST"])
def clear_data():
    data_buffer.clear()
    save_data()
    return jsonify({"status":"cleared"})

# endpoint: estado por nodo
@app.route("/nodes", methods=["GET"])
def nodes_info():
    # Armar diccionario con últimos valores por id
    latest = {}
    for entry in data_buffer:
        nid = entry.get("id")
        if not nid: continue
        latest[nid] = entry

    # construir respuesta con estado y mini-history (últimos 30)
    response = {}
    now = time.time()
    for nid, val in latest.items():
        # hist
        history = [e for e in data_buffer if e.get("id")==nid]
        history = history[-40:]  # últimos 40
        last_ts = val.get("timestamp", now)
        age = now - last_ts
        if age <=  NODE_TIMEOUT_OK:
            status = "connected"
        elif age <= NODE_TIMEOUT_RETRY:
            status = "reconnecting"
        else:
            status = "disconnected"
        response[nid] = {
            "id": nid,
            "last": last_ts,
            "temperatura": float(val.get("temperatura",0)),
            "humedad": float(val.get("humedad",0)),
            "gas": float(val.get("gas",0)),
            "status": status,
            "history": history
        }
    return jsonify(response)

# ------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
