import os
import logging
import yfinance as yf
from ibkr_service import ibkr_service
import asyncio
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Global variable for current data source
_current_source = os.getenv('MARKET_DATA_SOURCE', 'ibkr').lower()

def get_current_source():
    return _current_source

def set_current_source(source: str):
    global _current_source
    _current_source = source.lower()

# Base class for market data sources
class MarketDataSource:
    def get_market_data(self, symbol: str):
        raise NotImplementedError
    def get_news(self, symbol: str):
        raise NotImplementedError

# Yahoo Finance implementation
class YahooFinanceSource(MarketDataSource):
    def get_market_data(self, symbol: str):
        ticker = yf.Ticker(symbol)
        info = ticker.info
        price = info.get('regularMarketPrice')
        # Use previous close as the 'open' reference for price change, matching Yahoo's main display
        open_price = info.get('regularMarketPreviousClose')
        bid = info.get('bid')
        ask = info.get('ask')
        high = info.get('dayHigh')
        low = info.get('dayLow')
        volume = info.get('volume')
        timestamp = info.get('regularMarketTime')
        return {
            'symbol': symbol,
            'price': price,
            'bid': bid,
            'ask': ask,
            'high': high,
            'low': low,
            'volume': volume,
            'timestamp': timestamp,
            'open': open_price if open_price is not None else None
        }
    def get_news(self, symbol: str):
        # Yahoo Finance news via yfinance
        ticker = yf.Ticker(symbol)
        news = ticker.news
        result = []
        for n in news:
            # providerPublishTime is a Unix timestamp (seconds)
            published_at = None
            if n.get('providerPublishTime'):
                try:
                    published_at = datetime.fromtimestamp(n['providerPublishTime']).isoformat()
                except Exception:
                    published_at = None
            result.append({
                'title': n.get('title'),
                'publisher': n.get('publisher'),  # This is the real publisher (e.g., SeekingAlpha)
                'link': n.get('link'),
                'published_at': published_at,
                'source': 'yahoo',
                'summary': n.get('summary', ''),
                'raw_json': json.dumps(n)
            })
        return result

