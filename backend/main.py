# Requires: python-dotenv
from fastapi import FastAPI, HTTPException, Request, Body, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from ibkr_service import ibkr_service
from market_data import get_market_data, get_current_source, set_current_source, MARKET_DATA_SOURCES, get_all_news
from sentiment_analyzer import sentiment_analyzer
from news_scheduler import news_scheduler, get_quota_status
from stock_data_service import stock_data_service
from stock_data_scheduler import stock_data_scheduler
from i18n_service import i18n_service
import asyncio
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from database import get_db
from models import News, TargetSymbol, StockDaily, StockIntraday, TechnicalIndicators, TradingSignals
from sqlalchemy import func, and_
import pytz
from datetime import datetime, timedelta
import openai
import json

# Add dotenv support to load .env if present
load_dotenv()

# Set timezone
TIMEZONE = os.getenv('TZ', 'Canada/Vancouver')
try:
    tz = pytz.timezone(TIMEZONE)
    logger = logging.getLogger(__name__)
    logger.info(f"Timezone set to: {TIMEZONE}")
except Exception as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"Invalid timezone {TIMEZONE}, using UTC: {e}")
    tz = pytz.UTC

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DataSourceRequest(BaseModel):
    source: str

class NewsSourceRequest(BaseModel):
    news_source: str

class AIAnalysisRequest(BaseModel):
    portfolio: List[Dict[str, Any]]
    accountSummary: Dict[str, Any]
    message: str
    locale: Optional[str] = None

# Global settings with defaults
selected_market_data_source = os.getenv('MARKET_DATA_SOURCE', 'yahoo')
selected_news_source = os.getenv('NEWS_SOURCE', 'yahoo')

NEWS_FETCH_INTERVAL_HOURS = float(os.getenv('NEWS_FETCH_INTERVAL_HOURS', 2))
NEWS_FETCH_INTERVAL_MINUTES = int(NEWS_FETCH_INTERVAL_HOURS * 60)

scheduler = BackgroundScheduler()

logger = logging.getLogger(__name__)

async def get_request_body(request: Request) -> Dict[str, Any]:
    return await request.json()

@app.get("/")
async def root():
    return {"message": "IBKR Trading API"}

