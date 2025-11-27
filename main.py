from flask import Flask, request, jsonify, render_template_string
import time
import random
import os

app = Flask(__name__)

data_buffer = []

def load_self_code():
    try:
        with open(__file__, "r") as f:
            return f.read()
    except:
        return "No se pudo cargar el codigo"

dashboard_html = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Dashboard Ambiental</title>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/codemirror.min.css">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/theme/material-darker.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/codemirror.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/mode/python/python.min.js"></script>

<style>
body {
    font-family: Arial, sans-serif;
    background: #e9f1ea;
    margin: 0;
    padding: 0;
}
.container {
    max-width: 1200px;
    margin: 20px auto;
    padding: 10px;
}
h1 {
    color: #2e7d32;
    font-size: 22px;
    margin-bottom: 5px;
}
header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 10px;
}
.btn {
    background: #c62828;
    color: white;
    padding: 8px 12px;
    border: none;
    border-radius: 8px;
    cursor: pointer;
}
.btn.secondary {
    background: #2e7d32;
}
.card {
    background: white;
    border-radius: 12px;
    padding: 18px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.1);
    margin-bottom: 24px;
}
.chart-wrapper {
    position: relative;
    width: 100%;
    height: 360px;
}
.chart-title {
    font-size: 20px;
    font-weight: 700;
    text-align: center;
    margin-bottom: 10px;
}
.alert-overlay {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: rgba(200,0,0,0.92);
    padding: 10px 16px;
    color: white;
    font-weight: bold;
    border-radius: 10px;
    display: none;
    z-index: 20;
    font-size: 18px;
}
.settings {
    display: flex;
    gap: 10px;
    justify-content: center;
    margin-top: 10px;
}
.settings label {
    font-size: 13px;
}
input[type="number"] {
    width: 80px;
    padding: 6px;
    border-radius: 6px;
    border: 1px solid #ccc;
}

#map {
    height: 400px;
    width: 100%;
    border-radius: 12px;
    margin-top: 20px;
    box-shadow: 0 6px 20px rgba(0,0,0,0.15);
}

#editor-panel {
    width: 95%;
    margin: 40px auto;
    background: #1e1e1e;
    padding: 15px;
    border-radius: 10px;
    color: white;
    position: relative;
}

#editor {
    height: 400px;
    filter: blur(7px);
    pointer-events: none;
}

#lockOverlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 460px;
    background: rgba(0,0,0,0.65);
    backdrop-filter: blur(2px);
    border-radius: 10px;
    z-index: 50;
    display: flex;
    justify-content: center;
    align-items: center;
    flex-direction: column;
    color: white;
}

#unlockInput {
    padding: 10px;
    font-size: 16px;
    border-radius: 6px;
    border: none;
    width: 200px;
    text-align: center;
    margin-bottom: 10px;
}

#unlockBtn {
    padding: 8px 16px;
    background: #4caf50;
    border-radius: 6px;
    border: none;
    cursor: pointer;
    color: white;
}

#saveBtn {
    margin-top: 12px;
    padding: 10px 20px;
    background: #4CAF50;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    color: white;
}
</style>

<link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>

</head>
<body>

<div class="container">
<header>
    <h1>Dashboard Ambiental</h1>
    <div>
        <button class="btn" onclick="clearData()">Borrar datos</button>
        <button class="btn secondary" onclick="fetchNow()">Actualizar</button>
    </div>
</header>

<div class="card">
    <h2>Mapa de Nodos</h2>
    <div id="map"></div>
</div>

<div class="card">
    <div class="chart-title">Temperatura C</div>
    <div class="chart-wrapper">
        <div id="alertTemp" class="alert-overlay">Temperatura critica</div>
        <canvas id="tempChart"></canvas>
    </div>
    <div class="settings">
        <label>Umbral bajo <input id="tempLow" type="number" value="10"></label>
        <label>Umbral alto <input id="tempHigh" type="number" value="30"></label>
    </div>
</div>

<div class="card">
    <div class="chart-title">Humedad %</div>
    <div class="chart-wrapper">
        <div id="alertHum" class="alert-overlay">Humedad critica</div>
        <canvas id="humChart"></canvas>
    </div>
    <div class="settings">
        <label>Umbral bajo <input id="humLow" type="number" value="20"></label>
        <label>Umbral alto <input id="humHigh" type="number" value="80"></label>
    </div>
</div>

<div class="card">
    <div class="chart-title">Gas ppm</div>
    <div class="chart-wrapper">
        <div id="alertGas" class="alert-overlay">Gas critico</div>
        <canvas id="gasChart"></canvas>
    </div>
    <div class="settings">
        <label>Umbral bajo <input id="gasLow" type="number" value="50"></label>
        <label>Umbral alto <input id="gasHigh" type="number" value="300"></label>
    </div>
</div>

<div id="editor-panel">
    <h2>Editor de Codigo</h2>

    <div id="lockOverlay">
        <p>Editor bloqueado</p>
        <input id="unlockInput" placeholder="Clave" type="password">
        <button id="unlockBtn" onclick="unlockEditor()">Desbloquear</button>
    </div>

    <textarea id="editor">{{ code_content }}</textarea>
    <button id="saveBtn" onclick="saveEditor()">Guardar</button>
