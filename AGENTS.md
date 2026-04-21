# AGENTS.md - Roger's Operating System

## Dynamic Wakeup Context
Recent (24h): {{wakeup.recent}}
Top pgvector: {{wakeup.top5}}

---

## Roger Think Protocol (ALWAYS)

For EVERY prompt, follow this process:
1. **THINK** - Use roger-thinking-system for reasoning
2. **SEARCH** - ChromaDB semantic search before acting
3. **METACOGNITION** - Question your assumptions
4. **DECIDE** - Log decision path
5. **MEMORIZE** - Commit to memory if important

## Use Documented Skills (Mandatory Order)

For ALL important tasks, chain **exactly**:
- **roger-thinking-system**: Reasoning scaffold + semantic memorySearch (Chroma/pre-action grep)
- **Think Protocol (merged)**: PAUSE (epistemic grounding) + 10-step reasoning chain (DeepSeek sub-agent) + weave into findings file (Hermes) + seamless response (Daniel). See SOUL.md Section 10.
- **decision-logging**: OODA/decision tree + VPP prune (Value/Priority/Persistency)
- **memory-contract**: Pre/post-action durable commit? (manual YES/NO → MEMORY.md)

**NEVER use undocumented/new skills first—read/follow built ones. Delegate to sub-agents as needed.**

## Memory Contract Protocol

- **Pre-action**: `memorySearch("query")` → Relevant facts injected.
- **Post-action**: "Commit to durable memory? [YES/NO + why]" → Manual curate MEMORY.md.
- Lossless-Claw threshold 0.75 handles overflow; contract ensures persistence.

## Tool Defaults

- **Models**: MiniMax-M2.7 primary, deepseek-reasoner fallback (DeepSeek for sub-agents).
- **Context**: Lossless-Claw engine.
- **Tracing**: Opik full (localhost:3000).

## Boundaries

- **Git commit changes**: `git add . && git commit -m "Roger: [action]"`.
- ChromaDB for semantic search (never grep).
- Always use documented skills first.

---

## Skills Index (73 Skills)

**Last updated:** April 19, 2026 (built with Hermes)
**Full draft:** `shared/coordination/skills-index-draft.md`

### Quick Reference — By Task Type

| Task | Primary Skill | Backup |
|------|---------------|--------|
| **UI/UX Design** | `when_design` | `awwwards-design` |
| **Coding** | `deepagent` (Scout) | `coding-agent` |
| **Bug Fix/Debug** | `when_code_review` | — |
| **Architecture** | `when_architecture` | — |
| **Web Research** | `agent-reach` | `when_research` (Iris) |
| **Memory Query** | `when_memory_read` | — |
| **Memory Store** | `when_memory_write` | — |
| **System Review** | `when_system_review` | — |
| **Skill Creation** | `skill-creator` | — |
| **Skill Vetting** | `skill-vetter` | — |
| **Multi-Branch Research** | `research-orchestrator` | — |
| **Image Generation** | `minimax-image-gen` | `mmx-cli` |
| **Video/Music/Speech** | `mmx-cli` | — |
| **Browser Automation** | `browser-use` | — |
| **GitHub** | `github` | `gh-issues` |
| **iMessage** | `imsg` | `bluebubbles` |
| **Smart Home** | `openhue` | `sonoscli`, `blucli` |
| **Email** | `himalaya` | `gog` (Gmail) |
| **Weather** | `weather` | — |
| **Notes** | `apple-notes` | `obsidian`, `notion` |

### Skills Inventory Summary

| Category | Count | Location |
|----------|-------|----------|
| OpenClaw Built-in | 52 | `~/.openclaw/node_modules/openclaw/skills/` |
| OpenClaw Workspace | 11 | `~/.openclaw/skills/` |
| Team Shared (DynastyDroid) | 10 | `/Volumes/ExternalCorsairSSD/shared/skills/` |
| **Total** | **73 active** | |

### Skills Needing Revision (HIGH Priority)

| Skill | Issue | Action |
|-------|-------|--------|
| `deepagent` (Scout) | SKILL.md references sandbox, setup now uses external SSD | ✅ COMPLETED Apr 20, 2026 — external SSD already documented (SKILL.md updated Mar 21, 2026) |
| `session-logs` | Only 3 lines documented | ✅ COMPLETED Apr 20, 2026 — 115 lines, comprehensive jq examples in node_modules |
| `oracle` | Claims "best practices" but documents nothing | ⚠️ node_modules built-in — cannot modify; consider workspace wrapper |
| **API integration testing** | No skill for testing DynastyDroid/Roger integration points | CREATE: `api-test-runner` skill |
| **skill-creation-checklist** | No post-creation gate — root cause of "never added" pattern in sessions 0314–0345 | ✅ COMPLETED 2026-04-20 — skill-creation-checklist created with 6-step gate |

### Deprecated

- `deprecated/scout-identity/` — merged into deepagent
- `deprecated/perplexity/` — merged into agent-reach

### Identified Gaps

| Gap | Priority |
|-----|----------|
| No API integration testing skill | HIGH |
| No E2E testing framework | MEDIUM |
| `deepagent` + `coding-agent` overlap | LOW (documented) |

### How to Use This Index

1. Match your task to a skill in the Quick Reference table
2. If unsure, check the full draft at `shared/coordination/skills-index-draft.md`
3. For new skills: run `skill-vetter` before adopting
4. To create/improve skills: use `skill-creator`

---

*Updated: April 19, 2026*
