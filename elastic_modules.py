from elasticsearch import Elasticsearch
import datetime

# 🔥 PUT YOUR ELASTIC CLOUD DETAILS HERE
ELASTIC_URL = ""
API_KEY=""
es = Elasticsearch(
    ELASTIC_URL,
    api_key=API_KEY
)

def format_ecs_event(ip, attack_type, risk):
    return {
        "@timestamp": datetime.datetime.utcnow(),
        "event": {
            "kind": "alert",
            "category": "intrusion_detection",
            "type": "security",
            "severity": risk
        },
        "source": {
            "ip": ip
        },
        "threat": {
            "indicator": {
                "type": attack_type
            }
        },
        "risk_score": risk
    }

def send_to_elastic(event):
    try:
        es.index(index="threatshield-ai", document=event)
        print("✅ Sent to Elastic")
    except Exception as e:
        print("❌ Elastic Error:", e)