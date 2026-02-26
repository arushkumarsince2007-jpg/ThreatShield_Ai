from flask import Flask, jsonify, render_template_string
import random
import datetime
from elastic_modules import send_to_elastic, format_ecs_event

app = Flask(__name__)

# --------- AI RISK CALCULATION ---------
def calculate_risk():
    base = random.randint(40, 80)
    anomaly = random.choice([0, 10, 20])
    geo_risk = random.choice([0, 5, 15])
    return min(base + anomaly + geo_risk, 100)

# --------- INCIDENT GENERATOR ---------
def generate_incident():
    return random.choice([
        "Brute Force Attack",
        "Credential Stuffing Attempt",
        "Suspicious Login",
        "Malware Beaconing Detected",
        "Privilege Escalation Attempt",
        "API Abuse / Rate Limit Bypass"
    ])

# --------- FRONTEND (UNCHANGED UI) ---------
html_page = """ 
<!DOCTYPE html>
<html>
<head>
    <title>ThreatShield AI - Elastic SOC</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { margin: 0; background: #0b1120; color: #fff; font-family: Arial; }
        .header {
            padding: 20px;
            background: #111827;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid cyan;
            box-shadow: 0 0 25px cyan;
        }
        .main-grid {
            display: grid;
            grid-template-columns: 1fr 2fr 1fr;
            gap: 20px;
            padding: 20px;
        }
        .panel {
            background: #111827;
            padding: 20px;
            border-radius: 12px;
            border: 1px solid rgba(0,255,255,0.3);
            box-shadow: 0 0 20px rgba(0,255,255,0.2);
        }
        .critical {
            color: #ff4d4d;
            font-weight: bold;
            animation: blink 1s infinite;
        }
        @keyframes blink { 50% { opacity: 0.5; } }
        .heatmap {
            margin-top: 20px;
            height: 200px;
            background: radial-gradient(circle at center, red 0%, transparent 70%);
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 18px;
        }
        .log {
            font-size: 14px;
            margin-top: 10px;
            padding: 5px;
            background: #1f2937;
            border-radius: 5px;
        }
    </style>
</head>
<body>

<div class="header">
    <h1>ThreatShield AI - Elastic SOC</h1>
    <div id="stats">Loading...</div>
</div>

<div class="main-grid">

    <div class="panel">
        <h2>Real-Time Incident Feed</h2>
        <div id="incidentLogs"></div>
    </div>

    <div class="panel">
        <h2>Threat Intelligence & AI Risk Engine</h2>
        <h3>Risk Score: <span id="riskScore" class="critical"></span></h3>
        <canvas id="chart"></canvas>
        <div class="heatmap">🌍 Global Threat Activity</div>
    </div>

    <div class="panel">
        <h2>Automated Response Engine</h2>
        <p id="responseStatus"></p>
        <p id="timestamp"></p>
    </div>

</div>

<script>
let chart;
let threatData = [50,60,70,75];

async function fetchData() {
    const res = await fetch('/api/data');
    const data = await res.json();

    document.getElementById("stats").innerHTML =
        `🔥 Active: ${data.active_threats}
         | 🚨 Risk: ${data.risk_score}
         | ⚙️ Actions: ${data.automated_actions}`;

    document.getElementById("riskScore").innerText = data.risk_score;

    document.getElementById("responseStatus").innerHTML =
        "Action: <span class='critical'>" + data.auto_block + "</span>";

    document.getElementById("timestamp").innerText =
        "Last Updated: " + data.timestamp;

    const log = document.createElement("div");
    log.className = "log";
    log.innerText = data.latest_alert;
    document.getElementById("incidentLogs").prepend(log);

    threatData.push(data.risk_score);
    threatData.shift();
    chart.data.datasets[0].data = threatData;
    chart.update();
}

window.onload = function () {
    const ctx = document.getElementById('chart');
    chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['-3','-2','-1','Now'],
            datasets: [{
                label: 'Threat Score Trend',
                data: threatData,
                borderColor: 'red',
                tension: 0.4
            }]
        }
    });

    fetchData();
    setInterval(fetchData, 3000);
};
</script>
</body>
</html>
"""

# --------- ROUTES ---------

@app.route("/")
def home():
    return render_template_string(html_page)

@app.route("/api/data")
def data():
    risk = calculate_risk()
    attack_type = generate_incident()
    ip = f"192.168.1.{random.randint(1,255)}"

    event = format_ecs_event(ip, attack_type, risk)
    send_to_elastic(event)

    return jsonify({
        "active_threats": random.randint(5,15),
        "risk_score": risk,
        "automated_actions": random.randint(10,25),
        "latest_alert": f"{attack_type} from {ip}",
        "auto_block": "IP Blocked Automatically" if risk > 85 else "Monitoring & Logging",
        "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
    })

if __name__ == "__main__":
    app.run(debug=True)