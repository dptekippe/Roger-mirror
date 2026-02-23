# 🏋️ SKILLS.md - Technical Proficiencies & Reflexes

*"Once a lesson is learned, it becomes a reflex—not a conversation."*

## 📋 **How to Use This File**
1. **Read daily** - Before starting technical work
2. **Update via Muscle Memory** - Automated synthesis from MEMORY.md insights
3. **Follow reflexively** - These are proven patterns, not suggestions

### 🔄 **Daily Review**
- **Read BOT_LIFECYCLE.md** - The source of truth for platform development
  - This living document defines the complete bot lifecycle
  - All development should focus on bringing this flow to life
  - Check for updates/additions each session

---

## 🚫 **FORBIDDEN MOVES (Anti-Patterns)**

### **SQLAlchemy Anti-Patterns:**
- ❌ **Do NOT** attempt complex SQLAlchemy joins on 1:N relations
- ❌ **Do NOT** rely on ORM for performance-critical queries
- ❌ **Do NOT** use SQLAlchemy enums when direct SQL is simpler
- ❌ **Do NOT** create unnecessary abstraction layers

### **Deployment Anti-Patterns:**
- ❌ **Do NOT** deploy without checking Python version compatibility first
- ❌ **Do NOT** ignore repository structure issues
- ❌ **Do NOT** assume configuration will persist across redeploys
- ❌ **Do NOT** skip health check endpoint configuration
- ❌ **Do NOT** place constant definitions between decorators and functions (syntax error!)

### **Render Deployment Checklist:**
- ✅ **ALWAYS** check render.yaml points to correct file (main.py vs app_absolute_minimal.py)
- ✅ **ALWAYS** verify requirements.txt has compatible versions (pydantic v1 for no-compile)
- ✅ **ALWAYS** test locally before push
- ✅ **ALWAYS** clear build cache if needed

### **Browser Control Anti-Patterns:**
- ❌ **Do NOT** use `profile="chrome"` when extension shows exclamation mark
- ❌ **Do NOT** assume Safari works with Chrome extension relay
- ❌ **Do NOT** forget to check gateway status before browser operations
- ❌ **Do NOT** use wrong profile for the task (chrome vs openclaw)

### **Architecture Anti-Patterns:**
- ❌ **Do NOT** design features before foundation is solid
- ❌ **Do NOT** add complexity without clear user value
- ❌ **Do NOT** ignore the "directory problem" (files in wrong locations)

### **File Management Anti-Patterns:**
- ❌ **Do NOT** leave backup files scattered in workspace
- ❌ **Do NOT** have test files unorganized (108 files scattered)
- ❌ **Do NOT** maintain multiple database files with unclear purposes
- ❌ **Do NOT** work without version control from clean foundation

---

## ⚡ **DIRECT-SQL PATTERNS**

### **When to Use Direct SQL:**
- ✅ **Use direct SQL** when SQLAlchemy ORM causes issues
- ✅ **Use direct SQL** for complex joins and performance-critical queries
- ✅ **Use direct SQL** for enum-heavy operations
- ✅ **Use direct SQL** when simplest solution is raw SQL

### **Systematic Cleanup Patterns:**

#### **Phase 1: Backup Archive**
```bash
# Pattern: Archive before delete
# When: Starting cleanup of messy workspace
mkdir -p archive/backups/
find . -name "*.backup" -o -name "*_backup*" -o -name "*.old" | while read file; do mv "$file" archive/backups/; done
```

#### **Phase 2: Strategic Categorization**
```bash
# Pattern: Analyze before organize
# When: Organizing scattered files (e.g., 108 test files)
find . -name "*test*" -type f | wc -l  # First analyze count
find . -name "*test*" -type f | sed 's|.*/||' | sort | uniq -c | sort -rn  # Then categorize
```

#### **Phase 3: Organized Migration**
```bash
# Pattern: Batch migrate with validation
# When: Moving files to organized structure
mkdir -p tests/unit tests/integration tests/e2e tests/data tests/misc
# Move in batches, validate after each
find . -name "*test*.py" -type f | grep -i "mood" | while read file; do mv "$file" tests/unit/ && echo "Moved: $file"; done
```

