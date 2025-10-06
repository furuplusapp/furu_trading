import re
from typing import Dict
from openai import OpenAI
from app.core.config import settings

client = OpenAI(api_key=settings.openai_api_key)

class ChartAnalysisService:
    """Service to analyze user queries and determine chart updates"""
    
    def __init__(self):
        self.chart_keywords = {
            'indicators': ['rsi', 'macd', 'bollinger', 'sma', 'ema', 'stochastic', 'williams', 'cci', 'atr'],
            'symbols': ['aapl', 'msft', 'googl', 'amzn', 'tsla', 'nvda', 'meta', 'nflx', 'spy', 'qqq', 'btc', 'eth', 'xrp', 'doge', 'sol', 'ada', 'dot', 'link', 'uni', 'ltc'],
            'timeframes': ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w', '1M', '3M', '6M', '1Y'],
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
            'ethjp': 'BINANCE:ETHJPY', 'ethjpy': 'BINANCE:ETHJPY', 'eth/jpy': 'BINANCE:ETHJPY', 'eth-jpy': 'BINANCE:ETHJPY',
            'ethgbp': 'BINANCE:ETHGBP', 'ethgbp': 'BINANCE:ETHGBP', 'eth/gbp': 'BINANCE:ETHGBP', 'eth-gbp': 'BINANCE:ETHGBP',
            'ethcad': 'BINANCE:ETHCAD', 'ethcad': 'BINANCE:ETHCAD', 'eth/cad': 'BINANCE:ETHCAD', 'eth-cad': 'BINANCE:ETHCAD',
            'ethnzd': 'BINANCE:ETHNZD', 'ethnzd': 'BINANCE:ETHNZD', 'eth/nzd': 'BINANCE:ETHNZD', 'eth-nzd': 'BINANCE:ETHNZD',
            'ethaud': 'BINANCE:ETHAUD', 'ethaud': 'BINANCE:ETHAUD', 'eth/aud': 'BINANCE:ETHAUD', 'eth-aud': 'BINANCE:ETHAUD',
            'ethchf': 'BINANCE:ETHCHF', 'ethchf': 'BINANCE:ETHCHF', 'eth/chf': 'BINANCE:ETHCHF', 'eth-chf': 'BINANCE:ETHCHF',
            'ethgbp': 'BINANCE:ETHGBP', 'ethgbp': 'BINANCE:ETHGBP', 'ethgbp': 'BINANCE:ETHGBP', 'ethgbp': 'BINANCE:ETHGBP',
            'ethcad': 'BINANCE:ETHCAD', 'ethcad': 'BINANCE:ETHCAD', 'ethcad': 'BINANCE:ETHCAD', 'ethcad': 'BINANCE:ETHCAD',
            'ethnzd': 'BINANCE:ETHNZD', 'ethnzd': 'BINANCE:ETHNZD', 'ethnzd': 'BINANCE:ETHNZD', 'ethnzd': 'BINANCE:ETHNZD',
            'ethaud': 'BINANCE:ETHAUD', 'ethaud': 'BINANCE:ETHAUD', 'ethaud': 'BINANCE:ETHAUD', 'ethaud': 'BINANCE:ETHAUD', 
            'ethchf': 'BINANCE:ETHCHF', 'ethchf': 'BINANCE:ETHCHF', 'ethchf': 'BINANCE:ETHCHF', 'ethchf': 'BINANCE:ETHCHF',
            'ethgbp': 'BINANCE:ETHGBP', 'ethgbp': 'BINANCE:ETHGBP', 'ethgbp': 'BINANCE:ETHGBP', 'ethgbp': 'BINANCE:ETHGBP',
            
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
            
            # Major Options (SPY, QQQ, AAPL, TSLA, etc.)
            'spy options': 'AMEX:SPY', 'qqq options': 'NASDAQ:QQQ',
            'aapl options': 'NASDAQ:AAPL', 'tsla options': 'NASDAQ:TSLA',
            'nvda options': 'NASDAQ:NVDA', 'msft options': 'NASDAQ:MSFT',
            'amzn options': 'NASDAQ:AMZN', 'googl options': 'NASDAQ:GOOGL',
            'meta options': 'NASDAQ:META', 'nflx options': 'NASDAQ:NFLX'
        }
    
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
                extracted['indicators'].append(indicator.upper())
        
        # Extract timeframes
        for timeframe in self.chart_keywords['timeframes']:
            if timeframe in query:
                extracted['timeframes'].append(timeframe)
        
        # Extract comprehensive actions for all chart elements
        action_patterns = [
            # Indicator actions
            r'(add|show|display|plot)\s+(rsi|macd|bollinger|sma|ema|stochastic|williams|cci|atr)',
            r'(remove|delete|hide)\s+(rsi|macd|bollinger|sma|ema|stochastic|williams|cci|atr)',
            
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
                
                # Categorize actions
                if any(word in action_type.lower() for word in ['remove', 'delete', 'hide']):
                    extracted['actions'].append(f"remove:{target}")
                elif any(word in action_type.lower() for word in ['add', 'show', 'display', 'plot']):
                    extracted['actions'].append(f"add:{target}")
                elif any(word in action_type.lower() for word in ['switch', 'change', 'set']):
                    extracted['actions'].append(f"change:{target}")
                elif any(word in action_type.lower() for word in ['view', 'look']):
                    extracted['actions'].append(f"view:{target}")
                else:
                    extracted['actions'].append(f"action:{action_type}:{target}")
        
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
            'studies': ['STD;RSI', 'STD;MACD'],  # Default indicators
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
                '1Y': 'Y'
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
                'ATR': 'STD;ATR'
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
            
            # Start with default indicators
            new_studies = ['STD;RSI', 'STD;MACD']
            
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
                            '1M': 'M', '3M': '3M', '6M': '6M', '1Y': 'Y'
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
                temperature=0.1
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