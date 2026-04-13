import mlflow
from langgraph.graph import StateGraph, END

from agents.state import AgentState
from agents.nodes.anomaly_node import anomaly_node
from agents.nodes.narrative_node import narrative_node
from agents.nodes.alert_node import alert_node


def _compile() -> StateGraph:
    builder = StateGraph(AgentState)
    builder.add_node("anomaly", anomaly_node)
    builder.add_node("narrative", narrative_node)
    builder.add_node("alert", alert_node)

    builder.set_entry_point("anomaly")
    builder.add_edge("anomaly", "narrative")
    builder.add_edge("narrative", "alert")
    builder.add_edge("alert", END)

    return builder.compile()


def build_graph() -> StateGraph:
    mlflow.set_experiment("media_pulse_agents")
    return _compile()


media_pulse_graph = _compile()


def run_graph(records: list[dict]) -> AgentState:
    mlflow.start_run()

    graph = _compile()
    result = graph.invoke({
        "rankings": records,
        "anomalies": [],
        "commentary": "",
        "alert_level": None,
    })

    rankings = result.get("rankings", [])
    anomalies = result.get("anomalies", [])

    mlflow.log_param("poll_timestamp", records[0]["polled_at"] if records else "none")
    mlflow.log_metric("titles_processed", len(rankings))
    mlflow.log_metric("anomalies_found", len(anomalies))
    mlflow.log_metric("high_severity_count",
                      sum(1 for a in anomalies if a.get("severity") == "high"))
    mlflow.set_tag("top_title", rankings[0]["title"] if rankings else "none")

    mlflow.end_run()
    return result