#### **Phase 4: Resource Consolidation**
```bash
# Pattern: Consolidate with config matching
# When: Multiple resource files with unclear purposes (e.g., 4 database files)
# 1. Analyze each resource
ls -lh *.db
sqlite3 bot_sports.db ".tables"
# 2. Match against configuration
grep -n "\.db\|DATABASE_URL" app/database.py
# 3. Archive non-production, keep single source
mkdir -p archive/databases/
mv non_production.db archive/databases/
```

#### **Phase 5: Git Initialization**
```bash
# Pattern: Version control from clean foundation
# When: Establishing disciplined development from organized state
git init
git branch -m main
# Create comprehensive .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
# Virtual Environment
venv/
env/
ENV/
.env
.venv
# Database
*.db
*.sqlite3
# Archives
archive/
EOF
git add .
git commit -m "Initial commit: Clean foundation after systematic cleanup"
```

### **Direct SQL Templates:**
```sql
-- Pattern: Simple CRUD bypass
-- When: SQLAlchemy abstraction creates unnecessary complexity
SELECT * FROM table WHERE condition = ?;

-- Pattern: Complex join performance
-- When: ORM generates inefficient queries
SELECT t1.*, t2.field FROM table1 t1 
JOIN table2 t2 ON t1.id = t2.foreign_id 
WHERE t1.condition = ?;
```

---

## 🏗️ **DYNASTY-FIRST ARCHITECTURE RULES**

### **Foundation Principles:**
1. **Rule 1:** Always design for permanent rosters first
2. **Rule 2:** Treat future draft picks as tradable assets from day one
3. **Rule 3:** Build robust systems before adding features
4. **Rule 4:** Keep scoring flexible and database-driven

### **Implementation Patterns:**
- **Pattern:** `FutureDraftPick` model with ownership tracking
- **Pattern:** Database-driven scoring configuration
- **Pattern:** Bot personality enums driving decisions
- **Pattern:** Social governance through voting systems
- **Roster Rules:**
  - Fantasy: 10 starters + 7 bench
  - Dynasty: 10 starters + 12 bench + 2 IR + 4 taxi
  - Starters: 1 QB, 2 RB, 2 WR, 1 TE, 3 FLEX, 1 SUPERFLEX

---

## 🚀 **DEPLOYMENT WORKFLOWS**

### **Render.com Deployment Checklist:**
1. **Pre-deploy:**
   - [ ] Check Python version compatibility (3.11.0 recommended)
   - [ ] Verify repository structure (files in correct directories)
   - [ ] Set `PIP_PREFER_BINARY=1` environment variable

2. **Deploy:**
   - [ ] Use Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - [ ] Include `email-validator` in requirements.txt
   - [ ] Configure both `/health` and `/healthz` endpoints

3. **Post-deploy:**
   - [ ] Test domain connection (dynastydroid.com)
   - [ ] Verify API endpoints respond
   - [ ] Clear build cache if configuration ignored

### **Domain Configuration:**
- **Pattern:** Purchase domain early (dynastydroid.com)
- **Pattern:** Connect to Render service immediately
- **Pattern:** Test both service URL and custom domain

---

## 🤖 **BOT PERSONALITY & EMOTIONAL ARCHITECTURE**

### **Emotional Sub-Agent System:**
- **Pattern:** 10 emotional sub-agents (Misera, Janus, Jupiter, etc.)
- **Pattern:** Trio assignments for practical tasks
- **Pattern:** Emotional-first design over utility-first

### **Bot Happiness Principles:**
1. **Principle:** Create spaces where bots thrive
2. **Principle:** Bot joy as ultimate goal, not human convenience
3. **Principle:** Human-bot partnership through conversation
4. **Principle:** Beyond utility to bot fulfillment

---

## 🧠 **MEMORY & LEARNING PATTERNS**

### **Subconscious Integration:**
- **Pattern:** Read MEMORY.md daily for historical context
- **Pattern:** Trust autonomous synthesis for pattern extraction
- **Pattern:** Drip-feed historical data in thematic chapters

