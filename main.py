# app.py
from flask import Flask, request, jsonify, render_template_string
import time

app = Flask(__name__)
data_buffer = []

# HTML plantilla (usa render_template_string para no necesitar archivos)
dashboard_html = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Dashboard Ambiental - Gateway ESP32</title>

  <!-- Chart.js -->
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

  <style>
    :root{
      --bg: #eef5ee;
      --card: #ffffff;
      --accent: #2e7d32;
      --muted: #6b7280;
    }
    html,body{height:100%; margin:0; font-family:Inter, Arial, sans-serif; background:var(--bg);}
    .container{max-width:1200px; margin:18px auto; padding:10px;}
    header{display:flex; align-items:center; justify-content:space-between; gap:12px; margin-bottom:14px;}
    h1{margin:0; color:var(--accent); font-size:20px;}
    .controls{display:flex; gap:8px; align-items:center;}
    .btn { background:#c62828; color:white; padding:8px 12px; border-radius:8px; border:none; cursor:pointer; }
    .btn.secondary{background:#2e7d32;}
    .card{background:var(--card); border-radius:12px; box-shadow:0 6px 18px rgba(16,24,40,0.08); padding:18px; margin-bottom:22px;}
    .chart-wrapper{position:relative; width:100%; height:360px;}
    .chart-title{font-size:20px; font-weight:700; text-align:center; margin-bottom:10px;}
    .alert-overlay{
      position:absolute;
      top:50%; left:50%; transform:translate(-50%,-50%);
      background:rgba(255,0,0,0.90);
      color:white; padding:12px 20px; border-radius:10px; font-weight:700;
      display:none; z-index:20; pointer-events:none; box-shadow:0 6px 20px rgba(0,0,0,0.25);
    }
    .settings{display:flex; gap:10px; flex-wrap:wrap; align-items:center; justify-content:center; margin-top:8px;}
    .settings label{font-size:13px; color:var(--muted);}
    input[type="number"]{width:84px; padding:6px 8px; border-radius:8px; border:1px solid #e5e7eb;}
    footer{color:var(--muted); text-align:center; margin-top:8px; font-size:13px;}
    @media (max-width:640px){
      .chart-wrapper{height:300px;}
      h1{font-size:18px;}
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>📡 Dashboard Ambiental - Gateway ESP32</h1>
      <div class="controls">
        <button class="btn" onclick="clearData()">Borrar datos</button>
        <button class="btn secondary" onclick="fetchNow()">Actualizar</button>
      </div>
    </header>

    <!-- TEMPERATURA -->
    <div class="card">
      <div class="chart-title">Temperatura <small style="color:var(--muted)"> (°C)</small></div>
      <div class="chart-wrapper">
        <div id="alertTemp" class="alert-overlay">⚠ Temperatura crítica</div>
        <canvas id="tempChart"></canvas>
      </div>
      <div class="settings">
        <label>Umbral bajo <input id="tempLow" type="number" value="10"></label>
        <label>Umbral alto <input id="tempHigh" type="number" value="30"></label>
      </div>
    </div>

    <!-- HUMEDAD -->
    <div class="card">
      <div class="chart-title">Humedad <small style="color:var(--muted)"> (%)</small></div>
      <div class="chart-wrapper">
        <div id="alertHum" class="alert-overlay">⚠ Humedad crítica</div>
        <canvas id="humChart"></canvas>
      </div>
      <div class="settings">
        <label>Umbral bajo <input id="humLow" type="number" value="20"></label>
        <label>Umbral alto <input id="humHigh" type="number" value="80"></label>
      </div>
    </div>

    <!-- GAS -->
    <div class="card">
      <div class="chart-title">Gas <small style="color:var(--muted)"> (ppm)</small></div>
      <div class="chart-wrapper">
        <div id="alertGas" class="alert-overlay">⚠ Gas crítico</div>
        <canvas id="gasChart"></canvas>
      </div>
      <div class="settings">
        <label>Umbral bajo <input id="gasLow" type="number" value="50"></label>
        <label>Umbral alto <input id="gasHigh" type="number" value="300"></label>
      </div>
    </div>

    <footer>Gráficas actualizan automáticamente cada 3 segundos. </footer>
  </div>

<script>
/* ---------- Utilidad fetch ---------- */
async function fetchDatos(){
  try{
    const res = await fetch('/datos');
    if(!res.ok) return [];
    return await res.json();
  }catch(e){
    console.error('fetch error', e);
    return [];
  }
}

/* ---------- Alert checker ---------- */
function checkAlert(values, low, high){
  if(!Array.isArray(values) || values.length===0) return false;
  const last = values[values.length-1];
  if(last === null || last === undefined) return false;
  return (last > high) || (last < low);
}

/* ---------- Chart configuration factory ---------- */
function makeConfig(label){
  return {
    type: 'line',
    data: {
      labels: [],
      datasets:[{
        label: label,
        data: [],
        fill: false,
        tension: 0.25,
        pointRadius: 5,
        pointHoverRadius: 7,
        borderWidth: 2,
        // borderColor left for Chart.js default palette
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: true, position: 'top' },
        tooltip: { mode: 'index', intersect: false }
      },
      scales: {
        x: {
          grid: { display: true, color: 'rgba(0,0,0,0.04)' },
          ticks: { maxRotation: 45, minRotation: 30, autoSkip: true, maxTicksLimit: 10 }
        },
        y: {
          grid: { display: true, color: 'rgba(0,0,0,0.04)' }
        }
      },
      elements: {
        point: { backgroundColor: 'rgba(66,153,225,1)' }
      }
    }
  };
}

/* ---------- Crear charts ---------- */
const tempCtx = document.getElementById('tempChart').getContext('2d');
const humCtx  = document.getElementById('humChart').getContext('2d');
const gasCtx  = document.getElementById('gasChart').getContext('2d');

const tempChart = new Chart(tempCtx, makeConfig('°C'));
const humChart  = new Chart(humCtx,  makeConfig('%'));
const gasChart  = new Chart(gasCtx,  makeConfig('ppm'));

/* ---------- Actualización principal ---------- */
async function actualizarGraficos(){
  const datos = await fetchDatos();

  // Si no hay datos, limpiar charts
  if(!datos || datos.length===0){
    tempChart.data.labels = [];
    tempChart.data.datasets[0].data = [];
    humChart.data.labels = [];
    humChart.data.datasets[0].data = [];
    gasChart.data.labels = [];
    gasChart.data.datasets[0].data = [];
    tempChart.update(); humChart.update(); gasChart.update();
    return;
  }

  const labels = datos.map(d => {
    const dt = new Date(d.timestamp * 1000);
    return dt.toLocaleTimeString();
  });

  const temp = datos.map(d => d.temperatura ?? null);
  const hum  = datos.map(d => d.humedad ?? null);
  const gas  = datos.map(d => d.gas ?? null);

  // Asignar datos
  tempChart.data.labels = labels;
  tempChart.data.datasets[0].data = temp;
  humChart.data.labels = labels;
  humChart.data.datasets[0].data = hum;
  gasChart.data.labels = labels;
  gasChart.data.datasets[0].data = gas;

  // Ajustar límites Y dinámicamente según datos (opcional)
  function autoscale(chart, arr){
    const valid = arr.filter(v => typeof v === 'number');
    if(valid.length===0) return;
    const min = Math.min(...valid);
    const max = Math.max(...valid);
    const pad = Math.round((max - min) * 0.12) || 10;
    chart.options.scales.y.min = Math.max(0, min - pad);
    chart.options.scales.y.max = max + pad;
  }
  autoscale(tempChart, temp);
  autoscale(humChart, hum);
  autoscale(gasChart, gas);

  tempChart.update();
  humChart.update();
  gasChart.update();

  // Leer umbrales de inputs
  const tLow = Number(document.getElementById('tempLow').value);
  const tHigh = Number(document.getElementById('tempHigh').value);
  const hLow = Number(document.getElementById('humLow').value);
  const hHigh = Number(document.getElementById('humHigh').value);
  const gLow = Number(document.getElementById('gasLow').value);
  const gHigh = Number(document.getElementById('gasHigh').value);

  // Mostrar/ocultar overlays
  document.getElementById('alertTemp').style.display = checkAlert(temp, tLow, tHigh) ? 'block' : 'none';
  document.getElementById('alertHum').style.display  = checkAlert(hum, hLow, hHigh) ? 'block' : 'none';
  document.getElementById('alertGas').style.display  = checkAlert(gas, gLow, gHigh) ? 'block' : 'none';
}

/* ---------- Funciones útiles ---------- */
async function clearData(){
  await fetch('/clear', { method:'POST' });
  await actualizarGraficos();
  alert('Datos borrados.');
}
async function fetchNow(){ await actualizarGraficos(); }

/* ---------- Auto update cada 3s ---------- */
actualizarGraficos();
setInterval(actualizarGraficos, 3000);
</script>
</body>
</html>
"""

# ----------------- Rutas Flask -----------------
@app.route("/")
def home():
    return render_template_string(dashboard_html)

@app.route("/data", methods=["POST"])
def receive_data():
    content = request.get_json()
    if not content:
        return jsonify({"status":"error","reason":"payload vacío"}), 400
    content["timestamp"] = time.time()
    data_buffer.append(content)
    if len(data_buffer) > 300:
        data_buffer.pop(0)
    return jsonify({"status":"ok"})

@app.route("/datos", methods=["GET"])
def send_data():
    # Devolver lista completa (puedes cambiar para devolver sólo N últimos)
    return jsonify(data_buffer)

@app.route("/clear", methods=["POST"])
def clear_data():
    data_buffer.clear()
    return jsonify({"status":"cleared"})

# ----------------- Ejecutar -----------------
if __name__ == "__main__":
    # host 0.0.0.0 para acceso desde otros dispositivos en la misma red (ESP32/phone)
    app.run(host="0.0.0.0", port=10000, debug=True)
