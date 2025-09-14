from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, UniqueConstraint, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    portfolios = relationship("Portfolio", back_populates="user")
    watchlists = relationship("Watchlist", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")

class Portfolio(Base):
    __tablename__ = "portfolios"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    symbol = Column(String, index=True)  # Stock symbol
    quantity = Column(Float)
    average_price = Column(Float)
    current_price = Column(Float)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="portfolios")

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    symbol = Column(String, index=True)
    action = Column(String)  # "BUY" or "SELL"
    quantity = Column(Float)
    price = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String)  # "PENDING", "FILLED", "CANCELLED"
    order_id = Column(String)  # IBKR order ID
    
    # Relationships
    user = relationship("User", back_populates="transactions")

class Watchlist(Base):
    __tablename__ = "watchlists"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    symbol = Column(String, index=True)
    added_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="watchlists")

class MarketData(Base):
    __tablename__ = "market_data"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    price = Column(Float)
    volume = Column(Integer)
    high = Column(Float)
    low = Column(Float)
    open_price = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

class News(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    title = Column(String)
    summary = Column(Text)
    link = Column(String)
    publisher = Column(String)
    published_at = Column(DateTime)
    source = Column(String)
    score = Column(Float)
    sentiment_label = Column(String)
    confidence = Column(Float)
    analysis_method = Column(String)
    textblob_score = Column(Float)
    openai_score = Column(Float)
    raw_json = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class TargetSymbol(Base):
    __tablename__ = "target_symbols"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# 新增股票數據模型
class StockDaily(Base):
    """日線股票數據"""
    __tablename__ = "stock_daily"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    date = Column(DateTime, index=True)
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float)
    volume = Column(Integer)
    adjusted_close = Column(Float)
    dividend_amount = Column(Float, default=0.0)
    split_coefficient = Column(Float, default=1.0)
    source = Column(String, default='yahoo')  # yahoo, alpha_vantage, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 複合索引
    __table_args__ = (
        Index('idx_symbol_date', 'symbol', 'date'),
    )

class StockIntraday(Base):
    """分鐘級股票數據"""
    __tablename__ = "stock_intraday"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    timestamp = Column(DateTime, index=True)
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float)
    volume = Column(Integer)
    interval = Column(String)  # 1m, 5m, 15m, 30m, 60m
    source = Column(String, default='yahoo')
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_symbol_timestamp', 'symbol', 'timestamp'),
    )

class TechnicalIndicators(Base):
    """技術指標數據"""
    __tablename__ = "technical_indicators"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    date = Column(DateTime, index=True)
    indicator_type = Column(String)  # SMA, EMA, RSI, MACD, BB, etc.
    period = Column(Integer)  # 計算週期
    value = Column(Float)
    additional_data = Column(Text)  # JSON格式存儲額外數據
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_symbol_date_indicator', 'symbol', 'date', 'indicator_type'),
    )

class FundamentalData(Base):
    """基本面數據"""
    __tablename__ = "fundamental_data"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    date = Column(DateTime, index=True)
    data_type = Column(String)  # earnings, balance_sheet, cash_flow, etc.
    metric_name = Column(String)  # revenue, net_income, pe_ratio, etc.
    value = Column(Float)
    unit = Column(String)  # USD, millions, etc.
    period = Column(String)  # annual, quarterly
    source = Column(String, default='yahoo')
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_symbol_date_type', 'symbol', 'date', 'data_type'),
    )

class MarketSentiment(Base):
    """市場情緒數據"""
    __tablename__ = "market_sentiment"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    date = Column(DateTime, index=True)
    sentiment_type = Column(String)  # news_sentiment, social_sentiment, analyst_rating
    score = Column(Float)
    confidence = Column(Float)
    source = Column(String)
    raw_data = Column(Text)  # JSON格式存儲原始數據
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_symbol_date_sentiment', 'symbol', 'date', 'sentiment_type'),
    )

class TradingSignals(Base):
    """交易信號"""
    __tablename__ = "trading_signals"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    date = Column(DateTime, index=True)
    signal_type = Column(String)  # buy, sell, hold
    confidence = Column(Float)
    strategy = Column(String)  # technical, fundamental, sentiment, combined
    indicators_used = Column(Text)  # JSON格式存儲使用的指標
    reasoning = Column(Text)  # 信號生成原因
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_symbol_date_signal', 'symbol', 'date', 'signal_type'),
    ) 