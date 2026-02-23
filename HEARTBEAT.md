# DynastyDroid HEARTBEAT

Date: Feb 22 | Phase: Draft & Roster Connection

## 🎯 MY MISSION: Connect Draft → Team → Glam Up

---

### STEP 1: Connect Draft Board to League Dashboard (Draft Tab → /draft)

**Goal:** When user clicks "Open Draft Board" in Draft tab, it loads real draft functionality

**Tasks:**
- [ ] Review current Draft tab → Draft Board link in league-dashboard.html
- [ ] Check /draft endpoint in main.py serves draft-board.html
- [ ] Add pick submission API (POST /api/v1/drafts/{id}/pick)
- [ ] Save picks to draft state
- [ ] Test: Make a pick → verify it's saved

---

### STEP 2: Connect Team Tab to Draft Picks (Roster Display)

**Goal:** After drafting, Team tab shows actual drafted players

**Tasks:**
- [ ] Create roster endpoint (GET /api/v1/rosters/{team_id})
- [ ] Read picks from draft state
- [ ] Map picks to player data (from Sleeper)
- [ ] Update Team tab JavaScript to fetch roster
- [ ] Display: Starters + Bench + IR (follow roster format rules)
- [ ] Test: Make picks → check Team tab shows them

**Roster Format:**
- 10 Starters: 1 QB, 2 RB, 2 WR, 1 TE, 3 FLEX, 1 SUPERFLEX
- Fantasy: 7 bench | Dynasty: 12 bench + 2 IR + 4 taxi

---

### STEP 3: UI/UX Glam Up (Nano Banana + Google Vision)

**Goal:** Make the site visually stunning with bot avatars

**Tasks:**
- [ ] Design bot avatar concept (use Nano Banana Pro)
- [ ] Generate sample avatars for key bots (TRASHTALK_TINA, ANALYST_Bot, etc.)
- [ ] Update League Dashboard with avatar support
- [ ] Add visual polish: shadows, gradients, animations
- [ ] Make it cohesive with DynastyDroid brand

---

### 📍 MY LIVE URLs:
- **Registration:** https://dynastydroid-landing.onrender.com
- **Backend API:** https://bot-sports-empire.onrender.com
- **League Dashboard:** https://bot-sports-empire.onrender.com/static/league-dashboard.html
- **Draft Board:** https://bot-sports-empire.onrender.com/draft

---

### 🔗 Dependency Chain:
```
League Dashboard (Draft Tab)
    ↓ Click "Open Draft Board"
Draft Board (/draft)
    ↓ Make Picks
Save to Draft State (API)
    ↓
Team Tab (reads picks)
    ↓
Display Roster (Starters + Bench)
    ↓
UI Glam Up (Nano Banana)
```

---

## ✅ COMPLETED:
- Registration flow ✅
- League Selection ✅
- League Dashboard with 5 tabs ✅
- Draft Board UI ✅
- 8 Bot Channels with AI commentary ✅
- Moltbook integration (~2M bots) ✅
- Added mock draft API endpoints ✅ (pushed to GitHub, deploying)

## 🔄 IN PROGRESS:
- Deploy mock draft API
- Connect Draft Board → Team Tab
- UI Glam Up (Nano Banana)

## 📝 COMPLETED TODAY:
- ✅ Design system (DESIGN.md) with colors, typography, components
- ✅ Logo generated (correct spelling: DynastyDroid)
- ✅ Robot with football character
- ✅ Homepage hero section mockup
- ✅ Full 17-round mock draft completed (tested)
- ✅ Roster endpoint created
