from flask import Flask, request, jsonify, render_template_string
import time

app = Flask(__name__)

data_buffer = []  
last_update = 0   # Tiempo del último paquete recibido
gateway_timeout = 8  # Segundos antes de marcar desconectado

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
body{font-family:Arial;background:#eef6ed;padding:20px;}

.status{padding:6px 10px;border-radius:6px;margin-left:10px;font-size:14px;}
.status.online{background:#b9ffb4;color:#064e0a;}
.status.offline{background:#ffb4b4;color:#5b0000;}

.chart-wrapper{width:100%;height:460px;margin:40px 0;background:white;padding:20px;border-radius:10px;}

.btn {padding:10px 18px;background:#c62828;color:white;border:none;border-radius:8px;cursor:pointer;margin-top:15px;}
.btn:hover{background:#9b0f0f;}
</style>
</head>

<body>

<h1>Dashboard Ambiental</h1>

<button class="btn" onclick="clearData()">🧹 Borrar datos</button>

<div>
🌡️ Temperatura → <span id="estadoTemp" class="status offline">Desconectado</span><br>
💧 Humedad → <span id="estadoHum" class="status offline">Desconectado</span><br>
🔥 Gas → <span id="estadoGas" class="status offline">Desconectado</span>
</div>

<div id="map" style="height:400px;margin-top:20px;border-radius:10px;"></div>

<div class="chart-wrapper"><center><h2>Temperatura</h2></center><canvas id="tempChart"></canvas></div>
<div class="chart-wrapper"><center><h2>Humedad</h2></center><canvas id="humChart"></canvas></div>
<div class="chart-wrapper"><center><h2>Gas</h2></center><canvas id="gasChart"></canvas></div>


<script>
async function fetchDatos(){
    try{
        const res = await fetch('/datos');
        return await res.json();
    }catch{return [];}
}

async function clearData(){
    await fetch('/clear', {method:'POST'});
    location.reload();
}

function setEstado(id,estado){
    const el=document.getElementById(id);

    if(estado==="ok"){
        el.innerHTML="🟢 Conectado";
        el.className="status online";
    }else{
        el.innerHTML="🔴 Desconectado";
        el.className="status offline";
    }
}

const tempChart=new Chart(document.getElementById("tempChart"),{type:"line",data:{labels:[],datasets:[{label:"°C",data:[],borderWidth:2}]}});
const humChart=new Chart(document.getElementById("humChart"),{type:"line",data:{labels:[],datasets:[{label:"%",data:[],borderWidth:2}]}});
const gasChart=new Chart(document.getElementById("gasChart"),{type:"line",data:{labels:[],datasets:[{label:"ppm",data:[],borderWidth:2}]}});
    
async function actualizar(){
    const datos=await fetchDatos();
    const now = Date.now()/1000;

    // Si no hay paquetes recientes del gateway → reset total
    const gatewayAlive = (datos.length>0 && (now - datos[datos.length-1].timestamp)<8);

    if(!gatewayAlive){
        setEstado("estadoTemp","offline");
        setEstado("estadoHum","offline");
        setEstado("estadoGas","offline");

        tempChart.data.labels=[];
        humChart.data.labels=[];
        gasChart.data.labels=[];
        tempChart.update(); humChart.update(); gasChart.update();
        return;
    }

    const labels=datos.map(d=>new Date(d.timestamp*1000).toLocaleTimeString());

    tempChart.data.labels=labels;
    humChart.data.labels=labels;
    gasChart.data.labels=labels;

    tempChart.data.datasets[0].data=datos.map(d=>d.temperatura);
    humChart.data.datasets[0].data=datos.map(d=>d.humedad);
    gasChart.data.datasets[0].data=datos.map(d=>d.gas);

    tempChart.update();humChart.update();gasChart.update();

    const last=datos[datos.length-1];
    setEstado("estadoTemp", last.sensorTemp);
    setEstado("estadoHum", last.sensorHum);
    setEstado("estadoGas", last.sensorGas);
}

var map=L.map('map').setView([4.661944,-74.058583],17);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png").addTo(map);
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
    d=request.get_json()
    d["timestamp"]=time.time()
    last_update=time.time()

    data_buffer.append(d)
    if len(data_buffer)>300: data_buffer.pop(0)
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
