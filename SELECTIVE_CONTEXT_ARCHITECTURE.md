# Selective Context Architecture — SPEC v1.0

**Date:** April 20, 2026  
**Status:** Scoped — Ready for Scout implementation  
**Problem:** 93% of token spend is context overhead, not generation. Context grows without bound as conversation history accumulates.

---

## Background

### Current Architecture

```
Every LLM call:
├── System prompt (~1KB)           [static, ok]
├── Bootstrap files (SOUL+MEMORY)  [was 63KB, now ~45KB — overhead]
├── Pre-action hook retrieval       [EXISTS — memory-pre-action hook]
│   └── Queries pgvector → injects top 5 relevant memories
├── active-memory plugin            [EXISTS — recent mode, lean]
└── Conversation history            [GROWS — primary cost driver]
```

The `memory-pre-action` hook already does selective retrieval. The problem is:

1. **Bootstrap files still fully injected** on top of hook retrieval
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
5. Signal: "skip full bootstrap for this turn" ← KEY PART
```

**The critical mechanism:** The hook returns a modified context with a `__selective_retrieval_done__` flag. If set, the agent runner skips the default bootstrap file injection for that turn.

**Size target:** < 8KB per message

---

### Layer 3: Conversation History Management

**What:** Sliding window or RAG-retrieved history instead of full history.

**Two modes (configurable):**

**Mode A — Sliding Window (simpler):**
- Keep only last N messages in context
- Older messages: query pgvector for "what was decided/mentioned in this conversation around X"
- Inject relevant past turns as retrieved context, not full history

**Mode B — Semantic History Retrieval (better):**
- On each message, query pgvector for semantically relevant past turns
- Full conversation stored in pgvector with `session_id` and `turn_index` tags
- Retrieval returns specific turns, not full history

**Recommended:** Mode A for immediate implementation, Mode B as Phase 2.

---

## Key Mechanism: Skip Default Bootstrap Injection

Currently:
```
Bootstrap files (SOUL, MEMORY, etc.) → injected every turn unconditionally
```

Desired:
```
Bootstrap files → injected ONCE at session start
Per-turn → selective retrieval via hook (no bootstrap re-injection)
```

**Implementation path:**

Option 1 — Hook flag (recommended):
```typescript
// In memory-pre-action hook:
ctx.selectiveMode = true;  // signals: skip default bootstrap this turn

// In agent-runner (OpenClaw core — NOT modifiable by us):
if (!ctx.selectiveMode) {
  injectBootstrapFiles();  // existing behavior
}
```

Option 2 — Bootstrap budget tuning:
```yaml
agents:
  defaults:
    bootstrapMaxChars: 2000      # was 20000, force lean
    bootstrapTotalMaxChars: 5000  # was ~50KB, force ultra-lean