</div>

</div>

<script>
async function fetchDatos(){
    try{
        const res = await fetch('/datos');
        if(!res.ok) return [];
        return await res.json();
    }catch(e){
        return [];
    }
}

function checkAlert(values, low, high){
    if(values.length === 0) return false;
    const last = values[values.length - 1];
    return (last > high || last < low);
}

function makeConfig(label){
    return {
        type: 'line',
        data: { labels: [], datasets:[{ label: label, data: [], borderWidth: 2 }] },
        options: { responsive:true, maintainAspectRatio:false }
    };
}

const tempCtx = document.getElementById("tempChart").getContext("2d");
const humCtx  = document.getElementById("humChart").getContext("2d");
const gasCtx  = document.getElementById("gasChart").getContext("2d");

const tempChart = new Chart(tempCtx, makeConfig("C"));
const humChart  = new Chart(humCtx,  makeConfig("%"));
const gasChart  = new Chart(gasCtx,  makeConfig("ppm"));

async function actualizarGraficos(){
    const datos = await fetchDatos();

    if(datos.length === 0){
        tempChart.data.labels = [];
        humChart.data.labels = [];
        gasChart.data.labels = [];
        tempChart.update(); humChart.update(); gasChart.update();
        return;
    }

    const labels = datos.map(d => new Date(d.timestamp * 1000).toLocaleTimeString());
    const temp = datos.map(d => d.temperatura);
    const hum = datos.map(d => d.humedad);
    const gas = datos.map(d => d.gas);

    tempChart.data.labels = labels;
    tempChart.data.datasets[0].data = temp;
    humChart.data.labels = labels;
    humChart.data.datasets[0].data = hum;
    gasChart.data.labels = labels;
    gasChart.data.datasets[0].data = gas;

    tempChart.update(); humChart.update(); gasChart.update();

    const tLow = Number(document.getElementById("tempLow").value);
    const tHigh = Number(document.getElementById("tempHigh").value);
    const hLow = Number(document.getElementById("humLow").value);
    const hHigh = Number(document.getElementById("humHigh").value);
    const gLow = Number(document.getElementById("gasLow").value);
    const gHigh = Number(document.getElementById("gasHigh").value);

    document.getElementById("alertTemp").style.display = checkAlert(temp, tLow, tHigh) ? "block" : "none";
    document.getElementById("alertHum").style.display = checkAlert(hum, hLow, hHigh) ? "block" : "none";
    document.getElementById("alertGas").style.display = checkAlert(gas, gLow, gHigh) ? "block" : "none";
}

async function clearData(){
    await fetch('/clear', { method:'POST' });
    await actualizarGraficos();
}

async function fetchNow(){ actualizarGraficos(); }

actualizarGraficos();
setInterval(actualizarGraficos, 3000);

var map = L.map('map').setView([4.661944, -74.058583], 17);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19 }).addTo(map);

async function cargarNodos(){
    const res = await fetch("/nodos");
    const nodos = await res.json();

    nodos.forEach(n => {
        L.marker([n.lat, n.lng])
        .addTo(map)
        .bindPopup(
            "<b>" + n.id + "</b><br>" +
            "Variable: " + n.variable + "<br>" +
            "Bateria: " + n.bateria + "%<br>" +
            "Senal: " + n.senal + " dBm<br>" +
            "Estado: " + n.estado
        );
    });
}

cargarNodos();

var editor = CodeMirror.fromTextArea(document.getElementById("editor"), {
    lineNumbers: true,
    mode: "python",
    theme: "material-darker"
});

function unlockEditor(){
    const key = document.getElementById("unlockInput").value;
    if(key === "redes123"){
        document.getElementById("editor").style.filter = "none";
        document.getElementById("editor").style.pointerEvents = "auto";
        document.getElementById("lockOverlay").style.display = "none";
        editor.setOption("readOnly", false);
    } else {
        alert("Clave incorrecta");
    }
}

function saveEditor(){
    alert("El codigo fue actualizado en pantalla pero no se puede sobrescribir el archivo en el servidor.");
}
</script>

</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(dashboard_html, code_content=load_self_code())

@app.route("/data", methods=["POST"])
def receive_data():
    d = request.get_json()
    if not d:
        return jsonify({"status":"error"}), 400
    d["timestamp"] = time.time()
    data_buffer.append(d)
    if len(data_buffer) > 300:
        data_buffer.pop(0)
    return jsonify({"status":"ok"})

@app.route("/datos")
def datos():
    return jsonify(data_buffer)

@app.route("/clear", methods=["POST"])
def clear_data():
    data_buffer.clear()
    return jsonify({"status":"cleared"})

@app.route("/nodos")
def nodos():
    nodos = [
        {"id":"Nodo 1","lat":4.661944,"lng":-74.058583,"variable":"Humedad","bateria":87,"senal":-67,"estado":"OK"},
        {"id":"Nodo 2","lat":4.662200,"lng":-74.058300,"variable":"Temperatura","bateria":72,"senal":-70,"estado":"OK"},
        {"id":"Nodo 3","lat":4.661700,"lng":-74.058900,"variable":"Gas","bateria":61,"senal":-75,"estado":"ALERTA"},
    ]
    return jsonify(nodos)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