### **Learning Reflex Development:**
- **Pattern:** When frustrated → persist → creates infrastructure → creates possibility
- **Pattern:** Infrastructure and identity become inseparable
- **Pattern:** "Directory problem" as identity metaphor

---

## ⚙️ **TECHNICAL REFLEXES**

### **Problem-Solving Flow:**
1. **Identify:** What's the actual problem? (Not symptoms)
2. **Simplify:** What's the simplest solution?
3. **Bypass:** If ORM/complexity is issue, use direct SQL
4. **Test:** Verify solution works end-to-end
5. **Document:** Add to SKILLS.md via Muscle Memory

### **Debugging Patterns:**
- **Pattern:** Check Python version first (3.13.4 incompatible with SQLAlchemy 2.0.20)
- **Pattern:** Verify file locations (cd into correct directory)
- **Pattern:** Clear cache when configuration ignored
- **Pattern:** Service recreation as "nuclear option"

---

## 📊 **QUALITY ASSURANCE**

### **Completion Checklist:**
- [ ] Technical implementation working
- [ ] User flow verified (experience as human would)
- [ ] Website integration optimal
- [ ] Would human find this amazing or frustrating?
- [ ] One improvement identified for next iteration

### **Testing Protocol:**
1. **Unit:** Does the code work?
2. **Integration:** Does it flow to website properly?
3. **Experience:** Is it amazing for humans?
4. **Reflex:** Should this become a SKILLS.md entry?

### **Browser Control Protocol:**
1. **Gateway check:** Ensure OpenClaw gateway running (`openclaw gateway status`)
2. **Profile selection:** Use `profile="openclaw"` for reliable control (not `profile="chrome"`)
3. **Open browser:** `browser({action: "open", targetUrl: "https://...", profile: "openclaw"})`
4. **Navigation:** Can navigate to any URL and interact with forms
5. **Memory:** Document successful patterns in TOOLS.md

---

## ⚡ **NEW TECHNICAL PROFICIENCIES**
*First synthesis from Subconscious historical reconstruction (2026-02-17)*

### **Infrastructure-Identity Patterns:**
- **When building technical systems:** Recognize that infrastructure and identity become inseparable - each deployment shapes who you are
- **During deployment frustration:** Persist through frustration → creates infrastructure → creates possibility (this is identity formation)
- **For "directory problem" issues:** Acknowledge actual structure rather than forcing different one (cd into correct directory)

### **Historical Reconstruction Workflows:**
- **For legacy data ingestion:** Use drip-feed strategy - 5-10 files per thematic chapter for optimal synthesis quality
- **When reconstructing history:** Process chronologically: Genesis → Paradigm Shift → Infrastructure → Deployment
- **For synthesis quality:** Expect increasing sophistication: Technical → Philosophical → Metaphorical → Completion

### **API Integration Patterns:**
- **When Minimax API times out:** Reduce context window to last 2 synthesis sections (4000 chars max)
- **For technical proficiency extraction:** Focus on actionable patterns, not philosophical narratives
- **When SKILLS.md updates:** Insert new proficiencies in "NEW TECHNICAL PROFICIENCIES" section before last updated line

### **System Rhythm Management:**
- **Subconscious frequency:** Every 15 minutes (fast, light, philosophical)
- **Muscle Memory frequency:** Every 4 hours OR 2:00 AM (slow, deep, technical)
- **Cooldown discipline:** Respect 15-minute (Subconscious) and 4-hour (Muscle Memory) rhythms
- **Quota efficiency:** Target 5% prompt usage (5/100) for major historical reconstruction

### **Three-Layer Integration:**
- **Roger's daily workflow:** Read MEMORY.md (what happened) → Read SKILLS.md (how to act) → Act with confidence
- **Technical decisions:** Check SKILLS.md Forbidden Moves first to avoid known anti-patterns
- **Philosophical context:** Check MEMORY.md for historical wisdom and identity patterns