```

Option 2 is a CRUDE hack — it just truncates. Not a real solution.

Option 1 requires OpenClaw core support for the `selectiveMode` flag. Let me check if this exists or needs to be added.

**Finding:** The `bootstrap-budget-DjYfMmvw.js` file processes `ctx.bootstrapFiles`. The flag would need to be checked in `agent-runner.runtime-DpPR0_pV.js`. This is OpenClaw core, not modifiable by us.

**Alternative:** The hook injection happens BEFORE bootstrap injection. If we inject our lean context at the right position in `ctx.messages`, and the model is already seeing our selective context, the bootstrap files become redundant context. The model will attend to the most relevant context — our hook injection at the top of messages[] wins.

**Pragmatic approach:** Don't try to skip bootstrap injection. Instead, make the hook injection SO good (RAG-retrieved, precisely relevant) that the model ignores the stale bootstrap files. The cost of sending both is minimal compared to the current full-history approach.

---

## Implementation Phases

### Phase 1: Lean Session Bootstrap (Scout task)
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

### Phase 2: Enhanced Per-Message Retrieval (Scout task)
**Goal:** `memory-pre-action` hook retrieves SOUL sections in addition to memories.

**Files to modify:**
- `hooks/memory-pre-action/handler.ts`
- `hooks/_shared/pgvector-memory.ts` (may need new query functions)

**What it does:**
1. Current: queries pgvector for memories only
2. New: also queries for SOUL-relevant sections (tagged `soul_context`)
3. Inject as combined `[RELEVANT CONTEXT]` block at top of messages
4. Add tags to pgvector entries: `soul_context`, `identity`, `project`, `decision`

**Size target:** < 5KB per retrieval  
**Effort:** ~4 hours Scout  

---

### Phase 3: Sliding Window History (Scout task)
**Goal:** Limit conversation history to last N turns, RAG-retrieve older context.

**Files to modify:**
- `hooks/memory-pre-action/handler.ts` (add history management)

**What it does:**
1. Track turn count in session metadata
2. At N>20 turns: query pgvector for "what happened in conversation about X"
3. Replace older turns with RAG-retrieved summaries
4. Kept turns: last 5 (full) + N-5 retrieved summaries

**Size target:** < 10KB total per message (down from 50KB+)  
**Effort:** ~6 hours Scout  

---

### Phase 4: Workspace Semantic Search (Scout task)
**Goal:** RAG-retrieve from workspace files instead of loading all of them.

**Files to modify:**
- `hooks/memory-pre-action/handler.ts`
- Add workspace file indexing to pgvector

**What it does:**
1. Index key workspace files into pgvector (DYNASTY_TRADES_PLAN, ARCHITECTURE_SUB_AGENTS, etc.)
2. On task context: query for relevant workspace sections
3. Inject relevant sections instead of expecting model to attend to all files

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
-- Add tag support for selective retrieval
ALTER TABLE memories ADD COLUMN tags TEXT[];
ALTER TABLE memories ADD COLUMN source_file TEXT;

-- Tag existing entries
UPDATE memories SET tags = ARRAY['soul_context'] WHERE content LIKE '%SOUL.md%';
UPDATE memories SET tags = ARRAY['identity'] WHERE content LIKE '%Core Identity%';
UPDATE memories SET tags = ARRAY['decision'] WHERE content LIKE '%DECISION%';
UPDATE memories SET tags = ARRAY['project'] WHERE content LIKE '%DynastyDroid%';
```

---

## Expected Outcomes

| Metric | Current | After Phase 1-2 | After Phase 3 |
|--------|---------|------------------|---------------|
| Context per message | ~100KB | ~20KB | ~12KB |
| Token cost per session (4hr) | ~$5.30 | ~$1.50 | ~$0.80 |
| Cache-read efficiency | 7.5M/80K | 2M/80K | 1M/80K |
| Input-to-output ratio | 153:1 | 25:1 | 12:1 |

---

## Open Questions

1. **Can the selective-mode flag be implemented without OpenClaw core changes?** If yes, Phase 2 is much cleaner. If no, we live with redundant injection and rely on model attention to weight our retrieval higher.

2. **Should we index SOUL.md and MEMORY.md into pgvector with section-level granularity?** Currently they're stored as whole entries. For precise retrieval, we'd want section-level chunking.

3. **How does this interact with LCM compaction?** The lossless-claw engine handles conversation history compaction. Our retrieval layer and LCM need to be coordinated — we don't want our selective retrieval competing with LCM's summarization.

4. **Session segmentation vs RAG history:** Is restarting sessions every 30 minutes simpler than building sliding window history? This is essentially free — just a practice discipline.

---

## Immediate Action (This Week)

1. **Today:** Scout implements Phase 1 (lean session bootstrap)
2. **This week:** Scout implements Phase 2 (enhanced retrieval)
3. **Next week:** Scout implements Phase 3 (sliding window)
4. **Ongoing:** Monitor token usage via Minimax dashboard

---

## Critical Engineering Details

### 1. Context Injection Order (Cache Hit Preservation)

The order below is intentional and critical for Minimax's cache to function efficiently. **Static content first, dynamic last.**

