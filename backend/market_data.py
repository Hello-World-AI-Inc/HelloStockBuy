import os
import logging
import yfinance as yf
from ibkr_service import ibkr_service
import asyncio
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import json
from news_scheduler import news_scheduler
import pytz

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Set timezone
TIMEZONE = os.getenv('TZ', 'Canada/Vancouver')
try:
    tz = pytz.timezone(TIMEZONE)
    logger.info(f"Market data timezone set to: {TIMEZONE}")
except Exception as e:
    logger.warning(f"Invalid timezone {TIMEZONE}, using UTC: {e}")
    tz = pytz.UTC

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
            # Parse the nested content structure
            content = n.get('content', {})
            
            # Extract title from content
            title = content.get('title')
            
            # Extract publisher from provider
            provider = content.get('provider', {})
            publisher = provider.get('displayName', 'Yahoo Finance')
            
            # Extract link from canonicalUrl or clickThroughUrl
            canonical_url = content.get('canonicalUrl', {})
            click_through_url = content.get('clickThroughUrl', {})
            link = canonical_url.get('url') or click_through_url.get('url') or n.get('link')
            
            # Extract published date
            published_at = None
            pub_date = content.get('pubDate') or content.get('displayTime')
            if pub_date:
                try:
                    # Parse ISO format date
                    if isinstance(pub_date, str):
                        published_at = pub_date
                    else:
                        published_at = datetime.fromtimestamp(pub_date).isoformat()
                except Exception:
                    published_at = None
            
            # Extract summary
            summary = content.get('summary', '') or content.get('description', '')
            
            result.append({
                'title': title,
                'publisher': publisher,
                'link': link,
                'published_at': published_at,
                'source': 'yahoo',
                'summary': summary,
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
        # Check if we can make a request using the scheduler
        if not news_scheduler.can_make_request('finnhub'):
            logger.info(f"Skipping Finnhub news for {symbol} - request limit reached")
            return []
        
        # Get optimal number of articles to request
        articles_limit = news_scheduler.get_optimal_articles_per_request('finnhub')
        if articles_limit <= 0:
            logger.info(f"Skipping Finnhub news for {symbol} - no remaining quota")
            return []
        
        # Use last 7 days for news
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        url = f'https://finnhub.io/api/v1/company-news?symbol={symbol}&from={start_date.strftime("%Y-%m-%d")}&to={end_date.strftime("%Y-%m-%d")}&token={self.api_key}'
        logger.info(f"Fetching Finnhub news for {symbol} from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        try:
            r = requests.get(url)
            r.raise_for_status()
            news = r.json()
            
            # Record the request
            news_scheduler.record_request('finnhub')
            
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
            
            # Limit to optimal articles per request
            limited_news = valid_news[:articles_limit] if valid_news else []
            logger.info(f"Finnhub: Retrieved {len(limited_news)} articles for {symbol} (limit: {articles_limit})")
            return limited_news
            
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
        
        # Check if we can make a request using the scheduler
        if not news_scheduler.can_make_request('marketaux'):
            logger.info(f"Skipping Marketaux news for {symbol} - request limit reached or outside trading hours")
            return []
        
        # Get optimal number of articles to request
        articles_limit = news_scheduler.get_optimal_articles_per_request('marketaux')
        if articles_limit <= 0:
            logger.info(f"Skipping Marketaux news for {symbol} - no remaining quota")
            return []
            
        url = f'https://api.marketaux.com/v1/news/all?symbols={symbol}&filter_entities=true&language=en&limit={articles_limit}&api_token={self.api_key}'
        try:
            r = requests.get(url)
            r.raise_for_status()
            data = r.json()
            news = data.get('data', [])
            
            # Record the request
            news_scheduler.record_request('marketaux')
            
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
            
            logger.info(f"Marketaux: Retrieved {len(result)} articles for {symbol} (limit: {articles_limit})")
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
        
        # Check if we can make a request using the scheduler
        if not news_scheduler.can_make_request('fmp'):
            logger.info(f"Skipping FMP news for {symbol} - request limit reached")
            return []
        
        # Get optimal number of articles to request
        articles_limit = news_scheduler.get_optimal_articles_per_request('fmp')
        if articles_limit <= 0:
            logger.info(f"Skipping FMP news for {symbol} - no remaining quota")
            return []
            
        url = f'https://financialmodelingprep.com/api/v3/stock_news?tickers={symbol}&limit={articles_limit}&apikey={self.api_key}'
        try:
            r = requests.get(url)
            r.raise_for_status()
            news = r.json()
            
            # Record the request
            news_scheduler.record_request('fmp')
            
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
            
            logger.info(f"FMP: Retrieved {len(result)} articles for {symbol} (limit: {articles_limit})")
            return result
        except Exception as e:
            logger.error(f"FMP error for {symbol}: {e}")
            return []

# NewsAPI implementation
class NewsAPISource(MarketDataSource):
    def __init__(self, api_key):
        self.api_key = api_key
    def get_news(self, symbol: str):
        # Check if we can make a request using the scheduler
        if not news_scheduler.can_make_request('newsapi'):
            logger.info(f"Skipping NewsAPI news for {symbol} - request limit reached")
            return []
        
        # Get optimal number of articles to request
        articles_limit = news_scheduler.get_optimal_articles_per_request('newsapi')
        if articles_limit <= 0:
            logger.info(f"Skipping NewsAPI news for {symbol} - no remaining quota")
            return []
        
        url = f'https://newsapi.org/v2/everything?q={symbol}&sortBy=publishedAt&language=en&pageSize={articles_limit}&apiKey={self.api_key}'
        try:
            r = requests.get(url)
            r.raise_for_status()
            data = r.json()
            news = data.get('articles', [])
            
            # Record the request
            news_scheduler.record_request('newsapi')
            
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
            
            logger.info(f"NewsAPI: Retrieved {len(result)} articles for {symbol} (limit: {articles_limit})")
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
    start_time = datetime.now(tz)
    logger.info(f"=== Starting news fetch for {symbol} at {start_time.strftime('%Y-%m-%d %H:%M:%S %Z')} ===")
    all_news = []
    successful_sources = []
    failed_sources = []
    
    for name, source in MARKET_DATA_SOURCES.items():
        try:
            logger.info(f"Fetching news from {name} for {symbol}...")
            news = source.get_news(symbol)
            if news:
                all_news.extend(news)
                successful_sources.append(f"{name} ({len(news)} articles)")
                logger.info(f"✓ {name}: Successfully retrieved {len(news)} articles for {symbol}")
            else:
                logger.info(f"○ {name}: No articles found for {symbol}")
        except Exception as e:
            failed_sources.append(f"{name} (error: {str(e)})")
            logger.error(f"✗ {name}: Error fetching news for {symbol}: {e}")
    
    # Deduplicate by link
    seen = set()
    deduped = []
    for n in all_news:
        if n['link'] and n['link'] not in seen:
            deduped.append(n)
            seen.add(n['link'])
    
    # Sort by published_at desc
    deduped.sort(key=lambda x: x.get('published_at', ''), reverse=True)
    
    # Calculate duration
    end_time = datetime.now(tz)
    duration = (end_time - start_time).total_seconds()
    
    # Log summary with timestamps
    logger.info(f"=== News fetch completed for {symbol} at {end_time.strftime('%Y-%m-%d %H:%M:%S %Z')} (Duration: {duration:.2f}s) ===")
    logger.info(f"Total articles retrieved: {len(all_news)}")
    logger.info(f"After deduplication: {len(deduped)}")
    if successful_sources:
        logger.info(f"Successful sources: {', '.join(successful_sources)}")
    if failed_sources:
        logger.warning(f"Failed sources: {', '.join(failed_sources)}")
    logger.info(f"=== End news fetch for {symbol} ===")
    
    return deduped 