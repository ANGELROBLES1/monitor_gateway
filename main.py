<!DOCTYPE html>
<html>

<head>
    <title>Dashboard agricola</title>

    <style>
        body {
            margin: 0;
            font-family: Arial;
            background: #f4f4f4;
        }

        .container {
            width: 95%;
            margin: auto;
            padding-top: 20px;
        }

        .card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 0 8px #ccc;
            margin-bottom: 25px;
        }

        h2 {
            margin-top: 0;
        }

        #map {
            height: 420px;
            width: 100%;
            border-radius: 6px;
        }

        .node-card {
            border: 1px solid #ddd;
            padding: 12px;
            margin-bottom: 10px;
            border-radius: 6px;
        }

        .alerta {
            background: #ffdddd;
            color: #900;
            padding: 10px;
            border-radius: 4px;
            font-weight: bold;
        }

        .cultivo-box {
            background: #eef2ff;
            padding: 15px;
            border-radius: 6px;
        }
    </style>

    <!-- Leaflet CDN -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

</head>

<body>

    <div class="container">

        <!-- MAPA GPS -->
        <div class="card">
            <h2>Ubicacion del cultivo</h2>
            <div id="map"></div>
        </div>

        <!-- CLIMA ACTUAL -->
        <div class="card">
            <h2>Clima actual</h2>
            <div id="clima-box">Cargando clima...</div>
        </div>

        <!-- PANEL DE NODOS -->
        <div class="card">
            <h2>Estado de nodos</h2>
            <div id="nodos-box"></div>
        </div>

        <!-- MODO CULTIVO -->
        <div class="card">
            <h2>Seleccion de cultivo</h2>

            <select id="cultivo-select">
                {% for c in cultivos %}
                <option value="{{c}}">{{c}}</option>
                {% endfor %}
            </select>

            <div id="cultivo-info" class="cultivo-box" style="margin-top: 15px;">
                Selecciona un cultivo para ver recomendaciones
            </div>
        </div>

    </div>

    <script>
        // =========================
        // MAPA
        // =========================

        var map = L.map('map').setView([4.661944, -74.058583], 17);

        L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19
        }).addTo(map);

        function cargarNodos() {
            fetch("/api/nodos")
                .then(r => r.json())
                .then(nodos => {

                    nodos.forEach(n => {
                        var color = n.estado == "OK" ? "green" : "red";

                        var marker = L.circleMarker([n.lat, n.lng], {
                            radius: 10,
                            color: color,
                            fillColor: color,
                            fillOpacity: 0.8
                        }).addTo(map);

                        marker.bindPopup(
                            "<b>" + n.id + "</b><br>" +
                            "Variable: " + n.variable + "<br>" +
                            "Bateria: " + n.bateria + "%<br>" +
                            "Senal: " + n.senal + " dBm<br>" +
                            "Ultimo reporte: " + n.ultimo_reporte + "<br>" +
                            "Estado: " + n.estado
                        );
                    });
                });
        }

        cargarNodos();

        // =========================
        // CLIMA
        // =========================

        function cargarClima() {
            fetch("/api/clima")
                .then(r => r.json())
                .then(c => {
                    document.getElementById("clima-box").innerHTML =
                        "<b>Temperatura:</b> " + c.temperature_2m + " C<br>" +
                        "<b>Humedad:</b> " + c.relative_humidity_2m + " %<br>" +
                        "<b>Viento:</b> " + c.wind_speed_10m + " m/s<br>" +
                        "<b>Codigo de clima:</b> " + c.weather_code;
                });
        }

        cargarClima();

        // =========================
        // NODOS
        // =========================

        function cargarPanelNodos() {
            fetch("/api/nodos")
                .then(r => r.json())
                .then(nodos => {
                    let out = "";

                    nodos.forEach(n => {
                        out += `
                            <div class='node-card'>
                                <b>${n.id}</b><br>
                                Variable: ${n.variable}<br>
                                Bateria: ${n.bateria}%<br>
                                Senal: ${n.senal} dBm<br>
                                Ultimo reporte: ${n.ultimo_reporte}<br>
                                Estado: ${n.estado}
                            </div>
                        `;
                    });

                    document.getElementById("nodos-box").innerHTML = out;
                });
        }

        cargarPanelNodos();

        // =========================
        // CULTIVO - RECOMENDACIONES
        // =========================

        document.getElementById("cultivo-select").addEventListener("change", function () {
            let c = this.value;

            fetch("/api/cultivo/" + c)
                .then(r => r.json())
                .then(info => {
                    document.getElementById("cultivo-info").innerHTML =
                        "<b>Humedad ideal:</b> " + info.humedad_min + " - " + info.humedad_max + "<br>" +
                        "<b>Temperatura ideal:</b> " + info.temp_min + " - " + info.temp_max + "<br>" +
                        "<b>Riego:</b> " + info.riego + "<br>" +
                        "<b>Notas:</b> " + info.notas;
                });
        });

    </script>

</body>

</html>
