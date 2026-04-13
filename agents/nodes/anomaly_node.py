from agents.state import AgentState

# A record is flagged as anomalous if its popularity is more than 2 standard
# deviations above the batch mean — catches genuine spikes without false positives
# on consistently popular titles.
_ZSCORE_THRESHOLD = 2.0


def anomaly_node(state: AgentState) -> AgentState:
    rankings = state.get("rankings", [])
    if not rankings:
        return {**state, "anomalies": []}

    scores = [float(r["popularity"]) for r in rankings]
    mean = sum(scores) / len(scores)
    variance = sum((s - mean) ** 2 for s in scores) / len(scores)
    std = variance ** 0.5

    if std == 0:
        return {**state, "anomalies": []}

    anomalies = [
        r for r in rankings
        if (float(r["popularity"]) - mean) / std > _ZSCORE_THRESHOLD
    ]
    return {**state, "anomalies": anomalies}
