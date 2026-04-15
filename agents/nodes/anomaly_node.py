from agents.state import AgentState

_ZSCORE_THRESHOLD = 0.3


def anomaly_node(state: AgentState) -> AgentState:
    rankings = state.get("rankings", [])
    if not rankings:
        return {**state, "anomalies": [], "anomaly_detected": False, "severity": "none"}

    scores = [float(r["popularity"]) for r in rankings]
    mean = sum(scores) / len(scores)
    variance = sum((s - mean) ** 2 for s in scores) / len(scores)
    std = variance ** 0.5

    if std == 0:
        return {**state, "anomalies": [], "anomaly_detected": False, "severity": "none"}

    anomalies = []
    for r in rankings:
        zscore = (float(r["popularity"]) - mean) / std
        if zscore > _ZSCORE_THRESHOLD:
            if zscore > 3.0:
                severity = "high"
            elif zscore > 1.5:
                severity = "medium"
            else:
                severity = "low"

            anomalies.append({
                **r,
                "anomaly_type": "popularity_spike",
                "severity": severity,
                "zscore": round(zscore, 2),
            })

    if any(a["severity"] == "high" for a in anomalies):
        top_severity = "high"
    elif any(a["severity"] == "medium" for a in anomalies):
        top_severity = "medium"
    elif anomalies:
        top_severity = "low"
    else:
        top_severity = "none"

    return {
        **state,
        "anomalies": anomalies,
        "anomaly_detected": len(anomalies) > 0,
        "severity": top_severity,
    }
