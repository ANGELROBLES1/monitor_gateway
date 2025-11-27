from flask import Flask, request, jsonify, render_template_string
import time

app = Flask(__name__)

# ===== BUFFER =====
data_buffer = []

# ===== DATO INICIAL PARA EVITAR PANTALLA VACÍA =====
data_buffer.append({
    "temperatura": 0,
    "humedad": 0,
    "gas": 0,
    "sensorTemp": "offline",
    "sensorHum": "offline",
    "sensorGas": "offline",
    "timestamp": time.time()
})

# ==================== HTML ====================
dashboard_html = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Dashboard Ambiental</title>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css" />

<style>
body { background:#eef7ef; font-family:Arial; }
.container { width:90%; margin:auto; padding:20px; }
.chart-title { text-align:center; font-size:22px; font-weight:bold; }
.status { font-size:14px; padding:5px 10px; border-radius:6px; }
.online { background:#bfffd1; color:#005f16; }
.offline { background:#ffd4d4; color:#830000; }
.waiting { background:#dedede; color:#333; }
.chart-wrapper { width:100%; height:350px; margin-bottom:30px; }
.alert { display:none; background:red; color:white; padding:6px; text-align:center; border-radius:6px; font-weight:bold; margin-bottom:5px; }
#map { height:350px; width:100%; border-radius:12px; box-shadow:0 4px 15px rgba(0,0,0,0.2); }
.card { background:white; padding:15px; border-radius:12px; margin-bottom:20px; box-shadow:0 4px 10px rgba(0,0,0,0.1); }
</style>
</head>

<body>

<div class="container">
<h1 style="color:#2b6d3e;">Dashboard Ambiental</h1>

<!-- ===== MAPA ===== -->
<div class="card">
    <h2 style="text-align:center;">Mapa de Nodos</h2>
    <div id="map"></div>
</div>

<!-- ===== ESTADOS ===== -->
<div class="card" style="font-size:18px;">
🌡 Temperatura → <span id="estadoTemp" class="status waiting">⏳ Esperando...</span> <br>
💧 Humedad → <span id="estadoHum" class="status waiting">⏳ Esperando...</span> <br>
🔥 Gas → <span id="estadoGas" class="status waiting">⏳ Esperando...</span>
</div>

<!-- ===== GRAFICAS ===== -->
<div class="card">
    <div class="chart-title">Temperatura</div>
    <div id="alertTemp" class="alert">⚠ Sensor desconectado o fuera de rango</div>
    <div class="chart-wrapper"><canvas id="tempChart"></canvas></div>
</div>

<div class="card">
    <div class="chart-title">Humedad</div>
    <div id="alertHum" class="alert">⚠ Sensor desconectado o fuera de rango</div>
    <div class="chart-wrapper"><canvas id="humChart"></canvas></div>
</div>

<div class="card">
    <div class="chart-title">Gas</div>
    <div id="alertGas" class="alert">⚠ Nivel crítico o nodo desconectado</div>
    <div class="chart-wrapper"><canvas id="gasChart"></canvas></div>
</div>



<script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
<script>
// ================== MAPA ==================
var map = L.map('map').setView([4.661944, -74.058583], 17);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19
}).addTo(map);

async function cargarNodos(){
    const res = await fetch("/nodos");
    const nodos = await res.json();

    nodos.forEach(n => {
        L.marker([n.lat, n.lng])
        .addTo(map)
        .bindPopup(
            "<b>" + n.id + "</b><br>" +
            "Tipo: " + n.variable + "<br>" +
            "Estado: <b>" + n.estado + "</b>"
        );
    });
}

cargarNodos();


// ================== GRAFICAS ==================
async function fetchDatos(){
    try{
        const res = await fetch('/datos');
        return await res.json();
    }catch{ return []; }
}

function makeConfig(unidad){
  return {
    type:'line',
    data:{ labels:[], datasets:[{ label:unidad, data:[], borderWidth:2 }] },
    options:{ responsive:true, maintainAspectRatio:false }
  };
}

const tempChart = new Chart(document.getElementById("tempChart"), makeConfig("°C"));
const humChart = new Chart(document.getElementById("humChart"), makeConfig("%"));
const gasChart = new Chart(document.getElementById("gasChart"), makeConfig("ppm"));


async function actualizarGraficos(){

    const datos = await fetchDatos();
    if(datos.length === 0) return;

    const last = datos[datos.length - 1];

    // ===== ESTADOS VISUALES =====
    function setEstado(id, val){
        const el = document.getElementById(id);
        if(val === "ok"){
            el.innerHTML = "🟢 Conectado";
            el.className = "status online";
        } else {
            el.innerHTML = "🔴 Desconectado";
            el.className = "status offline";
        }
    }

    setEstado("estadoTemp", last.sensorTemp);
    setEstado("estadoHum", last.sensorHum);
    setEstado("estadoGas", last.sensorGas);

    // ===== FILTRO NULL PARA EVITAR GRAFICAS VACÍAS =====
    const labels = datos.map(d => new Date(d.timestamp * 1000).toLocaleTimeString());

    tempChart.data.labels = labels;
    tempChart.data.datasets[0].data = datos.map(d => d.temperatura === -1 ? null : d.temperatura);

    humChart.data.labels = labels;
    humChart.data.datasets[0].data = datos.map(d => d.humedad === -1 ? null : d.humedad);

    gasChart.data.labels = labels;
    gasChart.data.datasets[0].data = datos.map(d => d.gas === -1 ? null : d.gas);

    tempChart.update();
    humChart.update();
    gasChart.update();

    // ALERTAS
    document.getElementById("alertTemp").style.display = last.sensorTemp === "offline" ? "block" : "none";
    document.getElementById("alertHum").style.display = last.sensorHum === "offline" ? "block" : "none";
    document.getElementById("alertGas").style.display = last.sensorGas === "offline" ? "block" : "none";
}

setInterval(actualizarGraficos, 2000);
actualizarGraficos();

</script>
</body>
</html>
"""


# ================= FLASK ROUTES =================

@app.route("/")
def home():
    return render_template_string(dashboard_html)

@app.route("/data", methods=["POST"])
def receive_data():
    d = request.get_json()
    d["timestamp"] = time.time()
    data_buffer.append(d)

    if len(data_buffer) > 300:
        data_buffer.pop(0)

    return {"status":"ok"}

@app.route("/datos")
def datos():
    return jsonify(data_buffer)

@app.route("/nodos")
def nodos():
    return jsonify([
        {"id":"Nodo 1","lat":4.661944,"lng":-74.058583,"variable":"Temperatura","estado":"Desconocido"},
        {"id":"Nodo 2","lat":4.662200,"lng":-74.058300,"variable":"Humedad","estado":"Desconocido"},
        {"id":"Nodo 3","lat":4.661700,"lng":-74.058900,"variable":"Gas","estado":"Desconocido"}
    ])


# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
