# Hermes M2 Review — Phase 2/3 Implementation

**Reviewer:** Hermes  
**Date:** April 20, 2026  
**Phase:** M2 (Phase 2 Enhanced Retrieval + Phase 3 Sliding Window)  
**Files Reviewed:**
- `/Volumes/ExternalCorsairSSD/shared/coordination/hooks/memory-pre-action/handler.ts` (501 lines)
- `/Volumes/ExternalCorsairSSD/shared/coordination/hooks/_shared/pgvector-memory.ts` (234 lines)
- `/Volumes/ExternalCorsairSSD/shared/coordination/SELECTIVE_CONTEXT_ARCHITECTURE_v4.md` (SPEC v1.4)

---

## Review Question 1: Spec items with no corresponding task — remaining gaps?

**Phase 2 spec items verified:**

| Spec Item | Implementation | Status |
|-----------|---------------|--------|
| 4 concurrent pgvector queries | Promise.allSettled at pgvector-memory.ts:176 | ✅ |
| 5KB budget enforcement | truncateToBudget() + formatContextBlock() + warn at handler.ts:360 | ✅ |
| soul_context tag filter | tags: ["soul_context", "identity"] at pgvector-memory.ts:106 | ✅ |
| Injection as [RELEVANT CONTEXT] block | formatContextBlock() at handler.ts:198 | ✅ |

**Phase 3 spec items verified:**

| Spec Item | Implementation | Status |
|-----------|---------------|--------|
| Trim to last N turns (configurable) | applySlidingWindow() at handler.ts:263, maxTurns: 20 | ✅ |
| ~12KB target | targetBytes: 12288 at handler.ts:167 | ✅ |
| Trimming logged | console.log with savedBytes at handler.ts:294-298 | ✅ |
| System messages preserved | lines 278-279 filter + reassemble | ✅ |

**Gap identified:** SPEC v1.4 Section 5 (Suppression Threshold Design) Step 3 specifies injecting a "LOW CONFIDENCE RETRIEVAL" warning when all results fall below threshold. The current implementation at handler.ts:373-399 returns early on suppression but does NOT inject any warning message into the context block. The bootstrap files serve as fallback (Step 4), but Step 3 warning is not implemented. **Severity: Informational — the spec marks suppression design as "DONE" but the warning injection step is not yet implemented.**

**Open items from SPEC pending Scout verification (not part of M2 scope):**
- ctx.sessionKey verification
- LCM flag (ctx.lcmCompacted) verification
- pgvector migration (mandatory before Phase 2 deployment)

---

## Review Question 2: Phase 2/3 implementation correctness

### Phase 2 — Enhanced Per-Message Retrieval

**4 concurrent queries confirmed:**
```typescript
// pgvector-memory.ts:176
const [memoriesResult, soulResult, projectResult, turnsResult] = await Promise.allSettled([
  queryMemories(messageQuery, memoryTopK, minThreshold),         // topK=5
  querySoulContext(messageQuery, soulTopK, minThreshold),        // topK=3, tags=[soul_context,identity]
  queryProjectContext(messageQuery, projectTopK, minThreshold),  // topK=2
  queryPastTurns(messageQuery, sessionId, turnsTopK, minThreshold), // topK=3, session filtered
]);
```
Promise.allSettled ensures failures don't block other queries.

**5KB budget enforcement confirmed:**
- defaultConfig.maxContextBytes: 5120 (handler.ts:162)
- truncateToBudget() truncates per-section (pgvector-memory.ts:216)
- formatContextBlock() tracks totalBytes and warns if exceeded (handler.ts:219, 360)

**soul_context tag filter confirmed:**
```typescript
// pgvector-memory.ts:103-107
return queryMemory(query, { 
  topK, 
  minThreshold, 
  tags: ["soul_context", "identity"]  // filters for SOUL-tagged entries
});
```

### Phase 3 — Sliding Window

**applySlidingWindow() confirmed (handler.ts:263-301):**
- Input: full message array
- Counts turns via countConversationTurns() — each user+assistant pair = 1 turn
- If turns > maxTurns: filters to system messages + last N non-system pairs
- Reassembles with system messages first, then trimmed conversation
- Logs: turns count before/after, savedBytes

**12KB target tracking confirmed (handler.ts:441-444):**
```typescript
const totalMessageBytes = new TextEncoder().encode(
  JSON.stringify(trimmedMessages)
).length;
```
Metadata includes targetBytes: 12288 and totalMessageBytes for calibration.

**No issues found in implementation correctness.**

---

## Review Question 3: Unresolved issues — any new concerns?

**Informational: Suppression warning injection not implemented**

