#!/usr/bin/env python3
"""
write_sentinel.py — Scout writes completion/failure sentinels
Usage:
  python3 write_sentinel.py --complete --task-id 20 --output /path/to/output.md [--notes "optional notes"]
  python3 write_sentinel.py --failed --task-id 20 --error "connection timeout" [--exit-code 1]
"""
import json
import sys
import os
from datetime import datetime, timezone

SENTINELS_DIR = "/Volumes/ExternalCorsairSSD/shared/coordination/sentinels"

def write_success_sentinel(task_id, output_path, notes=""):
    data = {
        "task_id": task_id,
        "status": "complete",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "output_path": output_path,
        "exit_code": 0,
        "notes": notes
    }
    filename = f"{SENTINELS_DIR}/task_{task_id}_complete.json"
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    print(f"SUCCESS sentinel written: {filename}")

def write_failure_sentinel(task_id, error, exit_code=1):
    data = {
        "task_id": task_id,
        "status": "failed",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "error": error,
        "exit_code": exit_code
    }
    filename = f"{SENTINELS_DIR}/task_{task_id}_failed.json"
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    print(f"FAILURE sentinel written: {filename}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Write Scout completion/failure sentinel")
    parser.add_argument("--complete", action="store_true", help="Write success sentinel")
    parser.add_argument("--failed", action="store_true", help="Write failure sentinel")
    parser.add_argument("--task-id", type=int, required=True, help="Blackboard task ID")
    parser.add_argument("--output", help="Path to task output file (success only)")
    parser.add_argument("--error", help="Error message (failure only)")
    parser.add_argument("--exit-code", type=int, default=1, help="Exit code (default: 1)")
    parser.add_argument("--notes", default="", help="Optional notes")
    args = parser.parse_args()

    os.makedirs(SENTINELS_DIR, exist_ok=True)

    if args.complete:
        if not args.output:
            print("ERROR: --output required for success sentinel")
            sys.exit(1)
        write_success_sentinel(args.task_id, args.output, args.notes)
    elif args.failed:
        if not args.error:
            print("ERROR: --error required for failure sentinel")
            sys.exit(1)
        write_failure_sentinel(args.task_id, args.error, args.exit_code)
    else:
        print("ERROR: must specify --complete or --failed")
        sys.exit(1)
