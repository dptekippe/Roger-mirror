#!/usr/bin/env python3
"""
blackboard_client.py — Python DB wrapper for Scout (no sqlite3 shell needed)
Usage:
  python3 blackboard_client.py --query "SELECT ..."
  python3 blackboard_client.py --update "UPDATE tasks SET ..."
  python3 blackboard_client.py --insert "INSERT INTO tasks ..."
  python3 blackboard_client.py --list-pending
  python3 blackboard_client.py --count-tasks
"""
import sqlite3
import sys
import json
import argparse

DB = "/Volumes/ExternalCorsairSSD/shared/coordination/ai_plan_manager.db"

def query(sql, params=None):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    if params:
        cur.execute(sql, params)
    else:
        cur.execute(sql)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update(sql, params=None):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    if params:
        cur.execute(sql, params)
    else:
        cur.execute(sql)
    conn.commit()
    affected = cur.rowcount
    conn.close()
    return affected

def main():
    parser = argparse.ArgumentParser(description="Blackboard DB client for Scout")
    parser.add_argument("--query", help="Run a SELECT query")
    parser.add_argument("--update", help="Run an UPDATE/DELETE query")
    parser.add_argument("--insert", help="Run an INSERT query")
    parser.add_argument("--list-pending", action="store_true", help="List all pending tasks")
    parser.add_argument("--count-tasks", action="store_true", help="Count total tasks")
    parser.add_argument("--tag", default="spec:v1.4", help="Filter by tag")
    args = parser.parse_args()

    if args.query:
        rows = query(args.query)
        for r in rows:
            print(json.dumps(r, default=str))
        print(f"[{len(rows)} rows]")

    elif args.update:
        n = update(args.update)
        print(f"[{n} rows affected]")

    elif args.insert:
        n = update(args.insert)
        print(f"[{n} rows inserted]")

    elif args.list_pending:
        rows = query(
            "SELECT id, title, status, priority FROM tasks WHERE status='pending' AND tags LIKE ? ORDER BY id",
            (f"%{args.tag}%",)
        )
        print(f"Pending tasks (tag={args.tag}): {len(rows)}")
        for r in rows:
            print(f"  [{r['id']}] {r['title']} ({r['priority']})")

    elif args.count_tasks:
        rows = query(f"SELECT COUNT(*) as cnt FROM tasks WHERE tags LIKE ?", (f"%{args.tag}%",))
        print(rows[0]['cnt'])

if __name__ == "__main__":
    main()
