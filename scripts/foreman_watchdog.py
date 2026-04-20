#!/usr/bin/env python3
"""
foreman_watchdog.py — Watchdog-only sentinel processor.
Primary notification is handled by run_scout.sh (via openclaw agent).
This script only catches files that were NOT successfully notified to Roger
(i.e., files older than STALE_MINUTES that the openclaw agent call missed).

Usage: python3 foreman_watchdog.py [--dry-run]
"""
import json
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

SENTINELS_DIR = Path("/Volumes/ExternalCorsairSSD/shared/coordination/sentinels")
PROCESSED_DIR = Path("/Volumes/ExternalCorsairSSD/shared/coordination/sentinels/processed")
STALE_MINUTES = 10
DRY_RUN = "--dry-run" in sys.argv

def log(msg):
    print(f"[watchdog {datetime.utcnow().isoformat()}] {msg}")

def notify_roger(message):
    """Send message to Roger via openclaw agent CLI."""
    try:
        result = subprocess.run(
            ["openclaw", "agent", "--agent", "main", "--message", message],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            log(f"Roger notified successfully")
        else:
            log(f"WARNING: openclaw agent returned {result.returncode}: {result.stderr[:100]}")
    except Exception as e:
        log(f"ERROR: failed to notify Roger: {e}")

def process_sentinel(sentinel_file):
    """Process a single stale sentinel file."""
    try:
        with open(sentinel_file) as f:
            data = json.load(f)
    except Exception as e:
        log(f"ERROR reading {sentinel_file}: {e}")
        return

    task_id = data.get("task_id", "unknown")
    status = data.get("status", "unknown")

    if status == "complete":
        output_path = data.get("output_path", "")
        log(f"Stale complete sentinel: task {task_id}")
        notify_roger(f"[FOREMAN WATCHDOG] Missed notification — Scout task complete: task_id={task_id} output={output_path}")
    elif status == "failed":
        error = data.get("error", "unknown")
        log(f"Stale failure sentinel: task {task_id} — {error}")
        notify_roger(f"[FOREMAN WATCHDOG] Missed notification — Scout task FAILED: task_id={task_id} error={error}")
    else:
        log(f"Unknown status '{status}' for {sentinel_file.name}")

    # Archive to processed/
    if not DRY_RUN:
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        archived = PROCESSED_DIR / sentinel_file.name
        sentinel_file.rename(archived)
        log(f"Archived: {sentinel_file.name} → {archived}")

def main():
    if DRY_RUN:
        log("DRY RUN — no changes will be made")

    if not SENTINELS_DIR.exists():
        log("Sentinels dir does not exist — nothing to do")
        return

    # Find stale sentinel files (> STALE_MINUTES old)
    stale_files = []
    now = datetime.utcnow()
    for sentinel_file in SENTINELS_DIR.iterdir():
        if not sentinel_file.name.endswith((".json", ".jsonl")):
            continue
        # Skip already-processed/
        if "processed" in str(sentinel_file):
            continue
        age_seconds = (now - datetime.fromtimestamp(sentinel_file.stat().st_mtime)).total_seconds()
        if age_seconds > STALE_MINUTES * 60:
            stale_files.append(sentinel_file)
            log(f"Found stale sentinel: {sentinel_file.name} ({age_seconds/60:.1f} min old)")

    if not stale_files:
        log(f"No stale sentinels (>{STALE_MINUTES} min). Primary notification already handled by run_scout.sh.")
        return

    for f in stale_files:
        process_sentinel(f)

    log(f"Watchdog processed {len(stale_files)} stale sentinel(s).")

if __name__ == "__main__":
    main()
