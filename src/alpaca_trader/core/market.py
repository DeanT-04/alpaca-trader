from typing import List, Dict, Optional
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetAssetsRequest
from alpaca.trading.enums import AssetClass, AssetStatus
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest, StockSnapshotRequest
from alpaca_trader.config.settings import settings
import structlog

logger = structlog.get_logger()

class MarketService:
    """Core service for interacting with Alpaca Markets."""

    def __init__(self):
        self.trading_client = TradingClient(
            api_key=settings.alpaca_api_key,
            secret_key=settings.alpaca_secret_key,
            paper=True # Always default to paper for safety
        )
        self.data_client = StockHistoricalDataClient(
            api_key=settings.alpaca_api_key,
            secret_key=settings.alpaca_secret_key
        )
    
    def get_clock(self):
        return self.trading_client.get_clock()

    def get_all_assets(self, asset_class: AssetClass = AssetClass.US_EQUITY):
        """Fetch all active assets from Alpaca."""
        req = GetAssetsRequest(
            status=AssetStatus.ACTIVE,
            asset_class=asset_class
        )
        return self.trading_client.get_all_assets(req)

    def get_snapshots(self, symbols: List[str]) -> Dict:
        """Get latest trade, quote, and minute bar data for a list of symbols."""
        if not symbols:
            return {}
            
        request_params = StockSnapshotRequest(symbol_or_symbols=symbols)
        return self.data_client.get_stock_snapshot(request_params)
