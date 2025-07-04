from ib_insync import *
import asyncio
import os
from typing import Dict, List, Optional
import logging
import nest_asyncio

# Enable nested event loops
nest_asyncio.apply()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IBKRService:
    def __init__(self):
        self.ib = IB()
        self.connected = False
        self.host = os.getenv('IBKR_HOST', 'host.docker.internal')
        self.port = int(os.getenv('IBKR_PORT', '4002'))
        self.client_id = int(os.getenv('IBKR_CLIENT_ID', '12345'))
        
    async def connect(self):
        """Connect to IBKR Gateway"""
        try:
            if not self.connected:
                self.ib.connect(
                    host=self.host,
                    port=self.port,
                    clientId=self.client_id,
                    timeout=20
                )
                self.connected = True
                logger.info(f"Connected to IBKR Gateway at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to IBKR Gateway: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from IBKR Gateway"""
        if self.connected:
            self.ib.disconnect()
            self.connected = False
            logger.info("Disconnected from IBKR Gateway")
    
    def get_stock_contract(self, symbol: str) -> Contract:
        """Create a stock contract for the given symbol"""
        contract = Stock(symbol, 'SMART', 'USD')
        return contract
    
    async def get_market_data(self, symbol: str) -> Optional[Dict]:
        """Get real-time market data for a symbol"""
        try:
            if not self.connected:
                logger.info(f"Not connected, attempting to connect...")
                await self.connect()
            try:
                contract = self.get_stock_contract(symbol)
                logger.info(f"Requesting market data for {symbol}...")
                ticker = self.ib.reqMktData(contract)
                logger.info(f"Waiting for market data...")
                await asyncio.sleep(5)  # Wait longer for data
                def safe_float(value):
                    if value is None:
                        return None
                    try:
                        float_val = float(value)
                        if float_val in [float('inf'), float('-inf')] or float_val != float_val:
                            return None
                        return float_val
                    except (ValueError, TypeError):
                        return None
                market_price = ticker.marketPrice()
                open_price = safe_float(getattr(ticker, 'open', None))
                logger.info(f"IBKR {symbol}: price={market_price}, open={open_price}, ticker={ticker.__dict__}")
                logger.info(f"Market price for {symbol}: {market_price}")
                if market_price:
                    return {
                        'symbol': symbol,
                        'price': safe_float(market_price),
                        'bid': safe_float(ticker.bid),
                        'ask': safe_float(ticker.ask),
                        'high': safe_float(ticker.high),
                        'low': safe_float(ticker.low),
                        'volume': safe_float(ticker.volume),
                        'timestamp': ticker.time.isoformat() if ticker.time else None,
                        'open': open_price
                    }
                else:
                    logger.warning(f"No market data available for {symbol}")
                    return None
            except Exception as e:
                logger.error(f"Error getting market data for {symbol}: {e}")
                return None
        except Exception as e:
            logger.error(f"Fatal error in get_market_data for {symbol}: {e}")
            return None
    
    async def get_portfolio(self) -> List[Dict]:
        """Get current portfolio positions"""
        if not self.connected:
            await self.connect()
        
        try:
            positions = self.ib.positions()
            portfolio = []
            
            for position in positions:
                portfolio.append({
                    'symbol': position.contract.symbol,
                    'quantity': position.position,
                    'avg_cost': position.avgCost,
                    'market_value': position.marketValue
                })
            
            return portfolio
            
        except Exception as e:
            logger.error(f"Error getting portfolio: {e}")
            return []
    
    async def place_order(self, symbol: str, action: str, quantity: int, order_type: str = 'MKT') -> Optional[str]:
        """Place a trading order"""
        if not self.connected:
            await self.connect()
        
        try:
            contract = self.get_stock_contract(symbol)
            
            if action.upper() == 'BUY':
                order = MarketOrder('BUY', quantity)
            elif action.upper() == 'SELL':
                order = MarketOrder('SELL', quantity)
            else:
                raise ValueError(f"Invalid action: {action}")
            
            trade = self.ib.placeOrder(contract, order)
            self.ib.sleep(1)  # Wait for order to be processed
            
            if trade.orderStatus.status == 'Submitted':
                return trade.order.orderId
            else:
                logger.error(f"Order failed: {trade.orderStatus.status}")
                return None
                
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return None

    async def get_account_summary(self) -> Dict:
        """Get account summary including cash balance, net liquidation value, etc."""
        if not self.connected:
            logger.info(f"Not connected, attempting to connect...")
            await self.connect()
        
        try:
            # Get account details
            account = self.ib.managedAccounts()[0]  # Get the first account
            
            # Request account updates with timeout
            try:
                await asyncio.wait_for(self.ib.reqAccountUpdatesAsync(account), timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning("Account updates request timed out, continuing with available data")
            
            # Get portfolio
            portfolio = self.ib.portfolio()
            
            # Calculate total values
            total_value = sum(item.marketValue for item in portfolio if hasattr(item, 'marketValue'))
            unrealized_pnl = sum(item.unrealizedPNL for item in portfolio if hasattr(item, 'unrealizedPNL'))
            
            # Get account values with timeout
            try:
                values = await asyncio.wait_for(self.ib.accountSummaryAsync(), timeout=10.0)
            except asyncio.TimeoutError:
                logger.warning("Account summary request timed out, using cached values")
                # Use cached account values if available
                values = self.ib.accountValues()
                if not values:
                    # Return basic account info if no cached values
                    return {
                        'account': account,
                        'net_liquidation_value': 0.0,
                        'total_cash_value': 0.0,
                        'available_funds': 0.0,
                        'buying_power': 0.0,
                        'gross_position_value': total_value,
                        'realized_pnl': 0.0,
                        'unrealized_pnl': unrealized_pnl,
                        'maint_margin_req': 0.0,
                        'init_margin_req': 0.0,
                        'excess_liquidity': 0.0
                    }
            
            # Create summary dictionary
            summary_dict = {
                'account': account,
                'net_liquidation_value': 0.0,
                'total_cash_value': 0.0,
                'available_funds': 0.0,
                'buying_power': 0.0,
                'gross_position_value': total_value,
                'realized_pnl': 0.0,
                'unrealized_pnl': unrealized_pnl,
                'maint_margin_req': 0.0,
                'init_margin_req': 0.0,
                'excess_liquidity': 0.0
            }
            
            # Update values from account summary
            for v in values:
                if v.tag == 'NetLiquidation':
                    summary_dict['net_liquidation_value'] = float(v.value)
                elif v.tag == 'TotalCashValue':
                    summary_dict['total_cash_value'] = float(v.value)
                elif v.tag == 'AvailableFunds':
                    summary_dict['available_funds'] = float(v.value)
                elif v.tag == 'BuyingPower':
                    summary_dict['buying_power'] = float(v.value)
                elif v.tag == 'MaintMarginReq':
                    summary_dict['maint_margin_req'] = float(v.value)
                elif v.tag == 'InitMarginReq':
                    summary_dict['init_margin_req'] = float(v.value)
                elif v.tag == 'ExcessLiquidity':
                    summary_dict['excess_liquidity'] = float(v.value)
            
            logger.info(f"Account summary: {summary_dict}")
            return summary_dict
        except Exception as e:
            logger.error(f"Error getting account summary: {e}")
            return {}

    async def get_positions(self) -> List[Dict]:
        """Get detailed position information for all holdings"""
        if not self.connected:
            logger.info(f"Not connected, attempting to connect...")
            await self.connect()
        
        try:
            # Get account details
            account = self.ib.managedAccounts()[0]  # Get the first account
            
            # Request account updates to get fresh position data with timeout
            try:
                await asyncio.wait_for(self.ib.reqAccountUpdatesAsync(account), timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning("Account updates request timed out for positions, continuing with available data")
            
            # Get portfolio data
            portfolio = self.ib.portfolio()
            result = []
            
            for item in portfolio:
                contract = item.contract
                # Request market data for current price
                ticker = self.ib.reqMktData(contract)
                await asyncio.sleep(0.1)  # Small delay to allow market data to arrive
                
                position_data = {
                    'account': account,
                    'symbol': contract.symbol,
                    'exchange': contract.exchange,
                    'currency': contract.currency,
                    'position': item.position,  # Number of shares/contracts
                    'avg_cost': item.avgCost,
                    'market_price': item.marketPrice,
                    'market_value': item.marketValue,
                    'unrealized_pnl': item.unrealizedPNL,
                    'realized_pnl': item.realizedPNL,
                    'sec_type': contract.secType,  # Type of security (STK, OPT, FUT, etc.)
                    'multiplier': contract.multiplier,  # Contract multiplier for derivatives
                    'local_symbol': contract.localSymbol,  # Local exchange symbol
                }
                result.append(position_data)
            
            logger.info(f"Found {len(result)} positions")
            return result
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []

# Global IBKR service instance
ibkr_service = IBKRService() 