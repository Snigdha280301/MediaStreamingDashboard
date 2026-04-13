import os
import time
import logging
import schedule
from datetime import datetime, timezone
from dotenv import load_dotenv
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState

from ingestion.tmdb_client import TMDBClient
from expectations.tmdb_suite import validate_records

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def _get_warehouse_id() -> str:
    # HTTP path is /sql/1.0/warehouses/<id>
    return os.getenv("DATABRICKS_HTTP_PATH", "").split("/")[-1]


def _sql_val(value) -> str:
    """Format a Python value as a SQL literal, returning NULL for None."""
    if value is None:
        return "NULL"
    if isinstance(value, str):
        escaped = value.replace("'", "''")
        return f"'{escaped}'"
    return str(value)


def _write_records(records: list[dict], client: WorkspaceClient, warehouse_id: str) -> None:
    rows = ", ".join(
        "({})".format(", ".join([
            _sql_val(r.get("tmdb_id")),
            _sql_val(r.get("title")),
            _sql_val(r.get("media_type")),
            _sql_val(r.get("rank")),
            _sql_val(r.get("previous_rank")),
            _sql_val(r.get("rank_change")),
            _sql_val(r.get("popularity")),
            _sql_val(r.get("vote_average")),
            _sql_val(r.get("vote_count")),
            _sql_val(r.get("genre_ids")),
            _sql_val(r.get("overview")),
            _sql_val(r.get("release_date")),
            _sql_val(r.get("original_language")),
            _sql_val(r.get("endpoint_source")),
            _sql_val(r.get("polled_at")),
        ]))
        for r in records
    )
    statement = f"""
    INSERT INTO media_pulse.raw.media_stream
        (tmdb_id, title, media_type, rank, previous_rank, rank_change,
         popularity, vote_average, vote_count, genre_ids, overview,
         release_date, original_language, endpoint_source, polled_at)
    VALUES {rows}
    """
    response = client.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        wait_timeout="30s",
        statement=statement,
    )
    if response.status.state not in (StatementState.SUCCEEDED,):
        raise RuntimeError(f"Insert failed: {response.status.error}")


def run_ingestion() -> list[dict]:
    log.info("Pipeline starting %s", datetime.now(timezone.utc))

    records = TMDBClient().poll_all()
    log.info("Fetched %d records from TMDB", len(records))

    valid_records, invalid_records, _ = validate_records(records)
    log.info("Valid: %d, Invalid: %d", len(valid_records), len(invalid_records))

    if not valid_records:
        log.info("No valid records to write — skipping Delta write")
        return []

    db = WorkspaceClient(
        host=os.getenv("DATABRICKS_HOST"),
        token=os.getenv("DATABRICKS_TOKEN"),
    )
    _write_records(valid_records, db, _get_warehouse_id())
    log.info("Written %d records to Delta Lake", len(valid_records))

    log.info("Pipeline complete")
    return valid_records


if __name__ == "__main__":
    run_ingestion()
    schedule.every(15).minutes.do(run_ingestion)
    while True:
        schedule.run_pending()
        time.sleep(30)
