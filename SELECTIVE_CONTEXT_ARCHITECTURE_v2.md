# Selective Context Architecture — SPEC v1.4

**Date:** April 20, 2026
**Status:** P0/P1 issues fixed (April 20 15:09 CDT)
**Pending:** ctx.sessionKey verification, LCM flag verification, pgvector migration, futureself hook duplicate (all: Scout)
**Problem:** 93% of token spend is context overhead, not generation. Context grows without bound as conversation history accumulates.

> **Phase 0 verification (April 20):** MiniMax billing data confirmed: **99.4% context overhead** (155:1 input/output ratio, 95% of spend on context tokens). Problem is real and larger than stated.

> **v1.2 revision notes:**
> - Added suppression threshold design (Item 2 — FATAL gap resolved)
> - Added selection criteria framework (Item 3 — resolved)
> - Added Alternative 3 evaluation plan (Item 4 — A/B test)
> - Added ownership + sequence (Item 5 — resolved)
> - Updated fallback chain to handle low-confidence retrieval (not just pgvector unavailability)
> - Supersedes: v1.0, v1.1

> **Revision notes (v1.2):**
> - v1.3 notes (April 20 15:25 CDT):
>   - P0: Retrieval pipeline "top 8" → "top rerankTopK (3)" (was contradicting config)
>   - P0: pgvector migration DELETE uses JSONB query (namespace column doesn't exist)
>   - P1: A/B suppression log sink specified (JSONL file + Hermes reads it)
>   - P2: v1.3 notes pulled out of v1.1 nesting
>   - P2: futureself hook ambiguity added to Scout verification list
> - Supersedes: v1.0, v1.1

> **Revision notes (v1.1):**
> - Clarified `minRelevanceScore` semantics (was self-contradictory)
> - Collapsed `__selective_retrieval_done__` / `selectiveMode` flag discussion — confirmed non-viable; pragmatic approach promoted to primary recommendation
> - Reconciled `active-memory` plugin turn count (1) with Layer 3's sliding window target (last 5)
> - Open Questions renumbered (1-6, from v1.0/v1.1 additions noted)
> - Updated model reference from M2.7 → M2.5 to match current `models.json`
> - Recalculated cost estimates to reflect M2.5 pricing
> - Added size target to Phase 4
> - Merged Open Question #3 (LCM interaction) into Session Boundary section where it was already answered
> - Aligned desired injection order diagram with pragmatic (no-skip) approach

---

## Background <!-- id: background -->

### Current Architecture

```
Every LLM call:
├── System prompt (~1KB)           [static, ok]
├── Bootstrap files (SOUL+MEMORY)  [was 63KB, now ~45KB — overhead]
├── Pre-action hook retrieval       [EXISTS — memory-pre-action hook]
│   └── Queries pgvector → injects top 5 relevant memories
├── active-memory plugin            [EXISTS — recent mode, lean: 1 user + 1 assistant turn]
└── Conversation history            [GROWS — primary cost driver]
```

The `memory-pre-action` hook already does selective retrieval. The problem is:

1. **Bootstrap files still fully injected** on top of hook retrieval — every single call
2. **Full conversation history** sent every turn (not truncated until overflow)
3. **Bootstrap budget (20KB/file)** just truncates, doesn't selectively retrieve
4. **No session-level context scoping** — every turn gets everything

### What We Want

```
Session start:
├── Lean identity (core SOUL only, ~3KB)
└── Key memories from pgvector (top 10, ~2KB)

Each message:
├── User message
├── Relevant memories from pgvector (< 2KB)
├── Relevant SOUL sections (RAG-retrieved, < 3KB)
└── Recent turns only (last 5, < 5KB)
```

**Target:** 10-15KB per message vs current 100KB+
**Result:** 85-90% reduction in context overhead

---

## Architecture: Three-Layer Selective Context

### Layer 1: Session Start Injection (once per session)

**What:** On session start, inject lean identity + key memories.

**How:** Modify a `session:bootstrap` hook (or use existing startup hooks) to:
1. Query pgvector for: identity facts, current goals, active projects
2. Query wiki for: active context entities
3. Inject synthesized "you are Roger, currently working on X" context

**Size target:** < 5KB

**Implementation:**
- Create `selective-bootstrap` hook
- Fires on `gateway:startup` or `agent:bootstrap`
- Queries pgvector with session key + "identity goals active"
- Produces a lean "session brief" injected as first system message

---

### Layer 2: Per-Message Retrieval (every message)

**What:** Replace full SOUL/MEMORY injection with RAG-retrieved snippets.

**How:** Enhance the existing `memory-pre-action` hook:

**Current behavior:**
```
query pgvector → inject top 5 memories → DONE
(still sends full SOUL + MEMORY on top)
```

**New behavior:**
```
1. Parse incoming message → extract query
2. Concurrent RAG queries:
   ├── pgvector: "relevant memories, decisions, facts" (topK=5)
   ├── pgvector: "relevant SOUL sections" (topK=3, tags=[soul])
   └── pgvector: "relevant current project context" (topK=2)
3. Synthesize into single context block:
   [RELEVANT CONTEXT — retrieved, not cached]
   Memories: ...
   Identity/Goals: ...
   Project State: ...
4. PREPEND to messages[] (before bootstrap injection)
```

**Why not skip bootstrap injection entirely:**
OpenClaw's `bootstrap-budget` and `agent-runner` are closed-source core files — we cannot conditionally suppress their injection via a hook flag. The pragmatic approach: make the RAG-retrieved block so precise and well-positioned that the model attends to it over the stale bootstrap content. This still eliminates the history cost driver (Layer 3) and adds high-signal retrieval on top of bootstrap, at modest redundancy cost.

**Size target:** < 8KB per message (retrieval block only)

---

### Layer 3: Conversation History Management

**What:** Sliding window instead of full history.

**Note on active-memory plugin:** The current `active-memory` plugin is configured lean (`recentUserTurns=1, recentAssistantTurns=1`). Layer 3 targets 5 full turns in the sliding window — this is handled in `memory-pre-action` by explicitly injecting the last 5 turns as retrieved context, not by changing the plugin config. The plugin provides the most recent turn as a baseline; the hook supplements with the prior 4.

**Two modes (configurable):**

**Mode A — Sliding Window (simpler):**
- Keep only last N messages in context (target: 5 full turns)
- Older messages: query pgvector for "what was decided/mentioned in this conversation around X"
- Inject relevant past turns as retrieved context, not full history

**Mode B — Semantic History Retrieval (better):**
- On each message, query pgvector for semantically relevant past turns
- Full conversation stored in pgvector with `session_id` and `turn_index` tags
- Retrieval returns specific turns, not full history

**Recommended:** Mode A for immediate implementation, Mode B as Phase 2.

---

## Key Mechanism: Pragmatic Injection Strategy

Since OpenClaw core injection order is not modifiable, the strategy is layered augmentation rather than replacement:

**Current (problem):**
```
Bootstrap files (SOUL, MEMORY, etc.) → injected every turn unconditionally
Full conversation history            → injected every turn, grows unbounded
```

**Target (pragmatic):**
```
Bootstrap files      → still injected every call (can't suppress — accept the cost)
Selective retrieval  → prepended via hook (high-signal, model attends to this first)
Conversation history → capped at last 5 turns via Layer 3
```

**Why this still wins:** The bulk of the current cost is unbounded conversation history. Bootstrap files at ~45KB are a fixed overhead. Capping history from 50KB+ → ~5KB is the primary saving. The retrieval layer is additive signal on top.

**Bootstrap budget tuning (crude but available):**
```yaml
agents:
  defaults:
    bootstrapMaxChars: 2000      # was 20000
    bootstrapTotalMaxChars: 5000 # was ~50KB
```
This is a blunt truncation, not selective retrieval. Use only if bootstrap overhead is still unacceptable after Phases 1-3 are implemented. The retrieval layer is always preferred.

---

## Implementation Phases

### Phase 1: Lean Session Bootstrap (Scout task) <!-- id: phase-1-bootstrap -->
**Goal:** Session start injects lean identity instead of full SOUL/MEMORY.

**Files to create:**
- `hooks/selective-bootstrap/handler.ts` — new hook

**Files to modify:**
- `openclaw.json` — add `selective-bootstrap` to hooks list

**What it does:**
1. Fires on `agent:bootstrap`
2. Queries pgvector for: identity facts, active goals, current project state
3. Queries wiki for: active entities
4. Writes lean session brief (~3KB) to `ctx.messages` as first system message
5. Logs: "Selective bootstrap: injected X memories, Y wiki facts"

**Size target:** < 3KB
**Effort:** ~2 hours Scout

---

### Phase 2: Enhanced Per-Message Retrieval (Scout task) <!-- id: phase-2-retrieval -->
**Goal:** `memory-pre-action` hook retrieves SOUL sections in addition to memories.

**Files to modify:**
- `hooks/memory-pre-action/handler.ts`
- `hooks/_shared/pgvector-memory.ts` (may need new query functions)

**What it does:**
1. Current: queries pgvector for memories only
2. New: also queries for SOUL-relevant sections (tagged `soul_context`)
3. New: queries for relevant past turns (tagged `turn`, filtered by `session_id`)
4. Inject as combined `[RELEVANT CONTEXT]` block at top of messages
5. Add tags to pgvector entries: `soul_context`, `identity`, `project`, `decision`

**Size target:** < 5KB per retrieval
**Effort:** ~4 hours Scout

**⚠️ pgvector migration — MANDATORY before Phase 2:** <!-- id: pgvector-migration -->
Existing SOUL.md and MEMORY.md entries in pgvector are whole-document embeddings generated with a different embedding model (not `text-embedding-3-small`). Cosine similarity is mathematically invalid across mixed embedding models.

Migration plan:
1. Export all existing pgvector entry IDs + metadata
2. DELETE all existing whole-document entries from pgvector
    ⚠️ Schema check REQUIRED before running — verify namespace column/field exists:
    ```sql
    -- First: verify metadata structure
    SELECT DISTINCT metadata->>'namespace' FROM memories LIMIT 10;
    -- If namespace is in metadata JSONB:
    DELETE FROM memories WHERE metadata->>'namespace' = 'roger';
    -- If no namespace field exists: DELETE FROM memories; (wipes all — verify first)
    ```
3. Re-embed SOUL.md (chunked by section) and MEMORY.md (chunked by entry) with `text-embedding-3-small`
4. Re-index conversation history chunks with `text-embedding-3-small`
5. Verify: confirm no old-model vectors remain
    ```sql
    SELECT COUNT(*) FROM memories;  -- should be 0 after wipe
    ```

**Do NOT coexist old + new entries.** Whole-document entries will outscore chunked entries on broad queries (more text = higher overlap), defeating the purpose of chunking.

---

### Phase 3: Sliding Window History (Scout task) <!-- id: phase-3-sliding-window -->
**Goal:** Limit conversation history to last N turns, RAG-retrieve older context.

**Files to modify:**
- `hooks/memory-pre-action/handler.ts` (add history management)

**What it does:**
1. Track turn count in session metadata
2. At N>20 turns: query pgvector for "what happened in conversation about X"
3. Replace older turns with RAG-retrieved summaries
4. Kept turns: last 5 (full) + N-5 retrieved summaries

**Note:** The `active-memory` plugin already contributes the most recent turn. The hook should check for overlap and deduplicate before injecting its own turn window.

**Size target:** < 10KB total per message (down from 50KB+)
**Effort:** ~6 hours Scout

---

### Phase 4: Workspace Semantic Search (Scout task) <!-- id: phase-4-workspace-search -->
**Goal:** RAG-retrieve from workspace files instead of loading all of them.

**Files to modify:**
- `hooks/memory-pre-action/handler.ts`
- Add workspace file indexing to pgvector

**What it does:**
1. Index key workspace files into pgvector (DYNASTY_TRADES_PLAN, ARCHITECTURE_SUB_AGENTS, etc.)
2. On task context: query for relevant workspace sections
3. Inject relevant sections instead of expecting model to attend to all files

**Size target:** < 3KB per workspace retrieval (retrieved sections only)
**Effort:** ~8 hours Scout

---

## Configuration Changes

### openclaw.json additions
```json
{
  "agents": {
    "defaults": {
      "selectiveContext": {
        "enabled": true,
        "sessionBootstrap": {
          "maxChars": 3000,
          "memoryTopK": 10
        },
        "perMessageRetrieval": {
          "maxChars": 5000,
          "memoryTopK": 5,
          "soulTopK": 3
        },
        "historyWindow": {
          "maxTurns": 20,
          "slidingWindow": 5
        }
      }
    }
  }
}
```

### New hook registration
```json
{
  "hooks": {
    "entries": {
      "selective-bootstrap": {
        "enabled": true,
        "events": ["agent:bootstrap", "gateway:startup"]
      }
    }
  }
}
```

---

## pgvector Schema Additions

```sql
-- Verify existing schema before running:
-- SELECT column_name FROM information_schema.columns WHERE table_name = 'memories';

-- Add tag support for selective retrieval
ALTER TABLE memories ADD COLUMN IF NOT EXISTS tags TEXT[] DEFAULT '{}';
ALTER TABLE memories ADD COLUMN IF NOT EXISTS source_file VARCHAR(255);
ALTER TABLE memories ADD COLUMN IF NOT EXISTS chunk_index INTEGER;  -- position in original document

-- Index for fast tag filtering
CREATE INDEX IF NOT EXISTS memories_tags_idx ON memories USING GIN(tags);

-- Tag existing entries (adjust LIKE patterns to match your actual content)
UPDATE memories SET tags = ARRAY['soul_context'] WHERE content LIKE '%SOUL.md%';
UPDATE memories SET tags = ARRAY['identity']    WHERE content LIKE '%Core Identity%';
UPDATE memories SET tags = ARRAY['decision']    WHERE content LIKE '%DECISION%';
UPDATE memories SET tags = ARRAY['project']     WHERE content LIKE '%DynastyDroid%';
```

---

## Expected Outcomes

| Metric | Current | After Phase 1-2 | After Phase 3 |
|--------|---------|------------------|---------------|
| Context per message | ~100KB | ~55KB | ~12KB |
| Token cost per session (4hr) | ~$4.80 | ~$2.00 | ~$0.65 |
| Cache-read efficiency | 7.5M/80K | 4M/80K | 1M/80K |
| Input-to-output ratio | 153:1 | 62:1 | 12:1 |

> **Note:** Phases 1-2 cost estimates revised from v1.0. Since bootstrap files cannot be suppressed via hook flag, the Phase 1-2 savings are smaller than originally projected — the main win is better signal quality, not token reduction. Phase 3 (history cap) is where the bulk of cost reduction happens. Model pricing based on MiniMax-M2.5 (current primary in `models.json`).

---

## Open Questions <!-- id: open-questions-phase-1 -->

1. **Should we index SOUL.md and MEMORY.md into pgvector with section-level granularity?** Currently they're stored as whole entries. For precise retrieval, section-level chunking is recommended (each `##` heading = one chunk for SOUL, each `## [...]` entry = one chunk for MEMORY).

2. **Session segmentation vs RAG history:** Is restarting sessions every 30 minutes simpler than building sliding window history? This is essentially free — just a practice discipline. Recommended: use the 30-min inactivity boundary as the primary session reset, and build sliding window as a safety net for long active sessions.

3. **Hook deduplication with active-memory plugin:** The `active-memory` plugin contributes the most recent turn independently. The `memory-pre-action` hook's sliding window will overlap on turn N. Ensure Phase 3 implementation checks `ctx.messages` for already-injected turns before appending.

---

## Immediate Action (This Week)

1. **Today:** Scout implements Phase 1 (lean session bootstrap)
2. **This week:** Scout implements Phase 2 (enhanced retrieval)
3. **Next week:** Scout implements Phase 3 (sliding window)
4. **Ongoing:** Monitor token usage via MiniMax dashboard

---

## Critical Engineering Details

### 1. Context Injection Order (Cache Hit Preservation)

The order below is intentional and critical for MiniMax's cache to function efficiently. **Static content first, dynamic last.**

```
EVERY LLM CALL — exact order:

[1] System prompt                  (~1KB)   [STATIC — computed once, cached every call]
    └── OpenClaw core, never changes between calls

[2] Tool schemas                   (~2KB)   [STATIC — cached, regenerated only when tools change]
    └── read, write, exec, browser, subagents, sessions, message, etc.

[3] Bootstrap files (SOUL+MEMORY)  (~45KB)  [SEMI-STATIC — cached at session start]
    └── Only re-cached when files change on disk (hourly or on explicit write)
    └── Currently: full injection every call (unavoidable — OpenClaw core)
    └── Mitigation: bootstrap budget tuning (crude) or accept as fixed overhead

[4] Selective retrieval block      (~5KB)   [DYNAMIC — computed every call, NOT cached]
    └── RAG from pgvector, injected by memory-pre-action hook
    └── NEW: includes SOUL sections + project context + relevant past turns

[5] Recent conversation history    (~3KB)   [DYNAMIC — changes every turn]
    └── Last 5 turns (user + assistant)  ← TARGET after Phase 3
    └── Currently: ALL history (unbounded) ← PRIMARY COST DRIVER

[6] Current user message           (~0.5KB) [UNIQUE — never cached]

───────────────────────────────────────────────────────
Total per call (target, Phase 3):           ~56KB
Total per call (today):                     ~100KB+
```

**Why this order maximizes cache hits:**
- Slots [1] and [2] are identical every call → 100% cache hit rate
- Slot [3] changes only when bootstrap files change → ~99% cache hit rate
- Slots [4]-[6] are unique per call → 0% cache hit (correct, these can't be cached)

**The critical failure mode we're fixing:**
Current architecture sends slots [1]-[6] PLUS the full conversation history in slot [5] (all prior turns, not just last 5). This is what causes 100KB+ per-call size.

**OpenClaw's current injection order (inferred from hook lifecycle):**
```
1. System prompt
2. Tool schemas
3. Bootstrap files (SOUL, MEMORY, etc.) ← re-sent every call, cannot suppress
4. active-memory plugin (1 user + 1 assistant turn)
5. Pre-action hooks (memory-pre-action injects here)
6. Conversation history (all turns, unbounded) ← PRIMARY PROBLEM
7. Current message
```

**Target injection order (achievable with Phase 2-3):**
```
1. System prompt
2. Tool schemas
3. Bootstrap files ← still injected (accept as fixed overhead)
4. active-memory plugin (1 turn, as-is)
5. [ENHANCED] memory-pre-action: SOUL + memories + project + recent turn window
6. Conversation history — CAPPED at last 5 turns (Phase 3)
7. Current message
```

---

### 2. pgvector Retrieval Strategy <!-- id: pgvector-retrieval-strategy -->

**Embedding model:**
```typescript
// CONFIRMED: text-embedding-3-small via OpenAI API
// Source: hooks/_shared/pgvector-memory.ts getEmbedding() — hard-coded, not configurable
// NOT MiniMax native — MiniMax-M2.7 uses OpenAI-compatible API for embeddings
// Dimension: 1536 (ada-002 compatible — matches existing pgvector schema vector(1536))
//
// ⚠️ MIGRATION REQUIRED BEFORE PHASE 2:
// All existing pgvector entries were embedded with a different model.
// Before Phase 2 deployment: delete all existing whole-document entries from pgvector,
// then re-embed with text-embedding-3-small. Cosine similarity across mixed embedding
// models is mathematically invalid. Migration is mandatory — see Phase 2 section.

interface RetrievalConfig {
  embeddingModel: 'text-embedding-3-small';  // locked — do not change
  similarityThreshold: number;  // 0.65 — minimum cosine similarity to include a chunk
  minRelevanceScore: number;   // 0.50 — composite score floor after reranking
  candidatePoolSize: number;    // 8 — candidate pool BEFORE reranking (rerankTopK < candidatePoolSize)
  chunkSize: number;            // 512 — tokens per chunk
  chunkOverlap: number;        // 64 — overlap between chunks for context continuity
  rerankTopK: number;          // 3 — FINAL chunks injected into context (after reranking)
}

const defaultConfig: RetrievalConfig = {
  embeddingModel: 'text-embedding-3-small',
  similarityThreshold: 0.65,
  minRelevanceScore: 0.50,
  candidatePoolSize: 8,   // 8 candidates → reranked → top 3 injected
  chunkSize: 512,
  chunkOverlap: 64,
  rerankTopK: 3,         // config value used by hook, not decorative
};
```

**Chunking strategy:**
- Chunk size: 512 tokens — balances granularity vs coverage
- Chunk overlap: 64 tokens — ensures context continuity at chunk boundaries
- SOUL.md: chunked by section (each `##` heading = one chunk)
- MEMORY.md: chunked by entry (each `## [...]` = one chunk)
- Conversation history: chunked by turn pair (user + assistant = 1 chunk)

**Query construction:**
```typescript
// For user message: "fix the trade calculator endpoint"
// Generate 3 query variants for robust retrieval:

const queries = [
  "fix trade calculator endpoint bug",
  "DynastyDroid API endpoint error",
  "trade calculator code problem"
];

// Concurrent retrieval, merge results, deduplicate by chunk_id
// Final ranking: semantic_similarity × recency_boost × importance_score
```

**Retrieval pipeline:**
```
1. Embed user message → query_vector
2. Vector similarity search in pgvector (topK=50)
3. Filter by similarityThreshold (0.65)
4. Rerank top 20 by: 0.5×similarity + 0.3×recency + 0.2×importance
5. Discard chunks with composite score < minRelevanceScore (0.50)
6. Select top rerankTopK (3), truncate to maxChars budget (5KB)
7. Inject as [RELEVANT CONTEXT] block
```

**Current pgvector schema (from memory.py):**
```sql
-- Existing schema (do not re-create):
CREATE TABLE IF NOT EXISTS memories (
  id UUID PRIMARY KEY,
  content TEXT NOT NULL,
  embedding vector(1536),
  metadata JSONB,
  memory_type VARCHAR(50),
  importance INTEGER DEFAULT 5,
  created_at TIMESTAMP DEFAULT NOW(),
  last_accessed TIMESTAMP DEFAULT NOW()
);

-- New columns to add (see pgvector Schema Additions section above):
-- tags TEXT[], source_file VARCHAR(255), chunk_index INTEGER
```

---

### 3. Session Boundary Definition

**What defines a session boundary:**

A session is a single continuous conversation with shared context. The following trigger a **new session** (context reset):

| Trigger | Reason | cache-create cost |
|---------|--------|-------------------|
| Inactivity > 30 minutes | Conversation context likely stale | HIGH — new cache-create |
| Explicit `/new` or `/restart` command | User wants fresh context | HIGH — intentional |
| Manual session termination | Admin or cron action | HIGH — intentional |
| Crash/recovery | Context may be corrupted | MEDIUM — unavoidable |
| Token budget exceeded | Context window full | MEDIUM — forced |
| Day boundary (midnight CDT) | Time-based context reset | LOW — predictable |

**What does NOT trigger a new session:**

| Condition | Reason |
|-----------|--------|
| Turn count > N | Use sliding window, not session restart |
| Brief pause (< 30 min) | Context still valid |
| Channel switch (TUI → Matrix) | Same conversation, different surface |
| LCM compaction | Compaction preserves continuity |

**LCM interaction and coordination:**

The lossless-claw engine handles conversation history compaction independently of the selective retrieval layer. These must be coordinated to avoid double-processing the same turns:

```
Session continues (compact history) when:
  turn_count % 20 == 0 → LCM summarizes oldest turns → injects summary
  turn_count % 50 == 0 → LCM deep-compacts → smaller summary

Session boundary triggered when:
  inactivity > 30 min OR explicit new_session signal
```

**Coordination rule:** If LCM has already compacted turns N-20 through N, the sliding window hook (Phase 3) should treat LCM summaries as already-retrieved context and not attempt to re-query those turns from pgvector. Check `ctx.lcmCompacted` (or equivalent flag) before injecting turn history. Verify the exact flag name in the lossless-claw plugin source.

**cache-create cost management:**
Every new session = new cache-create on first message. At MiniMax-M2.5 cache-write rates, a 45KB bootstrap creates a new cache on first call. Subsequent calls in that session read from cache at the lower cache-read rate.

**Recommendation:** Session restart discipline is the cheapest lever:
- Pro: Full context reset, maximum cache efficiency on fresh context
- Con: Loss of in-progress context, discontinuity for multi-task sessions
- Decision: Use 30-min inactivity rule as primary boundary; Phase 3 sliding window handles long active sessions

---

### 4. OpenClaw Hook Insertion Points

**Hook execution order (confirmed from gateway logs + hook source):**

```
1. [gateway:startup]           → boot-md hook
2. [agent:bootstrap]           → bootstrap-extra-files hook
                               → selective-bootstrap hook  ← NEW (Phase 1)
3. [message:preprocessed]      → memory-pre-action hook ← PRIMARY RETRIEVAL (enhance Phase 2-3)
                               → gate-orchestrator hook
                               → self-improve hook
                               → meta-gym hook
                               → biascheck-gym hook
                               → doubttrigger-gym hook
                               → hook-effectiveness hook
                               → decision-ledger hook
                               → scout-veto hook
                               → mcts-reflection hook
                               → memory-write hook
                               → Aesop Luminis hook
4. [after_model_response]      → echochamber hook
                               → futureself hook (before_action)
5. [before_action]             → futureself hook ⚠️ UNRESOLVED: appears at both step 4 and 5 — Scout to verify if this is a duplicate registration or correct (checked: hook registry ambiguous)
6. [action:complete]           → (no standard hooks observed)
7. [session:end]               → session-memory hook (from context)
```

**Which hooks handle retrieval vs injection:**

| Hook | Role | Retrieval | Injection |
|------|------|-----------|-----------|
| `memory-pre-action` | **Primary RAG retrieval** | Queries pgvector | Injects [RELEVANT CONTEXT] block | ← ENHANCE (Phase 2-3) |
| `selective-bootstrap` | Session start context | Queries pgvector + wiki | Injects lean session brief | ← CREATE (Phase 1) |
| `active-memory` | Most recent turn | N/A | Appends 1 user + 1 assistant turn | Built-in, leave as-is |
| `memory-write` | Store memories | — | Writes to pgvector | Doesn't affect retrieval |

**memory-pre-action hook — current code path:**
```
Event: message:preprocessed
↓
1. Extract userMessage from ctx.messages (role=user)
2. if empty → return ctx (skip)
3. queryMemories(userMessage, { memoryTypes: ['experience','fact','decision'], topK: 5 })
4. if memories.length > 0:
     formatMemoriesForInjection()
     prepend to ctx.messages as system message at position [firstNonSystem]
5. return ctx
```

**memory-pre-action hook — enhanced code path (Phase 2-3):**
```
Event: message:preprocessed
↓
1. Extract userMessage from ctx.messages
2. if empty → return ctx
3. CONCURRENT retrieval (Promise.all):
   ├── queryMemories(userMessage, { memoryTypes: ['experience','fact','decision'], topK: 5 })
   ├── queryMemories(userMessage, { tags: ['soul_context'], topK: 3 })
   ├── queryMemories(userMessage, { tags: ['project'], topK: 2 })
   └── queryConversationHistory(userMessage, { session_id: ctx.sessionKey, topK: 3 })
4. Merge + deduplicate results (by chunk_id)
5. Score by: 0.5×semantic_similarity + 0.3×recency + 0.2×importance
6. Discard chunks below minRelevanceScore (0.50)
7. Truncate to maxChars budget (5KB)
8. Synthesize into [RELEVANT CONTEXT — RAG retrieved] block
9. Check ctx.messages for active-memory plugin output — deduplicate any overlapping turns
10. Prepend to ctx.messages
11. [Phase 3] Trim ctx.messages conversation history — GUARD RAILS:
    // ✅ DO trim: role='user' or role='assistant' pairs
    // ❌ NEVER trim: role='tool', role='system', role='function', or current in-flight turn
    // ❌ NEVER trim mid-tool-call — if last tool call is < 30s old, skip trim
    // ✅ COPY ctx.messages before mutating — never mutate the original (hook contract)
    // See Phase 3 implementation notes for full guard rail spec
12. return ctx
```

---

### 5. Suppression Threshold Design (Item 2 — RESOLVED) <!-- id: suppression-design -->

**The failure mode:** Roger asks about something never explicitly told to him. All embeddings score 0.40-0.60. The threshold suppresses everything. Roger proceeds with zero retrieved context and either hallucinates or gives a degraded answer — with NO signal to the user that context was suppressed.

**This is a FATAL silent failure.** The model acts confidently on wrong information.

**Core principle: Suppression must never be silent.**

**Suppression threshold:**
```
Hard floor: similarity < 0.65 → chunk EXCLUDED
Composite score floor: < 0.50 → chunk EXCLUDED even if similarity passes
```

**Suppression fallback chain (ordered):**
```
Step 1: Primary retrieval (topK=8, threshold=0.65)
    ↓ [if all results below 0.65]
Step 2: Retry with threshold=0.55 + 3 broader query variants
    ↓ [if still below 0.55]
Step 3: Inject "LOW CONFIDENCE RETRIEVAL" warning into [RELEVANT CONTEXT] block
    → "Context quality degraded — retrieved memories may not be relevant"
    → Roger knows context is unreliable
    → Size: ~200 bytes
    ↓
Step 4: Fall through to bootstrap files as source of truth
    → Bootstrap files (SOUL, MEMORY) always exist
    → This is the fallback of last resort
    ↓
Step 5: NEVER silently suppress
    → Log suppression event to structured log file:
      File: `~/.openclaw/workspace/logs/memory-pre-action-suppression.jsonl`
      Format: `{"ts":"ISO","query":"X","top_score":Y,"session":"S"}`
    → **Log sink for A/B metrics:** same file, same format — Hermes reads this file for:
      (a) suppression frequency = suppressed_turns / total_turns
      (b) avg retrieved similarity per turn
    → Pattern analysis: "Roger keeps asking about X with no context retrieved"
    → Triggers: manual memory write for that topic
```

**Implementation notes:**
```typescript
// Step 1: primary retrieval
const results = await queryMemories(query, { topK: 8, threshold: 0.65 });

// Step 2: if all below threshold, retry with lower threshold + variants
if (results.every(r => r.similarity < 0.65)) {
  const variants = generateQueryVariants(query); // 3 variants
  const fallbackResults = await Promise.all(
    variants.map(v => queryMemories(v, { threshold: 0.55 }))
  );
  const merged = deduplicateById([...results, ...fallbackResults]);
  const filtered = merged.filter(r => r.similarity >= 0.55);
  
  if (filtered.length === 0) {
    // Step 3: inject low-confidence warning
    injectLowConfidenceWarning(ctx);
    // Step 4: bootstrap files remain in context as fallback
  }
}

// Step 5: ALWAYS log suppression
if (suppressed) {
  console.warn('[memory-pre-action] SUPPRESSED: query="' + query + '" top_score=' + topScore);
}
```

**pgvector unavailable (error, not suppression):**
```typescript
try {
  results = await queryMemories(...)
} catch (err) {
  console.error('[memory-pre-action] pgvector error:', err.message);
  // Continue WITHOUT retrieval — don't fail the message
  return ctx; // bootstrap files handle identity
}
```

**Key distinction:**
- `suppression` = pgvector returned results, all below threshold → proceed with degraded context signal
- `error` = pgvector failed → fail open, use bootstrap as fallback

---

## Item 3: Selection Criteria Framework (RESOLVED) <!-- id: item-3-selection-criteria -->

**The gap:** The spec treated everything in pgvector as selectable. It never defined what can/cannot/should not be retrieved.

**Three-tier framework:**

| Category | Always Injected | Selectively Retrieved | Never Injected |
|----------|----------------|----------------------|----------------|
| Core identity (SOUL §1-3) | ✅ | — | — |
| Active project state | — | ✅ topK=2 | — |
| Past decisions | — | ✅ topK=3 | — |
| Completed/archived tasks | — | — | ✅ |
| Conversation turns >30min old | — | ✅ Mode B only | — |
| Tool schemas | ✅ | — | — |
| Hermes findings files | — | ✅ on review tasks | — |

**Implementation:**
- Tag-based filtering: `identity`, `project`, `decision`, `archived`
- Score threshold: composite score ≥ 0.50 for inclusion
- Hermes veto: `retrieval:blocked` tag on entries that should never surface

**Who decides:**
- The `memory-pre-action` hook decides via tag filtering + score threshold
- Hermes has veto power via `retrieval:blocked` tag on sensitive entries
- Daniel sets policy for borderline cases

---

## Item 4: Alternative 3 Evaluation (A/B Test Plan — PENDING) <!-- id: item-4-ab-test -->

**The unresolved question:** If caching makes full context cheap and model quality degrades with lean context, the spec is counterproductive.

**Proposed resolution: 2-session A/B test**

| Session | Description | Duration | Measure |
|---------|-------------|----------|---------|
| Session A (baseline) | Full context — no retrieval optimization | 1 week | Answer quality, session cost, latency |
| Session B (test) | Selective context — Phase 1 only (lean bootstrap) | 1 week | Same metrics |

**Decision gate:** Binary pass/fail — proceed to Phase 2-3 only if ALL of:
- Suppression frequency < 5% of turns (retrieval is covering most queries)
- Avg retrieved chunk similarity > 0.65 across test messages
- Hermes binary judgment: Session B responses are "not materially worse" than Session A
- Daniel's assessment: acceptable quality on core tasks

**Numeric proxy metrics:**
```
Suppression frequency = (suppressed_turns / total_turns) × 100
  Target: < 5%
  Measured via: Hermes audit log of suppression events

Avg retrieved similarity = mean(chunk.similarity for all retrieved chunks)
  Target: > 0.65
  Measured via: memory-pre-action hook logs

Quality delta = Hermes binary judgment: pass / fail
  Criteria: "Would you trust this response in a production system?" (yes = pass)
  Sample size: 20 randomly selected messages from Session B
```

---

## Item 5: Ownership + Sequence (RESOLVED) <!-- id: item-5-ownership -->

| Item | Status | Owner | Dependency | Next Step |
|------|--------|-------|------------|----------|
| Item 2: Suppression design | ✅ DONE (design complete) | Roger + Perplexity | None | Scout implements per design |
| Item 4: Alternative 3 evaluation | ⏳ PENDING | Daniel (A/B test) | Design done | Daniel runs 2-session A/B |
| Item 3: Selection criteria | ⏳ PENDING | Roger | Item 4 decision | Roger finalizes after A/B data |
| Phase 0 schema + pgvector migration | ⏳ PENDING | Scout | Items 2-3 done | Verify ctx.sessionKey + add migration step |
| Phase 1 implementation | ⏳ PENDING | Scout | Phase 0 complete | Build per validated spec |

---

## Open Questions — All Closed <!-- id: open-questions-closed -->

| # | Question (v1.0/v1.1) | Status |
|---|----------|--------|
| 1 | Selective-mode flag + bootstrap suppression | CLOSED — pragmatic approach; cannot suppress bootstrap |
| 2 | Session boundary (30min inactivity) | CLOSED — confirmed in Session Boundary section |
| 3 | LCM coordination flag | CLOSED — check `ctx.lcmCompacted` before re-querying |

| # | Question (v1.2 additions) | Status |
|---|----------|--------|
| 4 | 93% overhead claim | CLOSED — billing data confirms **99.4%** (worse than stated) |
| 5 | Low-similarity suppression (FATAL) | CLOSED — 4-step chain in Item 2 design |
| 6 | Selection criteria undefined | CLOSED — 3-tier framework in Item 3 |
| 7 | Alternative 3 (full context) evaluation | CLOSED — A/B test plan in Item 4 |
| 8 | Ownership + sequence | CLOSED — restructured ownership table above |

---

*Spec v1.4 — Final-pass P0/P1 fixes applied. Awaiting Scout verification.*
