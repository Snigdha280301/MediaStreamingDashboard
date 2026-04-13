import os
import logging
import requests
from datetime import datetime, timezone
from agents.state import AgentState

log = logging.getLogger(__name__)


def _post(webhook_url: str, text: str) -> None:
    try:
        requests.post(webhook_url, json={"text": text}, timeout=10)
    except requests.exceptions.Timeout as e:
        log.warning("Slack alert failed: %s", e)
    except requests.exceptions.ConnectionError as e:
        log.warning("Slack alert failed: %s", e)


def alert_node(state: AgentState) -> AgentState:
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        return {**state, "alert_level": "low"}

    rankings = state.get("rankings", [])
    anomalies = state.get("anomalies", [])
    commentary_dict = state.get("commentary", {})

    headline = commentary_dict.get("headline", "") if isinstance(commentary_dict, dict) else ""
    commentary = commentary_dict.get("commentary", "") if isinstance(commentary_dict, dict) else ""

    top = rankings[0] if rankings else {}
    top_title = top.get("title", "N/A")
    top_media_type = top.get("media_type", "N/A")

    timestamp = datetime.now(timezone.utc).strftime("%H:%M UTC")

    # 1. Pulse message — always send
    pulse = (
        f"📊 *MEDIA PULSE — {timestamp}*\n\n"
        f"*#1 Trending:* {top_title} ({top_media_type})\n"
        f"*Titles tracked:* {len(rankings)}\n"
        f"*Anomalies detected:* {len(anomalies)}\n\n"
        f"*Latest Insight:*\n"
        f"{headline}\n\n"
        f"{commentary}"
    )
    _post(webhook_url, pulse)

    # 2. Anomaly alert — only send if anomaly_detected
    alert_level = "low"
    if state.get("anomaly_detected") is True and anomalies:
        alert_level = "high"
        top_anomaly = anomalies[0]
        anomaly_alert = (
            f"🚨 *ANOMALY DETECTED*\n\n"
            f"*Type:* {top_anomaly.get('media_type', 'unknown')}\n"
            f"*Title:* {top_anomaly.get('title', 'unknown')}\n"
            f"*Movement:* {top_anomaly.get('rank_change', 0)} positions → #{top_anomaly.get('rank', '?')}\n"
            f"*Severity:* {state.get('severity', 'none')}"
        )
        _post(webhook_url, anomaly_alert)

    return {**state, "alert_level": alert_level}
