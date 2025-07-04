import os
import logging
import yfinance as yf
from ibkr_service import ibkr_service
import asyncio
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

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
        return [
            {
                'title': n.get('title'),
                'publisher': n.get('publisher'),
                'link': n.get('link'),
                'providerPublishTime': n.get('providerPublishTime'),
                'type': n.get('type'),
                'summary': n.get('summary', '')
            }
            for n in news
        ]

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
                
            # Map Finnhub fields to our expected format
            valid_news = []
            required_fields = {
                'headline': ['headline', 'title'],  # Try multiple possible field names
                'datetime': ['datetime', 'time', 'timestamp'],
                'summary': ['summary', 'description']
            }
            
            for n in news:
                # Try to find values using multiple possible field names
                news_item = {}
                valid = True
                
                for our_field, possible_fields in required_fields.items():
                    value = None
                    for field in possible_fields:
                        if field in n and n[field]:
                            value = n[field]
                            break
                    
                    if value is None:
                        logger.warning(f"Missing required field {our_field} in news item for {symbol}")
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
                    
                    # Additional validation for specific fields
                    if isinstance(formatted_item['providerPublishTime'], (int, float)):
                        # Convert Unix timestamp to ISO format if needed
                        formatted_item['providerPublishTime'] = datetime.fromtimestamp(
                            formatted_item['providerPublishTime']
                        ).isoformat()
                    
                    valid_news.append(formatted_item)
            
            logger.info(f"Found {len(valid_news)} valid news items for {symbol}")
            
            # Sort by timestamp (newest first) and return top 10
            valid_news.sort(key=lambda x: x['providerPublishTime'], reverse=True)
            return valid_news[:10]
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Finnhub news request error for {symbol}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error processing news for {symbol}: {e}")
            return []

# Registry for sources
MARKET_DATA_SOURCES = {
    'yahoo': YahooFinanceSource(),
    'finnhub': FinnhubSource(api_key=os.getenv('FINNHUB_API_KEY', '')),
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