import os
import logging
import asyncio
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional
import json
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class TradingSession(Enum):
    PRE_MARKET = "pre_market"
    REGULAR_TRADING = "regular_trading"
    AFTER_HOURS = "after_hours"
    CLOSED = "closed"

@dataclass
class APILimits:
    daily_requests: int
    articles_per_request: int
    trading_hours_only: bool = True

@dataclass
class NewsSourceConfig:
    name: str
    api_key: str
    limits: APILimits
    enabled: bool = True

class NewsScheduler:
    def __init__(self):
        self.trading_start = time(5, 30)  # 5:30 AM
        self.trading_end = time(14, 0)    # 2:00 PM
        self.sources = self._initialize_sources()
        self.request_counts = {}
        self.last_request_times = {}
        # Initialize scheduler state
        self._running = False
        self._next_run = "N/A"
        self._interval = "N/A"
        self._last_run = "N/A"
        self._job_count = 0
        
    def _initialize_sources(self) -> Dict[str, NewsSourceConfig]:
        """Initialize news sources with their API limits"""
        sources = {}
        
        # Marketaux
        marketaux_max_req = int(os.getenv('MARKETAUX_MAX_REQUEST_DAILY', 100))
        marketaux_max_news = int(os.getenv('MARKETAUX_MAX_NEWS_PER_REQUEST', 3))
        if os.getenv('MARKETAUX_API_KEY'):
            sources['marketaux'] = NewsSourceConfig(
                name='marketaux',
                api_key=os.getenv('MARKETAUX_API_KEY'),
                limits=APILimits(
                    daily_requests=marketaux_max_req,
                    articles_per_request=marketaux_max_news,
                    trading_hours_only=True
                ),
                enabled=True
            )
        
        # NewsAPI.org
        newsapi_max_req = int(os.getenv('NEWSAPI_MAX_REQUEST_DAILY', 100))
        newsapi_max_news = int(os.getenv('NEWSAPI_MAX_NEWS_PER_REQUEST', 100))
        if os.getenv('NEWSAPI_API_KEY'):
            sources['newsapi'] = NewsSourceConfig(
                name='newsapi',
                api_key=os.getenv('NEWSAPI_API_KEY'),
                limits=APILimits(
                    daily_requests=newsapi_max_req,
                    articles_per_request=newsapi_max_news,
                    trading_hours_only=False
                ),
                enabled=True
            )
        
        # Finnhub
        finnhub_max_req = int(os.getenv('FINNHUB_MAX_REQUEST_DAILY', 86400))
        finnhub_max_news = int(os.getenv('FINNHUB_MAX_NEWS_PER_REQUEST', 100))
        if os.getenv('FINNHUB_API_KEY'):
            sources['finnhub'] = NewsSourceConfig(
                name='finnhub',
                api_key=os.getenv('FINNHUB_API_KEY'),
                limits=APILimits(
                    daily_requests=finnhub_max_req,
                    articles_per_request=finnhub_max_news,
                    trading_hours_only=False
                ),
                enabled=True
            )
        
        # FMP
        fmp_max_req = int(os.getenv('FMP_MAX_REQUEST_DAILY', 250))
        fmp_max_news = int(os.getenv('FMP_MAX_NEWS_PER_REQUEST', 50))
        if os.getenv('FMP_API_KEY'):
            sources['fmp'] = NewsSourceConfig(
                name='fmp',
                api_key=os.getenv('FMP_API_KEY'),
                limits=APILimits(
                    daily_requests=fmp_max_req,
                    articles_per_request=fmp_max_news,
                    trading_hours_only=False
                ),
                enabled=True
            )
        
        return sources
    
    def get_trading_session(self) -> TradingSession:
        """Determine current trading session"""
        now = datetime.now()
        current_time = now.time()
        
        if self.trading_start <= current_time <= self.trading_end:
            return TradingSession.REGULAR_TRADING
        elif current_time < self.trading_start:
            return TradingSession.PRE_MARKET
        else:
            return TradingSession.AFTER_HOURS
    
    def is_trading_hours(self) -> bool:
        """Check if current time is within trading hours"""
        return self.get_trading_session() == TradingSession.REGULAR_TRADING
    
    def get_trading_hours_remaining(self) -> float:
        """Get remaining trading hours as decimal"""
        now = datetime.now()
        current_time = now.time()
        
        if current_time >= self.trading_end:
            return 0.0
        elif current_time < self.trading_start:
            # Full trading day ahead
            return 8.5  # 8.5 hours (5:30 AM to 2:00 PM)
        else:
            # Calculate remaining time
            end_dt = datetime.combine(now.date(), self.trading_end)
            remaining = end_dt - now
            return remaining.total_seconds() / 3600  # Convert to hours
    
    def can_make_request(self, source_name: str) -> bool:
        """Check if we can make a request for this source"""
        if source_name not in self.sources:
            return False
        
        source = self.sources[source_name]
        if not source.enabled:
            return False
        
        # Check if trading hours restriction applies
        if source.limits.trading_hours_only and not self.is_trading_hours():
            logger.info(f"{source_name} requires trading hours - current session: {self.get_trading_session()}")
            return False
        
        # Check daily request limit
        today = datetime.now().date().isoformat()
        if today not in self.request_counts:
            self.request_counts[today] = {}
        
        if source_name not in self.request_counts[today]:
            self.request_counts[today][source_name] = 0
        
        if self.request_counts[today][source_name] >= source.limits.daily_requests:
            logger.warning(f"{source_name} daily limit reached: {self.request_counts[today][source_name]}/{source.limits.daily_requests}")
            return False
        
        # Check rate limiting (for sources with high limits)
        if source.limits.daily_requests > 1000:  # High limit sources
            if source_name not in self.last_request_times:
                self.last_request_times[source_name] = {}
            
            if today not in self.last_request_times[source_name]:
                self.last_request_times[source_name][today] = []
            
            # Remove requests older than 1 minute
            now = datetime.now()
            self.last_request_times[source_name][today] = [
                t for t in self.last_request_times[source_name][today]
                if (now - t).total_seconds() < 60
            ]
            
            # Limit to 1 request per minute for high-volume sources
            if len(self.last_request_times[source_name][today]) >= 1:
                return False
        
        return True
    
    def record_request(self, source_name: str):
        """Record that a request was made"""
        today = datetime.now().date().isoformat()
        
        if today not in self.request_counts:
            self.request_counts[today] = {}
        
        if source_name not in self.request_counts[today]:
            self.request_counts[today][source_name] = 0
        
        self.request_counts[today][source_name] += 1
        
        # Record timestamp for rate limiting
        if source_name not in self.last_request_times:
            self.last_request_times[source_name] = {}
        
        if today not in self.last_request_times[source_name]:
            self.last_request_times[source_name][today] = []
        
        self.last_request_times[source_name][today].append(datetime.now())
        
        logger.info(f"Recorded request for {source_name}: {self.request_counts[today][source_name]}")
    
    def get_optimal_articles_per_request(self, source_name: str) -> int:
        """Calculate optimal number of articles to request based on remaining quota"""
        if source_name not in self.sources:
            return 10  # Default
        
        source = self.sources[source_name]
        today = datetime.now().date().isoformat()
        
        if today not in self.request_counts:
            self.request_counts[today] = {}
        
        requests_made = self.request_counts[today].get(source_name, 0)
        requests_remaining = source.limits.daily_requests - requests_made
        
        if requests_remaining <= 0:
            return 0
        
        # For Marketaux, always request 3 articles (their limit)
        if source_name == 'marketaux':
            return 3
        
        # For other sources, calculate based on remaining requests
        if source.limits.trading_hours_only:
            hours_remaining = self.get_trading_hours_remaining()
            if hours_remaining <= 0:
                return 0
            
            # Distribute remaining requests across remaining hours
            requests_per_hour = max(1, requests_remaining / hours_remaining)
            articles_per_request = min(
                source.limits.articles_per_request,
                max(10, int(requests_per_hour * 10))  # Request more articles when we have fewer requests
            )
        else:
            # Non-trading hours sources: be more conservative
            articles_per_request = min(
                source.limits.articles_per_request,
                max(10, int(requests_remaining / 10))  # Distribute across remaining requests
            )
        
        return articles_per_request
    
    def get_status(self) -> Dict:
        """Get current status of all sources"""
        status = {
            'trading_session': self.get_trading_session().value,
            'is_trading_hours': self.is_trading_hours(),
            'trading_hours_remaining': self.get_trading_hours_remaining(),
            'running': hasattr(self, '_running') and self._running,
            'next_run': getattr(self, '_next_run', 'N/A'),
            'interval': getattr(self, '_interval', 'N/A'),
            'last_run': getattr(self, '_last_run', 'N/A'),
            'job_count': getattr(self, '_job_count', 0),
            'sources': {}
        }
        
        today = datetime.now().date().isoformat()
        
        for source_name, source in self.sources.items():
            requests_made = self.request_counts.get(today, {}).get(source_name, 0)
            can_request = self.can_make_request(source_name)
            optimal_articles = self.get_optimal_articles_per_request(source_name)
            
            status['sources'][source_name] = {
                'enabled': source.enabled,
                'requests_made': requests_made,
                'daily_limit': source.limits.daily_requests,
                'requests_remaining': source.limits.daily_requests - requests_made,
                'can_make_request': can_request,
                'optimal_articles_per_request': optimal_articles,
                'trading_hours_only': source.limits.trading_hours_only
            }
        
        return status

    def get_quota_status(self) -> Dict:
        """Get quota status for all news sources"""
        quota_status = {}
        today = datetime.now().date().isoformat()
        
        for source_name, source in self.sources.items():
            requests_made = self.request_counts.get(today, {}).get(source_name, 0)
            quota_status[source_name] = {
                'used': requests_made,
                'limit': source.limits.daily_requests,
                'remaining': source.limits.daily_requests - requests_made,
                'enabled': source.enabled,
                'trading_hours_only': source.limits.trading_hours_only
            }
        
        return quota_status

    def start(self):
        """Start the scheduler (placeholder for future implementation)"""
        self._running = True
        self._next_run = "Every 30 minutes"
        self._interval = "30 minutes"
        self._last_run = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._job_count = 1
        logger.info("News scheduler started")
        return {"status": "running", "message": "Scheduler started"}

    def stop(self):
        """Stop the scheduler (placeholder for future implementation)"""
        self._running = False
        self._next_run = "N/A"
        self._interval = "N/A"
        self._last_run = "N/A"
        self._job_count = 0
        logger.info("News scheduler stopped")
        return {"status": "stopped", "message": "Scheduler stopped"}

# Global scheduler instance
news_scheduler = NewsScheduler()

def get_quota_status() -> Dict:
    """Global function to get quota status"""
    return news_scheduler.get_quota_status() 