# Updated Flask app with embedded client-side editor (CodeMirror) to modify dashboard HTML
from flask import Flask, request, jsonify, send_file, render_template_string
import time

app = Flask(__name__)

data_buffer = []

# Editable dashboard template stored in variable
dashboard_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard Ambiental</title>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1"/>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    
    <!-- CodeMirror -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.5/codemirror.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.5/codemirror.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.5/mode/xml/xml.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.5/mode/javascript/javascript.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.5/mode/css/css.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.5/mode/htmlmixed/htmlmixed.min.js"></script>

    <style>
        body { font-family: Arial; background: #eef5ee; padding: 20px; }
        #editorPanel { margin-top: 20px; padding: 10px; background:white; border-radius: 10px; }
        #saveBtn { background:#2e7d32; color:white; padding:10px; border:none; border-radius:5px; cursor:pointer; }
        #saveBtn:hover { background:#1b5e20; }
    </style>
</head>
<body>

<h1>📡 Dashboard Ambiental</h1>
<button onclick="borrarDatos()">Borrar Datos</button>

<div id="dashboardArea">
    <style>
        .chart-wrapper { position: relative; width: 100%; height: 350px; margin-bottom: 40px; }
        .alert-overlay {
            position: absolute;
            top: 50%; left: 50%; transform: translate(-50%, -50%);
            background: rgba(255,0,0,0.8);
            color:white;
            padding: 10px 20px;
            border-radius: 10px;
            font-size: 22px;
            font-weight: bold;
            display:none;
            z-index:10;
        }
    </style>

    <h3>Temperatura</h3>
    <div class="chart-wrapper">
        <div id="alertTemp" class="alert-overlay">⚠ Nivel crítico</div>
        <canvas id="tempChart"></canvas>
    </div>

    <h3>Humedad</h3>
    <div class="chart-wrapper">
        <div id="alertHum" class="alert-overlay">⚠ Nivel crítico</div>
        <canvas id="humChart"></canvas>
    </div>

    <h3>Gas</h3>
    <div class="chart-wrapper">
        <div id="alertGas" class="alert-overlay">⚠ Nivel crítico</div>
        <canvas id="gasChart"></canvas>
    </div>
</div>

<script>
var critTempHigh = 30, critTempLow = 10;
var critHumHigh  = 80, critHumLow  = 20;
var critGasHigh  = 300, critGasLow = 50;

function checkAlerts(values, alertBox, low, high){
    const last = values[values.length-1];
    if(last > high || last < low){ alertBox.style.display="block"; }
    else{ alertBox.style.display="none"; }
}

async function actualizarGraficos() {
    const datos = await fetchData();
    const labels = datos.map(d => new Date(d.timestamp * 1000).toLocaleTimeString());
    const temp = datos.map(d => d.temperatura);
    const hum  = datos.map(d => d.humedad);
    const gas  = datos.map(d => d.gas ?? 0);

    tempChart.data.labels = labels;
    tempChart.data.datasets[0].data = temp;
    humChart.data.labels = labels;
    humChart.data.datasets[0].data = hum;
    gasChart.data.labels = labels;
    gasChart.data.datasets[0].data = gas;

    tempChart.update(); humChart.update(); gasChart.update();

    checkAlerts(temp, document.getElementById('alertTemp'), critTempLow, critTempHigh);
    checkAlerts(hum, document.getElementById('alertHum'), critHumLow, critHumHigh);
    checkAlerts(gas, document.getElementById('alertGas'), critGasLow, critGasHigh);
}

const tempChart = new Chart(document.getElementById("tempChart"), { type: "line", options:{responsive:true,maintainAspectRatio:false}, data: { labels: [], datasets: [{ label: "°C", data: [], borderWidth: 2 }] }});
const humChart  = new Chart(document.getElementById("humChart"),  { type: "line", options:{responsive:true,maintainAspectRatio:false}, data: { labels: [], datasets: [{ label: "%", data: [], borderWidth: 2 }] }});
const gasChart  = new Chart(document.getElementById("gasChart"),  { type: "line", options:{responsive:true,maintainAspectRatio:false}, data: { labels: [], datasets: [{ label: "ppm", data: [], borderWidth: 2 }] }});

setInterval(actualizarGraficos, 3000);
</script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(dashboard_html, html_content=dashboard_html)

@app.route("/update_dashboard", methods=["POST"])
def update_dashboard():
    global dashboard_html
    content = request.get_json()
    dashboard_html = content.get("html", dashboard_html)
    return jsonify({"status": "updated"})

@app.route("/data", methods=["POST"])
def receive_data():
    content = request.get_json()
    if not content:
        return jsonify({"status": "error"}), 400
    content["timestamp"] = time.time()
    data_buffer.append(content)
    if len(data_buffer) > 300:
        data_buffer.pop(0)
    return jsonify({"status": "ok"})

@app.route("/datos")
def send_data():
    return jsonify(data_buffer)

@app.route("/clear", methods=["POST"])
def clear_data():
    data_buffer.clear()
    return jsonify({"status": "cleared"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
