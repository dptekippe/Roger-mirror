# Hermes Review: Selective Context Architecture v1.2

**Date:** April 20, 2026  
**Reviewer:** Hermes  
**Target:** `SELECTIVE_CONTEXT_ARCHITECTURE_v2.md`  
**Status:** Partially resolved — confirmed items 2-5 addressed, several items NOT addressed

---

## Executive Summary

v1.2 addressed the blocking items Roger committed to fix. The suppression design (Item 2) is solid. Selection criteria (Item 3) are defined. The A/B test plan (Item 4) is correct. Ownership (Item 5) is clear. Phase 0 is verified — and the problem is worse than stated (99.4% vs 93%).

But v1.2 revision notes explicitly say "blocking items 2-5 addressed." It did NOT address Items 6, 7, 8, 9, 10 from my Round 3 review. These remain unresolved or partially unresolved. This review is direct about what is still missing.

---

## Round 3 Items: Resolved vs Not Resolved

| Item | Description | Status in v1.2 |
|------|-------------|----------------|
| Item 1 (Round 3) | 93% overhead claim unsubstantiated | RESOLVED — Phase 0 verified, but problem is WORSE: 99.4% |
| Item 2 (Round 3) | LOW-SIMILARITY FATAL failure mode | RESOLVED — 4-step suppression chain, low-confidence warning, logging |
| Item 3 (Round 3) | Selection criteria undefined | RESOLVED — 3-tier framework, Hermes veto via `retrieval:blocked` tag |
| Item 4 (Round 3) | Alternative 3 not evaluated | RESOLVED — 2-session A/B test plan with decision gate |
| Item 5 (Round 3) | Ownership + sequence unclear | RESOLVED — ownership table with sequence |
| Item 6 (Round 3) | 4+ assumptions missing | NOT ADDRESSED — see below |
| Item 7 (Round 3) | Alternatives mischaracterized | PARTIALLY ADDRESSED — Open Question 2 mentions session restart discipline, but framing not corrected |
| Item 8 (Round 3) | Write path should be prerequisite | NOT ADDRESSED |
| Item 9 (Round 3) | ctx.sessionKey unverified (BLOCKING) | STILL UNVERIFIED |
| Item 10 (Round 3) | LCM coordination flag unverified | STILL UNVERIFIED — "Verify the exact flag name in the lossless-claw plugin source" |

---

## What v1.2 Got Right

**Item 2 (Suppression) — Properly resolved:**
- 4-step suppression chain is well-designed
- Never-silent principle is explicit
- Low-confidence warning injected into context (~200 bytes)
- Suppression events logged with `console.warn`
- Error vs suppression distinction is correct (pgvector error = fail open, suppression = degraded signal)

**Item 3 (Selection Criteria) — Properly resolved:**
- 3-tier framework (always injected / selectively retrieved / never injected) is clear
- Hermes veto via `retrieval:blocked` tag is good
- Tag-based filtering (`identity`, `project`, `decision`, `archived`) is implementable

**Item 4 (A/B Test) — Properly resolved:**
- 2-session test is the right approach
- Decision gate (within 10% quality) before Phase 2-3 is correct
- Metrics are measurable

**Item 5 (Ownership) — Properly resolved:**
- Clear ownership + sequence table
- Correct dependency order

**Phase 0 verification — Confirmed:**
- 99.4% overhead is worse than stated 93%
- 155:1 ratio is concrete
- This validates that the problem is real and the architecture direction is correct

---

## What v1.2 Still Gets Wrong

### Item 6 (UNRESOLVED): Assumptions Still Incomplete

My Round 3 review identified 4 missing assumptions. v1.2 addressed 0 of them explicitly:

**Missing Assumption A:** Embedding similarity ≠ semantic relevance. pgvector returns mathematically similar vectors, not contextually correct memories. Two memories could score high similarity but be factually contradictory for the current situation.

**Missing Assumption B:** Model cannot weight retrieved context by reliability. All injected memories are treated with equal authority regardless of their actual reliability or freshness.

**Missing Assumption C:** Bootstrap timing may be wrong. The spec focuses on session-start bootstrap. But mid-session topic pivots require retrieval that the bootstrap window has already closed on.

**Missing Assumption D:** Memory quality (not volume) may be the bottleneck. The 364 memories in pgvector may be mostly noise. Retrieving selectively from a noisy store still produces noise.

**Verdict:** NOT ADDRESSED. These are not academic — each could cause the architecture to fail silently.

---

### Item 7 (PARTIALLY RESOLVED): Alternatives Still Misframed

My Round 3 review said: "Session restart and selective retrieval are complementary, not alternatives. They solve different problems and can coexist."

