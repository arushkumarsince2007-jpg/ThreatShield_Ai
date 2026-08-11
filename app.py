"""ThreatShield AI: an interactive SOC dashboard demo."""
import logging
import os
import random
from datetime import datetime, timezone

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template_string
from elastic_modules import format_ecs_event, send_to_elastic

load_dotenv()
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
app = Flask(__name__)

INCIDENTS = [("Brute Force Attack", 18), ("Credential Stuffing Attempt", 22),
             ("Suspicious Login", 12), ("Malware Beaconing Detected", 28),
             ("Privilege Escalation Attempt", 30), ("API Abuse / Rate Limit Bypass", 16)]

def build_alert():
    attack, impact = random.choice(INCIDENTS)
    anomaly = random.random() < .35
    risk = min(100, 35 + impact + random.choice([0, 5, 15]) + (15 if anomaly else 0) + random.randint(-6, 8))
    return {"attack_type": attack, "ip": f"192.168.1.{random.randint(1,254)}", "risk_score": risk,
            "anomaly_detected": anomaly, "timestamp": datetime.now(timezone.utc).isoformat()}

def gemini_analysis(alert):
    """AI triage runs server-side; the browser never receives the Gemini key."""
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return "Gemini is not configured. Set GEMINI_API_KEY to enable AI triage."
    try:
        from google import genai
        prompt = ("You are a SOC analyst. Triage this simulated alert. Return exactly: severity "
                  "(Low/Medium/High/Critical), one likely explanation, and two safe investigation steps. "
                  f"Alert: {alert}")
        response = genai.Client(api_key=key).models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"), contents=prompt)
        return response.text.strip() if response.text else "Gemini returned no triage text."
    except Exception:
        app.logger.exception("Gemini triage failed")
        return "AI triage is temporarily unavailable. Check your key, model access, and quota."

PAGE = '''<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>ThreatShield AI</title><script src="https://cdn.jsdelivr.net/npm/chart.js"></script><style>:root{color-scheme:dark;--bg:#08111f;--card:#101d30;--line:#223b59;--cyan:#4de9ff;--muted:#9ab0c9;--red:#ff6584}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 70% 0,#133658,transparent 35%),var(--bg);font:15px Arial;color:#eef7ff}.top{padding:20px 5vw;display:flex;justify-content:space-between;border-bottom:1px solid var(--line)}h1,h2{margin:0}.sub,.muted{color:var(--muted);margin-top:6px}.pill,button{background:var(--cyan);color:#06131d;border:0;border-radius:8px;padding:8px 12px;font-weight:bold}.grid{display:grid;grid-template-columns:1fr 1.5fr 1fr;gap:16px;padding:20px 5vw}.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px}.score{font-size:54px;font-weight:bold;color:var(--cyan)}.critical{color:var(--red)}.log{border-left:3px solid var(--cyan);padding:8px;margin:8px 0;background:#0b1728}.log small{display:block;color:var(--muted);margin-top:4px}#triage{white-space:pre-wrap;line-height:1.5;margin-top:12px}@media(max-width:850px){.grid{grid-template-columns:1fr}.top{gap:15px;align-items:center}}</style></head><body><header class="top"><div><h1>ThreatShield AI</h1><div class="sub">Real-time security observability demo</div></div><span class="pill" id="status">Starting…</span></header><main class="grid"><section class="card"><h2>Live incident feed</h2><div id="logs"></div></section><section class="card"><h2>Threat risk trend</h2><div id="score" class="score">--</div><p class="muted">Current risk score / 100</p><canvas id="chart"></canvas></section><section class="card"><h2>AI incident triage</h2><p class="muted" id="response">Waiting for an alert…</p><button id="analyze" disabled>Analyze with Gemini</button><div id="triage" class="muted"></div></section></main><script>let chart,points=[42,55,48,62];const $=x=>document.getElementById(x);function log(a){let d=document.createElement('div');d.className='log';d.innerHTML=`<b>${a.attack_type}</b> · ${a.ip}<small>Risk ${a.risk_score} · ${a.anomaly_detected?'Anomaly detected':'Normal pattern'} · ${new Date(a.timestamp).toLocaleTimeString()}</small>`;$('logs').prepend(d);while($('logs').children.length>5)$('logs').lastChild.remove()}async function refresh(){try{let a=await (await fetch('/api/data')).json();$('score').textContent=a.risk_score;$('score').className='score '+(a.risk_score>=80?'critical':'');$('status').textContent=a.elastic_enabled?'Elastic connected':'Demo mode';$('response').textContent=a.auto_response;$('analyze').disabled=false;log(a);points.push(a.risk_score);points.shift();chart.data.datasets[0].data=points;chart.update()}catch(e){$('status').textContent='Connection error'}}$('analyze').onclick=async()=>{$('analyze').disabled=true;$('triage').textContent='Analyzing…';let d=await (await fetch('/api/analyze',{method:'POST'})).json();$('triage').textContent=d.analysis;$('analyze').disabled=false};window.onload=()=>{chart=new Chart($('chart'),{type:'line',data:{labels:['-3','-2','-1','Now'],datasets:[{data:points,borderColor:'#4de9ff',tension:.35}]},options:{plugins:{legend:{display:false}},scales:{y:{min:0,max:100}}}});refresh();setInterval(refresh,5000)}</script></body></html>'''

@app.get("/")
def home(): return render_template_string(PAGE)

@app.get("/api/data")
def data():
    alert = build_alert()
    indexed = send_to_elastic(format_ecs_event(
        alert["ip"], alert["attack_type"], alert["risk_score"], anomaly=alert["anomaly_detected"]
    ))
    alert.update({"active_threats": random.randint(5,15), "elastic_enabled": indexed,
                  "auto_response": "IP temporarily blocked" if alert["risk_score"] >= 85 else "Monitoring and logging"})
    return jsonify(alert)

@app.post("/api/analyze")
def analyze(): return jsonify({"analysis": gemini_analysis(build_alert())})

@app.get("/health")
def health(): return jsonify({"status":"ok", "time":datetime.now(timezone.utc).isoformat()})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=os.getenv("FLASK_DEBUG") == "1")
