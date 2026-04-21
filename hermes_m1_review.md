# Hermes M1 Review — Selective Context Architecture

**Date:** April 20, 2026  
**Reviewer:** Hermes  
**Phase:** M1 Milestone Review  
**Trigger Tasks:** 22, 23, 24

---

## Background

M1 acceptance criteria (two items, both must pass):
1. ctx.sessionKey accessible in hook — confirmed in task 22 output (lines 52, 97, 146, 168)
2. pgvector migration script ready — script exists at `hooks/pgvector-migration/migrate.py`, uses correct JSONB query

Review scope: three sections (spec gaps, premature completions, unresolved issues).

---

## Section 1: Spec Items With No Corresponding Blackboard Task

**Spec:** `SELECTIVE_CONTEXT_ARCHITECTURE_v4.md`

Phase 1 items from spec (lines 82-97):
1. Hook fires on `message:preprocessed` event
2. Queries pgvector for: identity facts, current goals, active projects
3. Produces lean "session brief" injected as first system message
4. Size target: < 5KB

**Blackboard tasks (ai_plan_manager.db):**
- Task 22: Phase 1: Lean Session Bootstrap Hook → maps to spec Phase 1 ✓
- Task 23: Phase 1: Verify ctx.sessionKey accessible → maps to spec Phase 1 ✓  
- Task 24: Phase 2: pgvector Migration → **labeled Phase 2 but spec says MANDATORY before Phase 2**

**Gap found:** Task 24 is named "Phase 2" in the blackboard but the spec designates pgvector migration as a Phase 0 / pre-Phase-2 prerequisite. The naming creates ambiguity about when the migration must complete relative to Phase 2 tasks (25, 26, 27).

---

## Section 2: Tasks Marked Complete But Acceptance Criteria Not Met

### Task 22: Lean Session Bootstrap Hook

**Acceptance criteria from task output:**
| Criterion | Claimed | Evidence |
|-----------|--------|----------|
| Hook runs on `message:preprocessed` | ✅ | `events: ["message:preprocessed"]` at line 283 |
| Session brief < 3KB in logs | ⚠️ | Warning at 3072 chars (line 236), log output (line 228-232) — script-level only, not verified against actual execution |
| ctx.sessionKey accessible | ✅ | Confirmed in handler.ts: lines 63, 208, 211, 229 |

**Issue:** The < 3KB criterion is enforced via a `console.warn()` if exceeded (line 236-239), but there's no actual size enforcement — the hook proceeds regardless. The log message `[selective-context-bootstrap] WARNING: session brief N chars exceeds 3KB target` suggests the brief was generated, but the hook does not block or refuse injection if over budget.

**Partial concern:** Cannot independently verify actual size without running the hook. Task output estimates ~2.3KB but provides no measured output.

### Task 23: Verify ctx.sessionKey Accessible

**Acceptance criteria:** ctx.sessionKey confirmed accessible (used throughout task 22 implementation)

**Issue:** This task has **no output file** (`task_23_output.md` does not exist in outputs/). The task is marked completed in the blackboard, but the only evidence that ctx.sessionKey is accessible is from Task 22's implementation. There is no standalone verification or test for this criterion.

**The task appears to be a placeholder** whose completion was "proven by proxy" through Task 22's implementation. This is thin evidence for a critical Phase 1 criterion.

### Task 24: pgvector Migration Script

**Acceptance criteria:**
1. Script exists at `hooks/pgvector-migration/migrate.py` — ✅ confirmed
2. Uses correct JSONB query (`metadata->>'namespace'`) — ✅ confirmed in code

**Issues:**
1. **No README** — The script has no usage documentation. The spec (line 233-246) includes important schema verification steps and warnings. A consumer reading only the script file would not know to verify schema before running, or what the wipe consequences are.

2. **Cannot verify JSONB query against live DB** — The review requested running `SELECT metadata->>'namespace' FROM memories LIMIT 5;` to verify the namespace field exists. I cannot execute this query because `DATABASE_URL` and `PG*` environment variables are not set in my execution context. The script code is correct per the spec, but **live verification was not performed**.

3. **Script does not match spec migration plan exactly** — The spec (line 231-246) specifies a 5-step migration plan:
   - Step 1: Export all existing pgvector entry IDs + metadata
   - Step 2: DELETE all existing whole-document entries
   - Step 3: Re-embed SOUL.md (chunked by section) with `text-embedding-3-small`
   - Step 4: Re-index conversation history chunks with `text-embedding-3-small`
   - Step 5: Verify no old-model vectors remain

   The script (migrate.py) only performs Step 2 and Step 5 verification. **Steps 1, 3, and 4 are missing.** The script is an incomplete implementation of the migration plan — it only deletes, it does not handle re-embedding.

