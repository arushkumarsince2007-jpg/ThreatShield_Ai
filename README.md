# ThreatShield AI

ThreatShield AI is a polished Flask-based SOC dashboard demo. It simulates security alerts, calculates a transparent risk score, optionally sends ECS-shaped events to Elastic, and uses Gemini only when an analyst requests triage.

## Features

- Responsive real-time incident dashboard with risk trend chart
- Simulated alerts: brute force, malware beaconing, privilege escalation, API abuse, and more
- Explainable risk score and automatic response status
- On-demand Gemini-powered analyst triage
- Optional Elastic Cloud indexing; the dashboard still works without Elastic
- `/health` endpoint for deployment health checks

## Quick start

Requires Python 3.10+.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python app.py
```

Open `http://localhost:5000`. The app runs in demo mode until optional credentials are configured.

## Gemini API setup

1. Create a Gemini API key in [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Copy `.env.example` to `.env`.
3. Set the key there:

```env
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash
```

Use the **Analyze with Gemini** button in the dashboard. Gemini is called only by the Flask backend, never from browser JavaScript; this keeps the secret out of the client and prevents polling from consuming your API quota. Do not commit `.env` or paste the key in source code.

If a model is unavailable for your account, change `GEMINI_MODEL` to a supported Flash model in your Google AI Studio account.

## Optional Elastic Cloud setup

Add these values to `.env`:

```env
ELASTIC_URL=https://your-deployment.es.region.gcp.elastic-cloud.com:443
ELASTIC_API_KEY=your_elastic_api_key
ELASTIC_INDEX=threatshield-ai
```

With no Elastic settings, events simply remain dashboard-only. With them, events are indexed in `threatshield-ai` and can be explored in Kibana Discover. Elastic connection failures are logged and do not take down the dashboard.

## API routes

| Route | Purpose |
| --- | --- |
| `GET /` | Dashboard |
| `GET /api/data` | Generates one simulated alert and optionally indexes it |
| `POST /api/analyze` | Gets Gemini triage guidance |
| `GET /health` | Deployment health check |

## Deploy on Render (recommended)

For this Flask demo, **Render Web Service** is the simplest choice: it supports Python, injects the `PORT` environment variable automatically, and the repository includes a `Procfile` production command.

1. Push this repository to GitHub.
2. In Render, select **New → Web Service** and connect the repository.
3. Use build command: `pip install -r requirements.txt`.
4. Use start command: `gunicorn --bind 0.0.0.0:$PORT app:app` (or allow Render to read the included `Procfile`).
5. Add `GEMINI_API_KEY`, `GEMINI_MODEL`, and—if used—Elastic variables under **Environment** / **Secret Files**. Never put secrets in GitHub.
6. Deploy, then verify `https://your-service.onrender.com/health` returns `{"status":"ok",...}`.

Render is ideal for a demo/college project. For a production security platform, prefer Google Cloud Run because it has better IAM, Secret Manager, scaling control, and a natural fit with Gemini/Google Cloud.

## Important demo note

This project **simulates** alerts and response states. “IP temporarily blocked” is a dashboard decision, not a real firewall action. Add authentication, rate limiting, audit logs, real telemetry ingestion, and an approved response workflow before treating it as a production SOC tool.

## Project layout

```text
app.py                Flask routes, dashboard, alert simulation, Gemini triage
elastic_modules.py    Optional Elastic Cloud event formatting and indexing
.env.example          Safe configuration template
Procfile              Production process command for Render-style platforms
```
