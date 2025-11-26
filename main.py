from flask import Flask, request, jsonify, send_file
from flask import render_template_string
import time

app = Flask(__name__)

data_buffer = []   # almacenamiento temporal

# ==============================
# Página Web (Dashboard)
# ==============================
dashboard_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard Ambiental</title>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1"/>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

    <style>
        body {
            font-family: Arial;
            background: #eef5ee;
            text-align: center;
            padding: 20px;
        }
        h1 { color: #2e7d32; }
        .chart-container {
            width: 90%%;
            max-width: 900px;
            margin: auto;
            background: white;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        button {
            background: #c62828;
            color: white;
            padding: 10px 18px;
            font-size: 16px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            margin-bottom: 20px;
        }
        button:hover { background: #8e0000; }
    </style>
</head>
<body>

    <h1>📡 Dashboard Ambiental - Gateway ESP32</h1>

    <button onclick="borrarDatos()">Borrar Datos</button>

    <div class="chart-container">
        <h3>Temperatura</h3>
        <canvas id="tempChart"></canvas>
    </div>

    <div class="chart-container">
        <h3>Humedad</h3>
        <canvas id="humChart"></canvas>
    </div>

    <div class="chart-container">
        <h3>Gas</h3>
        <canvas id="gasChart"></canvas>
    </div>

<script>
async function fetchData() {
    const res = await fetch('/datos');
    return await res.json();
}

async function borrarDatos() {
    await fetch('/clear', { method: "POST" });
    alert("Datos borrados");
}

async function actualizarGraficos() {
    const datos = await fetchData();

    const labels = datos.map(d => new Date(d.timestamp * 1000).toLocaleTimeString());
    const temp = datos.map(d => d.temperatura);
    const hum  = datos.map(d => d.humedad);
    const gas  = datos.map(d => d.gas);

    tempChart.data.labels = labels;
    tempChart.data.datasets[0].data = temp;

    humChart.data.labels = labels;
    humChart.data.datasets[0].data = hum;

    gasChart.data.labels = labels;
    gasChart.data.datasets[0].data = gas;

    tempChart.update();
    humChart.update();
    gasChart.update();
}

// ====== Gráficos ======
const tempChart = new Chart(document.getElementById("tempChart"), {
    type: "line",
    data: { labels: [], datasets: [{ label: "°C", data: [], borderWidth: 2 }] },
});

const humChart = new Chart(document.getElementById("humChart"), {
    type: "line",
    data: { labels: [], datasets: [{ label: "%", data: [], borderWidth: 2 }] },
});

const gasChart = new Chart(document.getElementById("gasChart"), {
    type: "line",
    data: { labels: [], datasets: [{ label: "ppm", data: [], borderWidth: 2 }] },
});

// Actualizar cada 3 segundos
setInterval(actualizarGraficos, 3000);
</script>

</body>
</html>
"""

# ==============================
# Rutas para la API
# ==============================

@app.route("/")
def home():
    return render_template_string(dashboard_html)

@app.route("/api/data", methods=["POST"])
def receive_data():
    content = request.get_json()

    if not content or "id" not in content:
        return jsonify({"status": "error", "reason": "payload inválido"}), 400

    # se agrega timestamp
    content["timestamp"] = time.time()

    data_buffer.append(content)

    # limitar tamaño
    if len(data_buffer) > 300:
        data_buffer.pop(0)

    return jsonify({"status": "ok"})

@app.route("/datos", methods=["GET"])
def send_data():
    return jsonify(data_buffer)

@app.route("/clear", methods=["POST"])
def clear_data():
    data_buffer.clear()
    return jsonify({"status": "cleared"})

# ==============================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
