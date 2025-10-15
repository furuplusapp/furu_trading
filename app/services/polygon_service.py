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
        
        url = f"{url}&apiKey={self.api_key}"
        
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
        max_price: float = 1000,
        page: int = 1,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Screen stocks using Polygon API with cursor-based pagination
        Step 1: Get ticker list from /v3/reference/tickers
        Step 2: Get price/volume data for filtered tickers
        
        Note: Polygon uses cursor-based pagination via next_url, not page numbers
        We fetch enough data upfront and handle pagination in memory
        """
        try:
            print("page", page)
            # Step 1: Fetch comprehensive ticker list
            # We'll fetch multiple pages to build a good screening pool
            tickers_url = f"https://api.polygon.io/v3/reference/tickers?market=stocks&active=true&limit={limit}&sort=ticker&order=asc&type=CS"
            
            current_page_results = []
            page_count = 1
            
            while tickers_url and page_count <= page:
                print(f"Fetching page {page_count} ...")
                tickers_data = await self._make_request(tickers_url)
                
                # If we're at the requested page, store just these results
                if page_count == page:
                    current_page_results = tickers_data.get("results", [])
                    print(f"Found {len(current_page_results)} results for page {page}")
                    # Apply limit to ensure we don't return more than requested
                    if len(current_page_results) > limit:
                        current_page_results = current_page_results[:limit]
                    break
                
                # Check for next_url to continue pagination
                next_url = tickers_data.get("next_url")
                if next_url:
                    print("nexturl", next_url)
                    tickers_url = next_url
                    page_count += 1
                else:
                    # No more pages available
                    print(f"Reached end of data at page {page_count}")
                    break
            
            if not current_page_results:
                print("No tickers returned from Polygon for requested page")
                return self._get_mock_stocks()
            
            print(f"Returning {len(current_page_results)} results for page {page}")
            return current_page_results
            
            # Step 2: Filter tickers by market cap upfront
            # filtered_tickers = []
            # for ticker in all_tickers:
            #     market_cap = ticker.get("market_cap", 0)
                
            #     # Filter by market cap range
            #     if market_cap and min_market_cap <= market_cap <= max_market_cap:
            #         filtered_tickers.append({
            #             "symbol": ticker.get("ticker"),
            #             "name": ticker.get("name"),
            #             "market_cap": market_cap,
            #             "sector": ticker.get("sic_description", "Unknown")
            #         })
            
            # logger.info(f"Filtered to {len(filtered_tickers)} tickers by market cap")
            
            # # Step 3: Get price/volume data for filtered tickers (batch request)
            # # Use previous trading day
            # today = datetime.now()
            # yesterday = today - timedelta(days=1)
            # date_str = yesterday.strftime("%Y-%m-%d")
            
            # results = []
            # # Process in smaller batches to avoid rate limits
            # for ticker_info in filtered_tickers[:100]:  # Process top 100
            #     symbol = ticker_info["symbol"]
                
            #     try:
            #         # Get daily bar for this specific ticker
            #         bar_endpoint = f"/v2/aggs/ticker/{symbol}/range/1/day/{date_str}/{date_str}"
            #         bar_data = await self._make_request(bar_endpoint, {"adjusted": "true"})
                    
            #         if not bar_data.get("results"):
            #             continue
                    
            #         bar = bar_data["results"][0]
            #         close_price = bar.get("c", 0)
            #         open_price = bar.get("o", close_price)
            #         volume = bar.get("v", 0)
                    
            #         # Filter by price range
            #         if close_price < min_price or close_price > max_price:
            #             continue
                    
            #         # Filter by volume
            #         if volume < min_volume:
            #             continue
                    
            #         # Calculate metrics
            #         change = close_price - open_price
            #         change_percent = (change / open_price * 100) if open_price > 0 else 0
                    
            #         # Calculate AI score
            #         score = self._calculate_stock_score(
            #             change_percent=change_percent,
            #             volume=volume,
            #             market_cap=ticker_info["market_cap"],
            #             price=close_price
            #         )
                    
            #         # Filter by score
            #         if score < min_score:
            #             continue
                    
            #         results.append({
            #             "symbol": symbol,
            #             "name": ticker_info["name"],
            #             "price": round(close_price, 2),
            #             "change": round(change, 2),
            #             "changePercent": round(change_percent, 2),
            #             "volume": volume,
            #             "marketCap": ticker_info["market_cap"],
            #             "pe": None,  # Requires /vX/reference/financials
            #             "sector": ticker_info["sector"],
            #             "dividendYield": None,
            #             "roe": None,
            #             "score": round(score, 1)
            #         })
                    
            #         # Limit to 50 results before sorting
            #         if len(results) >= 50:
            #             break
                        
            #     except Exception as e:
            #         logger.warning(f"Failed to get data for {symbol}: {str(e)}")
            #         continue
            
            # logger.info(f"Found {len(results)} stocks matching criteria")
            
            # # Sort results
            # if sort_by == "score":
            #     results.sort(key=lambda x: x["score"], reverse=True)
            # elif sort_by == "change":
            #     results.sort(key=lambda x: x["changePercent"], reverse=True)
            # elif sort_by == "volume":
            #     results.sort(key=lambda x: x["volume"], reverse=True)
            # elif sort_by == "marketCap":
            #     results.sort(key=lambda x: x["marketCap"], reverse=True)
            
            # # Apply pagination
            # start_idx = (page - 1) * limit
            # end_idx = start_idx + limit
            # return results[start_idx:end_idx]
            
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

