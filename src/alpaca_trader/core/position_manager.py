from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field
import structlog
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, OrderSide, TimeInForce
from alpaca_trader.core.technicals import Technicals

logger = structlog.get_logger()

class TradeState(BaseModel):
    symbol: str
    entry_price: float
    entry_time: datetime
    qty: float
    max_price: float
    tier1_sold: bool = False
    is_active: bool = True

class PositionManager:
    """
    Manages the lifecycle of active trades:
    - Safety Nets (`stale_timer`, `hard_stop`)
    - Profit Taking (`tier1`, `runner`)
    - Emergency Exits
    """
    def __init__(self, trading_client: TradingClient, technicals: Technicals):
        self.client = trading_client
        self.tech = technicals
        self.trades: dict[str, TradeState] = {}

    def open_position(self, symbol: str, amount_usd: float = 1000.0) -> bool:
        """Enter a new position."""
        try:
            # Get current price for estimating qty (Alpaca calc handles this too but good for logs)
            quote = self.client.get_latest_quote(symbol) # Note: requires DataClient, using simple market order
            # Actually simpler: Use Notional amount
            
            req = MarketOrderRequest(
                symbol=symbol,
                notional=amount_usd,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.DAY
            )
            order = self.client.submit_order(req)
            logger.info("Entry Order Submitted", symbol=symbol, id=order.id)
            
            # We need the fill price. For MVP assuming immediate fill or polling.
            # IN PRODUCTION: Listen to trade updates via WebSocket.
            # HERE: We create a placeholder state. We'll update it on next tick/poll if position exists.
            
            # For simplicity in MVP sync flow, we'll verify position existence in the update loop.
            return True
        except Exception as e:
            logger.error("Failed to open position", symbol=symbol, error=str(e))
            return False

    def update_trades(self):
        """
        Main Loop: Check all active trades against rules.
        Should be called every minute.
        """
        # Sync with Alpaca Port
        alpaca_positions = {p.symbol: p for p in self.client.get_all_positions()}
        
        # Identify new fills we don't track yet
        for symbol, p in alpaca_positions.items():
            if symbol not in self.trades:
                # New trade detected! Initialize state
                self.trades[symbol] = TradeState(
                    symbol=symbol,
                    entry_price=float(p.avg_entry_price),
                    entry_time=datetime.now(), # Approximate if missed
                    qty=float(p.qty),
                    max_price=float(p.current_price)
                )
                logger.info("Tracking New Position", symbol=symbol, entry=p.avg_entry_price)

        # Process Logic
        for symbol, state in list(self.trades.items()):
            if not state.is_active:
                continue

            # API Position Data
            if symbol not in alpaca_positions:
                # Closed externally?
                state.is_active = False
                continue
                
            pos = alpaca_positions[symbol]
            current_price = float(pos.current_price)
            state.max_price = max(state.max_price, current_price)

            # ---------------------------
            # 1. Safety Nets
            # ---------------------------
            
            # A. Hard Stop Loss (-5%)
            if current_price < state.entry_price * 0.95:
                self._sell(symbol, 1.0, "Hard Stop Loss Hit")
                continue

            # B. Stale Timer (45 mins, needs > 1.5% profit)
            time_held = datetime.now() - state.entry_time
            profit_pct = (current_price - state.entry_price) / state.entry_price
            
            if time_held > timedelta(minutes=45) and profit_pct < 0.015:
                self._sell(symbol, 1.0, "Stale Timer: Dead Money")
                continue

            # ---------------------------
            # 2. Profit Taking
            # ---------------------------
            
            # A. Tier 1 (Sell 50% at +6.5%)
            if not state.tier1_sold and profit_pct >= 0.065:
                self._sell(symbol, 0.5, "Tier 1 Profit Take")
                state.tier1_sold = True
                continue

            # B. The Runner (Trailing Stop -3% from Max)
            if state.tier1_sold:
                drawdown = (state.max_price - current_price) / state.max_price
                if drawdown >= 0.03:
                    self._sell(symbol, 1.0, "Runner Trailing Stop Hit")
                    continue

            # ---------------------------
            # 3. Emergency Triggers
            # ---------------------------
            
            # RSI Overheat (> 85)
            rsi = self.tech.get_rsi(symbol)
            if rsi > 85:
                self._sell(symbol, 1.0, f"RSI Overheat: {rsi}")
                continue

            # Volume Exhaustion
            if self.tech.check_volume_divergence(symbol):
                self._sell(symbol, 1.0, "Volume Exhaustion Detected")
                continue

    def _sell(self, symbol: str, pct: float, reason: str):
        """Execute sell order."""
        try:
            state = self.trades.get(symbol)
            if not state: return
            
            # Calculate qty
            # Note: stored state.qty might be stale if we sold partial.
            # Better to fetch live pos qty.
            pos = self.client.get_position(symbol)
            current_qty = float(pos.qty)
            qty_to_sell = current_qty * pct
            
            if qty_to_sell < 1.0: # Fractional support or strict logic
                 # For MVP, if < 1 share and not fractional enabled fully, close all
                 # Assuming minimal fractional support
                 pass 

            logger.info("Selling", symbol=symbol, reason=reason, pct=pct)
            
            if pct >= 0.99:
                self.client.close_position(symbol)
                del self.trades[symbol]
            else:
                req = MarketOrderRequest(
                    symbol=symbol,
                    qty=qty_to_sell,
                    side=OrderSide.SELL,
                    time_in_force=TimeInForce.DAY
                )
                self.client.submit_order(req)
                
        except Exception as e:
            logger.error("Sell Failed", symbol=symbol, error=str(e))