# Finnhub implementation (free tier)
class FinnhubSource(MarketDataSource):
    def __init__(self, api_key):
        if not api_key or len(api_key.strip()) < 10:  # Finnhub API keys are typically longer
            raise ValueError("Invalid Finnhub API key. Please check your .env file.")
        self.api_key = api_key.strip()
        logger.info(f"Initializing Finnhub source with API key: {self.api_key[:5]}...")
        
    def get_market_data(self, symbol: str):
        url = f'https://finnhub.io/api/v1/quote?symbol={symbol}&token={self.api_key}'
        try:
            r = requests.get(url)
            r.raise_for_status()
            data = r.json()
            logger.info(f"Finnhub market data response for {symbol}: {data}")
            
            if not data or 'error' in data:
                logger.error(f"Finnhub API error for {symbol}: {data.get('error', 'Unknown error')}")
                return None
                
            return {
                'symbol': symbol,
                'price': data.get('c'),
                'open': data.get('pc'),
                'bid': None,
                'ask': None,
                'high': data.get('h'),
                'low': data.get('l'),
                'volume': None,
                'timestamp': None
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Finnhub request error for {symbol}: {e}")
            return None
            
    def get_news(self, symbol: str):
        # Use last 7 days for news
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        url = f'https://finnhub.io/api/v1/company-news?symbol={symbol}&from={start_date.strftime("%Y-%m-%d")}&to={end_date.strftime("%Y-%m-%d")}&token={self.api_key}'
        logger.info(f"Fetching Finnhub news for {symbol} from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        try:
            r = requests.get(url)
            r.raise_for_status()
            news = r.json()
            
            # Log the raw response for debugging
            logger.debug(f"Raw Finnhub news response for {symbol}: {news[:2]}")
            
            if not news:
                logger.warning(f"No news found for {symbol}")
                return []
            
            if not isinstance(news, list):
                logger.error(f"Invalid response format from Finnhub for {symbol}. Expected list, got {type(news)}")
                return []
            
            valid_news = []
            required_fields = {
                'headline': ['headline', 'title'],
                'datetime': ['datetime', 'time', 'timestamp'],
                'summary': ['summary', 'description']
            }
            for n in news:
                news_item = {}
                valid = True
                for our_field, possible_fields in required_fields.items():
                    value = None
                    for field in possible_fields:
                        if field in n and n[field]:
                            value = n[field]
                            break
                    if value is None:
                        valid = False
                        break
                    news_item[our_field] = value
                if valid:
                    formatted_item = {
                        'title': news_item['headline'],
                        'publisher': n.get('source', 'Finnhub'),
                        'link': n.get('url', ''),
                        'providerPublishTime': news_item['datetime'],
                        'type': 'news',
                        'summary': news_item['summary']
                    }
                    if isinstance(formatted_item['providerPublishTime'], (int, float)):
                        formatted_item['providerPublishTime'] = datetime.fromtimestamp(
                            formatted_item['providerPublishTime']
                        ).isoformat()
                    valid_news.append(formatted_item)
            logger.info(f"Found {len(valid_news)} valid news items for {symbol}")
            valid_news.sort(key=lambda x: x['providerPublishTime'], reverse=True)
            return valid_news[:10] if valid_news else []
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Finnhub news request error for {symbol}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error processing news for {symbol}: {e}")
            return []

# Marketaux implementation
class MarketauxSource(MarketDataSource):
    def __init__(self, api_key):
        self.api_key = api_key
        # Test if we have access to news endpoint
        self._has_news_access = self._test_news_access()
        
    def _test_news_access(self):
        """Test if the API key has access to the news endpoint"""
        if not self.api_key:
            return False
        try:
            url = f'https://api.marketaux.com/v1/news/all?symbols=AAPL&filter_entities=true&language=en&api_token={self.api_key}'
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                logger.info("Marketaux news endpoint is accessible")
                return True
            elif r.status_code == 402:
                logger.info("Marketaux news endpoint requires payment - skipping")
                return False
            else:
                logger.warning(f"Marketaux news endpoint test returned status {r.status_code}")
                return False
        except Exception as e:
            logger.warning(f"Marketaux news endpoint test failed: {e}")
            return False
            
    def get_news(self, symbol: str):
        if not self._has_news_access:
            logger.debug(f"Skipping Marketaux news for {symbol} - no access to news endpoint")
            return []
            
        url = f'https://api.marketaux.com/v1/news/all?symbols={symbol}&filter_entities=true&language=en&api_token={self.api_key}'
        try:
            r = requests.get(url)
            r.raise_for_status()
            data = r.json()
            news = data.get('data', [])
            result = []
            for n in news:
                result.append({
                    'title': n.get('title'),
                    'summary': n.get('description', ''),
                    'link': n.get('url'),
                    'publisher': n.get('source', {}).get('name', ''),
                    'published_at': n.get('published_at'),
                    'source': 'marketaux',
                    'score': n.get('score'),
                    'raw_json': json.dumps(n)
                })
            return result
        except Exception as e:
            logger.error(f"Marketaux error for {symbol}: {e}")
            return []

# Financial Modeling Prep implementation
class FMPSource(MarketDataSource):
    def __init__(self, api_key):
        self.api_key = api_key
        # Test if we have access to news endpoint
        self._has_news_access = self._test_news_access()
        
    def _test_news_access(self):
        """Test if the API key has access to the news endpoint"""
        if not self.api_key:
            return False
        try:
            url = f'https://financialmodelingprep.com/api/v3/stock_news?tickers=AAPL&limit=1&apikey={self.api_key}'
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                logger.info("FMP news endpoint is accessible")
                return True
            elif r.status_code == 403:
                logger.info("FMP news endpoint requires higher subscription tier - skipping")
                return False
            else:
                logger.warning(f"FMP news endpoint test returned status {r.status_code}")
                return False
        except Exception as e:
            logger.warning(f"FMP news endpoint test failed: {e}")
            return False
            
    def get_news(self, symbol: str):
        if not self._has_news_access:
            logger.debug(f"Skipping FMP news for {symbol} - no access to news endpoint")
            return []
            
        url = f'https://financialmodelingprep.com/api/v3/stock_news?tickers={symbol}&limit=50&apikey={self.api_key}'
        try:
            r = requests.get(url)
            r.raise_for_status()
            news = r.json()
            result = []
            for n in news:
                result.append({
                    'title': n.get('title'),
                    'summary': n.get('text', ''),
                    'link': n.get('url'),
                    'publisher': n.get('site', ''),
                    'published_at': n.get('publishedDate'),
                    'source': 'fmp',
                    'score': None,
                    'raw_json': json.dumps(n)
                })
            return result
        except Exception as e:
            logger.error(f"FMP error for {symbol}: {e}")
            return []

# NewsAPI implementation
class NewsAPISource(MarketDataSource):
    def __init__(self, api_key):
        self.api_key = api_key
    def get_news(self, symbol: str):
        url = f'https://newsapi.org/v2/everything?q={symbol}&sortBy=publishedAt&language=en&apiKey={self.api_key}'
        try:
            r = requests.get(url)
            r.raise_for_status()
            data = r.json()
            news = data.get('articles', [])
            result = []
            for n in news:
                result.append({
                    'title': n.get('title'),
                    'summary': n.get('description', ''),
                    'link': n.get('url'),
                    'publisher': n.get('source', {}).get('name', ''),
                    'published_at': n.get('publishedAt'),
                    'source': 'newsapi',
                    'score': None,
                    'raw_json': json.dumps(n)
                })
            return result
        except Exception as e:
            logger.error(f"NewsAPI error for {symbol}: {e}")
            return []

MARKETAUX_API_KEY = os.getenv('MARKETAUX_API_KEY', '')
FMP_API_KEY = os.getenv('FMP_API_KEY', '')
NEWSAPI_API_KEY = os.getenv('NEWSAPI_API_KEY', '')

MARKET_DATA_SOURCES = {
    'yahoo': YahooFinanceSource(),
    'finnhub': FinnhubSource(api_key=os.getenv('FINNHUB_API_KEY', '')),
    'marketaux': MarketauxSource(api_key=MARKETAUX_API_KEY),
    'fmp': FMPSource(api_key=FMP_API_KEY),
    'newsapi': NewsAPISource(api_key=NEWSAPI_API_KEY),
}

async def get_market_data(symbol: str):
    source = get_current_source()
    if source == 'yahoo':
        try:
            loop = asyncio.get_event_loop()
            yahoo_source = MARKET_DATA_SOURCES['yahoo']
            data = await loop.run_in_executor(None, lambda: yahoo_source.get_market_data(symbol))
            if 'open' not in data:
                data['open'] = None
            return data
        except Exception as e:
            logger.error(f"Yahoo Finance error for {symbol}: {e}")
            return None
    else:
        # Default to IBKR
        data = await ibkr_service.get_market_data(symbol)
        if data is not None and 'open' not in data:
            data['open'] = None
        return data 

def get_all_news(symbol: str):
    all_news = []
    for name, source in MARKET_DATA_SOURCES.items():
        try:
            news = source.get_news(symbol)
            if news:
                all_news.extend(news)
        except Exception as e:
            logger.error(f"Error fetching news from {name} for {symbol}: {e}")
    # Deduplicate by link
    seen = set()
    deduped = []
    for n in all_news:
        if n['link'] and n['link'] not in seen:
            deduped.append(n)
            seen.add(n['link'])
    # Sort by published_at desc
    deduped.sort(key=lambda x: x.get('published_at', ''), reverse=True)
    return deduped 