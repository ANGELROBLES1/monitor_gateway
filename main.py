from flask import Flask, request, jsonify, render_template_string
import time

app = Flask(__name__)

data_buffer = []
last_update = 0
gateway_timeout = 8

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
body{
    font-family:Arial;
    background:#eef6ed;
    padding:20px;
}
.status{
    padding:6px 10px;
    border-radius:6px;
    margin-left:10px;
    font-size:14px;
}
.status.online{background:#b9ffb4;color:#064e0a;}
.status.offline{background:#ffb4b4;color:#5b0000;}

.chart-wrapper{
    width:100%;
    max-width:100%;
    height:650px;
    margin:40px 0;
    background:white;
    padding:30px;
    border-radius:14px;
    box-shadow:0 6px 20px rgba(0,0,0,0.15);
}

.chart-title{
    text-align:center;
    font-size:22px;
    font-weight:bold;
    margin-bottom:10px;
}

canvas{
    width:100% !important;
    height:90% !important;
}

.btn{
    padding:10px 18px;
    background:#c62828;
    color:white;
    border:none;
    border-radius:8px;
    cursor:pointer;
    margin-top:15px;
}
.btn:hover{background:#981c1c;}
</style>
</head>

<body>

<h1>Dashboard Ambiental</h1>

<button class="btn" onclick="clearData()">🧹 Borrar datos</button>

<div style="margin-top:10px;">
🌡️ Temperatura → <span id="estadoTemp" class="status offline">Desconectado</span><br>
💧 Humedad → <span id="estadoHum" class="status offline">Desconectado</span><br>
🔥 Gas → <span id="estadoGas" class="status offline">Desconectado</span>
</div>

<div id="map" style="height:400px;margin-top:20px;border-radius:10px;"></div>

<div class="chart-wrapper">
    <div class="chart-title">Temperatura (°C)</div>
    <canvas id="tempChart"></canvas>
</div>

<div class="chart-wrapper">
    <div class="chart-title">Humedad (%)</div>
    <canvas id="humChart"></canvas>
</div>

<div class="chart-wrapper">
    <div class="chart-title">Gas (ppm)</div>
    <canvas id="gasChart"></canvas>
</div>

<script>
async function fetchDatos(){
    try{return await (await fetch('/datos')).json();}catch{return [];}
}

async function clearData(){
    await fetch('/clear',{method:'POST'});
    location.reload();
}

function setEstado(id,estado){
    const el=document.getElementById(id);
    el.innerHTML=(estado==="ok")?"🟢 Conectado":"🔴 Desconectado";
    el.className="status "+((estado==="ok")?"online":"offline");
}

const tempChart=new Chart(document.getElementById("tempChart"),{type:"line",data:{labels:[],datasets:[{label:"°C",data:[],borderWidth:2}]}});
const humChart=new Chart(document.getElementById("humChart"),{type:"line",data:{labels:[],datasets:[{label:"%",data:[],borderWidth:2}]}});
const gasChart=new Chart(document.getElementById("gasChart"),{type:"line",data:{labels:[],datasets:[{label:"ppm",data:[],borderWidth:2}]}});
    
var map = L.map('map').setView([4.661944, -74.058583], 17);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",{maxZoom:19}).addTo(map);

function actualizarMapa(estados){

    map.eachLayer(layer=>{
        if(layer instanceof L.Marker) map.removeLayer(layer);
    });

    const iconOnline= L.icon({iconUrl:"https://cdn-icons-png.flaticon.com/512/190/190411.png",iconSize:[28,28]});
    const iconOffline=L.icon({iconUrl:"https://cdn-icons-png.flaticon.com/512/463/463612.png", iconSize:[28,28]});

    const nodos=[
        {name:"Nodo 1 (Temp)", lat:4.661944, lng:-74.058583, status:estados.temp},
        {name:"Nodo 2 (Hum)", lat:4.662200, lng:-74.058300, status:estados.hum},
        {name:"Nodo 3 (Gas)", lat:4.661700, lng:-74.058900, status:estados.gas},
    ];

    nodos.forEach(n=>{
        L.marker([n.lat,n.lng],{icon:(n.status==="ok")?iconOnline:iconOffline})
        .addTo(map)
        .bindPopup(`<b>${n.name}</b><br>Estado: ${(n.status==="ok")?"🟢 Conectado":"🔴 Desconectado"}`);
    });
}

async function actualizar(){
    const datos=await fetchDatos();
    const now=Date.now()/1000;
    const gatewayAlive=(datos.length>0&&(now-datos[datos.length-1].timestamp)<8);

    if(!gatewayAlive){
        setEstado("estadoTemp","offline");
        setEstado("estadoHum","offline");
        setEstado("estadoGas","offline");
        tempChart.data.labels=[];
        humChart.data.labels=[];
        gasChart.data.labels=[];
        tempChart.update(); humChart.update(); gasChart.update();
        actualizarMapa({temp:"offline",hum:"offline",gas:"offline"});
        return;
    }

    const labels=datos.map(d=>new Date(d.timestamp*1000).toLocaleTimeString());

    tempChart.data.labels=labels;
    humChart.data.labels=labels;
    gasChart.data.labels=labels;

    tempChart.data.datasets[0].data=datos.map(d=>d.temperatura);
    humChart.data.datasets[0].data=datos.map(d=>d.humedad);
    gasChart.data.datasets[0].data=datos.map(d=>d.gas);

    tempChart.update(); humChart.update(); gasChart.update();

    const last=datos[datos.length-1];

    setEstado("estadoTemp",last.sensorTemp);
    setEstado("estadoHum",last.sensorHum);
    setEstado("estadoGas",last.sensorGas);

    actualizarMapa({
        temp:last.sensorTemp,
        hum:last.sensorHum,
        gas:last.sensorGas
    });
}

setInterval(actualizar,3000);
</script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(dashboard_html)

@app.route("/data", methods=["POST"])
def receive():
    global last_update
    data=request.get_json()
    data["timestamp"]=time.time()
    last_update=time.time()
    data_buffer.append(data)
    if len(data_buffer)>300:
        data_buffer.pop(0)
    return jsonify({"status":"ok"})

@app.route("/datos")
def datos():
    return jsonify(data_buffer)

@app.route("/clear", methods=["POST"])
def clear():
    data_buffer.clear()
    return jsonify({"status":"cleared"})

if __name__=="__main__":
    app.run(host="0.0.0.0",port=10000,debug=True)
