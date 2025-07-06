import yfinance as yf
import pandas as pd
import numpy as np
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from models import StockDaily, StockIntraday, TechnicalIndicators, FundamentalData, MarketSentiment
from database import get_db

logger = logging.getLogger(__name__)

class StockDataService:
    def __init__(self):
        self.sources = {
            'yahoo': self.fetch_daily_data,
            'alpha_vantage': self.fetch_daily_data  # 暫時使用相同的方法
        }
    
    def fetch_daily_data(self, symbol: str, start_date: str = None, end_date: str = None, source: str = 'yahoo') -> pd.DataFrame:
        """抓取日線數據"""
        try:
            if source == 'yahoo':
                ticker = yf.Ticker(symbol)
                df = ticker.history(start=start_date, end=end_date)
                
                if df.empty:
                    logger.warning(f"No data found for {symbol}")
                    return pd.DataFrame()
                
                # 重命名列以匹配數據庫結構
                df = df.reset_index()
                df['symbol'] = symbol
                df['date'] = df['Date']
                df['open_price'] = df['Open']
                df['high_price'] = df['High']
                df['low_price'] = df['Low']
                df['close_price'] = df['Close']
                df['volume'] = df['Volume']
                df['adjusted_close'] = df['Adj Close']
                df['source'] = source
                
                return df[['symbol', 'date', 'open_price', 'high_price', 'low_price', 
                          'close_price', 'volume', 'adjusted_close', 'source']]
            
        except Exception as e:
            logger.error(f"Error fetching daily data for {symbol}: {e}")
            return pd.DataFrame()
    
    def fetch_intraday_data(self, symbol: str, interval: str = '1h', period: str = '1mo', source: str = 'yahoo') -> pd.DataFrame:
        """抓取分鐘級數據"""
        try:
            if source == 'yahoo':
                ticker = yf.Ticker(symbol)
                df = ticker.history(period=period, interval=interval)
                
                if df.empty:
                    logger.warning(f"No intraday data found for {symbol}")
                    return pd.DataFrame()
                
                df = df.reset_index()
                df['symbol'] = symbol
                df['timestamp'] = df['Datetime']
                df['open_price'] = df['Open']
                df['high_price'] = df['High']
                df['low_price'] = df['Low']
                df['close_price'] = df['Close']
                df['volume'] = df['Volume']
                df['interval'] = interval
                df['source'] = source
                
                return df[['symbol', 'timestamp', 'open_price', 'high_price', 'low_price', 
                          'close_price', 'volume', 'interval', 'source']]
            
        except Exception as e:
            logger.error(f"Error fetching intraday data for {symbol}: {e}")
            return pd.DataFrame()
    
    def store_daily_data(self, db: Session, data: pd.DataFrame) -> bool:
        """存儲日線數據到數據庫"""
        try:
            for _, row in data.iterrows():
                # 檢查是否已存在
                existing = db.query(StockDaily).filter(
                    and_(StockDaily.symbol == row['symbol'], 
                         StockDaily.date == row['date'])
                ).first()
                
                if not existing:
                    stock_data = StockDaily(
                        symbol=row['symbol'],
                        date=row['date'],
                        open_price=row['open_price'],
                        high_price=row['high_price'],
                        low_price=row['low_price'],
                        close_price=row['close_price'],
                        volume=row['volume'],
                        adjusted_close=row['adjusted_close'],
                        source=row['source']
                    )
                    db.add(stock_data)
            
            db.commit()
            logger.info(f"Stored {len(data)} daily records")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error storing daily data: {e}")
            return False
    
    def store_intraday_data(self, db: Session, data: pd.DataFrame) -> bool:
        """存儲分鐘級數據到數據庫"""
        try:
            for _, row in data.iterrows():
                existing = db.query(StockIntraday).filter(
                    and_(StockIntraday.symbol == row['symbol'], 
                         StockIntraday.timestamp == row['timestamp'],
                         StockIntraday.interval == row['interval'])
                ).first()
                
                if not existing:
                    intraday_data = StockIntraday(
                        symbol=row['symbol'],
                        timestamp=row['timestamp'],
                        open_price=row['open_price'],
                        high_price=row['high_price'],
                        low_price=row['low_price'],
                        close_price=row['close_price'],
                        volume=row['volume'],
                        interval=row['interval'],
                        source=row['source']
                    )
                    db.add(intraday_data)
            
            db.commit()
            logger.info(f"Stored {len(data)} intraday records")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error storing intraday data: {e}")
            return False
    
    def calculate_technical_indicators(self, db: Session, symbol: str, period: str = '1y') -> Dict:
        """計算技術指標"""
        try:
            # 獲取日線數據
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365 if period == '1y' else 30)
            
            data = db.query(StockDaily).filter(
                and_(StockDaily.symbol == symbol,
                     StockDaily.date >= start_date,
                     StockDaily.date <= end_date)
            ).order_by(StockDaily.date).all()
            
            if not data:
                logger.warning(f"No data found for {symbol}")
                return {}
            
            # 轉換為DataFrame
            df = pd.DataFrame([{
                'date': d.date,
                'close': d.close_price,
                'high': d.high_price,
                'low': d.low_price,
                'volume': d.volume
            } for d in data])
            
            indicators = {}
            
            # 移動平均線
            indicators['SMA_20'] = self._calculate_sma(df['close'], 20)
            indicators['SMA_50'] = self._calculate_sma(df['close'], 50)
            indicators['EMA_12'] = self._calculate_ema(df['close'], 12)
            indicators['EMA_26'] = self._calculate_ema(df['close'], 26)
            
            # RSI
            indicators['RSI_14'] = self._calculate_rsi(df['close'], 14)
            
            # MACD
            macd_data = self._calculate_macd(df['close'])
            indicators['MACD'] = macd_data['macd']
            indicators['MACD_Signal'] = macd_data['signal']
            indicators['MACD_Histogram'] = macd_data['histogram']
            
            # 布林帶
            bb_data = self._calculate_bollinger_bands(df['close'], 20)
            indicators['BB_Upper'] = bb_data['upper']
            indicators['BB_Middle'] = bb_data['middle']
            indicators['BB_Lower'] = bb_data['lower']
            
            # 存儲指標到數據庫
            self._store_indicators(db, symbol, df['date'], indicators)
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculating indicators for {symbol}: {e}")
            return {}
    
    def _calculate_sma(self, prices: pd.Series, period: int) -> pd.Series:
        """計算簡單移動平均線"""
        return prices.rolling(window=period).mean()
    
    def _calculate_ema(self, prices: pd.Series, period: int) -> pd.Series:
        """計算指數移動平均線"""
        return prices.ewm(span=period).mean()
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """計算相對強弱指數"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
        """計算MACD"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal).mean()
        histogram = macd - signal_line
        
        return {
            'macd': macd,
            'signal': signal_line,
            'histogram': histogram
        }
    
    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: int = 2) -> Dict:
        """計算布林帶"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        
        return {
            'upper': upper,
            'middle': sma,
            'lower': lower
        }
    
    def _store_indicators(self, db: Session, symbol: str, dates: pd.Series, indicators: Dict):
        """存儲技術指標到數據庫"""
        try:
            for i, date in enumerate(dates):
                for indicator_name, values in indicators.items():
                    if not pd.isna(values.iloc[i]):
                        # 檢查是否已存在
                        existing = db.query(TechnicalIndicators).filter(
                            and_(TechnicalIndicators.symbol == symbol,
                                 TechnicalIndicators.date == date,
                                 TechnicalIndicators.indicator_type == indicator_name)
                        ).first()
                        
                        if not existing:
                            indicator = TechnicalIndicators(
                                symbol=symbol,
                                date=date,
                                indicator_type=indicator_name,
                                period=self._get_indicator_period(indicator_name),
                                value=float(values.iloc[i]),
                                additional_data='{}'
                            )
                            db.add(indicator)
            
            db.commit()
            logger.info(f"Stored technical indicators for {symbol}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error storing indicators: {e}")
    
    def _get_indicator_period(self, indicator_name: str) -> int:
        """獲取指標週期"""
        if 'SMA' in indicator_name:
            return int(indicator_name.split('_')[1])
        elif 'EMA' in indicator_name:
            return int(indicator_name.split('_')[1])
        elif 'RSI' in indicator_name:
            return int(indicator_name.split('_')[1])
        elif 'BB' in indicator_name:
            return 20
        else:
            return 0
    
    def get_chart_data(self, db: Session, symbol: str, period: str = '1y', interval: str = '1d') -> Dict:
        """獲取圖表數據"""
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
            
            # 獲取價格數據
            if interval == '1d':
                data = db.query(StockDaily).filter(
                    and_(StockDaily.symbol == symbol,
                         StockDaily.date >= start_date,
                         StockDaily.date <= end_date)
                ).order_by(StockDaily.date).all()
                
                chart_data = {
                    'dates': [d.date.isoformat() for d in data],
                    'prices': [d.close_price for d in data],
                    'volumes': [d.volume for d in data],
                    'highs': [d.high_price for d in data],
                    'lows': [d.low_price for d in data],
                    'opens': [d.open_price for d in data]
                }
            else:
                # 分鐘級數據
                data = db.query(StockIntraday).filter(
                    and_(StockIntraday.symbol == symbol,
                         StockIntraday.timestamp >= start_date,
                         StockIntraday.timestamp <= end_date,
                         StockIntraday.interval == interval)
                ).order_by(StockIntraday.timestamp).all()
                
                chart_data = {
                    'dates': [d.timestamp.isoformat() for d in data],
                    'prices': [d.close_price for d in data],
                    'volumes': [d.volume for d in data],
                    'highs': [d.high_price for d in data],
                    'lows': [d.low_price for d in data],
                    'opens': [d.open_price for d in data]
                }
            
            # 獲取技術指標
            indicators = db.query(TechnicalIndicators).filter(
                and_(TechnicalIndicators.symbol == symbol,
                     TechnicalIndicators.date >= start_date,
                     TechnicalIndicators.date <= end_date)
            ).order_by(TechnicalIndicators.date).all()
            
            # 組織指標數據
            indicator_data = {}
            for indicator in indicators:
                if indicator.indicator_type not in indicator_data:
                    indicator_data[indicator.indicator_type] = {
                        'dates': [],
                        'values': []
                    }
                indicator_data[indicator.indicator_type]['dates'].append(indicator.date.isoformat())
                indicator_data[indicator.indicator_type]['values'].append(indicator.value)
            
            chart_data['indicators'] = indicator_data
            
            return chart_data
            
        except Exception as e:
            logger.error(f"Error getting chart data for {symbol}: {e}")
            return {}
    
    def generate_trading_signals(self, db: Session, symbol: str) -> Dict:
        """生成交易信號"""
        try:
            # 獲取最新技術指標
            latest_indicators = db.query(TechnicalIndicators).filter(
                TechnicalIndicators.symbol == symbol
            ).order_by(desc(TechnicalIndicators.date)).limit(50).all()
            
            if not latest_indicators:
                return {'signal': 'hold', 'confidence': 0.5, 'reasoning': 'No data available'}
            
            # 組織指標數據
            indicators = {}
            for indicator in latest_indicators:
                if indicator.indicator_type not in indicators:
                    indicators[indicator.indicator_type] = []
                indicators[indicator.indicator_type].append(indicator.value)
            
            # 簡單的信號生成邏輯
            signal = 'hold'
            confidence = 0.5
            reasoning = []
            
            # RSI 信號
            if 'RSI_14' in indicators and len(indicators['RSI_14']) > 0:
                rsi = indicators['RSI_14'][-1]
                if rsi < 30:
                    signal = 'buy'
                    confidence += 0.2
                    reasoning.append(f"RSI oversold ({rsi:.2f})")
                elif rsi > 70:
                    signal = 'sell'
                    confidence += 0.2
                    reasoning.append(f"RSI overbought ({rsi:.2f})")
            
            # MACD 信號
            if 'MACD' in indicators and 'MACD_Signal' in indicators and len(indicators['MACD']) > 0:
                macd = indicators['MACD'][-1]
                macd_signal = indicators['MACD_Signal'][-1]
                if macd > macd_signal and signal == 'hold':
                    signal = 'buy'
                    confidence += 0.15
                    reasoning.append("MACD bullish crossover")
                elif macd < macd_signal and signal == 'hold':
                    signal = 'sell'
                    confidence += 0.15
                    reasoning.append("MACD bearish crossover")
            
            # 移動平均線信號
            if 'SMA_20' in indicators and 'SMA_50' in indicators and len(indicators['SMA_20']) > 0:
                sma_20 = indicators['SMA_20'][-1]
                sma_50 = indicators['SMA_50'][-1]
                if sma_20 > sma_50 and signal == 'hold':
                    signal = 'buy'
                    confidence += 0.1
                    reasoning.append("SMA 20 above SMA 50")
                elif sma_20 < sma_50 and signal == 'hold':
                    signal = 'sell'
                    confidence += 0.1
                    reasoning.append("SMA 20 below SMA 50")
            
            confidence = min(confidence, 1.0)
            
            return {
                'signal': signal,
                'confidence': confidence,
                'reasoning': '; '.join(reasoning) if reasoning else 'No clear signal'
            }
            
        except Exception as e:
            logger.error(f"Error generating trading signals for {symbol}: {e}")
            return {'signal': 'hold', 'confidence': 0.5, 'reasoning': 'Error in signal generation'}

# 全局實例
stock_data_service = StockDataService() 