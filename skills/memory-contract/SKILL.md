---
name: memory-contract
description: "Memory Contract system for reliable memory capture and recall. Ensures all decisions are written to memory and can be recalled later. Use when: executing any tool that makes decisions or changes state. NOT for: read-only queries that don't change state."
metadata:
  openclaw:
    emoji: "🧠"
    requires:
      python: "3.8+"
    install:
      - id: "hooks"
        kind: "directory"
        path: "/Users/danieltekippe/.openclaw/workspace/hooks"
        label: "Memory Contract hooks directory"
---

# Memory Contract Skill

## Purpose

Ensure reliable memory capture and recall by wrapping tool calls with pre-action memory search and post-decision memory persistence.

## When to Use

✅ **ALWAYS use this skill when:**

- Executing `exec` commands that change state
- Writing or editing files with `write` or `edit`
- Using `browser` for actions (not just reading)
- Sending `message` to users/channels
- Any tool that makes a decision or changes state

❌ **DON'T use this skill when:**

- Reading files with `read` (unless part of edit flow)
- Checking status with `session_status`
- Searching memory with `memory_search`
- Other read-only operations

## Core Principle

**"No decision without memory, no memory without verification"**

Every action that changes state must be:
1. Preceded by memory search (context awareness)
2. Followed by memory persistence (decision recording)
3. Verified by validation checks (system health)

## Memory-Aware Tools

Replace standard OpenClaw tools with memory-aware versions:

### **exec** → **memory_aware_exec**
```python
# Instead of:
exec(command="git push origin main")

# Use:
from hooks.memory_aware_tools import memory_aware_exec
memory_aware_exec(command="git push origin main")
```

### **write** → **memory_aware_write**
```python
# Instead of:
write(path="/path/to/file", content="data")

# Use:
from hooks.memory_aware_tools import memory_aware_write
memory_aware_write(path="/path/to/file", content="data")
```

### **edit** → **memory_aware_edit** (coming soon)
### **browser** → **memory_aware_browser** (coming soon)
### **message** → **memory_aware_message** (coming soon)

## Workflow

### 1. Before Any Action
```python
# Import memory-aware tools
from hooks.memory_aware_tools import memory_aware_exec, memory_aware_write

# The tool will automatically:
# - Search memory for relevant context
# - Provide context-aware execution
```

### 2. During Execution
The memory-aware tool:
- Executes the original command
- Captures the result

### 3. After Execution
The memory-aware tool:
- Writes decision and outcome to memory
- Updates compliance metrics
- Logs the operation for validation

## Validation

### Daily Validation (Automatic)
Run every 30 minutes via cron:
```bash
python3 /Users/danieltekippe/.openclaw/workspace/hooks/session_validation.py
```

Checks:
- Today's memory file exists and has content
- Search logs have entries
- Write logs have entries
- Decisions log is updated
- Git backup is recent

### Weekly QA (Manual - White Roger)
White Roger performs:
- Spot-check of memory file content quality
- Recall tests ("what did we decide about X?")
- Compliance rate review (≥90% target)
- Error log review (0 critical errors target)

## Compliance Metrics

Tracked in `memory_contract_compliance.json`:
- **Pre-action searches**: Should increase with each action
- **Post-decision writes**: Should match decisions made
- **Compliance rate**: Target ≥90%
- **Error count**: Target 0

## Kill Switch

### Environment Variable
```bash
# Disable Memory Contract
MEMORY_CONTRACT_ENABLED=false python3 your_script.py

# Enable Memory Contract (default)
MEMORY_CONTRACT_ENABLED=true python3 your_script.py
```

### File-Based
```bash
# Create kill switch
touch /Users/danieltekippe/.openclaw/workspace/DISABLE_MEMORY_CONTRACT

# Remove kill switch
rm /Users/danieltekippe/.openclaw/workspace/DISABLE_MEMORY_CONTRACT
```

## Files Created

```
~/.openclaw/workspace/hooks/
├── pre_action_memory.py          # Search memory before actions
├── post_decision_memory.py       # Write decisions to memory
├── session_validation.py         # Validate memory capture
├── compliance_tracker.py         # Track compliance metrics
├── memory_aware_tools.py         # Memory-aware tool wrappers
├── integration.py                # Integration module
└── agent_integration.py          # Agent-level integration

~/.openclaw/workspace/
├── memory_contract_compliance.json  # Compliance metrics
├── DECISIONS.md                     # Structured decision log
└── memory/YYYY-MM-DD.md             # Daily memory files
```

## Success Criteria

1. **Session capture bug fixed**: Memory files contain real conversation (not just cron prompts)
2. **Recall works**: Can answer "what did we decide about X last week?"
3. **No silent failures**: Compliance dashboard shows ≥90% search/write rates
4. **Git sync healthy**: Commits at least daily

## Integration with Other Skills

When using other skills (github, weather, etc.):
1. Check if the skill makes decisions/changes state
2. If yes, use memory-aware versions of tools
3. If no, use original tools for read-only operations

## Example: GitHub Deployment with Memory Contract

```python
# Without Memory Contract (risky):
exec(command="git push origin main")

# With Memory Contract (safe):
from hooks.memory_aware_tools import memory_aware_exec
memory_aware_exec(command="git push origin main")

# Result:
# 1. Searches memory for previous deployment issues
# 2. Executes git push
# 3. Records decision: "Deployed to production"
# 4. Updates compliance metrics
```

## Troubleshooting

### Issue: Memory search fails
**Solution**: Check `hooks/search_log.jsonl` for errors. Memory search has graceful degradation - execution continues even if search fails.

### Issue: Memory write fails
**Solution**: Check `hooks/errors.jsonl`. Writes have graceful degradation - errors are logged but don't block execution.

### Issue: Compliance rate low
**Solution**: Run validation to identify which checks are failing. Common issues: memory file missing, search/write logs empty.

### Issue: Performance impact
**Solution**: Memory search <500ms, memory write <200ms. If slower, check system resources.

## The Janus Roger Partnership

This skill enables the **Janus Roger** partnership:
- **Black Roger**: Uses memory-aware tools for all execution
- **White Roger**: Validates memory capture and compliance
- **Together**: Ensure reliable memory and continuous improvement

## Remember

**"Trust is built through verification, not promises."**
- Verify memory works before declaring tasks complete
- Check compliance metrics regularly
- Use the kill switch if issues arise
- Document lessons in memory for continuous improvement