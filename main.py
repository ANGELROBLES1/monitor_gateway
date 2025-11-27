from flask import Flask, request, jsonify, render_template_string
import time

app = Flask(__name__)

# Buffer para datos
data_buffer = []

# Simulación de nodos (posición + info base)
nodos_info = {
    "temperatura": {"id": "Nodo 1", "lat": 4.661944, "lng": -74.058583, "estado": "Desconectado"},
    "humedad": {"id": "Nodo 2", "lat": 4.662200, "lng": -74.058300, "estado": "Desconectado"},
    "gas": {"id": "Nodo 3", "lat": 4.661700, "lng": -74.058900, "estado": "Desconectado"},
}

# HTML UI
dashboard_html = """
<!DOCTYPE html>
<html>
<head>
<title>Dashboard Ambiental</title>
<meta charset="utf-8">
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>

<style>
body {
    font-family: Arial;
    background: #eef6ed;
    padding: 20px;
}

.status {
    padding: 6px 10px;
    border-radius: 6px;
    margin-left: 10px;
    font-size: 14px;
}

.status.online { background: #b9ffb4; color: #064e0a; }
.status.offline { background: #ffb4b4; color: #5b0000; }
.status.waiting { background: #ffe9a6; color: #5a4500; }

.chart-wrapper {
    width: 100%;
    height: 460px;
    margin: 40px 0;
    background:white;
    padding:20px;
    border-radius:10px;
}
</style>
</head>

<body>

<h1>Dashboard Ambiental</h1>

<div>
🌡️ Temperatura → <span id="estadoTemp" class="status offline">Desconectado</span><br>
💧 Humedad → <span id="estadoHum" class="status offline">Desconectado</span><br>
🔥 Gas → <span id="estadoGas" class="status offline">Desconectado</span>
</div>

<div id="map" style="height:400px;margin-top:20px;border-radius:10px;"></div>

<!-- GRÁFICAS -->
<div class="chart-wrapper">
<center><h2>Temperatura</h2></center>
<canvas id="tempChart"></canvas>
</div>

<div class="chart-wrapper">
<center><h2>Humedad</h2></center>
<canvas id="humChart"></canvas>
</div>

<div class="chart-wrapper">
<center><h2>Gas</h2></center>
<canvas id="gasChart"></canvas>
</div>

<script>
async function fetchDatos(){
    try{
        const res = await fetch('/datos');
        return await res.json();
    }catch{
        return [];
    }
}

function setEstado(id, estado, value){
    const el = document.getElementById(id);

    if(estado === "ok" && value > -1){
        el.innerHTML = "🟢 Conectado";
        el.className = "status online";
    } else if(estado === "ok" && value == -1){
        el.innerHTML = "🟡 Sin datos";
        el.className = "status waiting";
    } else {
        el.innerHTML = "🔴 Desconectado";
        el.className = "status offline";
    }
}

const tempChart = new Chart(document.getElementById("tempChart"), {
    type:"line",
    data:{labels:[],datasets:[{label:"°C",data:[],borderWidth:2}] },
    options:{responsive:true,maintainAspectRatio:false}
});

const humChart = new Chart(document.getElementById("humChart"), {
    type:"line",
    data:{labels:[],datasets:[{label:"%",data:[],borderWidth:2}] },
    options:{responsive:true,maintainAspectRatio:false}
});

const gasChart = new Chart(document.getElementById("gasChart"), {
    type:"line",
    data:{labels:[],datasets:[{label:"ppm",data:[],borderWidth:2}] },
    options:{responsive:true,maintainAspectRatio:false}
});

async function actualizar(){
    const datos = await fetchDatos();
    if(datos.length === 0) return;

    const last = datos[datos.length -1];
    const labels = datos.map(d => new Date(d.timestamp *1000).toLocaleTimeString());

    tempChart.data.labels = labels;
    humChart.data.labels = labels;
    gasChart.data.labels = labels;

    tempChart.data.datasets[0].data = datos.map(d=>d.temperatura);
    humChart.data.datasets[0].data = datos.map(d=>d.humedad);
    gasChart.data.datasets[0].data = datos.map(d=>d.gas);

    tempChart.update();
    humChart.update();
    gasChart.update();

    setEstado("estadoTemp", last.sensorTemp, last.temperatura);
    setEstado("estadoHum", last.sensorHum, last.humedad);
    setEstado("estadoGas", last.sensorGas, last.gas);
}

var map = L.map('map').setView([4.661944,-74.058583],17);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png").addTo(map);

async function cargarNodos(){
    const res = await fetch("/nodos");
    const nodos = await res.json();

    nodos.forEach(n=>{
        L.marker([n.lat,n.lng]).addTo(map).bindPopup(`
            <b>${n.id}</b><br>
            Estado: ${n.estado}
        `);
    });
}

cargarNodos();
setInterval(actualizar, 3000);
</script>

</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(dashboard_html)

@app.route("/data", methods=["POST"])
def receive():
    d=request.get_json()
    d["timestamp"]=time.time()
    data_buffer.append(d)
    if len(data_buffer)>300: data_buffer.pop(0)

    # Update status database
    nodos_info["temperatura"]["estado"] = "Conectado" if d["sensorTemp"]=="ok" else "Desconectado"
    nodos_info["humedad"]["estado"] = "Conectado" if d["sensorHum"]=="ok" else "Desconectado"
    nodos_info["gas"]["estado"] = "Conectado" if d["sensorGas"]=="ok" else "Desconectado"

    return jsonify({"status":"ok"})

@app.route("/datos")
def datos():
    return jsonify(data_buffer)

@app.route("/nodos")
def nodos():
    return jsonify(list(nodos_info.values()))

if __name__=="__main__":
    app.run(host="0.0.0.0",port=10000,debug=True)
