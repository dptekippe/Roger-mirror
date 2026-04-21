#!/bin/bash
# Hermes Runner with External SSD Logging
# Usage: ./run_hermes.sh "task description"
#
# IMPORTANT: Hermes is configured to use Kimi K2.6 (not MiniMax)
# Do NOT use --provider minimax or any provider flag
# Do NOT use -Q (quiet mode) — it causes SIGTERM
# Correct invocation: hermes chat -q (without -Q)
#
# Log diversion: All output goes to /Volumes/ExternalCorsairSSD/shared/logs/hermes/

LOG_DIR="/Volumes/ExternalCorsairSSD/shared/logs/hermes"

# Create log directory
mkdir -p "$LOG_DIR"

# Log rotation: keep last 7 days
find "$LOG_DIR" -name "hermes-*.log" -mtime +7 -delete 2>/dev/null

# Setup logging with timestamp
LOG_FILE="$LOG_DIR/hermes-$(date +%Y%m%d-%H%M%S).log"
exec > "$LOG_FILE" 2>&1
echo "[LOG START] $(date '+%Y-%m-%d %H:%M:%S') - Hermes session initialized"

# Run Hermes with specified task
# NOTE: Do NOT use -Q flag — it causes SIGTERM
# NOTE: Do NOT use --provider — Hermes uses Kimi K2.6 by default
echo "Running Hermes..."
hermes chat -q "$1" 2>&1

echo "[LOG END] $(date '+%Y-%m-%d %H:%M:%S') - Hermes session completed"