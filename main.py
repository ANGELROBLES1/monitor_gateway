from flask import Flask, request, jsonify, render_template_string
import time

app = Flask(__name__)

data_buffer = []

# Default placeholder value
data_buffer.append({
    "temperatura": 0,
    "humedad": 0,
    "gas": 0,
    "sensorTemp": "offline",
    "sensorHum": "offline",
    "sensorGas": "offline",
    "timestamp": time.time()
})

dashboard_html = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<title>Dashboard Ambiental</title>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css" />

<style>
body{background:#eef7ef;font-family:Arial;}
.container{width:90%;margin:auto;padding:20px;}
.chart-title{text-align:center;font-size:22px;font-weight:bold;}
.status{font-size:14px;padding:5px 10px;border-radius:6px;}
.online{background:#bfffd1;color:#005f16;}
.offline{background:#ffd4d4;color:#830000;}
.waiting{background:#dedede;color:#333;}
.chart-wrapper{width:100%;height:350px;margin-bottom:30px;}
.alert{display:none;background:red;color:white;padding:6px;text-align:center;border-radius:6px;font-weight:bold;margin-bottom:5px;}
#map{height:350px;width:100%;border-radius:12px;}
.card{background:white;padding:15px;border-radius:12px;margin-bottom:20px;}
</style>
</head>

<body>

<div class="container">
<h1 style="color:#2b6d3e;">Dashboard Ambiental</h1>

<div class="card">
    <h2 style="text-align:center;">Mapa de Nodos</h2>
    <div id="map"></div>
</div>

<div class="card" style="font-size:18px;">
🌡 Temperatura → <span id="estadoTemp" class="status waiting">⏳ Esperando...</span><br>
💧 Humedad → <span id="estadoHum" class="status waiting">⏳ Esperando...</span><br>
🔥 Gas → <span id="estadoGas" class="status waiting">⏳ Esperando...</span>
</div>

<div class="card">
    <div class="chart-title">Temperatura</div>
    <div id="alertTemp" class="alert">⚠ Sensor desconectado</div>
    <div class="chart-wrapper"><canvas id="tempChart"></canvas></div>
</div>

<div class="card">
    <div class="chart-title">Humedad</div>
    <div id="alertHum" class="alert">⚠ Sensor desconectado</div>
    <div class="chart-wrapper"><canvas id="humChart"></canvas></div>
</div>

<div class="card">
    <div class="chart-title">Gas</div>
    <div id="alertGas" class="alert">⚠ Sensor desconectado</div>
    <div class="chart-wrapper"><canvas id="gasChart"></canvas></div>
</div>


<script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
<script>
var map = L.map('map').setView([4.661944, -74.058583], 17);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",{maxZoom:19}).addTo(map);

let markers = {};

async function actualizarMapa(){
    const res = await fetch('/nodos');
    const nodos = await res.json();

    nodos.forEach(n=>{
        if(!markers[n.id]){
            markers[n.id]= L.marker([n.lat,n.lng]).addTo(map);
        }
        markers[n.id].bindPopup(
            "<b>"+n.id+"</b><br>Estado:<b>"+n.estado+"</b>"
        );
    });
}

async function fetchDatos(){
    try{
        const res=await fetch('/datos');
        return await res.json();
    }catch{return [];}
}

function makeConfig(unidad){
  return {type:'line',data:{labels:[],datasets:[{label:unidad,data:[],borderWidth:2}]},options:{responsive:true}};
}

const tempChart=new Chart(document.getElementById("tempChart"),makeConfig("°C"));
const humChart=new Chart(document.getElementById("humChart"),makeConfig("%"));
const gasChart=new Chart(document.getElementById("gasChart"),makeConfig("ppm"));

async function actualizar(){
    const datos=await fetchDatos();
    if(datos.length==0)return;

    const last=datos[datos.length-1];

    function estado(id,v){
        const el=document.getElementById(id);
        if(v==="ok"){el.innerHTML="🟢 Conectado";el.className="status online";}
        else{el.innerHTML="🔴 Desconectado";el.className="status offline";}
    }

    estado("estadoTemp",last.sensorTemp);
    estado("estadoHum",last.sensorHum);
    estado("estadoGas",last.sensorGas);

    tempChart.data.labels=datos.map(d=>new Date(d.timestamp*1000).toLocaleTimeString());
    tempChart.data.datasets[0].data=datos.map(d=>d.temperatura==-1?null:d.temperatura);

    humChart.data.labels=tempChart.data.labels;
    humChart.data.datasets[0].data=datos.map(d=>d.humedad==-1?null:d.humedad);

    gasChart.data.labels=tempChart.data.labels;
    gasChart.data.datasets[0].data=datos.map(d=>d.gas==-1?null:d.gas);

    tempChart.update();humChart.update();gasChart.update();

    actualizarMapa();
}

setInterval(actualizar,2000);
actualizar();
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
    if len(data_buffer)>300:data_buffer.pop(0)
    return {"status":"ok"}

@app.route("/datos")
def datos():
    return jsonify(data_buffer)

@app.route("/nodos")
def nodos():
    return jsonify([
        {"id":"Nodo 1","lat":4.661944,"lng":-74.058583,"variable":"Temp"},
        {"id":"Nodo 2","lat":4.662200,"lng":-74.058300,"variable":"Hum"},
        {"id":"Nodo 3","lat":4.661700,"lng":-74.058900,"variable":"Gas"}
    ])

if __name__=="__main__":
    app.run(host="0.0.0.0",port=10000,debug=True)
