import logging
import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from database import get_db
from stock_data_service import stock_data_service
from models import TargetSymbol

logger = logging.getLogger(__name__)

class StockDataScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        
    def start(self):
        """啟動調度器"""
        if not self.is_running:
            # 每日數據更新 - 每個交易日收盤後
            self.scheduler.add_job(
                self.update_daily_data,
                CronTrigger(hour=16, minute=30),  # 4:30 PM EST
                id='update_daily_data',
                name='Update Daily Stock Data'
            )
            
            # 技術指標計算 - 每日收盤後
            self.scheduler.add_job(
                self.calculate_indicators,
                CronTrigger(hour=17, minute=0),  # 5:00 PM EST
                id='calculate_indicators',
                name='Calculate Technical Indicators'
            )
            
            # 交易信號生成 - 每日收盤後
            self.scheduler.add_job(
                self.generate_signals,
                CronTrigger(hour=17, minute=30),  # 5:30 PM EST
                id='generate_signals',
                name='Generate Trading Signals'
            )
            
            # 歷史數據初始化 - 每週一次
            self.scheduler.add_job(
                self.initialize_historical_data,
                CronTrigger(day_of_week='sun', hour=2, minute=0),  # 週日凌晨2點
                id='initialize_historical_data',
                name='Initialize Historical Data'
            )
            
            self.scheduler.start()
            self.is_running = True
            logger.info("Stock data scheduler started")
    
    def stop(self):
        """停止調度器"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Stock data scheduler stopped")
    
    def get_status(self) -> dict:
        """獲取調度器狀態"""
        if not self.is_running:
            return {
                'status': 'stopped',
                'jobs': []
            }
        
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        
        return {
            'status': 'running',
            'jobs': jobs
        }
    
    async def update_daily_data(self):
        """更新日線數據"""
        logger.info("Starting daily data update")
        try:
            db = next(get_db())
            symbols = db.query(TargetSymbol).all()
            
            for symbol_record in symbols:
                symbol = symbol_record.symbol
                logger.info(f"Updating daily data for {symbol}")
                
                # 獲取最近一年的數據
                end_date = datetime.now()
                start_date = end_date - timedelta(days=365)
                
                # 抓取數據
                data = stock_data_service.fetch_daily_data(
                    symbol=symbol,
                    start_date=start_date.strftime('%Y-%m-%d'),
                    end_date=end_date.strftime('%Y-%m-%d')
                )
                
                if not data.empty:
                    # 存儲數據
                    success = stock_data_service.store_daily_data(db, data)
                    if success:
                        logger.info(f"Successfully updated daily data for {symbol}")
                    else:
                        logger.error(f"Failed to store daily data for {symbol}")
                else:
                    logger.warning(f"No daily data available for {symbol}")
            
            db.close()
            logger.info("Daily data update completed")
            
        except Exception as e:
            logger.error(f"Error in daily data update: {e}")
    
    async def calculate_indicators(self):
        """計算技術指標"""
        logger.info("Starting technical indicators calculation")
        try:
            db = next(get_db())
            symbols = db.query(TargetSymbol).all()
            
            for symbol_record in symbols:
                symbol = symbol_record.symbol
                logger.info(f"Calculating indicators for {symbol}")
                
                # 計算技術指標
                indicators = stock_data_service.calculate_technical_indicators(db, symbol)
                
                if indicators:
                    logger.info(f"Successfully calculated indicators for {symbol}")
                else:
                    logger.warning(f"No indicators calculated for {symbol}")
            
            db.close()
            logger.info("Technical indicators calculation completed")
            
        except Exception as e:
            logger.error(f"Error in indicators calculation: {e}")
    
    async def generate_signals(self):
        """生成交易信號"""
        logger.info("Starting trading signals generation")
        try:
            db = next(get_db())
            symbols = db.query(TargetSymbol).all()
            
            for symbol_record in symbols:
                symbol = symbol_record.symbol
                logger.info(f"Generating signals for {symbol}")
                
                # 生成交易信號
                signal = stock_data_service.generate_trading_signals(db, symbol)
                
                if signal:
                    logger.info(f"Generated signal for {symbol}: {signal['signal']} (confidence: {signal['confidence']})")
                else:
                    logger.warning(f"No signal generated for {symbol}")
            
            db.close()
            logger.info("Trading signals generation completed")
            
        except Exception as e:
            logger.error(f"Error in signals generation: {e}")
    
    async def initialize_historical_data(self):
        """初始化歷史數據"""
        logger.info("Starting historical data initialization")
        try:
            db = next(get_db())
            symbols = db.query(TargetSymbol).all()
            
            for symbol_record in symbols:
                symbol = symbol_record.symbol
                logger.info(f"Initializing historical data for {symbol}")
                
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
                        logger.info(f"Successfully initialized daily data for {symbol}")
                        
                        # 計算技術指標
                        indicators = stock_data_service.calculate_technical_indicators(db, symbol, '5y')
                        if indicators:
                            logger.info(f"Successfully calculated historical indicators for {symbol}")
                    else:
                        logger.error(f"Failed to store historical data for {symbol}")
                else:
                    logger.warning(f"No historical data available for {symbol}")
            
            db.close()
            logger.info("Historical data initialization completed")
            
        except Exception as e:
            logger.error(f"Error in historical data initialization: {e}")
    
    def manual_update_symbol(self, symbol: str) -> bool:
        """手動更新單個股票的數據"""
        try:
            logger.info(f"Manual update for {symbol}")
            db = next(get_db())
            
            # 更新日線數據
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            daily_data = stock_data_service.fetch_daily_data(
                symbol=symbol,
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
            
            if not daily_data.empty:
                stock_data_service.store_daily_data(db, daily_data)
            
            # 計算指標
            stock_data_service.calculate_technical_indicators(db, symbol)
            
            # 生成信號
            stock_data_service.generate_trading_signals(db, symbol)
            
            db.close()
            logger.info(f"Manual update completed for {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Error in manual update for {symbol}: {e}")
            return False

# 全局實例
stock_data_scheduler = StockDataScheduler() 