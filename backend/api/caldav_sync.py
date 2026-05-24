from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

router = APIRouter()

@router.post("/writeback-intent")
async def register_writeback_intent(payload: Dict[str, Any]):
    # In a real scenario, this would use the auth context dependency.
    # Currently just a stub for Phase 10 API wiring.
    account_map = payload.get("calendar_account_map", {})
    if not account_map:
        raise HTTPException(status_code=400, detail="Missing account mapping")
    
    return {"status": "success", "message": "Writeback intent registered", "target": account_map}

@router.post("/sync")
async def sync_caldav_accounts():
    # Deprecated legacy endpoint path, should fail or require strict auth
    raise HTTPException(status_code=403, detail="Use specific writeback intent and verified sources instead.")
