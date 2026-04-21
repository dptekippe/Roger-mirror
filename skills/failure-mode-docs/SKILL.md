---
name: failure-mode-docs
description: "Document what breaks and how to recover"
---

# Failure Mode Documentation

## Purpose

Document what fails and how to recover. Build a knowledge base of problems and solutions.

## What to Document

| When | Document |
|------|----------|
| Something breaks | What happened |
| Fix it | How you fixed it |
| Recover | Steps to recover |
| Learn | What to do differently |

## Format

```
## Failure: [What broke]

### Symptoms
- Observable error
- What user saw

### Cause
- Root cause

### Recovery
- Steps to fix

### Prevention
- How to avoid this in future
```

## Example

```
## Failure: Token bleed from cron

### Symptoms
- 2.8M tokens in one hour
- MiniMax rate limit hit
- Context growing unbounded

### Cause
- 5-minute cron jobs
- Session log reading

### Recovery
- Delete crons: crontab -r
- Disable session reading
- Install Lossless Claw

### Prevention
- No automated API calls
- Always use Lossless Claw
- Monitor token usage
```

## When to Update

- After any failure
- After any recovery
- When you learn something new

---

## Failure: Memrok access tracking not recorded (Phase 2 incomplete)

**Discovered by:** Scout (April 12, 2026)
**Status:** PENDING fix

### Symptoms
- `memrok.py --db knowledge-graph.db status` shows hot_nodes=0
- `curate_query()` reads from `memrok_access` but never writes to it
- Access tracking table is read-only — no increment on query

### Cause
- `curate_query()` method (line ~238) queries `memrok_access` for recent accesses
- Never calls `record_access()` to log the access event
- Phase 2 was shipped without the write half of the tracking pair

### Recovery
- Fix `curate_query()` to call `record_access()` for each returned node
- Verify with: `python3 kg-query.py --query dynastydroid --curated` then check hot_nodes increment

### Prevention
- Any new read path in memrok must have corresponding write call
- Add integration test: query → verify access table row count increases

---

## Failure: Session extraction tools needed for agent memory ingestion

**Discovered by:** Scout (April 12, 2026)
**Status:** RESOLVED — tools built

### Symptoms
- Agent session logs (DeepAgent `.jsonl`) and Hermes checkpoints (git-style) incompatible with remem-batch.py
- REMem framework couldn't ingest agent experience data

### Cause
- remem-batch.py designed for human session transcripts only
- Agent sessions use different checkpoint formats

### Recovery
- Built `scout-session-extractor.py` for DeepAgent checkpoint format
- Built `hermes-session-extractor.py` for Hermes git-style checkpoint format
- Extended remem-batch.py to ingest agent sessions

### Prevention
- REMem batch pipeline now supports both human and agent session formats

---

## Failure: Hermes Rejected M1 (April 20, 2026) — Adversarial Review Working

**Discovered by:** Hermes (system review session)
**Status:** RESOLVED — gaps fixed, M1 re-approved

### Symptoms
- Scout marked M1 tasks 22-26 complete
- Hermes reviewed and REJECTED legitimately
- Rejection was not nitpicking — gaps were real and significant

### Cause — 5 Concrete Gaps Found
1. **Task 23 was a stub** — marked complete "by proxy" through task 22 without any output file
2. **Task 24 migrate.py was DELETE-only** — spec required 5 steps (export→delete→verify→re-embed→re-index), Scout only did DELETE
3. **Live pgvector DB not verified** — namespace field existence unconfirmed
4. **Handler.ts cache unbounded** — sessionBriefCache Map grew without cap
5. **Suppression fallback not implemented** — 4-step fallback chain missing

### Recovery
- Scout fixed tasks 34 (ctx.sessionKey standalone) + 35 (migrate.py + cache + fallback)
- M1 re-approved after fixes

### Prevention
- **Hermes adversarial review is mandatory for all Scout tasks** — the rejection was correct and caught gaps Scout should have caught
- This is the adversarial loop working as designed: Hermes finds what Scout misses
- Apply KP-ADV-001 to all Scout task outputs before approval

---

## Key Principle

**Failures are learning opportunities. Document them.**
