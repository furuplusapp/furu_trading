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
    filters: dict
    timestamp: str

@router.get("/stocks", response_model=ScreenerResponse)
async def screen_stocks(
    sortBy: str = Query("score", description="Sort by: score, change, volume, marketCap"),
    minScore: float = Query(7, description="Minimum AI score"),
    minMarketCap: float = Query(1000, description="Minimum market cap in millions"),
    maxMarketCap: float = Query(500000, description="Maximum market cap in millions"),
    minVolume: float = Query(1000000, description="Minimum trading volume"),
    sector: str = Query("all", description="Sector filter"),
    minDividendYield: float = Query(0, description="Minimum dividend yield %"),
    priceRange: str = Query("10,1000", description="Price range as 'min,max'"),
    page: int = Query(1, description="Page number", ge=1),
    limit: int = Query(20, description="Items per page", ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Screen stocks based on various fundamental and technical criteria using Polygon API
    """
    try:
        polygon_service = PolygonService()
        
        # Parse price range
        try:
            min_price, max_price = map(float, priceRange.split(','))
        except:
            min_price, max_price = 10, 1000
        
        # Get screened stocks from Polygon
        results = await polygon_service.screen_stocks(
            sort_by=sortBy,
            min_score=minScore,
            min_market_cap=minMarketCap * 1000000,  # Convert to actual value
            max_market_cap=maxMarketCap * 1000000,
            min_volume=minVolume,
            sector=sector,
            min_dividend_yield=minDividendYield,
            min_price=min_price,
            max_price=max_price,
            page=page,
            limit=limit
        )
        
        # Limit results for free users (override pagination)
        if current_user.plan == "free":
            results = results[:5]
        
        return ScreenerResponse(
            data=results,
            type="stocks",
            filters={
                "sortBy": sortBy,
                "minScore": minScore,
                "minMarketCap": minMarketCap,
                "sector": sector,
                "minDividendYield": minDividendYield,
                "minPrice": min_price,
                "maxPrice": max_price
            },
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to screen stocks: {str(e)}"
        )

@router.get("/crypto", response_model=ScreenerResponse)
async def screen_crypto(
    sortBy: str = Query("whale_flow", description="Sort by: whale_flow, volume, marketCap, change"),
    minMarketCap: float = Query(100, description="Minimum market cap in millions"),
    maxMarketCap: float = Query(1000000, description="Maximum market cap in millions"),
    minVolume24h: float = Query(10, description="Minimum 24h volume in millions"),
    whaleActivity: str = Query("all", description="Whale activity filter"),
    exchangeFlow: str = Query("all", description="Exchange flow filter"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Screen cryptocurrencies based on whale activity and on-chain metrics
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
            sort_by=sortBy,
            min_market_cap=minMarketCap * 1000000,
            max_market_cap=maxMarketCap * 1000000,
            min_volume_24h=minVolume24h * 1000000,
            whale_activity=whaleActivity,
            exchange_flow=exchangeFlow
        )
        
        return ScreenerResponse(
            data=results,
            type="crypto",
            filters={
                "sortBy": sortBy,
                "minMarketCap": minMarketCap,
                "whaleActivity": whaleActivity
            },
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to screen crypto: {str(e)}"
        )

@router.get("/forex", response_model=ScreenerResponse)
async def screen_forex(
    sortBy: str = Query("volatility", description="Sort by: volatility, change, volume"),
    pairType: str = Query("major", description="Pair type: major, minor, exotic"),
    minVolatility: float = Query(0.5, description="Minimum volatility %"),
    maxVolatility: float = Query(3.0, description="Maximum volatility %"),
    trend: str = Query("all", description="Trend filter: bullish, bearish, sideways"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
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
            sort_by=sortBy,
            pair_type=pairType,
            min_volatility=minVolatility,
            max_volatility=maxVolatility,
            trend=trend
        )
        
        return ScreenerResponse(
            data=results,
            type="forex",
            filters={
                "sortBy": sortBy,
                "pairType": pairType,
                "trend": trend
            },
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to screen forex: {str(e)}"
        )

@router.get("/options", response_model=ScreenerResponse)
async def screen_options(
    strategy: str = Query("csp", description="Strategy: csp, cc, wheel, iron_condor"),
    minYield: float = Query(8, description="Minimum yield %"),
    maxYield: float = Query(25, description="Maximum yield %"),
    minDTE: int = Query(30, description="Minimum days to expiry"),
    maxDTE: int = Query(60, description="Maximum days to expiry"),
    minIVRank: float = Query(20, description="Minimum IV rank"),
    maxIVRank: float = Query(80, description="Maximum IV rank"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
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
            strategy=strategy,
            min_yield=minYield,
            max_yield=maxYield,
            min_dte=minDTE,
            max_dte=maxDTE,
            min_iv_rank=minIVRank,
            max_iv_rank=maxIVRank
        )
        
        return ScreenerResponse(
            data=results,
            type="options",
            filters={
                "strategy": strategy,
                "minYield": minYield,
                "minDTE": minDTE
            },
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to screen options: {str(e)}"
        )

@router.get("/commodities", response_model=ScreenerResponse)
async def screen_commodities(
    sortBy: str = Query("momentum", description="Sort by: momentum, change, volume"),
    category: str = Query("all", description="Category: metals, energy, agriculture, industrial"),
    seasonalPattern: str = Query("all", description="Seasonal pattern filter"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
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
            sort_by=sortBy,
            category=category,
            seasonal_pattern=seasonalPattern
        )
        
        return ScreenerResponse(
            data=results,
            type="commodities",
            filters={
                "sortBy": sortBy,
                "category": category
            },
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to screen commodities: {str(e)}"
        )

