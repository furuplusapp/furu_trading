import re
from typing import Dict
from openai import OpenAI
from app.core.config import settings

client = OpenAI(api_key=settings.openai_api_key)

class ChartAnalysisService:
    """Service to analyze user queries and determine chart updates"""
    
    def __init__(self):
        self.chart_keywords = {
            'indicators': ['rsi', 'macd', 'bollinger', 'bollinger bands', 'sma', 'ema', 'stochastic', 'williams', 'cci', 'atr'],
            'symbols': ['aapl', 'msft', 'googl', 'amzn', 'tsla', 'nvda', 'meta', 'nflx', 'spy', 'qqq', 'btc', 'eth', 'xrp', 'doge', 'sol', 'ada', 'dot', 'link', 'uni', 'ltc'],
            'timeframes': ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w', '1M', '3M', '6M', '1Y', '1-month', '3-month', '6-month', '1-year', 'month', 'months', 'year'],
            'chart_types': ['candlestick', 'line', 'bar', 'area', 'heikin ashi'],
            'patterns': ['support', 'resistance', 'trend', 'breakout', 'reversal', 'triangle', 'head and shoulders']
        }
        
        # Comprehensive symbol mapping for user-friendly terms to TradingView symbols
        self.symbol_mapping = {
            # Major Cryptocurrencies
            'bitcoin': 'BINANCE:BTCUSD', 'btc': 'BINANCE:BTCUSD', 'btcusd': 'BINANCE:BTCUSD', 'btcusdt': 'BINANCE:BTCUSDT',
            'ethereum': 'BINANCE:ETHUSD', 'eth': 'BINANCE:ETHUSD', 'ethusd': 'BINANCE:ETHUSD', 'ethusdt': 'BINANCE:ETHUSDT',
            'ripple': 'BINANCE:XRPUSD', 'xrp': 'BINANCE:XRPUSD', 'xrpusd': 'BINANCE:XRPUSD', 'xrpusdt': 'BINANCE:XRPUSDT',
            'dogecoin': 'BINANCE:DOGEUSD', 'doge': 'BINANCE:DOGEUSD', 'dogeusd': 'BINANCE:DOGEUSD', 'dogeusdt': 'BINANCE:DOGEUSDT',
            'solana': 'BINANCE:SOLUSD', 'sol': 'BINANCE:SOLUSD', 'solusd': 'BINANCE:SOLUSD', 'solusdt': 'BINANCE:SOLUSDT',
            'cardano': 'BINANCE:ADAUSD', 'ada': 'BINANCE:ADAUSD', 'adausd': 'BINANCE:ADAUSD', 'adausdt': 'BINANCE:ADAUSDT',
            'polkadot': 'BINANCE:DOTUSD', 'dot': 'BINANCE:DOTUSD', 'dotusd': 'BINANCE:DOTUSD', 'dotusdt': 'BINANCE:DOTUSDT',
            'chainlink': 'BINANCE:LINKUSD', 'link': 'BINANCE:LINKUSD', 'linkusd': 'BINANCE:LINKUSD', 'linkusdt': 'BINANCE:LINKUSDT',
            'uniswap': 'BINANCE:UNIUSD', 'uni': 'BINANCE:UNIUSD', 'uniusd': 'BINANCE:UNIUSD', 'uniusdt': 'BINANCE:UNIUSDT',
            'litecoin': 'BINANCE:LTCUSD', 'ltc': 'BINANCE:LTCUSD', 'ltcusd': 'BINANCE:LTCUSD', 'ltcusdt': 'BINANCE:LTCUSDT',
            'bitcoin cash': 'BINANCE:BCHUSD', 'bch': 'BINANCE:BCHUSD', 'bchusd': 'BINANCE:BCHUSD', 'bchusdt': 'BINANCE:BCHUSDT',
            'ethereum classic': 'BINANCE:ETCUSD', 'etc': 'BINANCE:ETCUSD', 'etcusd': 'BINANCE:ETCUSD', 'etcusdt': 'BINANCE:ETCUSDT',
            'tether': 'BINANCE:USDTUSD', 'usdt': 'BINANCE:USDTUSD', 'usdc': 'BINANCE:USDCUSD', 'usd coin': 'BINANCE:USDCUSD',
            'binance coin': 'BINANCE:BNBUSD', 'bnb': 'BINANCE:BNBUSD', 'bnbusd': 'BINANCE:BNBUSD', 'bnbusdt': 'BINANCE:BNBUSDT',
            'avalanche': 'BINANCE:AVAXUSD', 'avax': 'BINANCE:AVAXUSD', 'avaxusd': 'BINANCE:AVAXUSD', 'avaxusdt': 'BINANCE:AVAXUSDT',
            'polygon': 'BINANCE:MATICUSD', 'matic': 'BINANCE:MATICUSD', 'maticusd': 'BINANCE:MATICUSD', 'maticusdt': 'BINANCE:MATICUSDT',
            'shiba inu': 'BINANCE:SHIBUSD', 'shib': 'BINANCE:SHIBUSD', 'shibusd': 'BINANCE:SHIBUSD', 'shibusdt': 'BINANCE:SHIBUSDT',
            
            # Major US Stocks
            'apple': 'NASDAQ:AAPL', 'aapl': 'NASDAQ:AAPL',
            'microsoft': 'NASDAQ:MSFT', 'msft': 'NASDAQ:MSFT',
            'google': 'NASDAQ:GOOGL', 'googl': 'NASDAQ:GOOGL', 'alphabet': 'NASDAQ:GOOGL',
            'amazon': 'NASDAQ:AMZN', 'amzn': 'NASDAQ:AMZN',
            'tesla': 'NASDAQ:TSLA', 'tsla': 'NASDAQ:TSLA',
            'nvidia': 'NASDAQ:NVDA', 'nvda': 'NASDAQ:NVDA',
            'meta': 'NASDAQ:META', 'facebook': 'NASDAQ:META',
            'netflix': 'NASDAQ:NFLX', 'nflx': 'NASDAQ:NFLX',
            'berkshire hathaway': 'NYSE:BRK.A', 'brk.a': 'NYSE:BRK.A', 'brk.b': 'NYSE:BRK.B',
            'johnson & johnson': 'NYSE:JNJ', 'jnj': 'NYSE:JNJ',
            'procter & gamble': 'NYSE:PG', 'pg': 'NYSE:PG',
            'jpmorgan': 'NYSE:JPM', 'jpm': 'NYSE:JPM',
            'visa': 'NYSE:V', 'v': 'NYSE:V',
            'mastercard': 'NYSE:MA', 'ma': 'NYSE:MA',
            'home depot': 'NYSE:HD', 'hd': 'NYSE:HD',
            'walmart': 'NYSE:WMT', 'wmt': 'NYSE:WMT',
            'coca cola': 'NYSE:KO', 'ko': 'NYSE:KO',
            'pepsi': 'NASDAQ:PEP', 'pep': 'NASDAQ:PEP',
            'disney': 'NYSE:DIS', 'dis': 'NYSE:DIS',
            'adobe': 'NASDAQ:ADBE', 'adbe': 'NASDAQ:ADBE',
            'salesforce': 'NYSE:CRM', 'crm': 'NYSE:CRM',
            'oracle': 'NYSE:ORCL', 'orcl': 'NYSE:ORCL',
            'intel': 'NASDAQ:INTC', 'intc': 'NASDAQ:INTC',
            'amd': 'NASDAQ:AMD', 'advanced micro devices': 'NASDAQ:AMD',
            'cisco': 'NASDAQ:CSCO', 'csco': 'NASDAQ:CSCO',
            'ibm': 'NYSE:IBM', 'international business machines': 'NYSE:IBM',
            'paypal': 'NASDAQ:PYPL', 'pypl': 'NASDAQ:PYPL',
            'uber': 'NYSE:UBER', 'uber': 'NYSE:UBER',
            'airbnb': 'NASDAQ:ABNB', 'abnb': 'NASDAQ:ABNB',
            'zoom': 'NASDAQ:ZM', 'zm': 'NASDAQ:ZM',
            'palantir': 'NYSE:PLTR', 'pltr': 'NYSE:PLTR',
            'roku': 'NASDAQ:ROKU', 'roku': 'NASDAQ:ROKU',
            'spotify': 'NYSE:SPOT', 'spot': 'NYSE:SPOT',
            'twitter': 'NYSE:TWTR', 'twtr': 'NYSE:TWTR',
            'snapchat': 'NYSE:SNAP', 'snap': 'NYSE:SNAP',
            'pinterest': 'NYSE:PINS', 'pins': 'NYSE:PINS',
            'square': 'NYSE:SQ', 'sq': 'NYSE:SQ',
            'shopify': 'NYSE:SHOP', 'shop': 'NYSE:SHOP',
            'zoom': 'NASDAQ:ZM', 'zm': 'NASDAQ:ZM',
            
            # Major Indices
            'spy': 'AMEX:SPY', 'sp500': 'AMEX:SPY', 's&p500': 'AMEX:SPY', 's&p 500': 'AMEX:SPY',
            'qqq': 'NASDAQ:QQQ', 'nasdaq': 'NASDAQ:QQQ', 'nasdaq100': 'NASDAQ:QQQ', 'nasdaq 100': 'NASDAQ:QQQ',
            'dow': 'NYSE:DJI', 'dow jones': 'NYSE:DJI', 'djia': 'NYSE:DJI',
            'russell 2000': 'AMEX:IWM', 'russell': 'AMEX:IWM', 'iwm': 'AMEX:IWM',
            'vix': 'CBOE:VIX', 'volatility': 'CBOE:VIX',
            
            # International Indices
            'dax': 'GERMANY:DAX', 'germany': 'GERMANY:DAX',
            'ftse': 'UK:FTSE', 'ftse100': 'UK:FTSE', 'london': 'UK:FTSE',
            'cac40': 'FRANCE:CAC40', 'france': 'FRANCE:CAC40',
            'nikkei': 'JAPAN:NIKKEI', 'nikkei225': 'JAPAN:NIKKEI', 'japan': 'JAPAN:NIKKEI',
            'hang seng': 'HONGKONG:HSI', 'hsi': 'HONGKONG:HSI', 'hong kong': 'HONGKONG:HSI',
            'shanghai': 'SHANGHAI:SHANGHAI', 'china': 'SHANGHAI:SHANGHAI',
            'asx': 'AUSTRALIA:ASX', 'australia': 'AUSTRALIA:ASX',
            'bovespa': 'BRAZIL:BVSP', 'brazil': 'BRAZIL:BVSP', 'ibovespa': 'BRAZIL:BVSP',
            
            # Major Commodities
            'gold': 'OANDA:XAUUSD', 'xauusd': 'OANDA:XAUUSD',
            'silver': 'OANDA:XAGUSD', 'xagusd': 'OANDA:XAGUSD',
            'crude oil': 'NYMEX:CL1!', 'wti': 'NYMEX:CL1!', 'oil': 'NYMEX:CL1!',
            'brent': 'OANDA:XBRUSD', 'brent oil': 'OANDA:XBRUSD',
            'natural gas': 'NYMEX:NG1!', 'gas': 'NYMEX:NG1!',
            'copper': 'OANDA:XCUUSD', 'copper futures': 'COMEX:HG1!',
            'platinum': 'OANDA:XPTUSD', 'palladium': 'OANDA:XPDUSD',
            'corn': 'CBOT:ZC1!', 'wheat': 'CBOT:ZW1!', 'soybeans': 'CBOT:ZS1!',
            
            # Major Forex Pairs
            'eurusd': 'FX:EURUSD', 'euro usd': 'FX:EURUSD', 'euro': 'FX:EURUSD',
            'gbpusd': 'FX:GBPUSD', 'pound usd': 'FX:GBPUSD', 'pound': 'FX:GBPUSD',
            'usdjpy': 'FX:USDJPY', 'usd jpy': 'FX:USDJPY', 'yen': 'FX:USDJPY',
            'usdchf': 'FX:USDCHF', 'usd chf': 'FX:USDCHF', 'swiss franc': 'FX:USDCHF',
            'audusd': 'FX:AUDUSD', 'aud usd': 'FX:AUDUSD', 'australian dollar': 'FX:AUDUSD',
            'usdcad': 'FX:USDCAD', 'usd cad': 'FX:USDCAD', 'canadian dollar': 'FX:USDCAD',
            'nzdusd': 'FX:NZDUSD', 'nzd usd': 'FX:NZDUSD', 'new zealand dollar': 'FX:NZDUSD',
            'usdcnh': 'FX:USDCNH', 'usd renminbi': 'FX:USDCNH', 'renminbi': 'FX:USDCNH',
            'usdzar': 'FX:USDZAR', 'usd south african rand': 'FX:USDZAR', 'south african rand': 'FX:USDZAR',
            'usdjpy': 'FX:USDJPY', 'usd yen': 'FX:USDJPY', 'yen': 'FX:USDJPY',
            'usdcad': 'FX:USDCAD', 'usd canadian dollar': 'FX:USDCAD', 'canadian dollar': 'FX:USDCAD',
            'usdtwd': 'FX:USDTWD', 'usd taiwan dollar': 'FX:USDTWD', 'taiwan dollar': 'FX:USDTWD',
            'usdthb': 'FX:USDTHB', 'usd thai baht': 'FX:USDTHB', 'thai baht': 'FX:USDTHB',
            'usdnok': 'FX:USDNOK', 'usd norwegian krone': 'FX:USDNOK', 'norwegian krone': 'FX:USDNOK',
            'usdkrw': 'FX:USDKRW', 'usd korean won': 'FX:USDKRW', 'korean won': 'FX:USDKRW',
            'usdsgd': 'FX:USDSGD', 'usd singapore dollar': 'FX:USDSGD', 'singapore dollar': 'FX:USDSGD',
            
            # Major Futures
            'sp500 futures': 'CME:ES1!', 'es futures': 'CME:ES1!',
            'nasdaq futures': 'CME:NQ1!', 'nq futures': 'CME:NQ1!',
            'dow futures': 'CME:YM1!', 'ym futures': 'CME:YM1!',
            'russell futures': 'CME:RTY1!', 'rty futures': 'CME:RTY1!',
            'vix futures': 'CBOE:VX1!', 'vx futures': 'CBOE:VX1!',
            'gold futures': 'COMEX:GC1!', 'gc futures': 'COMEX:GC1!',
            'silver futures': 'COMEX:SI1!', 'si futures': 'COMEX:SI1!',
            'crude oil futures': 'NYMEX:CL1!', 'cl futures': 'NYMEX:CL1!',
            'natural gas futures': 'NYMEX:NG1!', 'ng futures': 'NYMEX:NG1!',
            '10 year treasury': 'CBOT:TY1!', 'ty futures': 'CBOT:TY1!',
            '30 year treasury': 'CBOT:US1!', 'us futures': 'CBOT:US1!',
            'euro futures': 'CME:6E1!', '6e futures': 'CME:6E1!',
            'yen futures': 'CME:6J1!', '6j futures': 'CME:6J1!',
            'pound futures': 'CME:6B1!', '6b futures': 'CME:6B1!',
            'australian dollar futures': 'CME:6A1!', '6a futures': 'CME:6A1!',
            'new zealand dollar futures': 'CME:6N1!', '6n futures': 'CME:6N1!',
            'swiss franc futures': 'CME:6F1!', '6f futures': 'CME:6F1!',
            'japanese yen futures': 'CME:6J1!', '6j futures': 'CME:6J1!',
            'indonesian rupiah futures': 'CME:6I1!', '6i futures': 'CME:6I1!',
            'indian rupee futures': 'CME:6R1!', '6r futures': 'CME:6R1!',
            'south african rand futures': 'CME:6Z1!', '6z futures': 'CME:6Z1!',
            'brazilian real futures': 'CME:6B1!', '6b futures': 'CME:6B1!',
            'chinese yuan futures': 'CME:6C1!', '6c futures': 'CME:6C1!',
            
            # Major Options (SPY, QQQ, AAPL, TSLA, etc.)
            'spy options': 'AMEX:SPY', 'qqq options': 'NASDAQ:QQQ',
            'aapl options': 'NASDAQ:AAPL', 'tsla options': 'NASDAQ:TSLA',
            'nvda options': 'NASDAQ:NVDA', 'msft options': 'NASDAQ:MSFT',
            'amzn options': 'NASDAQ:AMZN', 'googl options': 'NASDAQ:GOOGL',
            'meta options': 'NASDAQ:META', 'nflx options': 'NASDAQ:NFLX',
            'brk.a options': 'NYSE:BRK.A', 'brk.b options': 'NYSE:BRK.B',
            'jnj options': 'NYSE:JNJ', 'pg options': 'NYSE:PG',
            'jpm options': 'NYSE:JPM', 'v options': 'NYSE:V',
            'ma options': 'NYSE:MA', 'hd options': 'NYSE:HD',
            'wmt options': 'NYSE:WMT', 'ko options': 'NYSE:KO',
            'pep options': 'NASDAQ:PEP', 'dis options': 'NYSE:DIS',
            'adbe options': 'NASDAQ:ADBE', 'crm options': 'NYSE:CRM',
            'orcl options': 'NYSE:ORCL', 'intc options': 'NASDAQ:INTC',
            'amd options': 'NASDAQ:AMD', 'csco options': 'NASDAQ:CSCO',
            'ibm options': 'NYSE:IBM', 'pypl options': 'NASDAQ:PYPL',
            'ubr options': 'NYSE:UBER', 'abnb options': 'NASDAQ:ABNB',
            'zm options': 'NASDAQ:ZM', 'pltr options': 'NYSE:PLTR',
            'roku options': 'NASDAQ:ROKU', 'spot options': 'NYSE:SPOT',
            'twtr options': 'NYSE:TWTR', 'snap options': 'NYSE:SNAP',
            'pins options': 'NYSE:PINS', 'sq options': 'NYSE:SQ',
            'shop options': 'NYSE:SHOP'
        }
    
    def _normalize_studies(self, studies: list) -> list:
        """Normalize study formats to correct TradingView format"""
        study_normalization = {
            'STD;BOLLINGER': 'STD;BB',
            'STD;BOLLINGERBANDS': 'STD;BB',
            'STD;BOLLINGER BANDS': 'STD;BB',
            'STD;BOLLINGER_BANDS': 'STD;BB',
            'BOLLINGER': 'STD;BB',
            'BOLLINGERBANDS': 'STD;BB',
            'BB': 'STD;BB',
            'RSI': 'STD;RSI',
            'MACD': 'STD;MACD',
            'SMA': 'STD;SMA',
            'EMA': 'STD;EMA',
            'STOCHASTIC': 'STD;STOCH',
            'STOCH': 'STD;STOCH',
            'WILLIAMS': 'STD;WPR',
            'WPR': 'STD;WPR',
            'CCI': 'STD;CCI',
            'ATR': 'STD;ATR',
            'ADX': 'STD;ADX',
            'MFI': 'STD;MFI',
            'MOM': 'STD;MOM',
            'PPO': 'STD;PPO',
            'PVO': 'STD;PVO',
            'ROC': 'STD;ROC',
            'RVI': 'STD;RVI',
            'SAR': 'STD;SAR',
            'TRIX': 'STD;TRIX',
            'VWAP': 'STD;VWAP',
            'WMA': 'STD;WMA',
            'BBANDS': 'STD;BB',
            'DEMA': 'STD;DEMA',
            'TEMA': 'STD;TEMA',
            'VIDYA': 'STD;VIDYA',
            'VWMA': 'STD;VWMA',
        }
        
        normalized = []
        for study in studies:
            # Check if already in correct format
            if study.startswith('STD;') and study in ['STD;RSI', 'STD;MACD', 'STD;BB', 'STD;SMA', 'STD;EMA', 'STD;STOCH', 'STD;WPR', 'STD;CCI', 'STD;ATR', 'STD;ADX', 'STD;MFI', 'STD;MOM', 'STD;PPO', 'STD;PVO', 'STD;ROC', 'STD;RVI', 'STD;SAR', 'STD;TRIX', 'STD;VWAP', 'STD;WMA', 'STD;BB', 'STD;DEMA', 'STD;TEMA', 'STD;VIDYA', 'STD;VWMA']:
                normalized.append(study)
            else:
                # Try to normalize
                study_upper = study.upper().replace(' ', '').replace('_', '')
                if study_upper in study_normalization:
                    normalized.append(study_normalization[study_upper])
                elif study.upper() in study_normalization:
                    normalized.append(study_normalization[study.upper()])
                else:
                    # Keep as-is if we don't recognize it
                    normalized.append(study)
        
        return normalized
    
    def _normalize_interval(self, interval: str, query: str = "") -> str:
        """Normalize interval from various formats to TradingView format"""
        interval_lower = interval.lower()
        
        # Check if query contains month/year patterns
        if 'month' in query.lower():
            if '6' in query or 'six' in query.lower():
                return '6M'
            elif '3' in query or 'three' in query.lower():
                return '3M'
            elif '1' in query or 'one' in query.lower():
                return '1M'
        
        if 'year' in query.lower():
            return '1Y'
        
        # Standard mapping
        interval_map = {
            '1m': '1', '1min': '1', '1 minute': '1',
            '5m': '5', '5min': '5', '5 minutes': '5',
            '15m': '15', '15min': '15', '15 minutes': '15',
            '30m': '30', '30min': '30', '30 minutes': '30',
            '1h': '60', '1hr': '60', '1 hour': '60', '60m': '60',
            '4h': '240', '4hr': '240', '4 hours': '240', '240m': '240',
            '1d': 'D', '1day': 'D', 'daily': 'D', 'day': 'D',
            '1w': 'W', '1week': 'W', 'weekly': 'W', 'week': 'W',
            '1m': '1M', '1month': '1M', '1-month': '1M', 'monthly': '1M',
            '3m': '3M', '3month': '3M', '3-month': '3M', '3 month': '3M', '3 months': '3M',
            '6m': '6M', '6month': '6M', '6-month': '6M', '6 month': '6M', '6 months': '6M',
            '1y': '12M', '1year': '12M', '1-year': '12M', 'yearly': '12M', 'year': '12M'
        }
        
        return interval_map.get(interval_lower, interval)
    
    def analyze_query_with_ai(self, query: str, current_state: Dict = None) -> Dict:
        """Use AI to analyze user query and extract chart updates"""
        try:
            # Format current state safely
            import json
            current_state_str = json.dumps(current_state) if current_state else "No current state (first query)"
            
            system_prompt = """You are a trading chart configuration expert. Analyze user queries and extract chart update information.

CURRENT CHART STATE:
""" + current_state_str + """

CRITICAL: Only update fields that the user EXPLICITLY mentions. Keep all other fields from current state unchanged.

Output JSON format:
{
    "needs_chart_update": boolean,
    "chart_config": {
        "symbol": "BINANCE:BTCUSD",
        "interval": "D",
        "studies": [],
        "chart_type": "1"
    },
    "extracted_info": {
        "symbols": ["BINANCE:BTCUSD"],
        "indicators": ["RSI", "MACD"],
        "timeframes": ["1h"],
        "actions": ["add:rsi", "remove:macd", "change:1h"]
    }
}"""
            
            response = client.chat.completions.create(
                model="gpt-5-nano",
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt + """

Rules:
1. Only update fields that user explicitly mentions
2. Preserve existing settings if not mentioned
3. Actions format: "add:indicator", "remove:indicator", "change:timeframe", "view:symbol"
4. Symbol formats (CRITICAL):
   - Crypto: BINANCE:BTCUSD, BINANCE:ETHUSD
   - Stocks: NASDAQ:AAPL, NYSE:TSLA
   - Forex: FX:EURUSD, FX:GBPUSD, FX:USDJPY, FX:AUDUSD
   - Commodities: OANDA:XAUUSD (gold), NYMEX:CL1! (crude oil)
   - Indices: AMEX:SPY, NASDAQ:QQQ
5. Intervals (CRITICAL - use EXACT format): 
   - Minutes: 1, 5, 15, 30
   - Hours: 60 (1h), 240 (4h)
   - Days/Weeks: D (daily), W (weekly)
   - Months: M (1 month), 3M (3 months), 6M (6 months)
   - Years: 12M (yearly/1 year)
   - "1 hour" → "60", "4 hour" → "240", "yearly" → "12M", "1 year" → "12M"
6. Chart types: 1=candlestick, 2=line, 3=bar, 4=area, 5=heikin ashi
7. Studies format (CRITICAL - MUST use EXACT format):
   - RSI → "STD;RSI"
   - MACD → "STD;MACD"
   - Bollinger Bands → "STD;BB" (NOT STD;BOLLINGER or STD;BOLLINGERBANDS)
   - SMA → "STD;SMA"
   - EMA → "STD;EMA"
   - Stochastic → "STD;STOCH"
   - Williams %R → "STD;WPR"
   - CCI → "STD;CCI"
   - ATR → "STD;ATR"
   - ADX → "STD;ADX"
   - MFI → "STD;MFI"
   - MOM → "STD;MOM"
   - PPO → "STD;PPO"
   - PVO → "STD;PVO"
   - ROC → "STD;ROC"
   - RVI → "STD;RVI"
   - SAR → "STD;SAR"
   - TRIX → "STD;TRIX"
   - VWAP → "STD;VWAP"
   - WMA → "STD;WMA"
   - BBANDS → "STD;BB"
   - DEMA → "STD;DEMA"
   - TEMA → "STD;TEMA"
   - VIDYA → "STD;VIDYA"
   - VWMA → "STD;VWMA"
8. If no chart update needed (just general question), set needs_chart_update: false

Examples:
- "Show Bitcoin" → symbol: "BINANCE:BTCUSD", needs_chart_update: true
- "USD/JPY chart" → symbol: "FX:USDJPY", needs_chart_update: true
- "Show Apple stock" → symbol: "NASDAQ:AAPL", needs_chart_update: true
- "Gold price" → symbol: "OANDA:XAUUSD", needs_chart_update: true
- "Add RSI indicator" → actions: ["add:rsi"], studies: ["STD;RSI"], needs_chart_update: true
- "Can u add MACD indicator" → actions: ["add:macd"], studies: ["STD;MACD"], needs_chart_update: true
- "I wanna see RSI" → actions: ["add:rsi"], studies: ["STD;RSI"], needs_chart_update: true
- "Show me MACD" → actions: ["add:macd"], studies: ["STD;MACD"], needs_chart_update: true
- "Add RSI and MACD" → actions: ["add:rsi", "add:macd"], studies: ["STD;RSI", "STD;MACD"], needs_chart_update: true
- "Add Bollinger Bands" → actions: ["add:bollinger"], studies: ["STD;BB"], needs_chart_update: true
- "Show EUR/USD 6-month chart with Bollinger Bands and RSI" → symbol: "FX:EURUSD", interval: "6M", studies: ["STD;BB", "STD;RSI"], needs_chart_update: true
- "Switch to 1 hour chart" → actions: ["change:1h"], interval: "60", needs_chart_update: true
- "What is RSI?" → needs_chart_update: false (just explanation, no chart change)
- "Remove MACD and add Bollinger Bands" → actions: ["remove:macd", "add:bollinger"], studies: ["STD;BB"], needs_chart_update: true
- "Update chart with USDJPY" → symbol: "FX:USDJPY", needs_chart_update: true

IMPORTANT STATE PRESERVATION:
- When user wants to ADD an indicator → KEEP existing studies and ADD the new one
- When user wants to REMOVE an indicator → KEEP other studies, only REMOVE the specified one
- When user changes symbol → KEEP interval, studies, and chart_type
- When user changes timeframe → KEEP symbol, studies, and chart_type
- ONLY update what user explicitly requests, preserve everything else

Studies format: "STD;RSI", "STD;MACD", "STD;BB", "STD;SMA", "STD;EMA", "STD;STOCH", "STD;WPR", "STD;CCI", "STD;ATR", "STD;ADX", "STD;MFI", "STD;MOM", "STD;PPO", "STD;PVO", "STD;ROC", "STD;RVI", "STD;SAR", "STD;TRIX", "STD;VWAP", "STD;WMA", "STD;BB", "STD;DEMA", "STD;TEMA", "STD;VIDYA", "STD;VWMA"

State Preservation Examples:
Current: {symbol: "BINANCE:BTCUSD", interval: "D", studies: ["STD;RSI"], chart_type: "1"}
Query: "Add MACD" → {symbol: "BINANCE:BTCUSD", interval: "D", studies: ["STD;RSI", "STD;MACD"], chart_type: "1"}

Current: {symbol: "FX:USDJPY", interval: "60", studies: ["STD;RSI", "STD;MACD"], chart_type: "1"}
Query: "Show Ethereum" → {symbol: "BINANCE:ETHUSD", interval: "60", studies: ["STD;RSI", "STD;MACD"], chart_type: "1"}

Current: {symbol: "NASDAQ:AAPL", interval: "D", studies: ["STD;RSI"], chart_type: "1"}
Query: "Remove RSI" → {symbol: "NASDAQ:AAPL", interval: "D", studies: [], chart_type: "1"}

Return ONLY valid JSON."""
                    },
                    {
                        "role": "user",
                        "content": query
                    }
                ],
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Parse JSON response
            import json
            try:
                # Find JSON in response
                json_start = ai_response.find('{')
                json_end = ai_response.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_str = ai_response[json_start:json_end]
                    result = json.loads(json_str)
                    
                    # Normalize studies to ensure correct format
                    if 'chart_config' in result and 'studies' in result['chart_config']:
                        result['chart_config']['studies'] = self._normalize_studies(
                            result['chart_config']['studies']
                        )
                    
                    # Normalize interval to ensure correct format
                    if 'chart_config' in result and 'interval' in result['chart_config']:
                        result['chart_config']['interval'] = self._normalize_interval(
                            result['chart_config']['interval'], query
                        )
                    
                    return result
            except Exception as parse_error:
                print(f"JSON parse error: {parse_error}, response: {ai_response}")
                return self.analyze_query(query)  # Fallback to rule-based
                
        except Exception as e:
            print(f"AI chart analysis error: {e}")
            return self.analyze_query(query)  # Fallback to rule-based
    
    def analyze_query(self, query: str) -> Dict:
        """
        Analyze user query to determine if chart update is needed
        
        Returns:
            {
                'needs_chart_update': bool,
                'chart_config': {
                    'symbol': str,
                    'interval': str,
                    'studies': List[str],
                    'chart_type': str
                },
                'extracted_info': {
                    'symbols': List[str],
                    'indicators': List[str],
                    'timeframes': List[str],
                    'actions': List[str]
                }
            }
        """
        query_lower = query.lower()
        
        # Extract information from query
        extracted_info = self._extract_chart_info(query_lower)
        
        # Determine if chart update is needed
        needs_update = self._should_update_chart(extracted_info)
        
        # Generate chart configuration
        chart_config = self._generate_chart_config(extracted_info)
        
        return {
            'needs_chart_update': needs_update,
            'chart_config': chart_config,
            'extracted_info': extracted_info
        }
    
    def _extract_chart_info(self, query: str) -> Dict:
        """Extract chart-related information from query"""
        extracted = {
            'symbols': [],
            'indicators': [],
            'timeframes': [],
            'actions': []
        }
        
        # First, try to extract symbols using our mapping
        found_symbols = []
        for term, tradingview_symbol in self.symbol_mapping.items():
            if term in query:
                found_symbols.append(tradingview_symbol)
        
        # If no symbols found in mapping, use AI to extract symbols
        if not found_symbols:
            ai_symbols = self._extract_symbols_with_ai(query)
            found_symbols.extend(ai_symbols)
        
        extracted['symbols'] = found_symbols
        
        # Extract indicators
        for indicator in self.chart_keywords['indicators']:
            if indicator in query:
                # Normalize indicator names
                indicator_upper = indicator.upper().replace(' ', '')
                if indicator_upper == 'BOLLINGERBANDS' or indicator.upper() == 'BOLLINGER':
                    if 'BOLLINGER' not in extracted['indicators']:
                        extracted['indicators'].append('BOLLINGER')
                elif indicator_upper not in extracted['indicators']:
                    extracted['indicators'].append(indicator_upper)
        
        # Extract timeframes - prioritize longer matches first
        timeframe_patterns = [
            ('6-month', '6M'), ('6 month', '6M'), ('6 months', '6M'), ('six month', '6M'),
            ('3-month', '3M'), ('3 month', '3M'), ('3 months', '3M'), ('three month', '3M'),
            ('1-month', '1M'), ('1 month', '1M'), ('one month', '1M'),
            ('1-year', '1Y'), ('1 year', '1Y'), ('one year', '1Y'),
            ('1h', '1h'), ('4h', '4h'), ('1d', '1d'), ('1w', '1w'),
            ('1m', '1m'), ('5m', '5m'), ('15m', '15m'), ('30m', '30m'),
            ('6M', '6M'), ('3M', '3M'), ('1M', '1M'), ('1Y', '1Y')
        ]
        
        for pattern, normalized in timeframe_patterns:
            if pattern in query:
                if normalized not in extracted['timeframes']:
                    extracted['timeframes'].append(normalized)
                    break  # Only take the first match
        
        # Extract comprehensive actions for all chart elements
        action_patterns = [
            # Indicator actions - check for "bollinger bands" before "bollinger"
            r'(add|show|display|plot|with)\s+(bollinger\s+bands|rsi|macd|bollinger|sma|ema|stochastic|williams|cci|atr|adx|mfi|mom|ppo|pvo|roc|rvi|sar|trix|vwap|wma|bb|dema|tema|vidya|vwma)',
            r'(remove|delete|hide)\s+(bollinger\s+bands|rsi|macd|bollinger|sma|ema|stochastic|williams|cci|atr|adx|mfi|mom|ppo|pvo|roc|rvi|sar|trix|vwap|wma|bb|dema|tema|vidya|vwma)',
            
            # Timeframe/Interval actions
            r'(switch|change|set)\s+to\s+(1m|5m|15m|30m|1h|4h|1d|1w|1M|3M|6M|1Y)',
            r'(show|display)\s+(1m|5m|15m|30m|1h|4h|1d|1w|1M|3M|6M|1Y)',
            
            # Symbol actions
            r'(show|display|switch|change)\s+to\s+(\w+)',
            r'(view|look\s+at)\s+(\w+)',
            
            # Chart type actions - improved to handle multi-word types
            r'(switch|change)\s+to\s+(candlestick|line\s+chart|bar\s+chart|area\s+chart|heikin\s+ashi)',
            r'(show|display|can\s+u\s+show)\s+(candlestick|line\s+chart|bar\s+chart|area\s+chart|heikin\s+ashi)',
            r'(switch|change)\s+to\s+(candlestick|line|bar|area|heikin\s+ashi)',
            r'(show|display|can\s+u\s+show)\s+(candlestick|line|bar|area|heikin\s+ashi)',
            
            # Pattern actions
            r'(show|display|highlight)\s+(support|resistance|trend|breakout|reversal|triangle|head\s+and\s+shoulders)',
            r'(find|detect)\s+(support|resistance|trend|breakout|reversal|triangle|head\s+and\s+shoulders)',
            
            # General actions
            r'(zoom|pan|reset)\s+(in|out|to\s+fit)',
            r'(save|export|screenshot)',
            r'(fullscreen|maximize|minimize)'
        ]
        
        for pattern in action_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    action_type, target = match
                else:
                    action_type = match
                    target = ""
                
                # Normalize target name
                normalized_target = target.replace(' bands', '').replace(' ', '_')
                
                # Categorize actions
                if any(word in action_type.lower() for word in ['remove', 'delete', 'hide']):
                    extracted['actions'].append(f"remove:{normalized_target}")
                elif any(word in action_type.lower() for word in ['add', 'show', 'display', 'plot', 'with']):
                    extracted['actions'].append(f"add:{normalized_target}")
                elif any(word in action_type.lower() for word in ['switch', 'change', 'set']):
                    extracted['actions'].append(f"change:{normalized_target}")
                elif any(word in action_type.lower() for word in ['view', 'look']):
                    extracted['actions'].append(f"view:{normalized_target}")
                else:
                    extracted['actions'].append(f"action:{action_type}:{normalized_target}")
        
        return extracted
    
    def _extract_symbols_with_ai(self, query: str) -> list:
        """Use AI to extract and convert symbols to TradingView format"""
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini-search-preview",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a financial symbol resolver for TradingView.
Given any user query (e.g. "bitcoin 1h", "apple stock", "eurusd chart"), 
identify the most likely TradingView symbol in the format EXCHANGE:SYMBOL.