@app.get("/connect")
async def connect():
    """Connect to IBKR"""
    try:
        await ibkr_service.connect()
        return {"message": "Connected to IBKR"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error connecting to IBKR: {str(e)}")

@app.get("/disconnect")
async def disconnect():
    """Disconnect from IBKR"""
    try:
        await ibkr_service.disconnect()
        return {"message": "Disconnected from IBKR"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error disconnecting from IBKR: {str(e)}")

@app.get("/account/summary")
async def get_account_summary():
    """Get account summary including cash balance and portfolio value"""
    try:
        summary = await ibkr_service.get_account_summary()
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting account summary: {str(e)}")

@app.get("/account/positions")
async def get_positions():
    """Get detailed information about current positions"""
    try:
        positions = await ibkr_service.get_positions()
        return {"positions": positions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting positions: {str(e)}")

@app.get("/market-data-source")
async def get_data_source():
    """Get the current market data source"""
    return {"source": get_current_source()}

@app.post("/market-data-source")
async def set_data_source(req: DataSourceRequest):
    """Set the current market data source (e.g., yahoo, ibkr)"""
    set_current_source(req.source)
    return {"source": get_current_source()}

@app.get("/market-data/{symbol}")
async def market_data_endpoint(symbol: str):
    """Get real-time market data for a symbol from the selected data source"""
    try:
        data = await get_market_data(symbol)
        if data:
            return data
        else:
            raise HTTPException(status_code=404, detail=f"No market data found for symbol: {symbol}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting market data for {symbol}: {str(e)}")

@app.get("/market-data/{symbol}/intraday")
async def get_intraday_data(symbol: str, db: Session = Depends(get_db)):
    """Get intraday price data for charting"""
    try:
        # Try to get intraday data from database for the last 24 hours
        end_time = datetime.now(tz)
        start_time = end_time - timedelta(hours=24)
        
        try:
            intraday_data = db.query(StockIntraday).filter(
                and_(
                    StockIntraday.symbol == symbol,
                    StockIntraday.timestamp >= start_time,
                    StockIntraday.timestamp <= end_time
                )
            ).order_by(StockIntraday.timestamp).all()
            
            if intraday_data:
                # Format data for chart
                chart_data = []
                for data_point in intraday_data:
                    chart_data.append({
                        "timestamp": data_point.timestamp.isoformat(),
                        "price": float(data_point.price),
                        "volume": int(data_point.volume) if data_point.volume else 0
                    })
                
                return {
                    "symbol": symbol,
                    "data": chart_data
                }
        except Exception as db_error:
            # Database table doesn't exist or other DB error, continue to fallback
            pass
        
        # Fallback: Generate mock intraday data based on current market price
        try:
            market_data = await get_market_data(symbol)
            if market_data and 'price' in market_data:
                current_price = float(market_data['price'])
                
                # Generate mock data points for today's trading hours (9:30 AM - 4:00 PM EST)
                import random
                chart_data = []
                
                # Get today's date in UTC
                today = datetime.now(tz).date()
                
                # Create data points for trading hours (9:30 AM - 4:00 PM EST = 2:30 PM - 9:00 PM UTC)
                # But let's use Hong Kong time for better display (9:30 AM - 4:00 PM HKT)
                start_hour = 9
                start_minute = 30
                end_hour = 16
                end_minute = 0
                
                # Create data points every 15 minutes during trading hours
                current_time = datetime.combine(today, datetime.min.time().replace(hour=start_hour, minute=start_minute))
                end_time = datetime.combine(today, datetime.min.time().replace(hour=end_hour, minute=end_minute))
                
                # Start with opening price (slightly different from current price)
                opening_price = current_price * random.uniform(0.98, 1.02)
                price = opening_price
                
                while current_time <= end_time:
                    # Add some realistic price variation
                    variation = random.uniform(-0.01, 0.01)  # ±1% variation per 15min
                    price = price * (1 + variation)
                    
                    chart_data.append({
                        "timestamp": current_time.isoformat(),
                        "price": round(price, 2),
                        "volume": random.randint(1000, 10000)
                    })
                    
                    current_time += timedelta(minutes=15)
                
                return {
                    "symbol": symbol,
                    "data": chart_data
                }
        except Exception as market_error:
            pass
        
        # Final fallback: return empty data
        return {
            "symbol": symbol,
            "data": []
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting intraday data for {symbol}: {str(e)}")

@app.get('/news/stats')
async def get_news_stats(db: Session = Depends(get_db)):
    """Get news statistics from database"""
    try:
        # Get total news count
        total_news = db.query(News).count()
        
        # Get unique symbols with news
        symbols_with_news = db.query(News.symbol).distinct().count()
        
        # Get latest news date
        latest_news = db.query(News).order_by(News.published_at.desc()).first()
        latest_news_date = latest_news.published_at.strftime('%Y-%m-%d') if latest_news else 'No news'
        
        # Get unique news sources
        news_sources = db.query(News.source).distinct().all()
        sources = [source[0] for source in news_sources]
        
        # Get sentiment analysis statistics
        sentiment_stats = db.query(News.sentiment_label, func.count(News.id)).group_by(News.sentiment_label).all()
        sentiment_counts = {sentiment: count for sentiment, count in sentiment_stats if sentiment}
        
        # Get average sentiment score
        avg_score = db.query(func.avg(News.score)).scalar()
        avg_score = round(avg_score, 2) if avg_score else 0
        
        return {
            "totalNews": total_news,
            "symbolsWithNews": symbols_with_news,
            "latestNewsDate": latest_news_date,
            "newsSources": sources,
            "sentimentCounts": sentiment_counts,
            "averageSentimentScore": avg_score
        }
    except Exception as e:
        logger.error(f"Error getting news stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting news stats: {str(e)}")

@app.get('/news/sentiment/{symbol}')
async def get_news_sentiment(symbol: str, db: Session = Depends(get_db)):
    """Get sentiment analysis results for news of a specific symbol"""
    try:
        # Get news with sentiment analysis for the symbol
        news_with_sentiment = db.query(News).filter(
            News.symbol == symbol.upper(),
            News.score.isnot(None)  # Only news with sentiment analysis
        ).order_by(News.published_at.desc()).all()
        
        if not news_with_sentiment:
            return {
                "symbol": symbol.upper(),
                "message": "No news with sentiment analysis found",
                "sentimentData": []
            }
        
        # Calculate sentiment statistics
        total_news = len(news_with_sentiment)
        avg_score = sum(n.score for n in news_with_sentiment if n.score) / total_news
        avg_confidence = sum(n.confidence for n in news_with_sentiment if n.confidence) / total_news
        
        # Group by sentiment label
        sentiment_groups = {}
        for news in news_with_sentiment:
            label = news.sentiment_label or 'unknown'
            if label not in sentiment_groups:
                sentiment_groups[label] = []
            sentiment_groups[label].append({
                "title": news.title,
                "score": news.score,
                "confidence": news.confidence,
                "analysisMethod": news.analysis_method,
                "publishedAt": news.published_at,
                "source": news.source
            })
        
        return {
            "symbol": symbol.upper(),
            "totalNewsAnalyzed": total_news,
            "averageSentimentScore": round(avg_score, 2),
            "averageConfidence": round(avg_confidence, 2),
            "sentimentDistribution": {label: len(news_list) for label, news_list in sentiment_groups.items()},
            "sentimentData": sentiment_groups
        }
    except Exception as e:
        logger.error(f"Error getting sentiment analysis for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting sentiment analysis: {str(e)}")

@app.get('/news/{symbol}')
async def get_news(symbol: str):
    """Get news for a symbol from the selected news source"""
    try:
        source = MARKET_DATA_SOURCES.get(selected_news_source)
        if not source:
            # Fallback to Yahoo if selected source not found
            source = MARKET_DATA_SOURCES['yahoo']
            
        # Run the news fetch in a thread pool since it's a blocking operation
        loop = asyncio.get_event_loop()
        news = await loop.run_in_executor(None, lambda: source.get_news(symbol))
        
        if not news:
            return {'symbol': symbol, 'news': [], 'message': 'No news found for this symbol'}
            
        return {'symbol': symbol, 'news': news}
    except Exception as e:
        logger.error(f"Error getting news for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting news for {symbol}: {str(e)}")

@app.get('/market-data-source/news')
def get_news_source():
    """Get the current news source"""
    return {'news_source': selected_news_source}

@app.post('/market-data-source/news')
def set_news_source(request: NewsSourceRequest):
    """Set the news source (yahoo or finnhub)"""
    if request.news_source not in MARKET_DATA_SOURCES:
        raise HTTPException(
            status_code=400,
            detail={
                'error': 'Invalid news source',
                'available_sources': list(MARKET_DATA_SOURCES.keys())
            }
        )
    
    global selected_news_source
    selected_news_source = request.news_source
    return {
        'news_source': selected_news_source,
        'status': 'success',
        'available_sources': list(MARKET_DATA_SOURCES.keys())
    }

@app.get('/news/all/{symbol}')
async def get_all_news_endpoint(symbol: str):
    """Get merged news for a symbol from all sources"""
    try:
        loop = asyncio.get_event_loop()
        news = await loop.run_in_executor(None, lambda: get_all_news(symbol))
        return {'symbol': symbol, 'news': news}
    except Exception as e:
        logger.error(f"Error getting all news for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting all news for {symbol}: {str(e)}")

@app.get('/news/scheduler/status')
async def get_scheduler_status():
    """Get the current status of the news scheduler"""
    try:
        status = news_scheduler.get_status()
        return status
    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting scheduler status: {str(e)}")

@app.get('/news/quota-status')
async def get_quota_status():
    """Get API quota status for all news sources"""
    try:
        quota_status = get_quota_status()
        return quota_status
    except Exception as e:
        logger.error(f"Error getting quota status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting quota status: {str(e)}")

@app.post('/news/scheduler/start')
async def start_scheduler():
    """Start the news scheduler"""
    try:
        news_scheduler.start()
        return {"message": "Scheduler started successfully", "status": "running"}
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}")
        raise HTTPException(status_code=500, detail=f"Error starting scheduler: {str(e)}")

@app.post('/news/scheduler/stop')
async def stop_scheduler():
    """Stop the news scheduler"""
    try:
        news_scheduler.stop()
        return {"message": "Scheduler stopped successfully", "status": "stopped"}
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")
        raise HTTPException(status_code=500, detail=f"Error stopping scheduler: {str(e)}")

@app.post('/news/fetch/{symbol}')
async def fetch_news_for_symbol(symbol: str, db: Session = Depends(get_db)):
    """Manually fetch and store news for a specific symbol"""
    try:
        await fetch_and_store_news_for_symbol(symbol, db)
        return {"message": f"News fetched and stored for {symbol}"}
    except Exception as e:
        logger.error(f"Error fetching news for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching news for {symbol}: {str(e)}")

@app.post('/news/fetch-all')
async def fetch_news_for_all_targets(db: Session = Depends(get_db)):
    """Fetch and store news for all target symbols"""
    try:
        # Get all target symbols
        target_symbols = db.query(TargetSymbol.symbol).all()
        symbols = [ts.symbol for ts in target_symbols]
        
        if not symbols:
            return {"message": "No target symbols found"}
        
        # Fetch news for each symbol
        results = []
        for symbol in symbols:
            try:
                await fetch_and_store_news_for_symbol(symbol, db)
                results.append({"symbol": symbol, "status": "success"})
            except Exception as e:
                logger.error(f"Error fetching news for {symbol}: {e}")
                results.append({"symbol": symbol, "status": "error", "message": str(e)})
        
        return {
            "message": f"News fetching completed for {len(symbols)} symbols",
            "results": results
        }
    except Exception as e:
        logger.error(f"Error fetching news for all targets: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching news for all targets: {str(e)}")

@app.post('/news/clear-all')
async def clear_all_news(db: Session = Depends(get_db)):
    """Clear all news from the database"""
    try:
        deleted_count = db.query(News).delete()
        db.commit()
        return {"message": f"Cleared {deleted_count} news articles"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error clearing all news: {e}")
        raise HTTPException(status_code=500, detail=f"Error clearing all news: {str(e)}")

async def fetch_and_store_news_for_symbol(symbol: str, db: Session):
    """Helper function to fetch and store news for a specific symbol"""
    try:
        # Get news from all available sources
        loop = asyncio.get_event_loop()
        all_news = await loop.run_in_executor(None, lambda: get_all_news(symbol))
        
        if not all_news:
            logger.info(f"No news found for {symbol}")
            return
        
        # Store news in database with sentiment analysis
        stored_count = 0
        for news_item in all_news:
            try:
                # Check if news already exists
                existing_news = db.query(News).filter(
                    News.title == news_item['title'],
                    News.symbol == symbol.upper(),
                    News.source == news_item['source']
                ).first()
                
                if existing_news:
                    continue
                
                # Perform sentiment analysis
                sentiment_result = sentiment_analyzer.analyze_sentiment(
                    text=news_item['summary'],
                    title=news_item['title']
                )
                
                # Create news record
                news_record = News(
                    symbol=symbol.upper(),
                    title=news_item['title'],
                    summary=news_item['summary'],
                    link=news_item['link'],
                    published_at=news_item['published_at'],
                    source=news_item['source'],
                    publisher=news_item.get('publisher', ''),
                    score=sentiment_result.get('score'),
                    sentiment_label=sentiment_result.get('sentiment'),
                    confidence=sentiment_result.get('confidence'),
                    analysis_method=sentiment_result.get('method', 'combined')
                )
                
                db.add(news_record)
                stored_count += 1
                
            except Exception as e:
                logger.error(f"Error storing news item for {symbol}: {e}")
                continue
        
        db.commit()
        logger.info(f"Stored {stored_count} new news articles for {symbol}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error in fetch_and_store_news_for_symbol for {symbol}: {e}")
        raise

def fetch_and_store_news():
    """Fetch news for target symbols and store in database"""
    start_time = datetime.now(tz)
    logger.info(f"🕐 SCHEDULER RUN STARTED at {start_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    try:
        # Get target symbols from database
        db = next(get_db())
        target_symbols = db.query(TargetSymbol).all()
        
        if not target_symbols:
            logger.info("No target symbols found, skipping news fetch")
            return
        
        symbols = [symbol.symbol for symbol in target_symbols]
        logger.info(f"📋 Processing {len(symbols)} target symbols: {symbols}")
        
        total_processed = 0
        total_stored = 0
        
        for symbol in symbols:
            try:
                # Get news from all sources
                news_data = get_all_news(symbol)
                total_processed += 1
                
                if news_data:
                    stored_count = 0
                    for news_item in news_data:
                        try:
                            # Check if news already exists
                            existing_news = db.query(News).filter(
                                News.title == news_item.get('title'),
                                News.source == news_item.get('source'),
                                News.published_at == news_item.get('published_at')
                            ).first()
                            
                            if not existing_news:
                                # Perform sentiment analysis
                                sentiment_result = sentiment_analyzer.analyze_sentiment(
                                    text=news_item.get('summary', ''),
                                    title=news_item.get('title', '')
                                )
                                
                                # Create new news record
                                news_record = News(
                                    title=news_item.get('title', ''),
                                    publisher=news_item.get('publisher', ''),
                                    link=news_item.get('link', ''),
                                    published_at=news_item.get('published_at'),
                                    source=news_item.get('source', ''),
                                    summary=news_item.get('summary', ''),
                                    score=sentiment_result['score'],
                                    sentiment_label=sentiment_result['sentiment'],
                                    confidence=sentiment_result['confidence'],
                                    analysis_method=sentiment_result['method'],
                                    textblob_score=sentiment_result.get('textblob_score'),
                                    openai_score=sentiment_result.get('openai_score'),
                                    raw_json=news_item.get('raw_json', ''),
                                    symbol=symbol
                                )
                                db.add(news_record)
                                stored_count += 1
                        except Exception as e:
                            logger.error(f"Error storing news item for {symbol}: {e}")
                            continue
                    
                    db.commit()
                    total_stored += stored_count
                    logger.info(f"💾 Stored {stored_count} new news items for {symbol}")
                else:
                    logger.info(f"📭 No news data received for {symbol}")
                    
            except Exception as e:
                logger.error(f"❌ Error fetching news for {symbol}: {e}")
                continue
        
        # Calculate duration and log summary
        end_time = datetime.now(tz)
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"🕐 SCHEDULER RUN COMPLETED at {end_time.strftime('%Y-%m-%d %H:%M:%S %Z')} (Duration: {duration:.2f}s)")
        logger.info(f"📊 SUMMARY: Processed {total_processed} symbols, stored {total_stored} new articles")
        logger.info(f"🔄 Next scheduled run in {NEWS_FETCH_INTERVAL_MINUTES} minutes")
                
    except Exception as e:
        end_time = datetime.now(tz)
        duration = (end_time - start_time).total_seconds()
        logger.error(f"❌ SCHEDULER RUN FAILED at {end_time.strftime('%Y-%m-%d %H:%M:%S %Z')} (Duration: {duration:.2f}s)")
        logger.error(f"Error in fetch_and_store_news: {e}")

scheduler.add_job(fetch_and_store_news, 'interval', minutes=NEWS_FETCH_INTERVAL_MINUTES, next_run_time=None)
scheduler.start()

@app.get('/target-symbols')
async def get_target_symbols(db: Session = Depends(get_db)):
    """Get the current list of target stock symbols"""
    try:
        symbols = db.query(TargetSymbol).all()
        return {"symbols": [symbol.symbol for symbol in symbols]}
    except Exception as e:
        logger.error(f"Error getting target symbols: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting target symbols: {str(e)}")

@app.post('/target-symbols')
async def set_target_symbols(symbols: list[str], db: Session = Depends(get_db)):
    """Set the list of target stock symbols"""
    try:
        # Clear existing symbols
        db.query(TargetSymbol).delete()
        
        # Add new symbols
        for symbol in symbols:
            if symbol.strip():  # Skip empty symbols
                target_symbol = TargetSymbol(symbol=symbol.strip().upper())
                db.add(target_symbol)
        
        db.commit()
        return {"message": f"Successfully set {len(symbols)} target symbols", "symbols": symbols}
    except Exception as e:
        db.rollback()
        logger.error(f"Error setting target symbols: {e}")
        raise HTTPException(status_code=500, detail=f"Error setting target symbols: {str(e)}")

# 股票數據相關端點
@app.get('/stock-data/daily/{symbol}')
async def get_daily_data(symbol: str, period: str = '1y', db: Session = Depends(get_db)):
    """獲取日線數據"""
    try:
        end_date = datetime.now()
        if period == '1y':
            start_date = end_date - timedelta(days=365)
        elif period == '6m':
            start_date = end_date - timedelta(days=180)
        elif period == '3m':
            start_date = end_date - timedelta(days=90)
        elif period == '1m':
            start_date = end_date - timedelta(days=30)
        else:
            start_date = end_date - timedelta(days=365)
        
        data = db.query(StockDaily).filter(
            and_(StockDaily.symbol == symbol,
                 StockDaily.date >= start_date,
                 StockDaily.date <= end_date)
        ).order_by(StockDaily.date).all()
        
        return [{
            'date': item.date.isoformat(),
            'open': item.open_price,
            'high': item.high_price,
            'low': item.low_price,
            'close': item.close_price,
            'volume': item.volume,
            'adjusted_close': item.adjusted_close
        } for item in data]
        
    except Exception as e:
        logger.error(f"Error getting daily data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/stock-data/intraday/{symbol}')
async def get_intraday_data(symbol: str, interval: str = '1h', period: str = '1mo', db: Session = Depends(get_db)):
    """獲取分鐘級數據"""
    try:
        end_date = datetime.now()
        if period == '1mo':
            start_date = end_date - timedelta(days=30)
        elif period == '1w':
            start_date = end_date - timedelta(days=7)
        elif period == '1d':
            start_date = end_date - timedelta(days=1)
        else:
            start_date = end_date - timedelta(days=30)
        
        data = db.query(StockIntraday).filter(
            and_(StockIntraday.symbol == symbol,
                 StockIntraday.timestamp >= start_date,
                 StockIntraday.timestamp <= end_date,
                 StockIntraday.interval == interval)
        ).order_by(StockIntraday.timestamp).all()
        
        return [{
            'timestamp': item.timestamp.isoformat(),
            'open': item.open_price,
            'high': item.high_price,
            'low': item.low_price,
            'close': item.close_price,
            'volume': item.volume
        } for item in data]
        
    except Exception as e:
        logger.error(f"Error getting intraday data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/stock-data/indicators/{symbol}')
async def get_technical_indicators(symbol: str, period: str = '1y', db: Session = Depends(get_db)):
    """獲取技術指標"""
    try:
        end_date = datetime.now()
        if period == '1y':
            start_date = end_date - timedelta(days=365)
        elif period == '6m':
            start_date = end_date - timedelta(days=180)
        elif period == '3m':
            start_date = end_date - timedelta(days=90)
        else:
            start_date = end_date - timedelta(days=365)
        
        data = db.query(TechnicalIndicators).filter(
            and_(TechnicalIndicators.symbol == symbol,
                 TechnicalIndicators.date >= start_date,
                 TechnicalIndicators.date <= end_date)
        ).order_by(TechnicalIndicators.date).all()
        
        # 按指標類型組織數據
        indicators = {}
        for item in data:
            if item.indicator_type not in indicators:
                indicators[item.indicator_type] = []
            indicators[item.indicator_type].append({
                'date': item.date.isoformat(),
                'value': item.value,
                'period': item.period
            })
        
        return indicators
        
    except Exception as e:
        logger.error(f"Error getting indicators for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/stock-data/chart/{symbol}')
async def get_chart_data(symbol: str, period: str = '1y', interval: str = '1d', db: Session = Depends(get_db)):
    """獲取圖表數據"""
    try:
        chart_data = stock_data_service.get_chart_data(db, symbol, period, interval)
        return chart_data
        
    except Exception as e:
        logger.error(f"Error getting chart data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/stock-data/signals/{symbol}')
async def get_trading_signals(symbol: str, db: Session = Depends(get_db)):
    """獲取交易信號"""
    try:
        signal = stock_data_service.generate_trading_signals(db, symbol)
        return signal
        
    except Exception as e:
        logger.error(f"Error getting trading signals for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 股票數據調度器控制端點
@app.get('/stock-data/scheduler/status')
async def get_stock_data_scheduler_status():
    """獲取股票數據調度器狀態"""
    try:
        status = stock_data_scheduler.get_status()
        return status
    except Exception as e:
        logger.error(f"Error getting stock data scheduler status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/stock-data/scheduler/start')
async def start_stock_data_scheduler():
    """啟動股票數據調度器"""
    try:
        stock_data_scheduler.start()
        return {"message": "Stock data scheduler started successfully"}
    except Exception as e:
        logger.error(f"Error starting stock data scheduler: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/stock-data/scheduler/stop')
async def stop_stock_data_scheduler():
    """停止股票數據調度器"""
    try:
        stock_data_scheduler.stop()
        return {"message": "Stock data scheduler stopped successfully"}
    except Exception as e:
        logger.error(f"Error stopping stock data scheduler: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/stock-data/update/{symbol}')
async def manual_update_stock_data(symbol: str):
    """手動更新股票數據"""
    try:
        success = stock_data_scheduler.manual_update_symbol(symbol)
        if success:
            return {"message": f"Stock data updated successfully for {symbol}"}
        else:
            raise HTTPException(status_code=500, detail=f"Failed to update stock data for {symbol}")
    except Exception as e:
        logger.error(f"Error updating stock data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/stock-data/initialize/{symbol}')
async def initialize_stock_data(symbol: str, db: Session = Depends(get_db)):
    """初始化股票歷史數據"""
    try:
        logger.info(f"Initializing stock data for {symbol}")
        
        # 獲取5年歷史數據
        end_date = datetime.now()
        start_date = end_date - timedelta(days=5*365)
        
        # 抓取日線數據
        daily_data = stock_data_service.fetch_daily_data(
            symbol=symbol,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
        
        if not daily_data.empty:
            success = stock_data_service.store_daily_data(db, daily_data)
            if success:
                # 計算技術指標
                stock_data_service.calculate_technical_indicators(db, symbol, '5y')
                return {"message": f"Stock data initialized successfully for {symbol}"}
            else:
                raise HTTPException(status_code=500, detail=f"Failed to store data for {symbol}")
        else:
            raise HTTPException(status_code=404, detail=f"No data available for {symbol}")
            
    except Exception as e:
        logger.error(f"Error initializing stock data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 在應用啟動時啟動股票數據調度器
@app.on_event("startup")
async def startup_event():
    # 啟動新聞調度器
    news_scheduler.start()
    
    # 啟動股票數據調度器
    stock_data_scheduler.start()
    
    logger.info("Both news and stock data schedulers started")

@app.post('/ai/analyze')
async def analyze_with_ai(request: AIAnalysisRequest):
    """使用AI分析投資組合並提供建議"""
    try:
        # 設置OpenAI API
        openai.api_key = os.getenv('OPENAI_API_KEY')
        
        if not openai.api_key:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        # 準備投資組合摘要
        portfolio_summary = []
        total_value = 0
        total_pnl = 0
        
        for position in request.portfolio:
            pnl = position.get('unrealized_pnl', 0)
            market_value = position.get('market_value', 0)
            total_value += market_value
            total_pnl += pnl
            
            portfolio_summary.append({
                'symbol': position.get('symbol', ''),
                'quantity': position.get('position', 0),
                'avg_cost': position.get('avg_cost', 0),
                'market_value': market_value,
                'unrealized_pnl': pnl,
                'pnl_percentage': (pnl / (position.get('avg_cost', 1) * position.get('position', 1))) * 100 if position.get('avg_cost', 0) > 0 else 0
            })
        
        # 獲取實時市場數據和新聞
        market_data = {}
        news_data = {}
        
        for position in portfolio_summary:
            symbol = position['symbol']
            try:
                # 獲取市場數據
                market_info = await get_market_data(symbol)
                if market_info:
                    market_data[symbol] = market_info
                
                # 獲取新聞數據
                try:
                    loop = asyncio.get_event_loop()
                    news = await loop.run_in_executor(None, lambda: get_all_news(symbol))
                    if news:
                        news_data[symbol] = news[:3]  # 只取最新3條新聞
                except Exception as e:
                    logger.warning(f"Failed to get news for {symbol}: {e}")
                    news_data[symbol] = []
                    
            except Exception as e:
                logger.warning(f"Failed to get market data for {symbol}: {e}")
                market_data[symbol] = None
        
        # 準備上下文信息
        context = {
            'account_summary': {
                'total_value': request.accountSummary.get('netLiquidationValue', 0),
                'cash_balance': request.accountSummary.get('totalCashValue', 0),
                'available_funds': request.accountSummary.get('availableFunds', 0),
                'buying_power': request.accountSummary.get('buyingPower', 0),
                'unrealized_pnl': request.accountSummary.get('unrealizedPnl', 0)
            },
            'portfolio': portfolio_summary,
            'portfolio_metrics': {
                'total_positions': len(request.portfolio),
                'total_market_value': total_value,
                'total_unrealized_pnl': total_pnl,
                'portfolio_pnl_percentage': (total_pnl / total_value) * 100 if total_value > 0 else 0
            },
            'market_data': market_data,
            'news_data': news_data
        }
        
        # 構建提示詞
        locale = request.locale or 'zh_tw'
        system_prompt = i18n_service.t('ai.systemPrompt', locale=locale)
        
        # 添加投資組合信息
        system_prompt += "\n\n用戶的投資組合信息："
        
        user_prompt = f"""
投資組合摘要：
- 總資產價值: ${context['account_summary']['total_value']:,.2f}
- 現金餘額: ${context['account_summary']['cash_balance']:,.2f}
- 可用資金: ${context['account_summary']['available_funds']:,.2f}
- 購買力: ${context['account_summary']['buying_power']:,.2f}
- 未實現損益: ${context['account_summary']['unrealized_pnl']:,.2f}

持倉詳情：
"""
        
        for position in portfolio_summary:
            symbol = position['symbol']
            user_prompt += f"- {symbol}: {position['quantity']}股, 平均成本${position['avg_cost']:.2f}, 市值${position['market_value']:,.2f}, 未實現損益${position['unrealized_pnl']:,.2f} ({position['pnl_percentage']:+.1f}%)\n"
            
            # 添加實時市場數據
            if symbol in context['market_data'] and context['market_data'][symbol]:
                market = context['market_data'][symbol]
                user_prompt += f"  實時價格: ${market.get('price', 'N/A')}, 漲跌: {market.get('change', 'N/A')}\n"
            
            # 添加相關新聞
            if symbol in context['news_data'] and context['news_data'][symbol]:
                user_prompt += f"  最新新聞: {len(context['news_data'][symbol])}條\n"
                for news in context['news_data'][symbol][:2]:  # 只顯示前2條
                    user_prompt += f"    - {news.get('title', 'N/A')[:50]}...\n"
        
        user_prompt += f"""
投資組合整體表現：
- 總持倉數量: {context['portfolio_metrics']['total_positions']}個
- 總市值: ${context['portfolio_metrics']['total_market_value']:,.2f}
- 總未實現損益: ${context['portfolio_metrics']['total_unrealized_pnl']:,.2f}
- 投資組合收益率: {context['portfolio_metrics']['portfolio_pnl_percentage']:+.1f}%

用戶問題: {request.message}

請基於以上實時數據和新聞，提供詳細的投資分析和建議。
"""
        
        # 調用OpenAI API (新版本)
        client = openai.OpenAI(api_key=openai.api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        analysis = response.choices[0].message.content
        
        return {
            "analysis": analysis,
            "context": context,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in AI analysis: {e}")
        raise HTTPException(status_code=500, detail=f"AI分析失敗: {str(e)}")

@app.post('/ai/analyze-ibkr')
async def analyze_ibkr_with_ai(request: AIAnalysisRequest):
    """使用AI分析IBKR真實投資組合並提供建議"""
    try:
        # 設置OpenAI API
        openai.api_key = os.getenv('OPENAI_API_KEY')
        
        if not openai.api_key:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        # 獲取真實的IBKR數據
        logger.info("獲取IBKR真實數據...")
        
        # 獲取賬戶摘要
        account_summary = await ibkr_service.get_account_summary()
        logger.info(f"賬戶摘要: {account_summary}")
        
        # 獲取持倉
        positions = await ibkr_service.get_positions()
        logger.info(f"持倉數量: {len(positions)}")
        
        # 準備投資組合摘要
        portfolio_summary = []
        total_value = 0
        total_pnl = 0
        
        for position in positions:
            pnl = position.get('unrealized_pnl', 0)
            market_value = position.get('market_value', 0)
            total_value += market_value
            total_pnl += pnl
            
            portfolio_summary.append({
                'symbol': position.get('symbol', ''),
                'quantity': position.get('position', 0),
                'avg_cost': position.get('avg_cost', 0),
                'market_value': market_value,
                'unrealized_pnl': pnl,
                'pnl_percentage': (pnl / (position.get('avg_cost', 1) * position.get('position', 1))) * 100 if position.get('avg_cost', 0) > 0 else 0
            })
        
        # 獲取實時市場數據和新聞
        market_data = {}
        news_data = {}
        
        for position in portfolio_summary:
            symbol = position['symbol']
            try:
                # 獲取市場數據
                market_info = await get_market_data(symbol)
                if market_info:
                    market_data[symbol] = market_info
                
                # 獲取新聞數據
                try:
                    loop = asyncio.get_event_loop()
                    news = await loop.run_in_executor(None, lambda: get_all_news(symbol))
                    if news:
                        news_data[symbol] = news[:3]  # 只取最新3條新聞
                except Exception as e:
                    logger.warning(f"Failed to get news for {symbol}: {e}")
                    news_data[symbol] = []
                    
            except Exception as e:
                logger.warning(f"Failed to get market data for {symbol}: {e}")
                market_data[symbol] = None
        
        # 準備上下文信息
        context = {
            'account_summary': {
                'total_value': account_summary.get('net_liquidation_value', 0),
                'cash_balance': account_summary.get('total_cash_value', 0),
                'available_funds': account_summary.get('available_funds', 0),
                'buying_power': account_summary.get('buying_power', 0),
                'unrealized_pnl': account_summary.get('unrealized_pnl', 0)
            },
            'portfolio': portfolio_summary,
            'portfolio_metrics': {
                'total_positions': len(positions),
                'total_market_value': total_value,
                'total_unrealized_pnl': total_pnl,
                'portfolio_pnl_percentage': (total_pnl / total_value) * 100 if total_value > 0 else 0
            },
            'market_data': market_data,
            'news_data': news_data
        }
        
        # 構建提示詞
        system_prompt = """你是一位專業的投資顧問AI助手，專門為中文用戶提供投資建議。請根據用戶的IBKR真實投資組合和問題，提供專業、客觀、實用的投資建議。

請注意：
1. 所有建議僅供參考，不構成投資建議
2. 投資有風險，請謹慎決策
3. 建議要具體、可操作
4. 考慮風險管理和分散投資
5. 用繁體中文回應
6. 基於實時市場數據和新聞提供分析

用戶的IBKR真實投資組合信息：
"""
        
        user_prompt = f"""
IBKR真實投資組合摘要：
- 總資產價值: ${context['account_summary']['total_value']:,.2f}
- 現金餘額: ${context['account_summary']['cash_balance']:,.2f}
- 可用資金: ${context['account_summary']['available_funds']:,.2f}
- 購買力: ${context['account_summary']['buying_power']:,.2f}
- 未實現損益: ${context['account_summary']['unrealized_pnl']:,.2f}

真實持倉詳情：
"""
        
        for position in portfolio_summary:
            symbol = position['symbol']
            user_prompt += f"- {symbol}: {position['quantity']}股, 平均成本${position['avg_cost']:.2f}, 市值${position['market_value']:,.2f}, 未實現損益${position['unrealized_pnl']:,.2f} ({position['pnl_percentage']:+.1f}%)\n"
            
            # 添加實時市場數據
            if symbol in context['market_data'] and context['market_data'][symbol]:
                market = context['market_data'][symbol]
                user_prompt += f"  實時價格: ${market.get('price', 'N/A')}, 漲跌: {market.get('change', 'N/A')}\n"
            
            # 添加相關新聞
            if symbol in context['news_data'] and context['news_data'][symbol]:
                user_prompt += f"  最新新聞: {len(context['news_data'][symbol])}條\n"
                for news in context['news_data'][symbol][:2]:  # 只顯示前2條
                    user_prompt += f"    - {news.get('title', 'N/A')[:50]}...\n"
        
        user_prompt += f"""
投資組合整體表現：
- 總持倉數量: {context['portfolio_metrics']['total_positions']}個
- 總市值: ${context['portfolio_metrics']['total_market_value']:,.2f}
- 總未實現損益: ${context['portfolio_metrics']['total_unrealized_pnl']:,.2f}
- 投資組合收益率: {context['portfolio_metrics']['portfolio_pnl_percentage']:+.1f}%

用戶問題: {request.message}

請基於以上IBKR真實數據、實時市場數據和新聞，提供詳細的投資分析和建議。
"""
        
        # 調用OpenAI API (新版本)
        client = openai.OpenAI(api_key=openai.api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=1500,
            temperature=0.7
        )
        
        analysis = response.choices[0].message.content
        
        return {
            "analysis": analysis,
            "context": context,
            "timestamp": datetime.now().isoformat(),
            "data_source": "IBKR Real Data"
        }
        
    except Exception as e:
        logger.error(f"Error in IBKR AI analysis: {e}")
        raise HTTPException(status_code=500, detail=f"IBKR AI分析失敗: {str(e)}")

@app.on_event("shutdown")
async def shutdown_event():
    # 停止調度器
    news_scheduler.stop()
    stock_data_scheduler.stop()
    
    logger.info("Both schedulers stopped")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 