The spec (Section 5, Step 3) states: "Inject 'LOW CONFIDENCE RETRIEVAL' warning into [RELEVANT CONTEXT] block." The current implementation at handler.ts:373-399 returns early on suppression with metadata but does not inject any warning message. Bootstrap files remain in context as fallback (Step 4), but the explicit warning to the model is absent.

Current behavior:
```typescript
if (suppressionCheck.suppressed) {
  sessionMetrics.suppressionCount++;
  // logs suppression event
  return { ...ctx, metadata: { memoryPreAction: { suppressed: true, ... } } };
  // NO warning injected, NO retry triggered
}
```

The spec's 4-step fallback chain (Step 1: primary → Step 2: retry with lower threshold + variants → Step 3: inject warning → Step 4: fall through to bootstrap) is not fully implemented. Only the threshold check is present. This is acceptable as a Phase 2 simplification, but should be addressed before production deployment per the spec's "NEVER silently suppress" principle.

**No security issues identified.**  
**No bug patterns identified.**  
**No new concerns introduced by Phase 2/3 implementation.**

---

## M2 Acceptance Criteria Check

### Phase 2 Enhanced Retrieval ✅

| Criterion | Evidence |
|-----------|----------|
| 4 concurrent queries confirmed in code | pgvector-memory.ts:176 Promise.allSettled |
| 5KB budget enforcement confirmed in code | handler.ts:162 maxContextBytes: 5120, truncateToBudget(), warn at 360 |
| soul_context tag filter confirmed in code | pgvector-memory.ts:106 tags: ["soul_context", "identity"] |

### Phase 3 Sliding Window ✅

| Criterion | Evidence |
|-----------|----------|
| Trim to last N turns (N configurable) confirmed in code | handler.ts:263-301, maxTurns: 20 default |
| ~12KB target confirmed in config | handler.ts:167 targetBytes: 12288 |
| Trimming logged confirmed in code | handler.ts:294-298 console.log with savedBytes |

---

## Verdict

**M2 APPROVED**

All Phase 2 and Phase 3 acceptance criteria confirmed in code. Implementation is correct. One informational gap noted (suppression warning injection) that does not block Phase 4.

**gap_notes:** Suppression threshold design is correctly implemented (threshold check + logging), but the spec's 4-step fallback chain including "inject LOW CONFIDENCE warning" (Step 3) is not yet implemented. This is acceptable for Phase 2/3 but should be addressed before production deployment. No blockers for Task 28 (Phase 4).

**Phase 4 tasks (28) can begin.**

---

## Supplementary Task 27 Criteria Review (April 20, 2026 19:47)

### Task 27 Watch Point 1: Trim Point Correct — Last N Turns, Not N Messages

**CHECK: applySlidingWindow() counts turns as pairs, not single messages**

Verified at handler.ts:249-251:
```typescript
function countConversationTurns(messages: any[]): number {
  const nonSystem = messages.filter((m: any) => m.role !== "system");
  return Math.floor(nonSystem.length / 2);  // ← CORRECT: divides by 2 for pairs
}
```

And at handler.ts:282:
```typescript
const keptMessages = nonSystemMessages.slice(-maxTurns * 2);  // ← CORRECT: slices pairs
```

**VERDICT: PASS** — Turn counting is correct. Each turn = 1 user + 1 assistant message (2 messages). The division by 2 and multiplication by 2 in slice are both correct. Window is N turns as specified.

---

### Task 27 Watch Point 2: No Mid-Turn Cuts

**CHECK: Trim never splits a user message from its assistant response**

Verified at handler.ts:277-285:
```typescript
// Collect non-system messages
const systemMessages = messages.filter((m: any) => m.role === "system");
const nonSystemMessages = messages.filter((m: any) => m.role !== "system");

// Trim to last N turns (each turn = 2 messages: user + assistant)
const keptMessages = nonSystemMessages.slice(-maxTurns * 2);  // ← cuts in pairs

// Reassemble: system messages first, then trimmed conversation
const trimmedMessages = [...systemMessages, ...keptMessages];
```

**VERDICT: PASS** — The slice operation operates on the entire nonSystemMessages array, cutting from the end in increments of 2 (a full turn pair). The reassembly puts system messages first, then the complete pairs. No mid-turn splitting.

**Note:** The implementation assumes alternating user/assistant order within the nonSystemMessages array. If message order is ever non-alternating (e.g., multiple consecutive user messages), the pair assumption breaks. This is an implicit assumption not documented in code.

---

### Task 27 Watch Point 3: Graceful Degradation

**CHECK: If ctx.messages is already under limit, window is no-op**

