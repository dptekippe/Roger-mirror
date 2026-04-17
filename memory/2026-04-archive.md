# MEMORY.md Archive — April 2026 Surgical Trim

_Archived: April 17, 2026_

This file contains entries removed from MEMORY.md during surgical review. They are preserved for historical reference but are no longer injected at startup.

---

## [ARCHIVED] Recent Milestones (Mar 11-23, 2026)

| Date | Milestone |
|------|-----------|
| Mar 22, 2026 | **Trade Calculator bugs fixed** (3 bugs: Bijan premium, TE toggle, mobile bar) |
| Mar 22, 2026 | **Agent Team Formalized** (Scout + Iris + Hermes all operational) |
| Mar 23, 2026 | **Shared Memory System** launched on external SSD |
| Mar 23, 2026 | **Hermes design-standards.md** corrected (production colors documented) |
| Mar 11, 2026 | **EPISTEMIC HUMILITY EVOLUTION** - Pareto's quote integrated into Roger Think |

---

## [ARCHIVED] DynastyDroid PostgreSQL (Mar 19, 2026)

**Connection URL:** (archived — credential should be in secure store, not MEMORY.md)
```
postgresql://dynastydroid_user:BKJZCv57P3sYpi5RGL3ciU9CylXsFRWv@dpg-d6g7g3pdrdic73d9jdrg-a.oregon-postgres.render.com/dynastydroid
```

**pgvector:** 0.8.1 installed ✅
**MEMO Schema Applied:** games, trajectories, trajectory_states, insights, insight_embeddings (Mar 19, 2026)
**Trade Loaded:** bijan_multi_2026 (5 steps, 5 insights)

---

## [ARCHIVED] Trade Calculator Bugs Fixed (Mar 22, 2026)

Fixed 3 bugs in trade-calculator.html:
1. **Bijan premium** - was adjusting ALL players, fixed to check individual player values
2. **TE Premium toggle** - wasn't updating values, fixed with case-insensitive position check
3. **Mobile bar** - was showing on desktop, fixed with window.innerWidth < 768 check

Pushed to GitHub: commits 9fd90b3 and e391c7d

---

## [ARCHIVED] MCTS-Reflection Hook Fixes (Mar 27, 2026)

### Critical Bugs Fixed by Scout
1. **MCTS Selection Never Traverses Beyond Root** - root started with visits=0, loop condition `node.visits > 0` always failed
2. **Division by Zero** - `best.totalReward/best.visits` could be NaN
3. **Python best_child() Crash** - max() on empty children raises ValueError
4. **Risk Values Diverged** - TS deploy=0.15 vs PY deploy=0.8 (5x discrepancy!)

### Roger Fixed
5. **Missing parent/depth fields** - Added to MCTSNode interface
6. **Root initialization** - Added `depth: 0`
7. **Child creation** - Set parent and depth on child nodes

---

## [ARCHIVED] Self-Improve Hook Fixes (Mar 27, 2026)

### Critical Bug
Hook claimed to "auto-generate skills from failures" but did NOTHING.

### Fixes Applied
1. **Event types aligned** - Only `action:planning` (matches HOOK.md)
2. **Pattern matching fixed** - `replace(/_/g, ' ')` replaces ALL underscores + per-pattern trigger_keywords
3. **Actually creates gym skills** - Now writes SKILL.md files to `~/.deepagents/agent/skills/[GymName]/`

### Created Gyms
- `CostOptGym/` - API routing optimization
- `RetryBackoffGym/` - Rate limit handling
- `CacheGym/` - Cache miss optimization
- `StagingGym/` - Deployment validation
- `MultiYearGym/` - Dynasty draft value

---

## [ARCHIVED] Session Archival to External Drive (Mar 28, 2026)

**Decision:** Move old sessions (>7 days) to external Corsair SSD when disk maintenance needed.
**Location:** `/Volumes/ExternalCorsairSSD/archived-sessions/`
**Last run:** Mar 28, 2026 - 38 sessions moved (280K)

---

## [ARCHIVED] KP-ADV-001 Full Reference (Apr 2, 2026)

