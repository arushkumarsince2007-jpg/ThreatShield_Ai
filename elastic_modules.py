"""Optional Elastic Cloud integration for ThreatShield AI."""

import logging
import os
from datetime import datetime, timezone

from elasticsearch import Elasticsearch

logger = logging.getLogger(__name__)


def _client():
    """Create an Elastic client only when the app has been configured for it."""
    url = os.getenv("ELASTIC_URL")
    api_key = os.getenv("ELASTIC_API_KEY")
    if not url or not api_key:
        return None
    return Elasticsearch(url, api_key=api_key, request_timeout=5)


def format_ecs_event(ip: str, attack_type: str, risk: int, *, anomaly: bool) -> dict:
    return {
        "@timestamp": datetime.now(timezone.utc).isoformat(),
        "event": {
            "kind": "alert",
            "category": ["intrusion_detection"],
            "type": ["indicator"],
            "severity": risk,
        },
        "source": {"ip": ip},
        "threat": {"indicator": {"type": attack_type}},
        "threatshield": {"risk_score": risk, "anomaly_detected": anomaly},
    }


def send_to_elastic(event: dict) -> bool:
    """Index an event if Elastic is enabled; never break the dashboard on failure."""
    client = _client()
    if client is None:
        return False
    try:
        client.index(index=os.getenv("ELASTIC_INDEX", "threatshield-ai"), document=event)
        return True
    except Exception:
        logger.exception("Unable to send event to Elastic")
        return False
