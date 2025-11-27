from flask import Flask, request, jsonify, render_template_string
import time

app = Flask(__name__)

# ===== BUFFER DE DATOS =====
data_buffer = []

# ===== SIMULACIÓN INICIAL PARA EVITAR PANTALLA VACÍA =====
data_buffer.append({
    "temperatura": 0,
    "humedad": 0,
    "gas": 0,
    "sensorTemp": "offline",
    "sensorHum": "offline",
    "sensorGas": "offline",
    "timestamp": time.time()
})

# ===== FUNCION PARA MOSTRAR EL CÓDIGO EN EDITOR =====
def load_self_code():
    try:
        with open(__file__, "r") as f:
            return f.read()
    except:
        return "No se pudo cargar el código"


# ============================ HTML UI ============================
dashboard_html = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Dashboard Ambiental</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<style>
body { background:#eef7ef; font-family: Arial; margin:0; }
.container { width:90%; margin:auto; padding:10px; }
.chart-title { text-align:center; font-size:22px; font-weight:bold; }
.status { font-size:14px; padding:5px 10px; border-radius:6px; }
.online { background:#bfffd1; color:#005f16; }
.offline { background:#ffd4d4; color:#830000; }
.waiting { background:#dedede; color:#555; }
.chart-wrapper { width:100%; height:350px; margin-bottom:25px; }
.alert { display:none; background:red; color:white; text-align:center; padding:6px; border-radius:6px; font-weight:bold; }
</style>
</head>

<body>

<div class="container">
<h1 style="color:#2b6d3e;">Dashboard Ambiental</h1>


<!-- ---------------- ESTADO SENSOR ---------------- -->
<div style="margin-bottom:20px; font-size:18px;">
🌡 Temperatura → <span id="estadoTemp" class="status waiting">⏳ Esperando...</span> <br>
💧 Humedad → <span id="estadoHum" class="status waiting">⏳ Esperando...</span> <br>
🔥 Gas → <span id="estadoGas" class="status waiting">⏳ Esperando...</span>
</div>


<!-- ----------------- GRAFICAS ----------------- -->
<div class="chart-title">Temperatura</div>
<div id="alertTemp" class="alert">⚠ Temperatura fuera de rango</div>
<div class="chart-wrapper"><canvas id="tempChart"></canvas></div>

<div class="chart-title">Humedad</div>
<div id="alertHum" class="alert">⚠ Humedad fuera de rango</div>
<div class="chart-wrapper"><canvas id="humChart"></canvas></div>

<div class="chart-title">Gas</div>
<div id="alertGas" class="alert">⚠ Nivel crítico de gas</div>
<div class="chart-wrapper"><canvas id="gasChart"></canvas></div>


<script>
async function fetchDatos(){
    try{
        const res = await fetch('/datos');
        return await res.json();
    }catch{ return []; }
}


// CONFIG BÁSICA DE GRÁFICO
function makeConfig(unidad){
  return {
    type: 'line',
    data: { labels: [], datasets:[{ label: unidad, data: [], borderWidth: 2 }] },
    options: { responsive:true, maintainAspectRatio:false }
  };
}

const tempChart = new Chart(document.getElementById("tempChart"), makeConfig("°C"));
const humChart  = new Chart(document.getElementById("humChart"),  makeConfig("%"));
const gasChart  = new Chart(document.getElementById("gasChart"),  makeConfig("ppm"));


// -------- FUNCIÓN PRINCIPAL --------
async function actualizarGraficos(){

    const datos = await fetchDatos();
    if(datos.length === 0) return;

    const last = datos[ datos.length-1 ];

    // ---- Actualizar textos de estado ----
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
    setEstado("estadoHum",  last.sensorHum);
    setEstado("estadoGas",  last.sensorGas);

    // --- Filtrar valores válidos (ignorar -1) ---
    const labels = datos.map(d => new Date(d.timestamp * 1000).toLocaleTimeString());

    tempChart.data.labels = labels;
    tempChart.data.datasets[0].data = datos.map(d => d.temperatura === -1 ? null : d.temperatura);

    humChart.data.labels = labels;
    humChart.data.datasets[0].data = datos.map(d => d.humedad === -1 ? null : d.humedad);

    gasChart.data.labels = labels;
    gasChart.data.datasets[0].data = datos.map(d => d.gas === -1 ? null : d.gas);

    tempChart.update(); humChart.update(); gasChart.update();


    // ---- ALERTAS (campo offline encendido también alerta) ----
    document.getElementById("alertTemp").style.display = 
        (last.sensorTemp === "offline") ? "block":"none";

    document.getElementById("alertHum").style.display = 
        (last.sensorHum === "offline") ? "block":"none";

    document.getElementById("alertGas").style.display = 
        (last.sensorGas === "offline") ? "block":"none";
}

setInterval(actualizarGraficos, 2000);
actualizarGraficos();
</script>

</body>
</html>
"""


# ---------------------- RUTAS ----------------------

@app.route("/")
def home():
    return render_template_string(dashboard_html, code_content=load_self_code())


@app.route("/data", methods=["POST"])
def receive_data():
    d = request.get_json()
    if not d:
        return jsonify({"status":"error"}),400

    d["timestamp"] = time.time()
    data_buffer.append(d)

    if len(data_buffer)>300:
        data_buffer.pop(0)

    return jsonify({"status":"ok"})


@app.route("/datos")
def datos():
    return jsonify(data_buffer)


@app.route("/clear", methods=["POST"])
def clear_data():
    data_buffer.clear()
    return jsonify({"status":"cleared"})


# ------------------ MAIN ------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
