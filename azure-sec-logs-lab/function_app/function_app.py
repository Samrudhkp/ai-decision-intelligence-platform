"""
AnalyzeLoginLog — Event Grid → Blob login-log analyzer.

Triggered when a new blob is created under the `logs` container.
Downloads the log JSON, counts failed logins per username, flags accounts
with >= FAILURE_THRESHOLD failures, and writes a JSON report to `reports`.
"""

from __future__ import annotations

import json
import logging
import os

import azure.functions as func
from azure.storage.blob import BlobServiceClient

from analyzer import analyze_login_events, blob_url_to_container_and_name

app = func.FunctionApp()

LOGGER = logging.getLogger("AnalyzeLoginLog")


def _failure_threshold() -> int:
    return int(os.environ.get("FAILURE_THRESHOLD", "5"))


def _reports_container() -> str:
    return os.environ.get("REPORTS_CONTAINER", "reports")


def _storage_connection() -> str:
    return os.environ.get("STORAGE_CONNECTION") or os.environ["AzureWebJobsStorage"]


@app.function_name(name="AnalyzeLoginLog")
@app.event_grid_trigger(arg_name="event")
def analyze_login_log(event: func.EventGridEvent) -> None:
    """Event Grid handler for Microsoft.Storage.BlobCreated on `logs`."""
    event_type = event.event_type
    data = event.get_json()
    LOGGER.info("Received Event Grid event type=%s subject=%s", event_type, event.subject)

    if event_type != "Microsoft.Storage.BlobCreated":
        LOGGER.info("Ignoring non-BlobCreated event: %s", event_type)
        return

    blob_url = data.get("url") or data.get("blobUrl")
    if not blob_url:
        LOGGER.error("BlobCreated event missing url: %s", data)
        return

    container, blob_name = blob_url_to_container_and_name(blob_url)
    if container != "logs":
        LOGGER.info("Ignoring blob outside logs container: %s/%s", container, blob_name)
        return

    if blob_name.endswith("/"):
        return

    client = BlobServiceClient.from_connection_string(_storage_connection())
    downloader = client.get_blob_client(container=container, blob=blob_name).download_blob()
    raw = downloader.readall().decode("utf-8")
    payload = json.loads(raw)

    if isinstance(payload, dict) and "events" in payload:
        events = payload["events"]
    elif isinstance(payload, list):
        events = payload
    else:
        events = [payload]

    report = analyze_login_events(events, _failure_threshold())
    report["source_blob"] = f"{container}/{blob_name}"

    stem = blob_name.rsplit("/", 1)[-1]
    if stem.endswith(".json"):
        stem = stem[: -len(".json")]
    report_name = f"{stem}-report.json"

    reports = client.get_container_client(_reports_container())
    reports.upload_blob(
        name=report_name,
        data=json.dumps(report, indent=2).encode("utf-8"),
        overwrite=True,
        content_type="application/json",
    )
    LOGGER.info(
        "Wrote report %s/%s — flagged=%s",
        _reports_container(),
        report_name,
        [row["username"] for row in report["flagged_accounts"]],
    )
