import os
import time
import logging
import schedule
import mlflow
from datetime import datetime, timezone
from dotenv import load_dotenv
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState

from agents.graph import media_pulse_graph
from agents.state import MediaPulseState
from ingestion.ingest import run_ingestion

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def _get_client() -> WorkspaceClient:
    return WorkspaceClient(
        host=os.getenv("DATABRICKS_HOST"),
        token=os.getenv("DATABRICKS_TOKEN"),
    )


def _mlflow_experiment_path() -> str:
    return os.getenv("MLFLOW_EXPERIMENT_PATH", "/Users/snigdha280301/media_pulse_agents")


def _get_warehouse_id() -> str:
    return os.getenv("DATABRICKS_HTTP_PATH", "").split("/")[-1]


def _sql_val(value) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, str):
        return f"'{value.replace(chr(39), chr(39)*2)}'"
    return str(value)


def _wait_for_statement(client: WorkspaceClient, statement_id: str, poll_interval: int = 2, max_wait: int = 120):
    import time
    elapsed = 0
    while elapsed < max_wait:
        response = client.statement_execution.get_statement(statement_id)
        if response.status.state == StatementState.SUCCEEDED:
            return response
        if response.status.state in (StatementState.FAILED, StatementState.CANCELED, StatementState.CLOSED):
            return response
        time.sleep(poll_interval)
        elapsed += poll_interval
    log.error("Statement %s timed out after %ds", statement_id, max_wait)
    return response


def query_mart_trending() -> list[dict]:
    client = _get_client()
    warehouse_id = _get_warehouse_id()

    response = client.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        wait_timeout="30s",
        statement="SELECT * FROM media_pulse.raw.media_stream ORDER BY polled_at DESC LIMIT 50",
    )

    if response.status.state == StatementState.PENDING:
        response = _wait_for_statement(client, response.statement_id)

    if response.status.state != StatementState.SUCCEEDED:
        log.error(f"Query failed: {response.status}")
        log.error(f"Error detail: {response.status.error}")
        return []

    columns = [col.name for col in response.manifest.schema.columns]
    rows = response.result.data_array or []
    return [dict(zip(columns, row)) for row in rows]


def write_insights(state: dict) -> None:
    client = _get_client()
    warehouse_id = _get_warehouse_id()

    commentary_raw = state.get("commentary", "")
    commentary_text = commentary_raw if isinstance(commentary_raw, str) else commentary_raw.get("commentary")
    headline = None if isinstance(commentary_raw, str) else commentary_raw.get("headline")

    # get anomaly info from state directly not from commentary
    anomalies = state.get("anomalies", [])
    anomaly_detected = state.get("anomaly_detected", False)
    severity = state.get("severity", "none")
    anomaly_type = anomalies[0].get("anomaly_type") if anomalies else None

    rankings = state.get("rankings", [])
    top = rankings[0] if rankings else {}
    titles_mentioned = ", ".join(r.get("title", "") for r in anomalies)

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    # convert bool to SQL boolean string
    anomaly_detected_sql = "true" if anomaly_detected else "false"

    statement = f"""
    INSERT INTO media_pulse.raw.media_ai_insights
        (generated_at, headline, commentary, titles_mentioned,
         top_title, top_media_type, anomaly_detected, anomaly_type, severity)
    VALUES (
        {_sql_val(generated_at)},
        {_sql_val(headline)},
        {_sql_val(commentary_text)},
        {_sql_val(titles_mentioned)},
        {_sql_val(top.get("title"))},
        {_sql_val(top.get("media_type"))},
        {anomaly_detected_sql},
        {_sql_val(anomaly_type)},
        {_sql_val(severity)}
    )
    """

    response = client.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        wait_timeout="30s",
        statement=statement,
    )

    if response.status.state != StatementState.SUCCEEDED:
        log.error("Insight write failed: %s", response.status.error)
        return

    log.info("Insight written to Delta")


def run_agents() -> None:
    log.info("Agent run starting %s", datetime.now(timezone.utc))

    log.info("Fetching fresh data from TMDB...")
    run_ingestion()

    rankings = query_mart_trending()
    if not rankings:
        log.info("No data yet")
        return

    initial_state = MediaPulseState(
        rankings=rankings,
        anomalies=[],
        commentary={},
        titles_mentioned=[],
        severity="none",
        anomaly_detected=False,
        run_id=str(datetime.now(timezone.utc)),
        polled_at=str(datetime.now(timezone.utc)),
        error=None,
    )

    mlflow.set_experiment(_mlflow_experiment_path())
    final_state = media_pulse_graph.invoke(initial_state)

    # MLflow tracking
    with mlflow.start_run():
        mlflow.log_param("poll_timestamp", str(datetime.now(timezone.utc)))
        mlflow.log_metric("titles_processed", len(final_state.get("rankings", [])))
        mlflow.log_metric("anomalies_found", len(final_state.get("anomalies", [])))
        mlflow.log_metric("high_severity_count", 
            sum(1 for a in final_state.get("anomalies", []) 
                if a.get("severity") == "high"))
        mlflow.set_tag("top_title", 
            final_state.get("rankings", [{}])[0].get("title", "none") 
            if final_state.get("rankings") else "none")
        mlflow.set_tag("severity", final_state.get("severity", "none"))

    write_insights(final_state)
    log.info("Agent run complete")


if __name__ == "__main__":
    load_dotenv()
    run_agents()
    schedule.every(15).minutes.do(run_agents)
    while True:
        schedule.run_pending()
        time.sleep(30)
