"""Pure login-log analysis helpers (no Azure SDK required for unit tests)."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any
from urllib.parse import unquote, urlparse


def blob_url_to_container_and_name(blob_url: str) -> tuple[str, str]:
    """Parse https://account.blob.core.windows.net/container/path/to/blob."""
    parsed = urlparse(blob_url)
    path = unquote(parsed.path.lstrip("/"))
    container, _, blob_name = path.partition("/")
    if not container or not blob_name:
        raise ValueError(f"Could not parse blob URL: {blob_url}")
    return container, blob_name


def analyze_login_events(events: list[dict[str, Any]], threshold: int) -> dict[str, Any]:
    """Count failed logins and flag usernames at/above threshold."""
    failed_counts: Counter[str] = Counter()
    total_events = 0
    failed_events = 0

    for event in events:
        total_events += 1
        username = str(event.get("username") or event.get("user") or "unknown")
        status = str(event.get("status") or event.get("result") or "").lower()
        success = event.get("success")
        is_failure = status in {"failure", "failed", "fail"} or success is False
        if is_failure:
            failed_events += 1
            failed_counts[username] += 1

    flagged = sorted(
        [
            {"username": user, "failed_logins": count}
            for user, count in failed_counts.items()
            if count >= threshold
        ],
        key=lambda row: (-row["failed_logins"], row["username"]),
    )

    return {
        "analyzed_at_utc": datetime.now(timezone.utc).isoformat(),
        "failure_threshold": threshold,
        "total_events": total_events,
        "failed_events": failed_events,
        "failed_logins_by_user": dict(sorted(failed_counts.items())),
        "flagged_accounts": flagged,
        "summary": (
            f"{len(flagged)} account(s) flagged with >={threshold} failed logins"
            if flagged
            else f"No accounts reached the failure threshold ({threshold})"
        ),
    }