Examples:
- bitcoin, btc, btcusdt → BINANCE:BTCUSDT
- ethereum, eth → BINANCE:ETHUSDT
- apple, aapl → NASDAQ:AAPL
- tesla → NASDAQ:TSLA
- eurusd, euro usd → FX:EURUSD
- gold → OANDA:XAUUSD
- s&p 500 → SP:SPX
- crude oil → NYMEX:CL1!

If the symbol is unclear, choose the most common version on TradingView.
Return only the TradingView symbol, nothing else."""
                    },
                    {
                        "role": "user",
                        "content": query
                    }
                ],
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # AI returns just the symbol string, so return it as a list
            if ai_response and ':' in ai_response:
                return [ai_response]
            
            return []
            
        except Exception as e:
            print(f"AI symbol extraction error: {e}")
            return []
    
    def _should_update_chart(self, extracted_info: Dict) -> bool:
        """Determine if chart should be updated based on extracted info"""
        # Update chart if:
        # 1. User mentions indicators
        # 2. User mentions symbols
        # 3. User mentions timeframes
        # 4. User mentions chart actions
        
        return (
            len(extracted_info['indicators']) > 0 or
            len(extracted_info['symbols']) > 0 or
            len(extracted_info['timeframes']) > 0 or
            len(extracted_info['actions']) > 0
        )
    
    def _generate_chart_config(self, extracted_info: Dict) -> Dict:
        """Generate chart configuration based on extracted info"""
        config = {
            'symbol': 'BINANCE:BTCUSD',  # Default to Bitcoin
            'interval': 'D',  # Default
            'studies': [],  # No default indicators - only add what user requests
            'chart_type': '1'  # Default candlestick
        }
        
        # Only update symbol if explicitly mentioned
        if extracted_info['symbols']:
            config['symbol'] = extracted_info['symbols'][0]  # Use first found symbol
        
        # Only update interval if explicitly mentioned
        if extracted_info['timeframes']:
            timeframe = extracted_info['timeframes'][0]
            interval_map = {
                '1m': '1',
                '5m': '5',
                '15m': '15',
                '30m': '30',
                '1h': '60',
                '4h': '240',
                '1d': 'D',
                '1w': 'W',
                '1M': 'M',
                '3M': '3M',
                '6M': '6M',
                '1Y': '12M',
                'yearly': '12M'
            }
            config['interval'] = interval_map.get(timeframe, 'D')
        
        # Handle all types of actions
        if extracted_info['indicators'] or extracted_info['actions']:
            study_map = {
                'RSI': 'STD;RSI',
                'MACD': 'STD;MACD',
                'BOLLINGER': 'STD;BB',
                'SMA': 'STD;SMA',
                'EMA': 'STD;EMA',
                'STOCHASTIC': 'STD;STOCH',
                'WILLIAMS': 'STD;WPR',
                'CCI': 'STD;CCI',
                'ATR': 'STD;ATR',
                'ADX': 'STD;ADX',
                'MFI': 'STD;MFI',
                'MOM': 'STD;MOM',
                'PPO': 'STD;PPO',
                'PVO': 'STD;PVO',
                'ROC': 'STD;ROC',
                'RVI': 'STD;RVI',
                'SAR': 'STD;SAR',
                'TRIX': 'STD;TRIX',
                'VWAP': 'STD;VWAP',
                'WMA': 'STD;WMA',
                'BBANDS': 'STD;BB',
                'DEMA': 'STD;DEMA',
                'TEMA': 'STD;TEMA',
                'VIDYA': 'STD;VIDYA',
                'VWMA': 'STD;VWMA',
            }
            
            chart_type_map = {
                'CANDLESTICK': '1',
                'LINE': '2',
                'LINE CHART': '2',
                'BAR': '3',
                'BAR CHART': '3',
                'AREA': '4',
                'AREA CHART': '4',
                'HEIKIN ASHI': '5'
            }
            
            # Start with empty studies - only add what user explicitly requests
            new_studies = []
            
            # Process all actions
            for action in extracted_info['actions']:
                action_parts = action.split(':')
                action_type = action_parts[0]
                target = action_parts[1] if len(action_parts) > 1 else ""
                
                if action_type == 'remove':
                    # Remove indicators
                    indicator_name = target.upper()
                    if indicator_name in study_map:
                        study_to_remove = study_map[indicator_name]
                        if study_to_remove in new_studies:
                            new_studies.remove(study_to_remove)
                
                elif action_type == 'add':
                    # Add indicators
                    indicator_name = target.upper()
                    if indicator_name in study_map and study_map[indicator_name] not in new_studies:
                        new_studies.append(study_map[indicator_name])
                
                elif action_type == 'change':
                    # Change timeframe or chart type
                    if target in ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w', '1M', '3M', '6M', '1Y']:
                        interval_map = {
                            '1m': '1', '5m': '5', '15m': '15', '30m': '30',
                            '1h': '60', '4h': '240', '1d': 'D', '1w': 'W',
                            '1M': 'M', '3M': '3M', '6M': '6M', '1Y': '12M', 'yearly': '12M'
                        }
                        config['interval'] = interval_map.get(target, 'D')
                    elif target.upper() in chart_type_map:
                        config['chart_type'] = chart_type_map[target.upper()]
                
                elif action_type == 'view':
                    # View specific symbol (handled by symbol extraction)
                    pass
            
            # Add requested indicators from direct extraction
            for indicator in extracted_info['indicators']:
                if indicator in study_map and study_map[indicator] not in new_studies:
                    new_studies.append(study_map[indicator])
            
            # Only update studies if user explicitly requested indicators
            if new_studies or extracted_info['indicators'] or any(a.startswith('add:') or a.startswith('remove:') for a in extracted_info['actions']):
                config['studies'] = new_studies
        
        return config
    
    async def analyze_with_ai(self, query: str) -> Dict:
        """
        Use AI to analyze query for more sophisticated chart updates
        """
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a chart analysis expert. Analyze the user's query and determine:
1. If a chart update is needed
2. What chart configuration should be applied
3. Extract relevant information

Respond with JSON format:
{
    "needs_chart_update": boolean,
    "chart_config": {
        "symbol": "BINANCE:BTCUSD",
        "interval": "D",
        "studies": ["STD;RSI"],
        "chart_type": "1"
    },
    "extracted_info": {
        "symbols": ["BINANCE:BTCUSD"],
        "indicators": ["RSI"],
        "timeframes": ["D"],
        "actions": ["add"]
    },
    "reasoning": "Brief explanation of the analysis"
}"""
                    },
                    {
                        "role": "user",
                        "content": query
                    }
                ],
            )
            
            # Parse AI response
            ai_response = response.choices[0].message.content
            
            # Try to extract JSON from response
            import json
            try:
                # Find JSON in response
                json_start = ai_response.find('{')
                json_end = ai_response.rfind('}') + 1
                json_str = ai_response[json_start:json_end]
                return json.loads(json_str)
            except:
                # Fallback to rule-based analysis
                return self.analyze_query(query)
                
        except Exception as e:
            print(f"AI analysis error: {e}")
            # Fallback to rule-based analysis
            return self.analyze_query(query)

# Global instance
chart_analysis_service = ChartAnalysisService()