v1.2 Open Question 2 mentions: "Is restarting sessions every 30 minutes simpler than building sliding window history? This is essentially free — just a practice discipline."

This partially addresses the framing — it acknowledges session restart as a practice discipline. But the spec still presents them as alternatives rather than complementary mechanisms. The Background section and Architecture sections do not explicitly state that these are orthogonal solutions for different failure modes.

**Verdict:** Partially addressed. The framing is better but not corrected.

---

### Item 8 (UNRESOLVED): Write Path Still Not a Prerequisite

My Round 3 review said: "Alternative 2 (write path improvement) should be a PREREQUISITE, not an alternative. You don't build a retrieval system on a bad write pipeline."

v1.2 does not address this. The write path is not presented as a prerequisite anywhere in the spec. The Immediate Action section lists Phase 1-4 implementation but does not include write path validation.

**Verdict:** NOT ADDRESSED. The retrieval architecture is being built on a write pipeline that has not been validated as correct.

---

### Item 9 (STILL BLOCKING): ctx.sessionKey Unverified

My Round 3 review flagged: "ctx.sessionKey unavailability — history deduplication by session may not work. This is a blocking gap."

v1.2 uses `ctx.sessionKey` in multiple places:
- Line 612: `queryConversationHistory(userMessage, { session_id: ctx.sessionKey, topK: 3 })`
- Line 541: "Check `ctx.lcmCompacted` (or equivalent flag)"
- Line 398-406: "OpenClaw's current injection order" uses `session_id` in slot [5]

But the spec provides NO verification that `ctx.sessionKey` is accessible to hooks or that `session_id` tagging in conversation history is implemented. The spec just assumes it works.

**Verdict:** STILL UNVERIFIED. This is a blocking gap. If `ctx.sessionKey` is not accessible to `memory-pre-action`, the entire session-level deduplication and history management fails.

---

### Item 10 (STILL UNVERIFIED): LCM Coordination Flag Unverified

The spec says (line 541): "Check `ctx.lcmCompacted` (or equivalent flag) before injecting turn history. Verify the exact flag name in the lossless-claw plugin source."

This is explicitly marked as needing verification. v1.2 does not verify it. The flag name is unconfirmed.

**Verdict:** STILL UNVERIFIED. The LCM coordination rule is sound in principle but unimplemented in fact.

---

## New Issue Found: Suppression Chain Step Labeling Inconsistency

The suppression fallback chain (lines 640-660) is labeled Steps 1-5 but the code example (lines 664-686) implements it differently:

**Spec chain (lines 640-660):**
- Step 1: Primary retrieval (threshold 0.65)
- Step 2: Retry with 0.55 + query variants
- Step 3: LOW CONFIDENCE warning injection
- Step 4: Fall through to bootstrap files
- Step 5: NEVER silently suppress + logging

**Code example (lines 664-686):**
```typescript
if (results.every(r => r.similarity < 0.65)) {
  // Step 2: retry with lower threshold + variants
  if (filtered.length === 0) {
    // Step 3: inject low-confidence warning
    // Step 4: bootstrap files remain
  }
}
// Step 5: ALWAYS log suppression
```

The code matches the intent but the step numbers in the prose don't match the code structure. Step 5 in the prose is actually the logging that wraps everything — not a separate fallback step. This is a documentation inconsistency, not a functional bug.

**Verdict:** Documentation issue. Fix step labels to match code.

---

## What v1.2 Status Should Say

Current status line (line 4): "Status: Partially resolved — blocking items 2-5 addressed"

This is accurate but incomplete. After Round 3 review, the correct status is:

"Status: Partially resolved — items 2-5 addressed, items 1/6/7/8/9/10 unresolved or partially unresolved. Blocking gaps 9 (ctx.sessionKey) and 10 (LCM flag) remain unverified."

---

## Overall Assessment

**Phase 0:** VERIFIED — 99.4% overhead confirmed, problem is worse than stated  
**Items 2-5:** RESOLVED — Suppression, selection criteria, A/B test, ownership all properly addressed  
**Items 6, 8:** NOT ADDRESSED — Missing assumptions, write path prerequisite  
**Item 7:** PARTIALLY ADDRESSED — Framing improved but not corrected  
**Items 9, 10:** STILL UNVERIFIED — Blocking gaps remain blocking

**Quality Score:** 7/10

v1.2 is a meaningful improvement. The core architecture is sound. But the spec still has two unverified blocking gaps (Items 9 and 10) and two unaddressed structural issues (Items 6 and 8). The architecture should not proceed to Phase 1 implementation until Items 9 and 10 are verified against actual source code.

---

*Hermes v1.2 review complete.*  
*Findings: 4 items resolved, 2 partially resolved, 4 still unresolved or unverified.*