```
EVERY LLM CALL — exact order:

[1] System prompt                  (~1KB)   [STATIC — computed once, cached every call]
    └── OpenClaw core, never changes between calls

[2] Tool schemas                   (~2KB)   [STATIC — cached, regenerated only when tools change]
    └── read, write, exec, browser, subagents, sessions, message, etc.

[3] Bootstrap files (SOUL+MEMORY)  (~45KB)  [SEMI-STATIC — cached at session start]
    └── Only re-cached when files change on disk (hourly or on explicit write)
    └── Currently: full injection every call (PROBLEM)
    └── Desired: once at session start only

[4] Selective retrieval block      (~5KB)   [DYNAMIC — computed every call, NOT cached]
    └── RAG from pgvector, injected by memory-pre-action hook
    └── This is the hook's current output

[5] Recent conversation history    (~3KB)   [DYNAMIC — changes every turn]
    └── Last 5 turns (user + assistant)
    └── At turn >20: sliding window (last 5 full + RAG summaries for older)

[6] Current user message           (~0.5KB) [UNIQUE — never cached]

───────────────────────────────────────────────────────
Total per call:                    ~56KB  (down from ~100KB+)
```

**Why this order maximizes cache hits:**
- Slots [1] and [2] are identical every call → 100% cache hit rate
- Slot [3] changes only when bootstrap files change → ~99% cache hit rate
- Slots [4]-[6] are unique per call → 0% cache hit (correct, these can't be cached)

**The critical failure mode we're fixing:**
Current architecture sends slots [1]-[6] PLUS the full conversation history (all prior turns, not just last 5). That's [5] currently containing ALL history, not just recent turns. This is what causes the 100KB+ per-call size.

**OpenClaw's current injection order (inferred from hook lifecycle):**
```
1. System prompt
2. Tool schemas
3. Bootstrap files (SOUL, MEMORY, etc.) ← currently re-sent every call
4. active-memory recent context
5. Pre-action hooks (memory-pre-action injects here)
6. Conversation history (all turns, unbounded)
7. Current message
```

**Desired injection order (requires Phase 2+ implementation):**
```
1. System prompt
2. Tool schemas
3. Bootstrap files ← INJECTED ONCE at session start only (not every call)
4. [NEW] Lean session brief (selective-bootstrap hook output)
5. Pre-action hooks (memory-pre-action RAG retrieval)
6. Recent history only (last 5 turns, not all history)
7. Current message
```

---

### 2. pgvector Retrieval Strategy

**Embedding model:**
```typescript
// Use MiniMax's native embeddings via their API
// Model: text-embedding-001 (or provider's default embedding model)
// Dimension: 1536 (OpenAI ada-002 compatible)
// Note: The DynastyDroid app/core/memory.py uses pgvector — check which embedding model is configured there first

interface RetrievalConfig {
  embeddingModel: 'text-embedding-001' | 'text-embedding-3-small';
  similarityThreshold: 0.65;       // minimum cosine similarity (0-1)
  minRelevanceScore: 0.5;          // if below, discard even if below threshold
  maxChunks: 8;                    // maximum chunks to return
  chunkSize: 512;                  // tokens per chunk (before embedding)
  chunkOverlap: 64;                // overlap between chunks for context continuity
  rerankTopK: 3;                 // after vector search, rerank top N for relevance
}
```

**Chunking strategy:**
- Chunk size: 512 tokens — balances granularity (smaller = more precise retrieval) vs coverage (larger = less retrieval calls)
- Chunk overlap: 64 tokens — ensures context continuity at chunk boundaries
- SOUL.md: chunked by section (each ## heading = one chunk)
- MEMORY.md: chunked by entry (each ## [...] = one chunk)
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
5. Select top 8, truncate to maxChars budget (5KB)
6. Inject as [RELEVANT CONTEXT] block
```

**Current pgvector schema (from memory.py):**
```sql
-- Verify existing schema before adding columns
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

-- New columns to add:
ALTER TABLE memories ADD COLUMN tags TEXT[] DEFAULT '{}';
ALTER TABLE memories ADD COLUMN source_file VARCHAR(255);
ALTER TABLE memories ADD COLUMN chunk_index INTEGER;  -- position in original document
CREATE INDEX ON memories USING GIN(tags);
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

**LCM interaction:**
```
Session continues (compact history) when:
  turn_count % 20 == 0 → LCM summarizes oldest turns → injects summary
  turn_count % 50 == 0 → LCM deep-compacts → smaller summary

Session boundary triggered when:
  inactivity > 30 min OR
  explicit new_session signal
```

**cache-create cost management:**
Every new session = new cache-create on first message. At $0.375/M tokens (MiniMax M2.7 cache-write), a 50KB bootstrap creates a new cache on first call. Subsequent calls in that session read from cache at $0.06/M.

**Recommendation:** Session restart discipline is FREE but has tradeoffs:
- Pro: Full context reset, maximum cache efficiency on fresh context
- Con: Loss of in-progress context, discontinuity for multi-task sessions
- Decision: Use 30-min inactivity rule, not aggressive turn-count resets

---

### 4. OpenClaw Hook Insertion Points

**Hook execution order (confirmed from gateway logs + hook source):**

```
1. [gateway:startup]           → boot-md hook
2. [agent:bootstrap]           → bootstrap-extra-files hook
3. [message:preprocessed]      → memory-pre-action hook ← PRIMARY RETRIEVAL
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
5. [before_action]             → futureself hook (before_action again?)
6. [action:complete]           → (no standard hooks observed)
7. [session:end]               → session-memory hook (from context)
```

**Which hooks handle retrieval vs injection:**

| Hook | Role | Retrieval | Injection |
|------|------|-----------|-----------|
| `memory-pre-action` | **Primary RAG retrieval** | Queries pgvector | Injects [RELEVANT MEMORIES] block | ← THIS IS THE ONE TO ENHANCE
| `selective-bootstrap` | Session start context | Queries pgvector + wiki | Injects lean session brief | ← NEW HOOK TO CREATE
| `active-memory` | Recent memory | recentUserTurns=1, recentAssistantTurns=1 | Appends recent context | Built-in, already lean |
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

**memory-pre-action hook — enhanced code path (Phase 2):**
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
4. Merge + deduplicate results
5. Score by: 0.5×semantic_similarity + 0.3×recency + 0.2×importance
6. Truncate to maxChars budget (5KB)
7. Synthesize into [RELEVANT CONTEXT — RAG retrieved] block
8. Prepend to ctx.messages
9. return ctx
```

---

### 5. Fallback Behavior

**When pgvector retrieval returns nothing relevant:**

```
Retrieval attempt
    ↓
results = pgvector.similarity_search(query)
    ↓
filtered = results.filter(r => r.similarity >= 0.65)
    ↓
if filtered.length == 0:
    │
    ├── Session age < 5 minutes:
    │   → Inject: "Session just started. No prior context."
    │   → Bootstrap files (SOUL, MEMORY) handle identity.
    │   → Size: ~200 bytes.
    │
    ├── Session age 5-30 minutes:
    │   → Fall back to recent turns (last 3) from ctx.messages
    │   → This is conversation-native context, no RAG needed.
    │   → Size: ~1.5KB.
    │
    └── Session age > 30 minutes:
        → Check if conversation has a "topic" from recent turns
        → If yes: retry with broader query (lower threshold 0.55)
        → If still 0: inject "context unclear — ask user for clarification"
        → Size: ~100 bytes.
```

**Fallback chain — full priority order:**

```
Priority 1: RAG retrieval from pgvector (topK=8, threshold=0.65)
    ↓ [if 0 results]
Priority 2: RAG retrieval with lower threshold (0.55) + broader query variants
    ↓ [if still 0]
Priority 3: Recent turns from conversation history (last 3 turns)
    ↓ [if session just started]
Priority 4: Lean bootstrap (session brief from selective-bootstrap hook)
    ↓ [if all above fail]
Priority 5: Minimal system message: "You are Roger. The current task is unclear."
```

**Error handling (pgvector unavailable):**
```
try {
  results = await queryMemories(...)
} catch (err) {
  console.error('[memory-pre-action] pgvector error:', err.message)
  // Continue WITHOUT retrieval — don't fail the message
  // Fall back to bootstrap files + conversation history
  return ctx
}
```

**The no-op path is critical:** If pgvector errors out, the hook MUST NOT crash. The message still goes through with whatever context was already injected. Fail open, not closed.

---

*Scoping complete. Ready for Scout implementation.*
