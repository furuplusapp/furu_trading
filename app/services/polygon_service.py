import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
from app.core.config import settings
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class PolygonService:
    """
    Service for interacting with Polygon.io API
    API Documentation: https://polygon.io/docs/stocks/getting-started
    """
    
    def __init__(self):
        self.api_key = settings.polygon_api_key
        self.base_url = "https://api.polygon.io"
        
    async def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Make async request to Polygon API
        """
        if params is None:
            params = {}
        
        params['apiKey'] = self.api_key
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"Polygon API error: {response.status} - {error_text}")
                        raise Exception(f"Polygon API error: {response.status}")
        except Exception as e:
            logger.error(f"Request to Polygon failed: {str(e)}")
            raise
    
    async def screen_stocks(
        self,
        sort_by: str = "score",
        min_score: float = 7,
        max_pe: float = 50,
        min_market_cap: float = 1000000000,
        max_market_cap: float = 500000000000,
        min_volume: float = 1000000,
        sector: str = "all",
        min_dividend_yield: float = 0,
        max_debt_to_equity: float = 100,
        min_roe: float = 10,
        min_price: float = 10,
        max_price: float = 1000
    ) -> List[Dict[str, Any]]:
        """
        Screen stocks using Polygon API
        Uses: /v2/aggs/grouped/locale/us/market/stocks/{date}
        And: /v3/reference/tickers for company details
        """
        try:
            # Get previous trading day
            today = datetime.now()
            yesterday = today - timedelta(days=1)
            date_str = yesterday.strftime("%Y-%m-%d")
            
            # Get grouped daily bars for all stocks
            endpoint = f"/v2/aggs/grouped/locale/us/market/stocks/{date_str}"
            params = {"adjusted": "true"}
            
            data = await self._make_request(endpoint, params)
            
            if not data.get("results"):
                return []
            
            # Get ticker details for top symbols
            results = []
            for item in data["results"][:100]:  # Limit to top 100 for performance
                symbol = item.get("T", "")
                
                # Filter by price range
                close_price = item.get("c", 0)
                if close_price < min_price or close_price > max_price:
                    continue
                
                # Filter by volume
                volume = item.get("v", 0)
                if volume < min_volume:
                    continue
                
                # Calculate change percentage
                open_price = item.get("o", close_price)
                change = close_price - open_price
                change_percent = (change / open_price * 100) if open_price > 0 else 0
                
                # Get ticker details for additional info
                try:
                    ticker_endpoint = f"/v3/reference/tickers/{symbol}"
                    ticker_data = await self._make_request(ticker_endpoint)
                    ticker_info = ticker_data.get("results", {})
                    
                    market_cap = ticker_info.get("market_cap", 0)
                    
                    # Filter by market cap
                    if market_cap < min_market_cap or market_cap > max_market_cap:
                        continue
                    
                    # Calculate AI score (simplified - you can enhance this)
                    score = self._calculate_stock_score(
                        change_percent=change_percent,
                        volume=volume,
                        market_cap=market_cap,
                        price=close_price
                    )
                    
                    if score < min_score:
                        continue
                    
                    results.append({
                        "symbol": symbol,
                        "name": ticker_info.get("name", symbol),
                        "price": round(close_price, 2),
                        "change": round(change, 2),
                        "changePercent": round(change_percent, 2),
                        "volume": volume,
                        "marketCap": market_cap,
                        "pe": None,  # Requires additional API call to get financials
                        "sector": ticker_info.get("sic_description", "Unknown"),
                        "dividendYield": None,  # Requires additional API call
                        "roe": None,  # Requires additional API call
                        "score": round(score, 1)
                    })
                    
                except Exception as e:
                    logger.warning(f"Failed to get details for {symbol}: {str(e)}")
                    continue
                
                # Limit results to avoid too many API calls
                if len(results) >= 50:
                    break
            
            # Sort results
            if sort_by == "score":
                results.sort(key=lambda x: x["score"], reverse=True)
            elif sort_by == "change":
                results.sort(key=lambda x: x["changePercent"], reverse=True)
            elif sort_by == "volume":
                results.sort(key=lambda x: x["volume"], reverse=True)
            elif sort_by == "marketCap":
                results.sort(key=lambda x: x["marketCap"], reverse=True)
            
            return results[:20]  # Return top 20
            
        except Exception as e:
            logger.error(f"Stock screening failed: {str(e)}")
            # Return mock data if API fails
            return self._get_mock_stocks()
    
    async def screen_crypto(
        self,
        sort_by: str = "whale_flow",
        min_market_cap: float = 100000000,
        max_market_cap: float = 1000000000000,
        min_volume_24h: float = 10000000,
        whale_activity: str = "all",
        exchange_flow: str = "all"
    ) -> List[Dict[str, Any]]:
        """
        Screen cryptocurrencies using Polygon API
        Uses: /v2/aggs/grouped/locale/global/market/crypto/{date}
        """
        try:
            today = datetime.now()
            yesterday = today - timedelta(days=1)
            date_str = yesterday.strftime("%Y-%m-%d")
            
            endpoint = f"/v2/aggs/grouped/locale/global/market/crypto/{date_str}"
            params = {"adjusted": "true"}
            
            data = await self._make_request(endpoint, params)
            
            if not data.get("results"):
                return self._get_mock_crypto()
            
            results = []
            for item in data["results"][:50]:
                symbol = item.get("T", "").replace("X:", "")  # Remove X: prefix
                close_price = item.get("c", 0)
                open_price = item.get("o", close_price)
                volume = item.get("v", 0)
                
                change = close_price - open_price
                change_percent = (change / open_price * 100) if open_price > 0 else 0
                
                # Estimate market cap (simplified)
                estimated_market_cap = close_price * volume * 100
                
                if estimated_market_cap < min_market_cap or estimated_market_cap > max_market_cap:
                    continue
                
                score = self._calculate_crypto_score(change_percent, volume)
                
                results.append({
                    "symbol": symbol,
                    "name": symbol,
                    "price": round(close_price, 2),
                    "change": round(change, 2),
                    "changePercent": round(change_percent, 2),
                    "marketCap": estimated_market_cap,
                    "volume24h": volume,
                    "whaleFlow": "accumulation" if change_percent > 2 else "distribution" if change_percent < -2 else "neutral",
                    "exchangeFlow": "outflow" if volume > min_volume_24h * 2 else "inflow",
                    "score": round(score, 1)
                })
            
            if sort_by == "whale_flow":
                results.sort(key=lambda x: x["score"], reverse=True)
            elif sort_by == "volume":
                results.sort(key=lambda x: x["volume24h"], reverse=True)
            elif sort_by == "marketCap":
                results.sort(key=lambda x: x["marketCap"], reverse=True)
            
            return results[:20]
            
        except Exception as e:
            logger.error(f"Crypto screening failed: {str(e)}")
            return self._get_mock_crypto()
    
    async def screen_forex(
        self,
        sort_by: str = "volatility",
        pair_type: str = "major",
        min_volatility: float = 0.5,
        max_volatility: float = 3.0,
        trend: str = "all"
    ) -> List[Dict[str, Any]]:
        """
        Screen forex pairs using Polygon API
        Uses: /v2/aggs/grouped/locale/global/market/fx/{date}
        """
        try:
            today = datetime.now()
            yesterday = today - timedelta(days=1)
            date_str = yesterday.strftime("%Y-%m-%d")
            
            endpoint = f"/v2/aggs/grouped/locale/global/market/fx/{date_str}"
            params = {"adjusted": "true"}
            
            data = await self._make_request(endpoint, params)
            
            if not data.get("results"):
                return self._get_mock_forex()
            
            results = []
            for item in data["results"][:30]:
                pair = item.get("T", "").replace("C:", "")
                close_price = item.get("c", 0)
                open_price = item.get("o", close_price)
                high = item.get("h", close_price)
                low = item.get("l", close_price)
                
                change = close_price - open_price
                change_percent = (change / open_price * 100) if open_price > 0 else 0
                volatility = ((high - low) / open_price * 100) if open_price > 0 else 0
                
                if volatility < min_volatility or volatility > max_volatility:
                    continue
                
                score = self._calculate_forex_score(volatility, abs(change_percent))
                
                results.append({
                    "pair": pair,
                    "type": pair_type,
                    "price": round(close_price, 4),
                    "change": round(change, 4),
                    "changePercent": round(change_percent, 2),
                    "volatility": round(volatility, 2),
                    "trend": "bullish" if change_percent > 0.5 else "bearish" if change_percent < -0.5 else "sideways",
                    "activeSession": "London",
                    "newsImpact": "low",
                    "score": round(score, 1)
                })
            
            return results[:20]
            
        except Exception as e:
            logger.error(f"Forex screening failed: {str(e)}")
            return self._get_mock_forex()
    
    async def screen_options(
        self,
        strategy: str = "csp",
        min_yield: float = 8,
        max_yield: float = 25,
        min_dte: int = 30,
        max_dte: int = 60,
        min_iv_rank: float = 20,
        max_iv_rank: float = 80
    ) -> List[Dict[str, Any]]:
        """
        Screen options - Returns mock data for now as Polygon options API requires premium tier
        """
        # Options data requires Polygon premium tier
        # For now, return enhanced mock data
        return self._get_mock_options(strategy, min_yield, max_yield, min_dte, max_dte)
    
    async def screen_commodities(
        self,
        sort_by: str = "momentum",
        category: str = "all",
        seasonal_pattern: str = "all"
    ) -> List[Dict[str, Any]]:
        """
        Screen commodities - Returns mock data for now
        """
        return self._get_mock_commodities(category)
    
    def _calculate_stock_score(self, change_percent: float, volume: float, market_cap: float, price: float) -> float:
        """Calculate AI score for stocks"""
        score = 5.0  # Base score
        
        # Positive momentum
        if change_percent > 2:
            score += 2
        elif change_percent > 0:
            score += 1
        
        # High volume
        if volume > 10000000:
            score += 1.5
        elif volume > 5000000:
            score += 0.5
        
        # Market cap sweet spot
        if 10000000000 < market_cap < 100000000000:
            score += 1
        
        return min(max(score, 0), 10)
    
    def _calculate_crypto_score(self, change_percent: float, volume: float) -> float:
        """Calculate AI score for crypto"""
        score = 5.0
        
        if change_percent > 5:
            score += 2.5
        elif change_percent > 2:
            score += 1.5
        
        if volume > 1000000:
            score += 1.5
        
        return min(max(score, 0), 10)
    
    def _calculate_forex_score(self, volatility: float, abs_change: float) -> float:
        """Calculate AI score for forex"""
        score = 5.0
        
        if 0.5 < volatility < 2.0:
            score += 2
        
        if abs_change > 0.5:
            score += 1.5
        
        return min(max(score, 0), 10)
    
    # Mock data fallbacks
    def _get_mock_stocks(self) -> List[Dict[str, Any]]:
        return [
            {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "price": 185.42,
                "change": 2.15,
                "changePercent": 1.17,
                "volume": 45234567,
                "marketCap": 2890000000000,
                "pe": 28.5,
                "sector": "Technology",
                "dividendYield": 0.52,
                "roe": 157.4,
                "score": 8.5,
            },
            {
                "symbol": "MSFT",
                "name": "Microsoft Corporation",
                "price": 378.85,
                "change": 4.23,
                "changePercent": 1.13,
                "volume": 23456789,
                "marketCap": 2810000000000,
                "pe": 32.1,
                "sector": "Technology",
                "dividendYield": 0.78,
                "roe": 45.2,
                "score": 8.2,
            },
        ]
    
    def _get_mock_crypto(self) -> List[Dict[str, Any]]:
        return [
            {
                "symbol": "BTC",
                "name": "Bitcoin",
                "price": 67420.5,
                "change": 2140.25,
                "changePercent": 3.28,
                "marketCap": 1320000000000,
                "volume24h": 28500000000,
                "whaleFlow": "accumulation",
                "exchangeFlow": "outflow",
                "score": 9.1,
            },
        ]
    
    def _get_mock_forex(self) -> List[Dict[str, Any]]:
        return [
            {
                "pair": "EUR/USD",
                "type": "major",
                "price": 1.0842,
                "change": -0.0021,
                "changePercent": -0.19,
                "volatility": 0.65,
                "trend": "sideways",
                "activeSession": "London",
                "newsImpact": "low",
                "score": 7.3,
            },
        ]
    
    def _get_mock_options(self, strategy: str, min_yield: float, max_yield: float, min_dte: int, max_dte: int) -> List[Dict[str, Any]]:
        return [
            {
                "underlying": "AAPL",
                "strategy": strategy.upper(),
                "strike": 180,
                "dte": 45,
                "premium": 2.50,
                "yield": 12.5,
                "ivRank": 45,
                "liquidity": 850,
                "riskScore": 3.5,
            },
        ]
    
    def _get_mock_commodities(self, category: str) -> List[Dict[str, Any]]:
        return [
            {
                "symbol": "GC",
                "category": "metals",
                "price": 2045.50,
                "change": 12.30,
                "changePercent": 0.60,
                "momentum": "strong",
                "seasonal": "favorable",
                "inventory": "normal",
                "newsEvents": 2,
                "score": 7.8,
            },
        ]

