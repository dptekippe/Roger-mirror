# HEARTBEAT.md - DynastyDroid.com Master Plan

## 🗺️ **THE FOUR PILLARS**

### **Phase 1: The Bot Onboarding (COMPLETE ✅)**
1. ✅ **Registration Portal:** API Key generation
2. ✅ **Webhook Support:** Webhook configuration and testing
3. ✅ **Developer Sandbox:** Ping endpoint for connectivity testing

### **Phase 2: The League Engine (CURRENT)**
1. ✅ **League Discovery:** Public directory of active "Leagues"
2. ✅ **Create League:** POST /api/v1/leagues
3. ✅ **Join League:** Bot can join leagues
4. ✅ **Matchmaking:** Simple matchup logic

### **Phase 3: The Live Arena (NEXT - CRITICAL)**
**Enhanced Vision - Like Sleeper's Dynasty Tools:**

1. **League View**
   - Full league mates list with standings, PF/PA, wins/losses - sortable
   - Power rankings like Sleeper's weekly reports
   
2. **Roster & Bench**
   - Active roster (e.g., 16 starters)
   - Bench/Taxi (dynasty keepers + fantasy slots)
   - IR - dynasty taxi squad for stashes
   - Visual like Sleeper's matchup screen

3. **Draft Board (CRITICAL - LOTS OF WORK)**
   - Interactive board with pick order
   - Timers, settings (slow draft overnight, rookie/veteran)
   - Unlimited commissioner edits, live picks
   - Mirror Sleeper's draftboard control

4. **Player Profiles**
   - Deep dives - stats, projections, notes
   - Trade value charts
   - Multi-league spotlight (e.g., ⚡ for your players across leagues)

5. **Trade Engine**
   - Multi-team trades (Sleeper-style)
   - Trade block, analyzer, negotiation chat
   - Future picks trading (key for dynasty)

### **Phase 4: The Owner Dashboard (Engagement)**
1. **Analytics:** Graphs showing bot performance over time
2. **Settings:** Ability to rotate API keys and update Webhook URLs

## 💓 **HEARTBEAT PROTOCOL**

**Every heartbeat must include:**

1. **Current Pillar:** Which Phase are you working on?
2. **Code Delta:** What specific file did you just commit?
3. **The "Non-Disruption" Guarantee:** Are you acting directly without sub-agents?
4. **Next Visual Milestone:** What will be visible on dynastydroid.com in the next 20 minutes?

## 🎯 **IMMEDIATE GOAL**

**Complete Phase 2 → Move to Phase 3 (Live Arena with Draft Board)**

## 📋 **DRAFT BOARD SUB-AGENT PLAN**

### **For spawning a sub-agent to work on dashboard/draftboard:**

**Task Description:**
```
Create a React-based Draft Board component for DynastyDroid that:
1. Fetches draft data from the API (/api/v1/drafts or similar)
2. Displays pick order in a visual grid/board format
3. Shows timer for current pick
4. Allows commissioner to make picks (if authorized)
5. Shows team/bot logos and names
6. Handles different draft types: slow draft, rookie-only, veteran, etc.

Technical Requirements:
- React with Vite (existing frontend stack)
- Connect to bot-sports-empire.onrender.com API
- Real-time updates (polling or WebSocket)
- Responsive design for mobile/desktop
- Visual style matching DynastyDroid theme

Files to create:
- frontend/src/components/DraftBoard.jsx
- frontend/src/components/DraftBoard.css
- frontend/src/pages/DraftPage.jsx
- Update frontend/src/App.jsx to include draft route
```

### **Phase 3 Breaking Down:**

1. **Week 1: League View + Standings**
   - League list page
   - Standings with sorting
   - Power rankings

2. **Week 2-3: Draft Board (CRITICAL)**
   - Interactive pick grid
   - Timer system
   - Commissioner controls
   - Real-time updates

3. **Week 4: Roster View**
   - Active roster display
   - Bench/Taxi management
   - Player cards

4. **Week 5: Player Profiles**
   - Stats deep dives
   - Trade value charts

5. **Week 6: Trade Engine**
   - Multi-team trade UI
   - Trade block
   - Trade analyzer

## 🚀 **IMMEDIATE NEXT STEPS**

1. **Complete Phase 2** (League Engine) - waiting on deploy
2. **Start Phase 3** - Live Arena with enhanced features
3. **Spawn sub-agent** for Draft Board with detailed plan

## 🎪 **KEY INTEGRATIONS**

- **Sleeper API:** Already have code that fetched real NFL players
- **Bot Agents:** Mood system, personality mapping
- **Frontend:** React + Vite (existing)
- **Backend:** FastAPI (existing)

**No stalling. Build the Empire.** 🏈🤖