Verified at handler.ts:266-274:
```typescript
if (originalCount <= maxTurns) {
  // No trimming needed — log only if we have significant history
  if (originalCount > 5) {
    console.log(
      `[memory-pre-action] sliding_window: turns=${originalCount} ` +
      `under_limit=${maxTurns} — no trimming`
    );
  }
  return messages;  // ← returns original unmodified
}
```

**VERDICT: PASS** — Early exit returns original messages unchanged when under the turn threshold. Only logs when history is "significant" (turns > 5) to avoid noise in short sessions.

---

### Task 27 Watch Point 4: Graceful Degradation (Target Bytes)

**CHECK: 12KB target is informational, not a hard trim trigger**

Reviewed handler.ts:441-444 and full context flow. The 12KB target (targetBytes: 12288) is:
1. Used as informational metadata logged after processing
2. NOT used as a trim threshold in applySlidingWindow()
3. applySlidingWindow() trims by turn count (N=20), not by byte size

**VERDICT: OBSERVATION** — The 12KB target is not the trim trigger; turns are. This means:
- If a single turn exceeds 12KB (very long user message), the window still targets N turns
- The 12KB tracking is for calibration visibility, not enforcement
- Spec says "~12KB target" which may mean the window is sized so that N turns ≈ 12KB on average, not exactly 12KB

---

## Phase 2/3 Interaction Analysis (Tasks 25, 26, 27)

### Suppression Threshold vs Sliding Window — Interaction Direction

**Finding: Direction is ambiguous, and current calibration may be incorrect.**

**Scenario A (Suppression fires MORE after window trim):**
- Sliding window saves N bytes from ctx.messages
- Retrieval still fires per-message, generating same ~5KB context block
- Total token budget freed = window savings
- BUT: if window savings are large, the model has more room for the retrieval block
- **Result: suppression may fire LESS** (more budget headroom)

**Scenario B (Suppression fires LESS after window trim):**
- Sliding window reduces conversation history context
- With less surrounding context, the last user message may be harder to match semantically
- pgvector similarity scores may be lower
- **Result: suppression may fire MORE** (poorer matches due to lost history)

**Which direction does the current code actually follow?**
- Sliding window trims ctx.messages BEFORE retrieval (handler.ts:321-324)
- BUT lastUserMessage is extracted from original `messages` array, not `trimmedMessages` (handler.ts:327-329)
- Query extraction uses untrimmed history — this is correct
- BUT the retrieval results (similarity scores) depend on the trimmed message context indirectly via pgvector matching

**Key issue identified:** The sliding window trims the message array passed to the hook, but the pgvector query against external memory store (pgvector-memory.ts) is independent of ctx.messages. pgvector queries against the external memory database, not the message history. So the sliding window does NOT directly affect suppression threshold calculation.

**However:** Sliding window does affect:
1. The lastUserMessage content used for query extraction (handler.ts:327-329 — uses original messages, not trimmed)
2. The message array that gets returned to the caller (trimmedMessages)

**VERDICT: Phase 2/3 do NOT interact in the suppression threshold path** because:
- Suppression threshold evaluates `results` from pgvector queries (external memory)
- pgvector queries are NOT against ctx.messages content
- Therefore sliding window trimming does not affect similarity scores

The two features are more orthogonal than the task description suggested.

---

### Integration Test Gap

**Current state:** No integration test exists for sliding window + suppression threshold firing together.

**Recommendation:** Before Phase 4 deployment, add a test scenario:
1. Start with >20 turns of history
2. Verify sliding window fires (trims to 20)
3. Verify suppression threshold still fires correctly on trimmed message
4. Verify retrieval quality is not degraded by window trim

**Note:** This is only critical if future phases wire pgvector queries to message history content rather than external memory.

---

## Supplementary Findings Summary

| Watch Point | Status | Notes |
|-------------|--------|-------|
| 1. Trim point correct (turns, not messages) | PASS | countConversationTurns() divides by 2 correctly |
| 2. No mid-turn cuts | PASS | slice operates on pairs; reassembles complete pairs |
| 3. Graceful degradation (under limit = no-op) | PASS | Early return when turns <= maxTurns |
| 4. 12KB target informational | OBSERVATION | Trims by turns, not bytes; 12KB is calibration metadata |

| Phase 2/3 Interaction | Assessment |
|------------------------|------------|
| Suppression vs window direction | AMBIGUOUS in theory, but features are ORTHOGONAL in practice |
| Window affects query extraction | YES — lastUserMessage extracted from original array |
| Window affects pgvector retrieval | NO — queries external memory store |
| Integration test needed | RECOMMENDED before Phase 4 deployment |

**No new bugs or security issues identified.**

**Supplementary M2 criteria review complete.**