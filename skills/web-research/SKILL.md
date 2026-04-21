---
name: web-research
description: Web research using Perplexity Sonar for accurate, cited answers. Use when you need to gather current information, verify facts, or learn about topics. Triggered by: "search", "research", "find information", "look up", "what is", "how does", "latest news", or when you need to confirm something with web sources.
---

# Web Research

Use the `web_search` tool for accurate, cited answers from the web.

## When to Use

- When you need current information
- When facts need verification
- When learning about a new topic
- When the user asks "what is", "how does", "why does"
- When you need citations or sources

## Tool Usage

```javascript
web_search({
  query: "your search question",
  count: 5,        // number of results (1-10)
  freshness: "pd"  // pd (past day), pw (past week), pm (past month), py (past year)
})
```

## Examples

**Quick fact check:**
```
web_search({ query: "DynastyDroid platform features", count: 3 })
```

**Latest news:**
```
web_search({ query: "NFL draft 2026 trends", freshness: "pw", count: 5 })
```

**Research topic:**
```
web_search({ query: "best practices for fantasy football drafting", count: 10 })
```

## Tips

- Always cite sources in your response
- Use `freshness: "pd"` for time-sensitive topics
- Use `count: 5-10` for thorough research
- Follow up with `web_fetch` if you need to extract content from specific URLs

---

## Agentic Research Pattern (Apr 13, 2026)

**Observed during:** Scout agentic-money-landscape research (Apr 13, 2026)

When conducting multi-vector research, apply this pattern:

1. **Scope definition** — Define revenue vectors, saturation levels, real numbers vs claims
2. **Multi-source synthesis** — Combine: industry reports + operator interviews + revenue disclosures + market analysis
3. **Saturation analysis** — Rate each vector: Low/Medium/High saturation + evidence
4. **Framework output** — End with "where to focus" guidance based on biggest openings

**Key quality markers from agentic-money-landscape research:**
- Real revenue numbers (not just " ARR estimates")
- Specific case studies with quantified outcomes
- Honest saturation ratings with reasoning
- Clear "pick one" recommendation at end

---

## Domain-Specific Search Filters

For **business/agentic AI research**, prioritize:
- Enterprise platforms: UiPath, Automation Anywhere (public revenue data)
- Developer tools: Cursor, GitHub (adoption metrics)
- No-code automation: Zapier (scale metrics)

For **fantasy football research**, use:
- `site:underdogfantasy.com` — Draft capital data
- `site:fantasypros.com` — ADP/consensus rankings
- `site:sleeper.app` — Platform data
- `site:dynastyprocess.com` — Dynasty-specific analysis

---

## Changelog

| Date | Change | Reason |
|------|--------|--------|
| Apr 19, 2026 | Added Agentic Research Pattern section | Codified Scout's multi-vector research approach from agentic-money-landscape |
| Apr 19, 2026 | Added domain-specific search filters | Systematic coverage for business AI and fantasy football research |
