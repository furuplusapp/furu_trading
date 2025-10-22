from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.services.polygon_service import PolygonService
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, timezone

router = APIRouter()

class ScreenerResponse(BaseModel):
    data: List[dict]
    type: str
    timestamp: str

@router.get("/stocks", response_model=ScreenerResponse)
async def screen_stocks(
    page: int = Query(1, description="Page number", ge=1),
    limit: int = Query(20, description="Items per page", ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    """
    Screen stocks based on various fundamental and technical criteria using Polygon API
    """
    try:
        polygon_service = PolygonService()
        
        # Get screened stocks from Polygon
        results = await polygon_service.screen_stocks(
            page=page,
            limit=limit
        )
        
        # Limit results for free users (override pagination)
        if current_user.plan == "free":
            results = results[:5]
        
        return ScreenerResponse(
            data=results,
            type="stocks",
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to screen stocks: {str(e)}"
        )

@router.get("/crypto", response_model=ScreenerResponse)
async def screen_crypto(
    page: int = Query(1, description="Page number", ge=1),
    limit: int = Query(20, description="Items per page", ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    """
    Screen cryptocurrencies based on on-chain metrics
    Pro/Elite only
    """
    if current_user.plan == "free":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Crypto screener requires Pro or Elite plan"
        )
    
    try:
        polygon_service = PolygonService()
        
        results = await polygon_service.screen_crypto(
            page=page,
            limit=limit
        )
        
        return ScreenerResponse(
            data=results,
            type="crypto",
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to screen crypto: {str(e)}"
        )

@router.get("/forex", response_model=ScreenerResponse)
async def screen_forex(
    page: int = Query(1, description="Page number", ge=1),
    limit: int = Query(20, description="Items per page", ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    """
    Screen forex pairs based on volatility and trends
    Pro/Elite only
    """
    if current_user.plan == "free":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forex screener requires Pro or Elite plan"
        )
    
    try:
        polygon_service = PolygonService()
        
        results = await polygon_service.screen_forex(
            page=page,
            limit=limit
        )
        
        return ScreenerResponse(
            data=results,
            type="forex",
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to screen forex: {str(e)}"
        )

@router.get("/options", response_model=ScreenerResponse)
async def screen_options(
    page: int = Query(1, description="Page number", ge=1),
    limit: int = Query(20, description="Items per page", ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    """
    Screen options based on strategy and yield requirements
    Pro/Elite only
    """
    if current_user.plan == "free":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Options screener requires Pro or Elite plan"
        )
    
    try:
        polygon_service = PolygonService()
        
        results = await polygon_service.screen_options(
            page=page,
            limit=limit
        )
        
        return ScreenerResponse(
            data=results,
            type="options",
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to screen options: {str(e)}"
        )

@router.get("/commodities", response_model=ScreenerResponse)
async def screen_commodities(
    page: int = Query(1, description="Page number", ge=1),
    limit: int = Query(20, description="Items per page", ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    """
    Screen commodities based on momentum and seasonal patterns
    Pro/Elite only
    """
    if current_user.plan == "free":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Commodities screener requires Pro or Elite plan"
        )
    
    try:
        polygon_service = PolygonService()
        
        results = await polygon_service.screen_commodities(
            page=page,
            limit=limit
        )
        
        return ScreenerResponse(
            data=results,
            type="commodities",
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to screen commodities: {str(e)}"
        )