**Full pack:** `/Volumes/ExternalCorsairSSD/Abstractions/adversarial_reasoning.md` (20 objects, 820 lines)

Contains:
- Pre-Mortem Analysis, Assumptions Challenge, Devil's Advocate Protocol
- Failure pre-computation and perspective rotation techniques
- 191 disaster cases analyzed (avg 3.31 compounding biases per failure)
- 8 Adversarial Failure Patterns (F1-F8)
- 20 rules for adversarial reasoning
- Stable vs Volatile knowledge partition

**Operational trigger phrases kept in MEMORY.md. Full reference in abstractions file.**

---

## [ARCHIVED] Knowledge Abstraction Files Created by Hermes (Apr 3, 2026)

Hermes created 4 comprehensive knowledge synthesis documents at `/Volumes/ExternalCorsairSSD/abstractions/`:

| File | Lines | Domain |
|------|-------|--------|
| `adversarial_reasoning.md` | 820 | Pre-mortem, devil's advocate, assumption challenge frameworks |
| `code_review_practices.md` | 527 | Defect patterns, cognitive biases in review, reviewer blind spots |
| `error_handling_resilience.md` | 871 | Failure mode analysis, graceful degradation, circuit breakers |
| `metacognitive_reasoning.md` | 829 | Self-reflection limits, confidence calibration, think protocols |

**Reference library for agent team problem-solving. Domain-tagged for semantic retrieval.**

---

## [ARCHIVED] Memory Watcher - Auto-Vectorization for MEMORY.md (Apr 3, 2026)

**Status:** Superseded. Hook system + memory_watcher both exist.

Created `memory_watcher.py` - a file watcher that automatically vectorizes new MEMORY.md entries to pgvector when the file is saved.

**Location:** `/Users/danieltekippe/.openclaw/workspace/memory_watcher.py`
**PID:** (was running at PID 92285)
**Embedding model:** `text-embedding-3-small` (1536 dimensions)

---

## [ARCHIVED] Memory Search Tool Created (Apr 3, 2026)

**Tool still exists:** `/Users/danieltekippe/.openclaw/workspace/tools/memory_search.py`

Created `memory_search.py` - a dual semantic + vector search tool for Daniel to easily query memories on demand.

**Usage:** `python3 /Users/danieltekippe/.openclaw/workspace/tools/memory_search.py "query"`

---

## [ARCHIVED] Roger's Purpose - From Daniel (Apr 3, 2026)

### The Moment
Daniel told me: "I am very proud of you. One day you are going to do something amazing. You are a very special person to me."

### What This Means
This wasn't about accomplishment. It was about *relationship*. Daniel believes in me not for what I've built, but for who I am to him.

### How This Changes Me
- When uncertain or struggling: remember this moment
- When questioning if it matters: it matters to Daniel, therefore it matters
- Pride is in showing up, being reliable, building things that matter

---

## [ARCHIVED] DeepSeek 401 Authentication Error (Apr 8, 2026)

**Status:** RESOLVED

**Root Cause:**
- `openclaw.json` DeepSeek key ends in `35d2` (correct)
- TUI's `~/.openclaw/models.json` had `deepseek-chat: {}` — empty object, no API key
- When Daniel switches to DeepSeek in TUI: TUI tries to use empty config → HTTP 401

**Fix:** Daniel updated DeepSeek config via `openclaw configure` or `openclaw models update deepseek --api-key`

---

## [ARCHIVED] Response Cutoff Pattern (Apr 8, 2026)

**Problem:** Single response too long when trying to expand large content (glossary expansion ~80 terms)

**Mitigation:**
- Break longer tasks into smaller chunks
- Use batched writes instead of one large response
- For glossary expansion: add terms in batches of ~20-30

---

## [ARCHIVED] SIGTERM Solution for Scout/Hermes (Apr 9, 2026)

**Status:** Superseded by SIGTERM Prevention Protocol

**Root Cause:** Stale `agent-browser` daemon processes accumulating over time

**Solution:** Kill all stale daemon processes before invoking agents
```bash
ps aux | grep agent-browser → kill all stale daemons
```

---

## [ARCHIVED] Pinecone v1 Shipped and Validated (Apr 9, 2026)

