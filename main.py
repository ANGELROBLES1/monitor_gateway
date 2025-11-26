from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime

# -----------------------------------------------------
# Inicializar Flask
# -----------------------------------------------------
app = Flask(__name__)
CORS(app)

# -----------------------------------------------------
# Ruta inicial para probar que Flask está funcionando
# -----------------------------------------------------
@app.route("/")
def home():
    return "Servidor Flask funcionando 🚀", 200

# -----------------------------------------------------
# BASE DE DATOS EN MEMORIA
# -----------------------------------------------------
data_store = {
    "NodoA": {
        "temperatura": [],
        "humedad": [],
        "timestamp": None
    },
    "NodoB": {
        "temperatura": [],
        "gas": [],
        "timestamp": None
    }
}

MAX_POINTS = 50  # Máximo historial


# -----------------------------------------------------
# Recibir datos desde el ESP32 (POST)
# -----------------------------------------------------
@app.route("/data", methods=["POST"])
def receive_data():
    try:
        data = request.get_json()

        node_id = data.get("id")

        if node_id not in data_store:
            data_store[node_id] = {}

        now = datetime.now().strftime("%d/%m/%Y, %I:%M:%S %p")

        # ---- NODO A ----
        if node_id == "NodoA":
            temp = float(data.get("temperatura"))
            hum = float(data.get("humedad"))

            data_store["NodoA"]["temperatura"].append(temp)
            data_store["NodoA"]["humedad"].append(hum)
            data_store["NodoA"]["timestamp"] = now

            # Limitar historial
            data_store["NodoA"]["temperatura"] = data_store["NodoA"]["temperatura"][-MAX_POINTS:]
            data_store["NodoA"]["humedad"] = data_store["NodoA"]["humedad"][-MAX_POINTS:]

        # ---- NODO B ----
        elif node_id == "NodoB":
            temp = float(data.get("temperatura"))
            gas = float(data.get("gas"))

            data_store["NodoB"]["temperatura"].append(temp)
            data_store["NodoB"]["gas"].append(gas)
            data_store["NodoB"]["timestamp"] = now

            data_store["NodoB"]["temperatura"] = data_store["NodoB"]["temperatura"][-MAX_POINTS:]
            data_store["NodoB"]["gas"] = data_store["NodoB"]["gas"][-MAX_POINTS:]

        print("Dato recibido desde:", node_id)
        return jsonify({"status": "ok"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400


# -----------------------------------------------------
# Enviar datos al Dashboard (GET)
# -----------------------------------------------------
@app.route("/data", methods=["GET"])
def send_data():
    return jsonify(data_store)


# -----------------------------------------------------
# Borrar datos del historial
# -----------------------------------------------------
@app.route("/clear", methods=["POST"])
def clear():
    for node in data_store.values():
        for key in node:
            if isinstance(node[key], list):
                node[key].clear()
        node["timestamp"] = None

    return jsonify({"status": "cleared"})


# -----------------------------------------------------
# Ejecutar servidor localmente
# (Render ignora esta línea porque usa Gunicorn)
# -----------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
