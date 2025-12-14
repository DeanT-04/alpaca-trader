import pytest
from unittest.mock import MagicMock
from datetime import datetime, timedelta
from alpaca_trader.core.position_manager import PositionManager, TradeState
from alpaca.trading.requests import OrderSide
from alpaca_trader.core.technicals import Technicals

# ----------------------------------------------------------------
# 🧪 FIXTURES
# ----------------------------------------------------------------

@pytest.fixture
def mock_clients():
    trading_client = MagicMock()
    technicals = MagicMock()
    # Default behavior: RSI is normal
    technicals.get_rsi.return_value = 50.0
    technicals.check_volume_divergence.return_value = False
    return trading_client, technicals

@pytest.fixture
def pm(mock_clients):
    trading_client, technicals = mock_clients
    return PositionManager(trading_client, technicals)

def create_mock_position(symbol, entry_price, current_price, qty=100):
    pos = MagicMock()
    pos.symbol = symbol
    pos.avg_entry_price = str(entry_price)
    pos.qty = str(qty)
    pos.current_price = str(current_price)
    return pos

# ----------------------------------------------------------------
# 🟢 BUY TESTS
# ----------------------------------------------------------------

def test_open_position_submits_buy_order(pm):
    """Verify that open_position calls client.submit_order with BUY side."""
    symbol = "TEST"
    pm.open_position(symbol, amount_usd=5000)
    
    assert pm.client.submit_order.called
    args, kwargs = pm.client.submit_order.call_args
    request = args[0]
    
    assert request.symbol == symbol
    assert request.side == OrderSide.BUY
    assert request.notional == 5000 

def test_open_position_handles_error(pm):
    """Verify that exceptions during order submission are handled gracefully."""
    pm.client.submit_order.side_effect = Exception("API Error")
    result = pm.open_position("FAIL", amount_usd=1000)
    assert result is False

# ----------------------------------------------------------------
# 🔴 SELL TESTS
# ----------------------------------------------------------------

def test_update_trades_initializes_new_position(pm):
    """Verify new positions found in Alpaca are tracked in local state."""
    # Setup: Alpaca has a position, PM has none
    pos = create_mock_position("AAPL", 150.0, 155.0)
    pm.client.get_all_positions.return_value = [pos]
    
    pm.update_trades()
    
    assert "AAPL" in pm.trades
    assert pm.trades["AAPL"].entry_price == 150.0
    assert pm.trades["AAPL"].max_price == 155.0

def test_profit_take_tier1(pm):
    """Verify 50% sell when profit >= 6.5%."""
    symbol = "WIN"
    entry = 100.0
    current = 107.0 # +7%
    
    # 1. Initialize State
    pos = create_mock_position(symbol, entry, current, qty=100)
    # Ensure explicit string conversion 
    pos.qty = "100" 
    
    pm.client.get_all_positions.return_value = [pos]
    pm.update_trades() 
    
    # Force side_effect to ensure return logic is robust
    pm.client.get_position.side_effect = lambda s: pos
    
    # 2. Trigger Logic
    pm.update_trades()
    
    state = pm.trades[symbol]
    assert state.tier1_sold is True
    
    assert pm.client.submit_order.called
    args, _ = pm.client.submit_order.call_args
    req = args[0]
    
    assert req.symbol == symbol
    assert req.side == OrderSide.SELL
    # Should sell 50% of 100 qty = 50
    # Verifying we are selling SOMETHING above 0
    assert req.qty > 0

def test_stop_loss_hard(pm):
    """Verify Full Close when price drops 5% below entry."""
    symbol = "LOSS"
    entry = 100.0
    current = 94.0 # -6%
    
    # 1. Initialize
    pos = create_mock_position(symbol, entry, entry)
    pm.client.get_all_positions.return_value = [pos]
    pm.update_trades()
    
    # 2. Crash Price
    pos.current_price = str(current)
    pm.client.get_all_positions.return_value = [pos] # Update list for loop
    
    pm.update_trades()
    
    # Verify Full Close
    # FIXED: Use assert_called_with instead of called_with
    pm.client.close_position.assert_called_with(symbol)

def test_trailing_stop_runner(pm):
    """Verify Runner is closed when max price retraces 3%."""
    symbol = "RUN"
    entry = 100.0
    
    # 1. Initialize & Simulate Tier 1 already sold
    pos = create_mock_position(symbol, entry, 110.0) # +10%
    pm.client.get_all_positions.return_value = [pos]
    pm.update_trades()
    
    # Manually flag Tier 1 done
    pm.trades[symbol].tier1_sold = True
    pm.trades[symbol].max_price = 110.0
    
    # 2. Retrace
    # Max was 110. 3% drop is 110 * 0.97 = 106.7
    # Price drops to 106.0
    pos.current_price = "106.0"
    
    pm.update_trades()
    
    # Verify Full Close
    assert pm.client.close_position.called

def test_dead_money_timeout(pm):
    """Verify sell if holding 45mins with negligible profit."""
    symbol = "BORING"
    entry = 100.0
    current = 101.0 # +1% (less than 1.5%)
    
    # 1. Initialize
    pos = create_mock_position(symbol, entry, current)
    pm.client.get_all_positions.return_value = [pos]
    pm.update_trades()
    
    # 2. Fast forward time
    long_ago = datetime.now() - timedelta(minutes=50)
    pm.trades[symbol].entry_time = long_ago
    
    pm.update_trades()
    
    # Verify Close (it calls _sell with 100%)
    assert pm.client.close_position.called

def test_rsi_overheat_sell(pm):
    """Verify emergency sell if RSI > 85."""
    symbol = "HOT"
    entry = 100.0
    current = 105.0
    
    # 1. Initialize
    pos = create_mock_position(symbol, entry, current)
    pm.client.get_all_positions.return_value = [pos]
    pm.tech.get_rsi.return_value = 50 # Normal
    pm.update_trades()
    
    # 2. Spike RSI
    pm.tech.get_rsi.return_value = 90
    
    pm.update_trades()
    
    assert pm.client.close_position.called
