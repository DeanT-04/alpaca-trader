import pytest
from unittest.mock import MagicMock, call
from datetime import datetime, timedelta
from decimal import Decimal
from alpaca_trader.core.bot import AlpacaBot
from alpaca_trader.models.asset import Asset
from alpaca_trader.core.news import NewsArticle
from alpaca.trading.requests import MarketOrderRequest, OrderSide

# ----------------------------------------------------------------
# 🧪 MOCK FIXTURES (The "Simulated World")
# ----------------------------------------------------------------

@pytest.fixture
def mock_bot(mocker):
    """Creates a bot with all external clients mocked."""
    
    # Mock MarketService
    mocker.patch('alpaca_trader.core.market.StockHistoricalDataClient')
    mocker.patch('alpaca_trader.core.market.TradingClient') # This patches the class instantiation
    
    # We need to deeper mock the bot's internal services
    # because they instantiate their own clients.
    # Easiest way: Instantiate bot, then replace its components' clients.
    
    # BUT bot __init__ creates them. 
    # So we patch the Modules where they are imported.
    mocker.patch('alpaca_trader.core.bot.MarketService')
    mocker.patch('alpaca_trader.core.bot.NewsClient')
    mocker.patch('alpaca_trader.core.bot.BackgroundScheduler')
    
    bot = AlpacaBot()
    
    # Replace the mocks with nice MagicMocks we can control
    bot.market = MagicMock()
    bot.market.trading_client = MagicMock()
    bot.market.data_client = MagicMock()
    
    bot.news_client = MagicMock()
    
    # Override components to use these same mocks
    bot.screener.market = bot.market
    bot.pm.client = bot.market.trading_client
    bot.pm.tech.data_client = bot.market.data_client
    bot.tech.data_client = bot.market.data_client
    
    return bot

# ----------------------------------------------------------------
# 🎬 THE MIMIC TEST (End-to-End Flow)
# ----------------------------------------------------------------

def test_full_system_simulation(mock_bot):
    """
    Simultates the full lifecycle:
    1. Screener picks 'WXYZ' ($10).
    2. News finds 'WXYZ Earnings Beat'.
    3. Bot buys 'WXYZ'.
    4. Price goes up 7% -> Profit Take.
    5. Price crashes -> Trailing Stop.
    """
    symbol = "WXYZ"
    
    # ----------------------------------------
    # STEP 1: SCREENER SIMULATION
    # ----------------------------------------
    # Setup Screener to return our fake stock
    mock_bot.screener.run_screen = MagicMock(return_value=[
        Asset(symbol=symbol, exchange="NAS", price=Decimal("10.00"), volume=500000)
    ])
    
    # Run Watchlist Update
    mock_bot.update_watchlist()
    assert symbol in mock_bot.watchlist
    print(f"\n[1] Watchlist updated with {symbol}")

    # ----------------------------------------
    # STEP 2: NEWS & SIGNAL SIMULATION
    # ----------------------------------------
    # Mock News API returning a valid hit
    mock_item = MagicMock()
    mock_item.id = "news_123"
    mock_item.headline = "WXYZ Reports Massive Earnings Beat Amazing Excellent"
    mock_item.symbols = [symbol]
    mock_item.source = "Benzinga"
    mock_item.created_at = datetime.now()
    mock_item.summary = "EPS up 500% year over year. Wonderful performance. Fantastic."
    mock_item.url = "http://fake.url"
    
    mock_bot.news_client.get_news.return_value.news = [mock_item]
    
    # Mock Techs (RSI) to be safe (50)
    mock_bot.tech.get_rsi = MagicMock(return_value=50.0)
    
    # Run News Scan
    mock_bot.scan_news()
    
    # VERIFY BUY ORDER
    # Check if submit_order was called on the trading_client
    assert mock_bot.market.trading_client.submit_order.called
    args, kwargs = mock_bot.market.trading_client.submit_order.call_args
    request = args[0] if args else kwargs.get('order_data')
    
    assert request.symbol == symbol
    assert request.side == OrderSide.BUY
    print(f"[2] BUY Order verified for {symbol}")

    # ----------------------------------------
    # STEP 3: POSITION MANAGEMENT (Entry)
    # ----------------------------------------
    # Manually inject the trade state since we don't have a real broker to fill it
    # AND we mocked the client so it returned a mock order
    
    # Simulate the Bot identifying the new position
    # Mock get_all_positions to return our new position
    mock_position = MagicMock()
    mock_position.symbol = symbol
    mock_position.avg_entry_price = "10.00"
    mock_position.qty = "100"
    mock_position.current_price = "10.00"
    
    mock_bot.market.trading_client.get_all_positions.return_value = [mock_position]
    
    # Run PM Update Loop -> Should initialize state
    mock_bot.pm.update_trades()
    assert symbol in mock_bot.pm.trades
    print(f"[3] Position initialized in Manager")

    # ----------------------------------------
    # STEP 4: PROFIT TAKE SCENARIO (+7%)
    # ----------------------------------------
    # Price moves to $10.70 (+7%)
    mock_position.current_price = "10.70"
    # Mock get_position for the sell logic
    mock_bot.market.trading_client.get_position.return_value = mock_position
    
    # Reset order mock to check for new sell
    mock_bot.market.trading_client.submit_order.reset_mock()
    
    # Run PM Update Loop
    mock_bot.pm.update_trades()
    
    # Verify Sell 50%
    state = mock_bot.pm.trades[symbol]
    assert state.tier1_sold is True
    assert mock_bot.market.trading_client.submit_order.called
    print(f"[4] Tier 1 Profit Taken at $10.70")

    # ----------------------------------------
    # STEP 5: RUNNER TRAILING STOP SCENARIO
    # ----------------------------------------
    # Price pumps to $12.00 (New Max)
    mock_position.current_price = "12.00"
    mock_bot.pm.update_trades()
    assert mock_bot.pm.trades[symbol].max_price == 12.00
    
    # Price crashes to $11.50 ( < 11.64 which is 3% drop from 12)
    # 12 * 0.97 = 11.64. So 11.50 should trigger stop.
    mock_position.current_price = "11.50"
    
    # Reset mocks
    mock_bot.market.trading_client.submit_order.reset_mock()
    mock_bot.market.trading_client.close_position = MagicMock()
    
    # Run PM Update Loop
    mock_bot.pm.update_trades()
    
    # Verify Full Close
    # Since it's a 100% sell, we configured it to call close_position or sell 100%
    # In logic: if pct >= 0.99: client.close_position()
    assert mock_bot.market.trading_client.close_position.called
    # Position should be removed from local tracking
    assert symbol not in mock_bot.pm.trades
    print(f"[5] Runner Stopped out at $11.50")
