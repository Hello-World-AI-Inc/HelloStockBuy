# Requires: python-dotenv
from fastapi import FastAPI, HTTPException, Request, Body, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from ibkr_service import ibkr_service
from market_data import get_market_data, get_current_source, set_current_source, MARKET_DATA_SOURCES, get_all_news
import asyncio
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from typing import Dict, Any
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from database import get_db
from models import News

# Add dotenv support to load .env if present
load_dotenv()

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

# Global settings with defaults
selected_market_data_source = os.getenv('MARKET_DATA_SOURCE', 'yahoo')
selected_news_source = os.getenv('NEWS_SOURCE', 'yahoo')

NEWS_FETCH_INTERVAL_HOURS = int(os.getenv('NEWS_FETCH_INTERVAL_HOURS', 2))

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

# Background job to fetch and store news for TSLA
def fetch_and_store_news():
    from market_data import get_all_news
    from database import SessionLocal
    session = SessionLocal()
    symbol = 'TSLA'
    news_items = get_all_news(symbol)
    for item in news_items:
        # Deduplicate by link
        exists = session.query(News).filter_by(link=item['link']).first()
        if not exists:
            news = News(
                symbol=symbol,
                title=item.get('title'),
                summary=item.get('summary'),
                link=item.get('link'),
                publisher=item.get('publisher'),
                published_at=item.get('published_at'),
                source=item.get('source'),
                score=item.get('score'),
                raw_json=item.get('raw_json'),
            )
            session.add(news)
    session.commit()
    session.close()

scheduler.add_job(fetch_and_store_news, 'interval', hours=NEWS_FETCH_INTERVAL_HOURS, next_run_time=None)
scheduler.start()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 