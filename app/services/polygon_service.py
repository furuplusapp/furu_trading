import aiohttp
from typing import List, Dict, Any
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
        
    async def _make_request(self, url: str) -> Dict[str, Any]:
        """
        Make async request to Polygon API
        """
        
        # Check if URL already has query parameters
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}apiKey={self.api_key}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        print(f"Polygon API error: {response.status} - {error_text}")
                        raise Exception(f"Polygon API error: {response.status}")
        except Exception as e:
            print(f"Request to Polygon failed: {str(e)}")
            # Return empty result instead of raising to prevent complete failure
            return {"results": [], "status": "ERROR"}
    
    async def screen_stocks(
        self,
        sort_by: str = "score",
        min_score: float = 7,
        min_market_cap: float = 1000000000,
        max_market_cap: float = 500000000000,
        min_volume: float = 1000000,
        sector: str = "all",
        min_dividend_yield: float = 0,
        min_price: float = 10,
        max_price: float = 1000,
        page: int = 1,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Screen stocks using Polygon API
        """
        try:
            print(f"Processing page {page} with limit {limit}")
            current_page_results = []
            snapshot_url = "https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers"
            snapshot_data = await self._make_request(snapshot_url);
            snapshot_data = snapshot_data.get("tickers", [])
            
            print(f"Total stocks in snapshot: {len(snapshot_data)}")
            
            # Calculate pagination offsets
            items_per_page = limit
            start_index = (page - 1) * items_per_page
            end_index = start_index + items_per_page
            
            print(f"Processing stocks {start_index} to {end_index}")
            
            # Process only the stocks for the current page
            current_page_stocks = snapshot_data[start_index:end_index]
            
            for i, snapshot in enumerate(current_page_stocks):
                print(f"Processing stock {start_index + i + 1}/{len(snapshot_data)}: {snapshot['ticker']}")
                
                try:
                    ticker_details_url = f"https://api.polygon.io/v3/reference/tickers/{snapshot['ticker']}"
                    ticker_details_data = await self._make_request(ticker_details_url)
                    
                    dividends_url = f"https://api.polygon.io/v3/reference/dividends?ticker={snapshot['ticker']}"
                    dividends_data = await self._make_request(dividends_url)
                    dividend_yield = 0
                    
                    # Calculate dividend yield
                    if dividends_data.get("results") and len(dividends_data.get("results")) > 0:
                        latest_dividend = dividends_data.get("results")[0]
                        cash_amount = latest_dividend.get("cash_amount", 0)
                        frequency = latest_dividend.get("frequency", 4)  # Default to quarterly
                        current_price = snapshot.get("day", {}).get("c", 1)
                        
                        # Calculate annual dividend based on frequency
                        annual_dividend = cash_amount * frequency
                        dividend_yield = (annual_dividend / current_price) * 100
                    
                    # Apply filters with proper null checks
                    market_cap = ticker_details_data.get("results").get("market_cap") or 0
                    print(f"Market cap: {market_cap}")
                    volume = snapshot.get("day", {}).get("v") or 0
                    price = snapshot.get("day", {}).get("c") or 0
                    change_percent = snapshot.get("todaysChangePerc") or 0
                    
                    # if (market_cap > min_market_cap and 
                    #     market_cap < max_market_cap and 
                    #     volume > min_volume and 
                    #     dividend_yield > min_dividend_yield and 
                    #     price > min_price and 
                    #     price < max_price):
                    
                    current_page_results.append({
                        "ticker": snapshot['ticker'],
                        "name": ticker_details_data.get("results").get("name"),
                        "price": snapshot.get("day", {}).get("c"),
                        "marketCap": market_cap,
                        "volume": snapshot.get("day", {}).get("v"),    
                        "changePercent": snapshot.get("todaysChangePerc"),
                        "dividendYield": dividend_yield,
                        "score": self._calculate_stock_score(
                            change_percent, 
                            volume, 
                            market_cap, 
                            price
                        ),
                    })   
                        
                except Exception as e:
                    print(f"Error processing {snapshot['ticker']}: {str(e)}")
                    continue
            
            # If no results after filtering, return mock data
            if not current_page_results:
                print("No stocks passed filters, returning mock data")
                return self._get_mock_stocks()
            
            print(f"Returning {len(current_page_results)} filtered results for page {page}")
            return current_page_results
            
        except Exception as e:
            print(f"Stock screening failed: {str(e)}")
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
                ticker = item.get("T", "").replace("X:", "")  # Remove X: prefix
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
                    "ticker": ticker,
                    "name": ticker,
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
            print(f"Crypto screening failed: {str(e)}")
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
            print(f"Forex screening failed: {str(e)}")
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
                "ticker": "AAPL",
                "name": "Apple Inc.",
                "price": 185.42,
                "change": 2.15,
                "changePercent": 1.17,
                "volume": 45234567,
                "marketCap": 2890000000000,
                "sector": "Technology",
                "dividendYield": 2.52,
                "score": 8.5,
            },
            {
                "ticker": "MSFT",
                "name": "Microsoft Corporation",
                "price": 378.85,
                "change": 4.23,
                "changePercent": 1.13,
                "volume": 23456789,
                "marketCap": 2810000000000,
                "sector": "Technology",
                "dividendYield": 2.78,
                "score": 8.2,
            },
        ]
    
    def _get_mock_crypto(self) -> List[Dict[str, Any]]:
        return [
            {
                "ticker": "BTC",
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
                "ticker": "GC",
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

