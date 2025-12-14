import pandas as pd
import pandas_ta as ta
from typing import List
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta
from alpaca_trader.config.settings import settings

class Technicals:
    """Helper for technical analysis calculations."""

    def __init__(self, data_client: StockHistoricalDataClient):
        self.data_client = data_client

    def get_rsi(self, symbol: str, timeframe=TimeFrame.Minute, length: int = 14) -> float:
        """Calculate latest RSI."""
        try:
            # Fetch enough bars for RSI calculation (14 + buffer)
            # Getting last 100 bars to be safe
            req = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=timeframe,
                start=datetime.now() - timedelta(days=2), # small window for 5m/1m bars
                limit=100
            )
            
            bars = self.data_client.get_stock_bars(req)
            if not bars.data:
                return 50.0 # Neural default if no data
                
            df = bars.df
            if df.empty or len(df) < length:
                return 50.0
                
            # Reseting index to ensure simple integer index if multi-index
            if isinstance(df.index, pd.MultiIndex):
                df = df.reset_index()

            # Calculate RSI
            rsi_series = ta.rsi(df['close'], length=length)
            if rsi_series is None or rsi_series.empty:
                return 50.0
                
            return float(rsi_series.iloc[-1])
        except Exception:
            return 50.0

    def check_volume_divergence(self, symbol: str) -> bool:
        """
        Check for volume exhaustion: New High in Price but Lower Volume.
        Simple logic: Compare last candle to previous candle.
        """
        try:
            req = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Minute,
                start=datetime.now() - timedelta(days=1), # REQUIRED PARAM
                limit=5
            )
            bars = self.data_client.get_stock_bars(req)
            if not bars.data:
                return False
                
            df = bars.df
            if isinstance(df.index, pd.MultiIndex):
                df = df.reset_index()
                
            if len(df) < 2:
                return False
                
            curr = df.iloc[-1]
            prev = df.iloc[-2]
            
            # New High (in close) with Lower Volume
            if curr['close'] > prev['close'] and curr['volume'] < prev['volume']:
                return True
                
            return False
        except Exception:
            return False