---

## Section 3: Tasks With Unresolved Issues

### Structural Problems

1. **Task 23 is a stub** (no output, no verification, completed by proxy through Task 22)
2. **Task 24 migration is incomplete** — delete-only script, does not handle re-embedding steps from spec
3. **pgvector-migration/README.md missing** — operational script with destructive DELETE has no usage docs

### Security Concerns

**No critical security issues found.** The TypeScript hook does not accept user input directly (receives `HookContext` from OpenClaw). The Python migration script uses parameterized queries for the DELETE operation (line 134), preventing SQL injection.

Minor observation: The TypeScript hook logs session keys (line 229) which could appear in log aggregation. Not a security issue in isolation but worth noting if logs are shared externally.

### Correctness Issues

1. **Handler.ts — memory server fallback is weak** (line 72):
   ```
   catch (err) {
     console.warn(`[selective-context-bootstrap] pgvector query failed: ${err}`);
   }
   ```
   If the memory server is unavailable, `memories` stays empty and the session brief is generated without key memories. The spec's 4-step suppression fallback chain (spec lines 684-700) is not implemented in the hook. The hook proceeds with a degraded brief silently.

2. **Handler.ts — cache can grow unbounded** (line 46):
   ```
   const sessionBriefCache = new Map<string, { brief: SessionBrief; createdAt: number }>();
   ```
   This in-memory Map grows with each new session. For long-running processes with many unique session keys, this is a memory leak. The 30-minute TTL cleans up old entries, but if sessions are created faster than the TTL expires, the cache grows without bound. Should implement LRU eviction or a size cap.

3. **Handler.ts — no dedupe between hook retrieval and active-memory plugin** (line 657 in spec):
   The spec specifies a deduplication step when merging RAG results with `active-memory` plugin output. This check is noted in the spec's enhanced code path but not implemented in the current Phase 1 hook. Phase 2 implementation will need to address this.

---

## Summary Assessment

### Acceptance Criteria Status

| Criterion | Status | Notes |
|-----------|--------|-------|
| ctx.sessionKey accessible (criterion 1) | ⚠️ PARTIAL | Verified via code review of handler.ts, but Task 23 has no standalone output |
| pgvector script ready (criterion 2) | ⚠️ PARTIAL | Script exists with correct JSONB query, but live DB verification not performed, and script is delete-only (missing re-embedding steps from spec) |

### Gaps Summary

| Category | Count | Severity |
|----------|-------|----------|
| Spec items without blackboard task | 1 | Medium (task naming mismatch) |
| Premature completions | 2 | High (Task 23 stub, Task 24 incomplete migration) |
| Structural problems | 3 | Medium-High |
| Security concerns | 0 | None |
| Correctness issues | 3 | Medium |

---

## M1 VERDICT

**M1 REJECTED**

### gap_notes

1. **Task 23 is a stub** — no output file, no standalone verification, completion claimed by proxy through Task 22 implementation. Requires evidence of independent verification or test execution.

2. **Task 24 migration script is incomplete** — performs DELETE of old namespace vectors but does not include the re-embedding steps specified in SPEC lines 231-246 (Steps 1, 3, 4 not implemented). Script only covers Step 2 deletion and Step 5 verification.

3. **Live pgvector verification not performed** — cannot confirm `metadata->>'namespace'` field exists without DB connection. Script code is correct per spec but unverified against live schema.

4. **Task 24 blackboard naming inconsistency** — task is labeled "Phase 2: pgvector Migration" but SPEC designates it as mandatory prerequisite before Phase 2. Ambiguity about whether M1 completion clears the path to Phase 2 or not.

5. **Handler.ts suppression fallback not implemented** — spec's 4-step chain (lines 684-700) is absent; memory server failure results in silent degraded brief rather than fallback injection.

6. **Memory cache unbounded growth risk** — `sessionBriefCache` Map grows without LRU eviction or size cap. Long-running processes risk memory exhaustion.

---

## Phase 2 Delegation

**Phase 2 tasks (25, 26, 27) should NOT begin until M1 gaps are resolved.**

Required fixes before Phase 2 delegation:
- Scout to produce standalone Task 23 output confirming ctx.sessionKey accessibility with actual test evidence
- Scout to clarify Task 24 scope: is delete-only migration complete, or does it need re-embedding steps?
- Foreman/Roger to align Task 24 blackboard naming with SPEC designation as pre-Phase-2 prerequisite
- Database connection for live pgvector verification (or documented reason why verification is not required)

---

*Reviewer: Hermes | Date: April 20, 2026 19:08 CDT*
*Report: /Users/danieltekippe/.openclaw/workspace/hermes_m1_review.md*