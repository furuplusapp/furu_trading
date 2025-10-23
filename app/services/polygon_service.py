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
                        raise Exception(f"Polygon API error: {response.status}")
        except Exception as e:
            # Return empty result instead of raising to prevent complete failure
            return {"results": [], "status": "ERROR"}
    
    async def screen_stocks(
        self,
        page: int = 1,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Screen stocks using Polygon API
        """
        try:
            current_page_results = []
            snapshot_url = "https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers"
            snapshot_data = await self._make_request(snapshot_url);
            snapshot_data = snapshot_data.get("tickers", [])
            print(f"Total stocks in snapshot: {len(snapshot_data)}")
            
            if not snapshot_data:
                print("No snapshot data received from Polygon API")
                return []
            
            # Calculate pagination offsets
            items_per_page = limit
            start_index = (page - 1) * items_per_page
            end_index = start_index + items_per_page
            
            # Process only the stocks for the current page
            current_page_stocks = snapshot_data[start_index:end_index]
            
            for i, snapshot in enumerate(current_page_stocks):
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
                    market_cap = ticker_details_data.get("results", {}).get("market_cap", 0)
                    volume = snapshot.get("day", {}).get("v", 0)
                    price = snapshot.get("day", {}).get("c", 0)
                    change_percent = snapshot.get("todaysChangePerc", 0)
                    
                    current_page_results.append({
                        "ticker": snapshot['ticker'],
                        "name": ticker_details_data.get("results", {}).get("name", "N/A"),
                        "price": price,
                        "marketCap": market_cap,
                        "volume": volume,    
                        "changePercent": change_percent,
                        "dividendYield": dividend_yield,
                    })   
                        
                except Exception as e:
                    print("error processing stock", e)
                    continue
            
            if not current_page_results:
                print("no current page results")
                return []
            
            return current_page_results
            
        except Exception as e:
            print("error processing stocks", e)
            return []
    
    async def screen_crypto(
        self,
        page: int = 1,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Screen cryptocurrencies using Polygon API
        """
        try:
            current_page_results = []
            snapshot_url = "https://api.polygon.io/v2/snapshot/locale/global/markets/crypto/tickers"
            snapshot_data = await self._make_request(snapshot_url);
            snapshot_data = snapshot_data.get("tickers", [])
            print(f"Total crypto in snapshot: {len(snapshot_data)}")
            
            if not snapshot_data:
                print("No crypto snapshot data received from Polygon API")
                return []
            
            # Calculate pagination offsets
            items_per_page = limit
            start_index = (page - 1) * items_per_page
            end_index = start_index + items_per_page
            
            # Process only the stocks for the current page
            current_page_crypto = snapshot_data[start_index:end_index]
            
            for i, snapshot in enumerate(current_page_crypto):
                try:
                    ticker_details_url = f"https://api.polygon.io/v3/reference/tickers/{snapshot['ticker']}"
                    ticker_details_data = await self._make_request(ticker_details_url)
                    
                    # Apply filters with proper null checks
                    volume = snapshot.get("day", {}).get("v", 0)
                    price = snapshot.get("day", {}).get("c", 0)
                    change_percent = snapshot.get("todaysChangePerc", 0)
                    
                    current_page_results.append({
                        "ticker": snapshot['ticker'],
                        "name": ticker_details_data.get("results", {}).get("name", "N/A"),
                        "price": price,
                        "volume": volume,
                        "changePercent": change_percent,
                    })   
                        
                except Exception as e:
                    print("error processing crypto", e)
                    continue
            
            if not current_page_results:
                print("no current page results")
                return []
            
            return current_page_results
            
        except Exception as e:
            print("error processing crypto", e)
            return []
    
    async def screen_forex(
        self,
        page: int = 1,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Screen forex using Polygon API
        """
        try:
            current_page_results = []
            snapshot_url = "https://api.polygon.io/v2/snapshot/locale/global/markets/forex/tickers"
            snapshot_data = await self._make_request(snapshot_url);
            snapshot_data = snapshot_data.get("tickers", [])
            
            # Calculate pagination offsets
            items_per_page = limit
            start_index = (page - 1) * items_per_page
            end_index = start_index + items_per_page
            
            # Process only the stocks for the current page
            current_page_forex = snapshot_data[start_index:end_index]
            
            for i, snapshot in enumerate(current_page_forex):
                print(f"Processing forex {snapshot}")
                
                try:
                    ticker_details_url = f"https://api.polygon.io/v3/reference/tickers/{snapshot['ticker']}"
                    ticker_details_data = await self._make_request(ticker_details_url)
                    
                    print(f"Ticker details data: {ticker_details_data}")
                    # Apply filters with proper null checks
                    volume = snapshot.get("day", {}).get("v", 0)
                    price = snapshot.get("day", {}).get("c", 0)
                    change_percent = snapshot.get("todaysChangePerc", 0)
                    
                    current_page_results.append({
                        "ticker": snapshot['ticker'],
                        "name": ticker_details_data.get("results", {}).get("name", "N/A"),
                        "price": price,
                        "volume": volume,
                        "changePercent": change_percent,
                    })   
                        
                except Exception as e:
                    print("error processing forex", e)
                    continue
                
            if not current_page_results:
                print("no current page results")
                return []
            
            return current_page_results
            
        except Exception as e:
            print("error processing forex", e)
            return []
        
    async def screen_options(
        self,
        page: int = 1,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Screen options - Returns mock data for now as Polygon options API requires premium tier
        """
        return []
    
    def _calculate_stock_score(self, change_percent: float, volume: float, price: float) -> float:
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
        
        # Price
        if price > 100:
            score += 1
        elif price > 50:
            score += 0.5
        
        return min(max(score, 0), 10)