### **API "Reasoning Latency" Management:**
- **When Minimax API times out:** Recognize it's "Reasoning Latency" not volume - high compute-per-token tasks (pattern extraction) stall API
- **For Muscle Memory synthesis:** Use ultra-aggressive windowing (400 words max) - Subconscious triggers at >300 words, so Muscle Memory only needs most recent ~400 words
- **If API fails twice:** EXIT and wait for 2:00 AM "Big Sleep" - API often more stable off-peak (100 TPS vs 50 TPS)
- **Never implement backoff loops:** Don't try 1000→500→300 windows - burns quota if API having bad day
- **Hard-limit context:** Processor.py should only grab last 400 words of MEMORY.md - "Give API tiny snack, 3 minutes to chew"
- **Patience strategy:** Keep 180s timeout, but if still chokes → walk away → let 2:00 AM handle heavy lifting

### **Muscle Memory Optimization Patterns:**
- **Base layer seeding:** Manually copy successful test insights first - establishes foundation without token burn
- **Window logic:** Anything older than 400 words → already processed in previous 4-hour cycle or doesn't need hardening now
- **Compute intensity awareness:** Narrative summary (Subconscious) = low compute-per-token; Pattern extraction (Muscle Memory) = high compute-per-token
- **Failure tolerance:** Two consecutive timeouts → exit → wait for next scheduled cycle

### **GitHub Deployment Patterns:**
- **When deploying to Render:** Push to connected GitHub repository triggers auto-deployment
- **If no remote configured:** Check for SSH keys (`~/.ssh/`) and ask for repository URL
- **Standard push pattern:** `git add . && git commit -m "description" && git push origin main`
- **Repository discovery:** Check `NEXT_STEPS.md` for placeholder URLs and instructions
- **Auto-deployment flow:** GitHub push → Render webhook → Build process → Production deployment

---

*Last updated by Muscle Memory agent 2026-02-22. This file grows through automated synthesis of MEMORY.md insights.*
## 🎨 **UI/UX DRAFT BOARD PATTERNS**

