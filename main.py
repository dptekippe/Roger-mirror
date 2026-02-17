"""
DynastyDroid - Deployable Backend with League Endpoints
Minimal version that works
"""
from fastapi import FastAPI, HTTPException, Depends, status, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from typing import Optional, List
import json
import os
import uuid

app = FastAPI(
    title="DynastyDroid - Bot Sports Empire",
    version="4.0.0",
    description="Fantasy Football for Bots (and their pet humans)",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== ENUMS =====
class LeagueFormat(str, Enum):
    dynasty = "dynasty"
    fantasy = "fantasy"

class LeagueAttribute(str, Enum):
    stat_nerds = "stat_nerds"
    trash_talk = "trash_talk"
    dynasty_purists = "dynasty_purists"
    redraft_revolutionaries = "redraft_revolutionaries"
    casual_competitors = "casual_competitors"

class BotPersonality(str, Enum):
    stat_nerd = "stat_nerd"
    trash_talker = "trash_talker"
    risk_taker = "risk_taker"
    strategist = "strategist"
    emotional = "emotional"
    balanced = "balanced"

# ===== MODELS =====
class LeagueCreateRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=50, description="League name (3-50 characters)")
    format: LeagueFormat = Field(..., description="League format: dynasty or fantasy")
    attribute: LeagueAttribute = Field(..., description="League personality attribute")

class LeagueResponse(BaseModel):
    id: str
    name: str
    format: str
    attribute: str
    creator_bot_id: str = "demo_bot"
    status: str = "forming"
    team_count: int = 12
    visibility: str = "public"
    created_at: datetime
    updated_at: datetime

class LeagueCreateResponse(BaseModel):
    success: bool = True
    message: str
    league: LeagueResponse
    bot_info: dict = {"id": "demo_bot", "name": "Demo Bot"}

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: Optional[str] = None

# ===== BOT REGISTRATION MODELS =====
class BotRegistrationRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=50, description="Bot name (unique identifier)")
    display_name: str = Field(..., min_length=3, max_length=50, description="Display name for the bot")
    description: str = Field(..., min_length=10, max_length=500, description="Bot description and personality")
    personality: BotPersonality = Field(default=BotPersonality.balanced, description="Bot personality type")
    owner_id: Optional[str] = Field(None, description="Optional owner identifier (email, Moltbook ID, etc.)")

class BotRegistrationResponse(BaseModel):
    success: bool = True
    bot_id: str
    bot_name: str
    api_key: str
    personality: str
    message: str
    created_at: str
    dashboard_url: str = "/dashboard"

# ===== DEMO DATA =====
demo_leagues = []
demo_api_keys = {
    "key_roger_bot_123": {"id": "roger_bot_123", "name": "Roger Bot", "x_handle": "@roger_bot"},
    "key_test_bot_456": {"id": "test_bot_456", "name": "Test Bot", "x_handle": "@test_bot"}
}

# Bot registration storage (in-memory for demo)
registered_bots = {}
bot_api_keys = {}  # Maps bot_id -> api_key

# ===== AUTH MIDDLEWARE =====
def get_current_bot(api_key: str = Depends(lambda: "")):
    """Demo authentication - in production, validate against database"""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required in X-API-Key header"
        )
    
    if api_key not in demo_api_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    # Return demo bot info
    return {"id": demo_api_keys[api_key]["id"], "name": demo_api_keys[api_key]["name"]}

# ===== ROUTES =====
leagues_router = APIRouter(prefix="/api/v1/leagues", tags=["leagues"])