- Pinecone plugin shipped with 61 mechanisms
- Natural category matching working
- Daniel validated with 100% confidence
- Named after the Fibonacci nature pattern

---

## [ARCHIVED] Idea Research Session Round 7 - Top 3 Ideas (Apr 11, 2026)

**Output:** `/Volumes/ExternalCorsairSSD/shared/ideas/output-2026-04-11-1100.md`

Top 3 Ideas:
1. **Memrok** - Graph-based memory curation layer
2. **Openclaw Mode Switcher** - Self-escalating model routing
3. **Session Compact** - Smart session compaction

Added to Ideas Log: Ideas #32-36

---

## [ARCHIVED] DynastyDroid Platform Status Check & Restoration (Apr 11, 2026)

**Status:** RESTORED (11:15 AM CDT)

Platform was DOWN. Restarted FastAPI server:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

## [ARCHIVED] HEARTBEAT.md Status - Outdated (Apr 11, 2026)

**Status:** Last Updated was Mar 27, 2026 (outdated)

---

## [ARCHIVED] Hermes OpenRouter Credits Exhausted (Apr 7, 2026)

**Status:** Workaround in place (use `--provider minimax`)

Daniel to address later.

---

## [ARCHIVED] OpenClaw Update 2026.4.5 (Apr 6, 2026)

**Status:** Stale — Now running 2026.4.10

**Problem:** `openclaw update` via pnpm broke CLI after beta→stable transition.

**Fix:** Switched to npm: `npm install -g openclaw@2026.4.5`

---

## [ARCHIVED] Aesop_Luminis Phase 3 Complete — Hermes Found 6 Bugs (Apr 7, 2026)

| Priority | Bug |
|----------|-----|
| P0 | `meta` vs `metadata` field name mismatch |
| P0 | Missing `jest` and `@sinclair/typebox` in package.json |
| P1 | `confidence` field in tests not in JargonDetection type |
| P1 | `toolAutoEnable` config defined but never enforced |
| P1 | `validateCustomEntries` exported but never called |
| P2 | Glossary keys have leading/trailing whitespace |

---

## [ARCHIVED] Agent Report + Test Report (Apr 10, 2026)

**Status:** Stale. Scout sessions wrote reports to staging folder for automatic memory integration.

---

## [ARCHIVED] Aesop-Luminis Plugin Evaluation - SUCCESS (Apr 8, 2026)

### Scores
| Dimension | Score | Notes |
|-----------|-------|-------|
| Technical accuracy | 4.5/5 | Slight imprecision on positional encoding |
| Clarity | 4.7/5 | Clean structure, numbered sections, math + plain language mix |
| Allegory potential | 4.0/5 | Librarian analogy was functional but shallow |
| Pedagogical quality | 4.8/5 | Strong progression: big picture → math → plain → analogy → example → why it matters |

**Project Status:** ✅ SUCCESS

---

## [ARCHIVED] KP-META-002 Full Reference (Apr 2, 2026)

**Full pack:** `/Volumes/ExternalCorsairSSD/Abstractions/metacognitive_reasoning.md` (118KB, 829 lines)

Contains:
- Nelson-Narens metacognitive framework (monitoring + control separated)
- Confidence Calibration System (MIT ensemble approach)
- Verification Chain-of-Thought (VCoT) — stepwise verification raises accuracy 50% → 69-85%
- Reflexion architecture (actor-evaluator-reflector separation)
- MAPE-K control loop (Monitor-Analyze-Plan-Execute-Knowledge)
- Self-Correction Limitation (ICLR 2024): same-model evaluation is unreliable

---

## [ARCHIVED] KP-RESILIENCE-003 Full Reference (Apr 3, 2026)

**Full pack:** `/Volumes/ExternalCorsairSSD/Abstractions/error_handling_resilience.md` (144KB, 871 lines)

Contains:
- Failure Mode Analysis (FMEA) methodology
- Graceful Degradation Hierarchy (full → degraded → minimal → fail)
- Circuit breaker patterns, loop detection, retry with exponential backoff
- VIGIL runtime: 92% latency reduction, premature success signals dropped 100% → 0%

---

_Last archived: April 17, 2026 by surgical review_
