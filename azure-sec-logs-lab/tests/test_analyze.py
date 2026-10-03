"""Local unit tests for login-log analysis (no Azure required)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "function_app"))

from analyzer import analyze_login_events  # noqa: E402


def test_alice_is_flagged_at_threshold() -> None:
    events = [
        {"username": "alice", "status": "failure"},
        {"username": "alice", "status": "failure"},
        {"username": "alice", "status": "failure"},
        {"username": "alice", "status": "failure"},
        {"username": "alice", "status": "failure"},
        {"username": "bob", "status": "success"},
    ]
    report = analyze_login_events(events, threshold=5)
    assert report["flagged_accounts"] == [{"username": "alice", "failed_logins": 5}]
    assert report["failed_logins_by_user"]["alice"] == 5


def test_below_threshold_not_flagged() -> None:
    events = [
        {"username": "erin", "status": "failure"},
        {"username": "erin", "status": "failure"},
        {"username": "erin", "status": "success"},
    ]
    report = analyze_login_events(events, threshold=5)
    assert report["flagged_accounts"] == []


def test_sample_alice_file() -> None:
    import json

    payload = json.loads((ROOT / "sample_logs" / "login-log-alice-flagged.json").read_text())
    report = analyze_login_events(payload["events"], threshold=5)
    assert any(row["username"] == "alice" and row["failed_logins"] == 5 for row in report["flagged_accounts"])
