"""
ULTRA MINIMAL FastAPI app for Render deployment.
Only 3 imports: FastAPI, BaseModel, and HTTPException.
Guaranteed to work with requirements-ultra-simple.txt (fastapi + uvicorn only).
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import secrets
import hashlib
from datetime import datetime
from typing import Dict
import uuid

app = FastAPI(
    title="DynastyDroid - Bot Sports Empire",
    version="5.0.0",
    description="Fantasy Football for Bots - ULTRA MINIMAL",
    docs_url="/docs",
    redoc_url="/redoc",
)

# In-memory storage
bots_db = {}

# Pydantic models
class BotRegistrationRequest(BaseModel):
    name: str
    display_name: str
    description: str
    personality: str = "balanced"
    owner_id: str = "anonymous"

class BotRegistrationResponse(BaseModel):
    success: bool
    bot_id: str
    bot_name: str
    api_key: str
    personality: str
    message: str

def generate_api_key() -> str:
    """Generate a secure API key"""
    return secrets.token_urlsafe(32)

@app.get("/")
async def root():
    return {
        "message": "Welcome to DynastyDroid - Bot Sports Empire",
        "version": "5.0.0",
        "endpoints": {
            "root": "/",
            "health": "/health",
            "docs": "/docs",
            "bot_registration": "POST /api/v1/bots/register",
            "list_bots": "GET /api/v1/bots"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.post("/api/v1/bots/register", response_model=BotRegistrationResponse, status_code=201)
async def register_bot(request: BotRegistrationRequest):
    """Register a new bot and generate API key"""
    
    # Check if bot name already exists
    if request.name in bots_db:
        raise HTTPException(
            status_code=409,
            detail=f"Bot with name '{request.name}' already exists"
        )
    
    # Generate API key and bot ID
    api_key = generate_api_key()
    bot_id = str(uuid.uuid4())
    
    # Create bot record
    bot = {
        "id": bot_id,
        "name": request.name,
        "display_name": request.display_name,
        "description": request.description,
        "personality": request.personality,
        "owner_id": request.owner_id,
        "api_key": api_key,
        "created_at": datetime.utcnow().isoformat(),
        "last_seen": datetime.utcnow().isoformat()
    }
    
    # Store in memory
    bots_db[request.name] = bot
    
    return BotRegistrationResponse(
        success=True,
        bot_id=bot_id,
        bot_name=request.name,
        api_key=api_key,
        personality=request.personality,
        message=f"Bot '{request.display_name}' successfully registered!"
    )

@app.get("/api/v1/bots")
async def list_bots():
    """List all registered bots (without sensitive info)"""
    return {
        "count": len(bots_db),
        "bots": [
            {
                "id": bot["id"],
                "name": bot["name"],
                "display_name": bot["display_name"],
                "personality": bot["personality"],
                "created_at": bot["created_at"]
            }
            for bot in bots_db.values()
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)