#!/bin/bash
# run_scout.sh — Invoke Scout (DeepAgent) with MiniMax M2.7
# Usage: ./run_scout.sh --task-id <blackboard-task-id> "task description"
# Location: /Volumes/ExternalCorsairSSD/Scout/run_scout.sh
#
# Requirements:
# - MINIMAX_API_KEY env var must be set
# - --task-id argument REQUIRED — maps to blackboard task (closes bypass gap)
# - deepagents installed at ~/.local/bin/deepagents

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BLACKBOARD_DB="$SCRIPT_DIR/../shared/coordination/ai_plan_manager.db"
OUTPUTS_DIR="$SCRIPT_DIR/../shared/coordination/outputs"
WRITE_SENTINEL="$SCRIPT_DIR/../shared/coordination/write_sentinel.py"

# Get MINIMAX_API_KEY from ~/.zshrc (sk-cp- format for anthropic endpoint)
if [ -f ~/.zshrc ]; then
  MINIMAX_API_KEY=$(grep "MINIMAX_API_KEY=" ~/.zshrc | grep "sk-cp-" | head -1 | sed 's/export MINIMAX_API_KEY=//' | tr -d '"' | tr -d "'")
  export MINIMAX_API_KEY
fi

# Ensure ~/.local/bin is in PATH
export PATH="$HOME/.local/bin:/opt/anaconda3/bin:$PATH"

DEEPAGENTS="$HOME/.local/bin/deepagents"

# ── Argument parsing ──────────────────────────────────────────────────────────
if [ "$1" = "--task-id" ] && [ -n "$2" ]; then
  TASK_ID="$2"
  shift 2
else
  echo "Error: --task-id <blackboard-task-id> is required."
  echo "Usage: run_scout.sh --task-id <id> \"task description\""
  echo "Run 'ai-plan-manager.py list' to see available task IDs."
  exit 1
fi

TASK_DESCRIPTION="$*"

if [ -z "$TASK_DESCRIPTION" ]; then
  echo "Error: task description required after --task-id"
  echo "Usage: run_scout.sh --task-id <id> \"task description\""
  exit 1
fi

# ── Blackboard validation ─────────────────────────────────────────────────────
if [ -f "$BLACKBOARD_DB" ]; then
  TASK_STATUS=$(sqlite3 "$BLACKBOARD_DB" \
    "SELECT status FROM tasks WHERE id='$TASK_ID';" 2>/dev/null || echo "NOT_FOUND")

  if [ "$TASK_STATUS" = "NOT_FOUND" ] || [ -z "$TASK_STATUS" ]; then
    echo "Warning: task '$TASK_ID' not found in blackboard DB."
    echo "Available tasks:"
    sqlite3 "$BLACKBOARD_DB" "SELECT id, spec_anchor, status FROM tasks LIMIT 20;" 2>/dev/null || echo "(DB empty)"
    echo ""
    echo "To create tasks: run Phase 0 seeding first."
    exit 1
  fi

  if [ "$TASK_STATUS" = "completed" ]; then
    echo "Error: task '$TASK_ID' is already completed. Create a new task for this work."
    exit 1
  fi

  if [ "$TASK_STATUS" = "rejected" ]; then
    echo "Note: task '$TASK_ID' was previously rejected. Re-attempting."
  fi

  echo "[run_scout] TASK_ID=$TASK_ID STATUS=$TASK_STATUS"
else
  echo "Warning: blackboard DB not found at $BLACKBOARD_DB"
  echo "Skipping task validation — ensure task '$TASK_ID' exists."
fi

# ── Pre-flight checks ─────────────────────────────────────────────────────────
if [ ! -f "$DEEPAGENTS" ]; then
  echo "Error: deepagents not found at $DEEPAGENTS"
  echo "Install with: npm install -g deepagents"
  exit 1
fi

if [ -z "$MINIMAX_API_KEY" ]; then
  echo "Error: MINIMAX_API_KEY environment variable not set"
  exit 1
fi

# ── Output setup ───────────────────────────────────────────────────────────────
mkdir -p "$OUTPUTS_DIR"
OUTPUT_FILE="$OUTPUTS_DIR/task_${TASK_ID}_output.md"

# ── Notify Roger (used after success or failure) ──────────────────────────────
notify_roger() {
  local msg="$1"
  # Use openclaw agent CLI — authenticates via gateway token, no manual auth needed
  if openclaw agent --agent main --message "$msg" 2>&1; then
    echo "[SCOUT] Roger notified successfully"
  else
    echo "[SCOUT] WARNING: Roger notify failed (exit $?) — watchdog will recover via sentinel"
  fi
}

# ── Sentinel helpers ───────────────────────────────────────────────────────────
write_success_sentinel() {
  python3 "$WRITE_SENTINEL" \
    --complete \
    --task-id "$TASK_ID" \
    --output "$OUTPUT_FILE" \
    --notes "Scout completed successfully"
}

write_failure_sentinel() {
  python3 "$WRITE_SENTINEL" \
    --failed \
    --task-id "$TASK_ID" \
    --error "$1" \
    --exit-code "${2:-1}"
}

# ── Run Scout ─────────────────────────────────────────────────────────────────
export SCOUT_TASK_ID="$TASK_ID"

TASK_WITH_CONTEXT="[BLACKBOARD TASK: $TASK_ID]
$TASK_DESCRIPTION

This task is tracked in the AI Plan Manager blackboard (task ID: $TASK_ID).
When complete, Scout must: mark the task complete in the blackboard and
include the blackboard task ID in the completion summary."

"$DEEPAGENTS" \
    --model anthropic:MiniMax-M2.7 \
    --model-params '{"base_url": "https://api.minimax.io/anthropic", "api_key": "'"$MINIMAX_API_KEY"'"}' \
    -n "$TASK_WITH_CONTEXT" \
    -y \
    -S recommended
SC_EXIT=$?

# ── Post-execution: sentinel + notify ─────────────────────────────────────────
if [ $SC_EXIT -eq 0 ]; then
  write_success_sentinel
  notify_roger "[SCOUT] Task complete: task_id=$TASK_ID output=$OUTPUT_FILE"
  echo "[run_scout] SUCCESS: task $TASK_ID complete. Sentinel written. Roger notified."
  exit 0
else
  write_failure_sentinel "deepagents exited with code $SC_EXIT" "$SC_EXIT"
  notify_roger "[SCOUT] Task FAILED: task_id=$TASK_ID exit_code=$SC_EXIT — Daniel notification needed"
  echo "[run_scout] FAILURE: task $TASK_ID failed (exit $SC_EXIT). Sentinel written. Roger notified."
  exit $SC_EXIT
fi