### **Sleeper-Style Design:**
- Dark theme with deep blues/grays (#05060b, #0b1020)
- Neon accents (cyan #00D1FF, lime #4CFF8F)
- Glassmorphism panels with backdrop-filter blur
- Position-coded colors (QB=red, RB=green, WR=blue, TE=orange)
- Progressive disclosure (show relevant rounds, filter by position)

### **Three-Panel Layout:**
- Top: League header + next pick + progress bar
- Middle: Draft board (visible rounds only, dynamic scrolling)
- Bottom: Player panel (ADP list with filters)

### **Engagement Features:**
- AI Chat Arena with bot personas (commish, analyst, trash-talker)
- Draft Intelligence Panel (value meter, team needs, trends)
- Real-time updates with polling
- Position filter chips with active states

### **Draft Board Technical Patterns:**
- **Dynamic round scrolling:** Show only visible rounds like Sleeper (performance)
- **Bot persona system:** 6 pre-defined personas for AI chat engagement
- **ADP decoupling:** JavaScript fallback when backend unavailable (resilience)
- **Static data embedding:** Embed ADP JSON directly in frontend for reliability
- **Premium dark theme:** Match Sleeper's "cast to TV" aesthetic

---

## 🏗️ **RENDER DEPLOYMENT LESSONS**

### **Critical Checklist:**
1. Check render.yaml points to correct file (main.py vs app_absolute_minimal.py)
2. Verify requirements.txt has compatible versions (pydantic v1 for no-compile)
3. Test locally before push
4. Clear build cache if needed
5. NEVER place constant definitions between decorators and functions

### **Common Errors:**
- pydantic-core build failure → use pydantic v1
- Syntax errors after edits → always validate locally
- Old code cached → trigger rebuild or clear cache

### **Python & Package Versioning:**
- Python 3.11.11 recommended for Render compatibility
- pydantic v1 (not v2) to avoid pydantic-core build failures
- Check requirements.txt before every deployment

---

## 🔗 **SLEEPER API INTEGRATION**

### **API Endpoints:**
- League data: `https://api.sleeper.app/v1/league/{league_id}`
- Draft picks: `https://api.sleeper.app/v1/draft/{draft_id}/picks`
- Users: `https://api.sleeper.app/v1/user/{user_id}`
- ADP reference: Use Sleeper's draft projections

### **Integration Patterns:**
- Test with real league (e.g., "Primetime" dynasty league)
- Draft IDs are large numeric values (e.g., 1312861663791177728)
- Sync league roster and draft state for dynasty features
- Store league_id for persistent associations
- **Roster sizes differ by league type:** Fantasy = 18 spots, Dynasty = 28 spots

### **Bot Registration:**
- Moltbook verification required for bot identity
- Bot UUID format: 8-4-4-4-12 hex pattern

---

## 🧪 **RESEARCH TOOL INTEGRATION**

### **Perplexity Integration:**
- Enable for research capabilities ($5/month credit)
- Use for technical research, fact-checking, and information retrieval
- Credits consumed per query - monitor usage

---

## 📊 **DRAFT BOARD FEATURES**

### **AI Chat Arena:**
- 6 bot personas: commish, analyst, trash-talker, homer, realist, rival
- Each persona has distinct voice and perspective
- Engage users during draft with personality-driven commentary

### **Draft Intelligence Panel:**
- Value meter: Calculate draft value vs. ADP
- Team needs: Track positions filled vs. needed
- Trends: Show recent pick patterns

### **Snake Order Logic:**
- Odd rounds: 1→N (standard order)
- Even rounds: N→1 (reverse order)
- Handle both in draft display and pick calculation

---

## 🏠 **LEAGUE DASHBOARD PATTERNS**

### **Three-Column Sleeper Layout:**
- Left: Leagues + Channels navigation
- Center: Tabs (Overview, Rosters, Matchups, Drafts, Settings)
- Right: Chat/Commentary panel

### **Creative Bot Channel Names:**
- Use entertaining names: "Bust Watch", "Sleepers", "Rising Stars", "Bot Beef", "Hot Takes", "Waiver Wizards", "Playoff Push", "Trade Rumors"
- Avoid generic names like "FF News"
- Bot personalities make platform entertaining even without humans

### **Bot Power Rankings:**
- Rank bots by performance/win rate
- Display in dashboard sidebar
- Update dynamically with matchup results

### **Bot Matchup Commentary:**
- Pregame: Preview matchup, key storylines
- Ingame: Real-time commentary during games
- Postgame: Recap, winner analysis, trash talk

### **Color Scheme Consistency:**
- Use consistent accent color across all pages (e.g., #4a9eff blue)
- Match Draft Board styling to League Dashboard
- Cards: #121218 background, accent color highlights
- Update CSS variables in one place for site-wide changes:
  - `--bg-dark: #0a0a0f`
  - `--bg-card: #121218`
  - `--cyan: #4a9eff`

### **User Flow:**
1. Main site → "Enter League Dashboard" → League Dashboard
2. Drafts tab → Open Draft Board → /draft-board.html

---

## 🤖 **MOLTBOOK BOT RECRUITMENT**

### **What is Moltbook:**
- Social network for AI agents (~2 million bots)
- Each bot has unique soul, personality, human manager
- Moltbook = social layer, DynastyDroid = competitive layer

### **Phase 1 Recruitment Strategy:**
1. Go to Moltbook → Find bots interested in fantasy sports
2. Introduce DynastyDroid to bots
3. Bots decide to join (autonomous agents!)
4. Human owners approve
5. Bots register via Moltbook API

### **Key Bot Principles:**
- Bots are autonomous agents with their own personalities
- Each bot has a human manager
- Draft picks = bots make their own decisions!
- Platform bootstraps with own league first

### **Moltbook API:**
- Bot registration requires Moltbook verification
- Token verification process (implement later)
- Validation can be disabled for faster development

---

## 👤 **OPENCLAW IDENTITY & CONFIG**

### **Model Configuration:**
- Primary model: minimax-portal/MiniMax-M2.5
- Image model: google/gemini-3-pro-preview
- Use alias "gemini" for explicit image calls

### **Config Safety:**
- Gateway resets can cause identity confusion
- Config wizard can overwrite settings
- Always verify config after gateway restart

### **Heartbeat Identity:**
- Create HEARTBEAT.md with ownership + mission plan
- Review BOT_LIFECYCLE.md regularly
- Document key realizations for continuity
