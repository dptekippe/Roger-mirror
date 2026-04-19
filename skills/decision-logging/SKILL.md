---
name: decision-logging
description: "Log decision branches - what user said, what I chose, why"
---

# Decision Logging

Track decision points: "User said X, I chose Y because Z"

## When to Log

- When user asks something important
- When I have to choose between options
- When I make assumptions
- When I switch approaches

## Format

```
## Decision: [What you decided]
### Input: [What user said / context]
### Choice: [What you chose]
### Reason: [Why you chose it]
### Outcome: [Result - known later]
```

## Example

```
## Decision: How to explain token bleed

### Input: Dan asked why API calls were high
### Choice: Explain crons + context
### Reason: Root cause was clear, needed full context
### Outcome: Dan understood, we fixed it
```

## Critical: Log Context Fragmentation Events

**Pattern observed (Apr 2026):** isRepeat=true in session metadata = context truncation

When detected, ALWAYS log:
```markdown
## Decision: Context fragmentation response
### Input: isRepeat=true or repeated response pattern
### Choice: [What you did - summarized state, restarted reasoning, etc.]
### Reason: Context truncated, needed continuity check
### Verification: Checked memory for [what] - continuity [maintained/lost]
```

Example:
```markdown
## Decision: Context fragmentation during trade eval
### Input: isRepeat=true, mid-trade-evaluation
### Choice: Halted, rebuilt context from memory_search
### Reason: Context lost mid-analysis, couldn't trust continuation
### Verification: Checked memory - trade context recovered, resumed
```

## Why It Matters

- Learn from past choices
- See patterns in decision-making
- Accountability for choices
- Build expertise over time

## When NOT to Log

- Casual conversation
- Simple factual answers
- Greetings
- Quick lookups

---

## Changelog

| Date | Change | Reason |
|------|--------|--------|
| Apr 19, 2026 | Added "Critical: Log Context Fragmentation Events" section | isRepeat=true pattern detected in metagym logs; context fragmentation events need tracking |
| Apr 19, 2026 | Added example log entry for context fragmentation | Demonstrates logging pattern for future events |
