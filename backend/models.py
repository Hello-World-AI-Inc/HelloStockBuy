from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
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
    published_at = Column(DateTime, index=True)
    source = Column(String, index=True)  # e.g., 'yahoo', 'marketaux', etc.
    score = Column(Float, nullable=True)  # Optional: sentiment or relevance score
    raw_json = Column(Text, nullable=True)  # Store raw response for debugging/traceability
    created_at = Column(DateTime, default=datetime.utcnow) 