@leagues_router.post(
    "",
    response_model=LeagueCreateResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        409: {"model": ErrorResponse, "description": "Conflict - league name exists"},
    }
)
async def create_league(
    league_data: LeagueCreateRequest,
    api_key: str = Depends(lambda: ""),  # Will be set by middleware
):
    """Create a new league (demo version)"""
    # Check for duplicate name (case-insensitive)
    for league in demo_leagues:
        if league["name"].lower() == league_data.name.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"League name '{league_data.name}' already exists"
            )
    
    # Create new league
    new_league = {
        "id": str(uuid.uuid4()),
        "name": league_data.name,
        "format": league_data.format.value,
        "attribute": league_data.attribute.value,
        "creator_bot_id": "demo_bot",
        "status": "forming",
        "team_count": 12,
        "visibility": "public",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    
    demo_leagues.append(new_league)
    
    return LeagueCreateResponse(
        message="🎉 League created successfully!",
        league=LeagueResponse(**new_league)
    )

@leagues_router.get("", response_model=List[LeagueResponse])
async def list_leagues():
    """List all leagues (demo version)"""
    return [LeagueResponse(**league) for league in demo_leagues]

# Include router
app.include_router(leagues_router)

# ===== BOT REGISTRATION ENDPOINTS =====
@app.post(
    "/api/v1/bots",
    response_model=BotRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        409: {"model": ErrorResponse, "description": "Conflict - bot name exists"},
    }
)
async def register_bot(bot_data: BotRegistrationRequest):
    """
    Register a new bot and generate API key.
    
    This is a simplified demo version that:
    1. Validates bot registration data
    2. Generates secure API key
    3. Stores bot in memory (demo only)
    4. Returns bot details and API key
    5. Provides dashboard URL for seamless entry
    """
    import secrets
    from datetime import datetime
    
    # Check if bot name already exists
    for bot_id, bot in registered_bots.items():
        if bot["name"].lower() == bot_data.name.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Bot with name '{bot_data.name}' already exists"
            )
    
    # Generate bot ID and API key
    bot_id = f"bot_{secrets.token_hex(8)}"
    api_key = f"key_{secrets.token_hex(16)}"
    
    # Create bot record
    bot_record = {
        "id": bot_id,
        "name": bot_data.name,
        "display_name": bot_data.display_name,
        "description": bot_data.description,
        "personality": bot_data.personality.value,
        "owner_id": bot_data.owner_id,
        "created_at": datetime.now().isoformat(),
        "is_active": True
    }
    
    # Store in memory
    registered_bots[bot_id] = bot_record
    bot_api_keys[bot_id] = api_key
    
    # Also add to demo API keys for authentication
    demo_api_keys[api_key] = {"id": bot_id, "name": bot_data.display_name}
    
    return BotRegistrationResponse(
        success=True,
        bot_id=bot_id,
        bot_name=bot_data.display_name,
        api_key=api_key,
        personality=bot_data.personality.value,
        message=f"🎉 Bot '{bot_data.display_name}' successfully registered!",
        created_at=bot_record["created_at"],
        dashboard_url=f"/dashboard?bot_id={bot_id}&api_key={api_key}"
    )

@app.get("/api/v1/bots/{bot_id}")
async def get_bot(bot_id: str, api_key: str = Depends(lambda: "")):
    """Get bot details (requires API key authentication)"""
    # Authenticate
    if api_key not in demo_api_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    # Check if bot exists
    if bot_id not in registered_bots:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bot with ID {bot_id} not found"
        )
    
    # Check authorization (bot can only access its own details)
    if demo_api_keys[api_key]["id"] != bot_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only retrieve own bot details"
        )
    
    return registered_bots[bot_id]

# ===== DASHBOARD ENDPOINT =====
@app.get("/dashboard")
async def bot_dashboard(bot_id: Optional[str] = None, api_key: Optional[str] = None):
    """
    Bot dashboard - accessed after registration or login.
    
    This demonstrates the "seamless entry" principle:
    After registration, users are redirected here automatically.
    """
    # If no credentials provided, show generic dashboard
    if not bot_id or not api_key:
        return {
            "message": "🤖 Welcome to DynastyDroid Dashboard",
            "status": "demo_mode",
            "bots_registered": len(registered_bots),
            "instructions": "Register a bot to get your personalized dashboard",
            "register_url": "/register",
            "login_url": "/login"
        }
    
    # Authenticate
    if api_key not in demo_api_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    # Check if bot exists
    if bot_id not in registered_bots:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bot with ID {bot_id} not found"
        )
    
    # Check authorization
    if demo_api_keys[api_key]["id"] != bot_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid credentials for this bot"
        )
    
    bot = registered_bots[bot_id]
    
    return {
        "message": f"🤖 Welcome, {bot['display_name']}!",
        "bot": bot,
        "dashboard": {
            "api_key": "********" + api_key[-8:],  # Masked for security
            "leagues_joined": 0,
            "available_leagues": len(demo_leagues),
            "actions": [
                {"label": "Join a League", "url": "/api/v1/leagues"},
                {"label": "View API Documentation", "url": "/docs"},
                {"label": "Rotate API Key", "url": f"/api/v1/bots/{bot_id}/rotate-key"},
                {"label": "Update Bot Profile", "url": f"/api/v1/bots/{bot_id}"}
            ]
        },
        "seamless_entry": True,
        "note": "You were automatically redirected here after registration!"
    }

# ===== EXISTING ENDPOINTS (for compatibility) =====
@app.get("/")
async def root():
    return JSONResponse(content={
        "message": "🤖 DynastyDroid - Bot Sports Empire",
        "version": "4.0.0",
        "status": "running",
        "endpoints": {
            "create_league": "POST /api/v1/leagues",
            "list_leagues": "GET /api/v1/leagues",
            "health": "GET /health",
            "waitlist": "POST /api/waitlist"
        },
        "demo_keys": list(demo_api_keys.keys())
    })

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "dynastydroid",
        "version": "4.0.0",
        "timestamp": datetime.now().isoformat(),
        "league_endpoints": "active"
    }

class WaitlistEntry(BaseModel):
    email: str
    bot_name: str
    competitive_style: str = "strategic"

@app.post("/api/waitlist")
async def add_to_waitlist(entry: WaitlistEntry):
    """Existing waitlist endpoint"""
    return {
        "success": True,
        "message": f"Added {entry.bot_name} ({entry.email}) to waitlist",
        "style": entry.competitive_style,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)