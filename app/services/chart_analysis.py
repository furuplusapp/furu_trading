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
            'symbols': ['aapl', 'msft', 'googl', 'amzn', 'tsla', 'nvda', 'meta', 'nflx', 'spy', 'qqq', 'djx', 'djia', 'ixic', 'spx', 'russell', 'dow', 'nasdaq', 's&p', 'nasdaq100', 'nasdaqcomposite', 'nasdaq100tr', 'btc', 'eth', 'xrp', 'doge', 'sol', 'ada', 'dot', 'link', 'uni', 'ltc', 'xlm', 'xmr', 'xem', 'xag', 'xau', 'xpd', 'xpt', 'xpf', 'xpb', 'xpg', 'xpm', 'xpn', 'xpo', 'xpp', 'xpq', 'xpr', 'xps', 'xpu', 'btcusd', 'ethusd', 'btcusdt', 'ethusdt', 'btcusdc', 'ethusdc'],
            'timeframes': ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w', '1M', '3M', '6M', '1Y'],
            'chart_types': ['candlestick', 'line', 'bar', 'area', 'heikin ashi'],
            'patterns': ['support', 'resistance', 'trend', 'breakout', 'reversal', 'triangle', 'head and shoulders']
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
        
        # Extract symbols
        for symbol in self.chart_keywords['symbols']:
            if symbol in query:
                extracted['symbols'].append(symbol.upper())
        
        # Extract indicators
        for indicator in self.chart_keywords['indicators']:
            if indicator in query:
                extracted['indicators'].append(indicator.upper())
        
        # Extract timeframes
        for timeframe in self.chart_keywords['timeframes']:
            if timeframe in query:
                extracted['timeframes'].append(timeframe)
        
        # Extract actions
        action_patterns = [
            r'add\s+(\w+)',
            r'show\s+(\w+)',
            r'display\s+(\w+)',
            r'plot\s+(\w+)',
            r'remove\s+(\w+)',
            r'change\s+(\w+)',
            r'switch\s+to\s+(\w+)'
        ]
        
        for pattern in action_patterns:
            matches = re.findall(pattern, query)
            extracted['actions'].extend(matches)
        
        return extracted
    
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
            'symbol': 'NASDAQ:AAPL',  # Default
            'interval': 'D',  # Default
            'studies': [],
            'chart_type': '1'  # Default candlestick
        }
        
        # Set symbol
        if extracted_info['symbols']:
            symbol = extracted_info['symbols'][0]
            config['symbol'] = f'NASDAQ:{symbol}' if symbol in ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'DJX', 'BTC', 'ETH', 'XRP', 'DOGE', 'SOL', 'ADA', 'DOT', 'LINK', 'UNI', 'LTC', 'XLM', 'XMR', 'XEM', 'XAG', 'XAU', 'XPD', 'XPT', 'XPF', 'XPB', 'XPG', 'XPM', 'XPN', 'XPO', 'XPP', 'XPQ', 'XPR', 'XPS', 'XPT', 'XPU', 'XPQ', 'XPR', 'XPS', 'XPT', 'XPU'] else f'NASDAQ:{symbol}'
        
        # Set interval
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
        
        # Set studies (indicators)
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
        
        for indicator in extracted_info['indicators']:
            if indicator in study_map:
                config['studies'].append(study_map[indicator])
        
        # Default RSI if no indicators specified but chart update needed
        if not config['studies'] and extracted_info['indicators']:
            config['studies'].append('STD;RSI')
        
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
        "symbol": "NASDAQ:AAPL",
        "interval": "D",
        "studies": ["STD;RSI"],
        "chart_type": "1"
    },
    "extracted_info": {
        "symbols": ["AAPL"],
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
