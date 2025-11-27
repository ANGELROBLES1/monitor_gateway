from flask import Flask, request, jsonify, render_template_string
import time

app = Flask(__name__)

# ===== Buffer de datos (máx 300 entradas) =====
data_buffer = []


# ====== Cargar código fuente en panel ======
def load_self_code():
    try:
        with open(__file__, "r") as f:
            return f.read()
    except:
        return "No se pudo cargar el código"


# ====== Dashboard HTML ======
dashboard_html = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Dashboard Ambiental</title>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<style>
body {
    font-family: Arial, sans-serif;
    background: #e9f1ea;
}
.container { max-width:1200px; margin:20px auto; padding:10px; }

.chart-title {
    font-size:20px; font-weight:700; text-align:center; margin-bottom:10px;
}

.status {
    font-size:14px; 
    font-weight:bold;
    margin-left:10px;
    padding:4px 8px;
    border-radius:6px;
}

.online { color:#0c7a17; background:#b5ffbe; }
.offline { color:#8b0000; background:#ffc4c4; }
.waiting { color:#444; background:#d9d9d9; }

.alert-overlay {
    position:absolute; top:50%; left:50%; transform:translate(-50%,-50%);
    background:rgba(200,0,0,0.92);
    padding:10px 16px; color:white; font-weight:bold;
    border-radius:10px; display:none; z-index:20; font-size:18px;
}
.chart-wrapper { position:relative; width:100%; height:360px; }

</style>
</head>

<body>

<div class="container">
<h1>Dashboard Ambiental</h1>

<!-- ░░░░░ ESTADOS NODE ░░░░░ -->
<div class="card">
    <h2>Estado de Sensores</h2>
    <p>🌡 Temperatura → <span id="estadoTemp" class="status waiting">⏳ Esperando...</span></p>
    <p>💧 Humedad → <span id="estadoHum" class="status waiting">⏳ Esperando...</span></p>
    <p>🔥 Gas → <span id="estadoGas" class="status waiting">⏳ Esperando...</span></p>
</div>

<!-- ░░░░░ GRAFICAS ░░░░░ -->

<div class="card">
    <div class="chart-title">Temperatura</div>
    <div class="chart-wrapper">
        <div id="alertTemp" class="alert-overlay">⚠ Temperatura crítica</div>
        <canvas id="tempChart"></canvas>
    </div>
</div>

<div class="card">
    <div class="chart-title">Humedad</div>
    <div class="chart-wrapper">
        <div id="alertHum" class="alert-overlay">⚠ Humedad crítica</div>
        <canvas id="humChart"></canvas>
    </div>
</div>

<div class="card">
    <div class="chart-title">Gas</div>
    <div class="chart-wrapper">
        <div id="alertGas" class="alert-overlay">⚠ Nivel de gas crítico</div>
        <canvas id="gasChart"></canvas>
    </div>
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

function makeConfig(label){
    return {
        type:'line',
        data:{ labels:[], datasets:[{ label:label, data:[], borderWidth:2 }] },
        options:{ responsive:true, maintainAspectRatio:false }
    };
}

// Graficos
const tempChart = new Chart(document.getElementById("tempChart"), makeConfig("°C"));
const humChart  = new Chart(document.getElementById("humChart"),  makeConfig("%"));
const gasChart  = new Chart(document.getElementById("gasChart"),  makeConfig("ppm"));

// ACTUALIZACIÓN PRINCIPAL
async function actualizarGraficos(){

    const datos = await fetchDatos();

    if(datos.length === 0){
        document.getElementById("estadoTemp").className="status offline";
        document.getElementById("estadoHum").className="status offline";
        document.getElementById("estadoGas").className="status offline";
        document.getElementById("estadoTemp").innerHTML = "Sin datos";
        document.getElementById("estadoHum").innerHTML = "Sin datos";
        document.getElementById("estadoGas").innerHTML = "Sin datos";
        return;
    }

    const last = datos[datos.length - 1];

    function actualizarEstado(id, estado){
        const el = document.getElementById(id);
        if(estado === "ok"){
            el.innerHTML = "🟢 Online";
            el.className = "status online";
        }else{
            el.innerHTML = "🔴 Offline";
            el.className = "status offline";
        }
    }

    actualizarEstado("estadoTemp", last.sensorTemp);
    actualizarEstado("estadoHum",  last.sensorHum);
    actualizarEstado("estadoGas",  last.sensorGas);

    const labels = datos.map(d => new Date(d.timestamp * 1000).toLocaleTimeString());

    tempChart.data.labels = labels;
    tempChart.data.datasets[0].data = datos.map(d => d.temperatura);

    humChart.data.labels = labels;
    humChart.data.datasets[0].data = datos.map(d => d.humedad);

    gasChart.data.labels = labels;
    gasChart.data.datasets[0].data = datos.map(d => d.gas);

    tempChart.update(); humChart.update(); gasChart.update();

    document.getElementById("alertTemp").style.display = 
      (last.sensorTemp === "offline") ? "block" : "none";

    document.getElementById("alertHum").style.display = 
      (last.sensorHum === "offline") ? "block" : "none";

    document.getElementById("alertGas").style.display = 
      (last.sensorGas === "offline") ? "block" : "none";
}

setInterval(actualizarGraficos, 3000);
actualizarGraficos();

</script>
</body>
</html>
"""


# ========= RUTAS FLASK =========

@app.route("/")
def home():
    return render_template_string(dashboard_html, code_content=load_self_code())


@app.route("/data", methods=["POST"])
def receive_data():
    d = request.get_json()
    if not d:
        return jsonify({"status": "error"}), 400

    d["timestamp"] = time.time()
    data_buffer.append(d)

    if len(data_buffer) > 300:
        data_buffer.pop(0)

    return jsonify({"status": "ok"})


@app.route("/datos")
def datos():
    return jsonify(data_buffer)


@app.route("/clear", methods=["POST"])
def clear_data():
    data_buffer.clear()
    return jsonify({"status": "cleared"})


# ========= MAIN =========
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
