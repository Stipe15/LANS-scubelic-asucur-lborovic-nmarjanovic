"""FastAPI router for user configuration endpoints (brands, intents)."""

import logging
import sqlite3
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from llm_answer_watcher.auth.dependencies import get_current_user, get_db_path
from llm_answer_watcher.storage.db import (
    create_user_brand,
    create_user_intent,
    delete_user_brand,
    delete_user_intent,
    get_user_brands,
    get_user_intents,
    init_db_if_needed,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user", tags=["user-config"])

# ----------------------------------------------------------------------------
# Pydantic Models
# ----------------------------------------------------------------------------

class BrandCreate(BaseModel):
    brand_name: str
    is_mine: bool

class BrandResponse(BaseModel):
    id: int
    brand_name: str
    is_mine: bool
    created_at: str

class IntentCreate(BaseModel):
    intent_alias: str
    prompt: str

class IntentResponse(BaseModel):
    id: int
    intent_alias: str
    prompt: str
    created_at: str

# ----------------------------------------------------------------------------
# Brand Endpoints
# ----------------------------------------------------------------------------

@router.get("/brands", response_model=List[BrandResponse])
async def list_brands(
    current_user: dict = Depends(get_current_user),
    db_path: str = Depends(get_db_path),
):
    """
    List all brands configured for the current user.
    """
    init_db_if_needed(db_path)
    with sqlite3.connect(db_path) as conn:
        brands = get_user_brands(conn, current_user["id"])
    return brands

@router.post("/brands", response_model=BrandResponse, status_code=status.HTTP_201_CREATED)
async def add_brand(
    brand: BrandCreate,
    current_user: dict = Depends(get_current_user),
    db_path: str = Depends(get_db_path),
):
    """
    Add a new brand (mine or competitor) for the current user.
    """
    init_db_if_needed(db_path)
    with sqlite3.connect(db_path) as conn:
        try:
            brand_id = create_user_brand(
                conn, current_user["id"], brand.brand_name, brand.is_mine
            )
            # Fetch back to get created_at
            # Optimization: could return full object from db function, but re-fetching is safer
            brands = get_user_brands(conn, current_user["id"])
            created_brand = next((b for b in brands if b["id"] == brand_id), None)
            if not created_brand:
                 raise HTTPException(status_code=500, detail="Failed to retrieve created brand")
            return created_brand
        except sqlite3.IntegrityError:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Brand '{brand.brand_name}' already exists",
            )

@router.delete("/brands/{brand_id}")
async def remove_brand(
    brand_id: int,
    current_user: dict = Depends(get_current_user),
    db_path: str = Depends(get_db_path),
):
    """
    Delete a brand.
    """
    init_db_if_needed(db_path)
    with sqlite3.connect(db_path) as conn:
        deleted = delete_user_brand(conn, brand_id, current_user["id"])
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand not found",
        )
    return {"message": "Brand deleted"}

# ----------------------------------------------------------------------------
# Intent Endpoints
# ----------------------------------------------------------------------------

@router.get("/intents", response_model=List[IntentResponse])
async def list_intents(
    current_user: dict = Depends(get_current_user),
    db_path: str = Depends(get_db_path),
):
    """
    List all intents configured for the current user.
    """
    init_db_if_needed(db_path)
    with sqlite3.connect(db_path) as conn:
        intents = get_user_intents(conn, current_user["id"])
    return intents

@router.post("/intents", response_model=IntentResponse, status_code=status.HTTP_201_CREATED)
async def add_intent(
    intent: IntentCreate,
    current_user: dict = Depends(get_current_user),
    db_path: str = Depends(get_db_path),
):
    """
    Add a new intent for the current user.
    """
    init_db_if_needed(db_path)
    with sqlite3.connect(db_path) as conn:
        try:
            intent_id = create_user_intent(
                conn, current_user["id"], intent.intent_alias, intent.prompt
            )
            intents = get_user_intents(conn, current_user["id"])
            created_intent = next((i for i in intents if i["id"] == intent_id), None)
            if not created_intent:
                 raise HTTPException(status_code=500, detail="Failed to retrieve created intent")
            return created_intent
        except sqlite3.IntegrityError:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Intent alias '{intent.intent_alias}' already exists",
            )

@router.delete("/intents/{intent_id}")
async def remove_intent(
    intent_id: int,
    current_user: dict = Depends(get_current_user),
    db_path: str = Depends(get_db_path),
):
    """
    Delete an intent.
    """
    init_db_if_needed(db_path)
    with sqlite3.connect(db_path) as conn:
        deleted = delete_user_intent(conn, intent_id, current_user["id"])
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Intent not found",
        )
    return {"message": "Intent deleted"}
