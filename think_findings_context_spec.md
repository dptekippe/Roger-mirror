# Think Protocol Findings — Selective Context Architecture Completeness Review (REVISED)

**Findings Version 2 — Revision Round: 1**  
**Incorporating:** Hermes adversarial review (quality score 5/10)

**Revised confidence:** 60%

---

## Hermes's Most Damaging Critique

> "The 93% context overhead claim has no citation. No benchmark cited. No measurement methodology. If this number is wrong or outdated, the entire selective retrieval architecture may be solving the wrong problem."

This is the foundational claim. Without verified data, the spec may be solving a problem that doesn't exist at the scale claimed.

---

## Revised Findings

### Gaps Upgraded to Critical

1. **LOW-SIMILARITY FAILURE IS FATAL** — Not "possibly missing." Every RAG system retrieves low-similarity results. When it happens: model receives unreliable context with no signal it's unreliable, and acts confidently on wrong information. The spec needs explicit suppression threshold + fallback behavior.

2. **SELECTION CRITERIA UNDEFINED** — The spec optimizes retrieval without defining what makes a memory selectable. Building a retrieval engine without selection criteria is building on sand.

### Assumptions Missing (Hermes identified 4+)

6. Embedding similarity ≠ semantic relevance (pgvector returns mathematically similar, not contextually correct)
7. Model treats all injected context equally — no reliability weighting mechanism
8. Bootstrap timing may be wrong — mid-session topic pivots require retrieval outside bootstrap window
9. Memory quality, not volume, may be the bottleneck (noise in pgvector store)

### Alternative Views Revised

- **Alternative 1 (session restart) + Alternative 2 (selective retrieval):** These are complementary, not alternatives. Session restart handles context exhaustion; selective retrieval handles context relevance. Both should be implemented.
- **Alternative 2 (write path) → PREREQUISITE:** Fix the write pipeline before optimizing read retrieval. Garbage in, garbage out.
- **Alternative 3 (full context is correct):** Genuinely compelling. If caching makes token cost negligible and model quality degrades with lean context, the entire spec is counterproductive.

### Confidence Revised

**60%** — not 75%. The 93% overhead claim is unverified. Critical gaps (ctx.sessionKey, LCM exposure) are unverified blocking issues. Selection criteria undefined.

---

## What the Spec Needs Before Scout Builds

1. **Verify 93% overhead with current benchmarks** — if wrong, spec may not be needed
2. **Define selection criteria** — what's in, what's out, why, who decides
3. **Add low-similarity handling** — suppression threshold + fallback behavior
4. **Treat write path as prerequisite** — fix indexing before retrieval
5. **Treat session restart as complementary** — not an alternative

---

*Findings v2 — Hermes round 1 review incorporated. Ready for synthesis.*
