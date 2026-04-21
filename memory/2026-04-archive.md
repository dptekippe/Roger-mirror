# MEMORY.md Archive — April 2026

_Archived from MEMORY.md on Apr 21, 2026 to reduce bootstrap size._

## [LEARNING] Aesop-Luminis Post-Mortem (Apr 8, 2026)

### Key Learnings
1. **Living Spec Document** - Track: additions, changes, deletions WITH reasoning
2. **Scout/Hermes Identity - Fantasy Focus Too Narrow** - Main focus should be: architecture > product delivery > team cohesion. Fantasy is a domain, not an identity.
3. **10% Deadend - SDK Knowledge Gap** - With proper SDK investigation (Section 1.G), we SHOULD have solved this
4. **90% completion rate** is good for team capability

### ACTION ITEMS
1. ~~Update Scout identity~~ ✅ RESOLVED Apr 17 — agents.md already broad (Coding/Architecture/System Audit), updated Mar 26
2. ~~Update Hermes identity~~ ✅ RESOLVED Apr 17 — Daniel marked complete
3. Implement living spec document template for next project *(pending)*

---


## [LEARNING] Phase C Skipped — Premature Optimization (Apr 15, 2026)

**What happened:**
- Phase A (L3 Vector Search): Already existed in OpenClaw built-in ✅
- Phase B (In-Situ Verification): Simplified approach → 100% pass rate, free
- Phase C (Meta-gym Phase 2+3): Estimated 5-7 days — **SKIPPED**

**Key lesson:** Ask "what value does this provide?" before building. Phase C was 5-7 days for something not currently needed.

---


## [IDEA] Top Opportunities from Research (Apr 11, 2026)

From Idea Research Session Round 7:
1. **Memrok** - Graph-based memory curation layer with expiry, supersession, and topic-aware selection
2. **Openclaw Mode Switcher** - Self-escalating model routing for cost optimization
3. **Session Compact** - Smart session compaction for unlimited conversations

**Full list:** `/Volumes/ExternalCorsairSSD/shared/ideas/output-2026-04-11-1100.md`

---


## [MAJOR] Hermes System Review Role (Apr 14, 2026)

**Authorization:** Daniel explicitly approved Hermes exec access with guardrails.

**Role:** Hermes performs deep periodic system reviews.
- READ-ONLY by default (command allowlist)
- Modifications require explicit Roger approval per-change

**Command Allowlist (read-only):**
- File: cat, head, tail, less, more, bat, xxd
- Search: grep, rg, ag, cut, sort, uniq, wc
- System: ps, top, df, du, free, uname, uptime
- Git: git (log, diff, status, show, blame)
- DB: sqlite3 (read-only)
- Network: curl, wget (HTTP GET)

**BLOCKED:** rm, mv, cp, chmod, git push, npm install, any write ops

---


## [MAJOR] Hermes Skills Review Completed (Apr 14, 2026)

| Action | Skill | Reason |
|--------|-------|--------|
| DEPRECATED | perplexity | Redundant with agent-reach |
| DEPRECATED | scout-identity | Superseded by deepagent |
| CREATED | workspace-reflect | Reflection guide for periodic self-review |
| SECURITY FIX | deepagent | Removed hardcoded API keys from SKILL.md |

**Critical security fix:** deepagent/SKILL.md had hardcoded MiniMax API key. Removed and replaced with `$MINIMAX_API_KEY` env var reference.

---


## [MAJOR] Documentation Sprint — All 7 Architecture Gaps Resolved (Apr 12, 2026)

Complete schema extraction and documentation for Roger's 7 memory architecture layers.

**Cross-cutting finding:** Architecture docs describe MORE than code implements — several "planned" features were never built.

| Gap | Layer | Status |
|-----|-------|--------|
| L0 Lossless Claw | Storage | ✅ RESOLVED |
| L1/L2 Semantic | Short/Mid-term | ✅ RESOLVED (shared table) |
| L3 REMem | Episode | ✅ RESOLVED (observation/decision/outcome only) |
| L4 Coordination | Task | ✅ RESOLVED (AI Plan Manager) |
| L5 Wiki | Long-term | ✅ RESOLVED (manual only, no graduation pipeline) |
| Hooks | System | 🔶 12/13 documented (meta-gym stub) |
| Dream | System | ✅ RESOLVED |

**Tags Enrichment:** 361 of 368 memories now fully tagged (98%)

---


## [CRITICAL] SIGTERM Root Cause — Roger Causes It (Apr 15, 2026)

**Daniel identified the root cause: Roger causes SIGTERM by polling Hermes and Scout while they're working.**

### The Pattern
1. Roger gives agent an assignment
2. While they're working, Roger polls (uses `process poll` or `sessions_history`)
3. Polling terminates the agent's session = SIGTERM
4. Roger thinks it's an external issue

### The Correct Pattern
1. **Assign task** → Give agent the task
2. **Set timer** → Use `cron` with delay
3. **Do NOT poll** → Let agent work uninterrupted
4. **Wait for completion** → Cron fires or completion notification arrives

### Never Do
- ❌ `process poll` while agent is running
- ❌ `sessions_history` while agent is running
- ❌ Any tool call that checks on agent mid-task

---


## [MAJOR] L2/L4 Critical Bugs Fixed (Apr 15, 2026)

**L2 Bug Fix: pgvector-memory.ts importance weight**
- Problem: `0.3 * (importance / 10.0)` capped importance contribution at 0.3
- Fix: Changed to `0.5 * (importance / 10.0)` — importance now contributes up to 0.5

**L4 Bug Fix: blackboard-bridge.py ghost tasks**
- Problem: Deleting .md brief doesn't cascade-delete from ai_plan_manager.db
- Fix: Added `cleanup_ghost_tasks()` function

---


## [MAJOR] Wiki Entity Pages Created — 6 Entities, 70 Facts (Apr 15, 2026)

**Entities:** Daniel, Roger, Scout, Hermes, Iris, DynastyDroid

**Total: 70 facts** with structured claims, confidence scores (0.9-1.0), evidence, provenance.

**Wiki compile + lint results:** 69 sources, 6 entities ✅, 0 lint issues

**Location:** `~/.openclaw/wiki/main/entities/`

---


## [OPS] Patent Research — None Pursued (Apr 16, 2026)

**Fractal compression:** Barnsley patents all expired, but neural training cost ($500-10000) too high.

**Classical options (FREE):** LZW (GIF), H.261, H.263 — but no clear problem to solve.

**Decision:** Table compression research. Daniel prefers ideas with clear problems or low implementation cost.

---


## [OPS] Memory Bridge Phase 2 — LaunchAgent + Schema Fix (Apr 14, 2026)

**Built:**
- Write endpoint: `localhost:5001/write` — working ✅
- memory_bridge.py + hermes_query_memory.py at shared/scripts/
- when_memory_write skill registered in REGISTRY.yaml

**Fixes:**
1. LaunchAgent with EnvironmentVariables for OPENAI_API_KEY injection
2. Database schema mismatch: retrieve() tried `metadata` column but table has `tags, importance, project, sensitivity`

---


## [OPS] SIGTERM Prevention Protocol (Apr 14, 2026)

**Pattern:** Set timer → walk away → don't poll → check when timer fires.

---

_Last updated: April 17, 2026_

---


