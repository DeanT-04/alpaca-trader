import time
import asyncio
from datetime import datetime, timedelta
from typing import List, Set
import structlog
from apscheduler.schedulers.background import BackgroundScheduler
from alpaca.data.historical import NewsClient
from alpaca.data.requests import NewsRequest

from alpaca_trader.config.settings import settings
from alpaca_trader.core.market import MarketService
from alpaca_trader.core.screener import MarketScreener
from alpaca_trader.core.news import NewsEngine, NewsArticle
from alpaca_trader.core.position_manager import PositionManager
from alpaca_trader.core.technicals import Technicals

logger = structlog.get_logger()

class AlpacaBot:
    """
    Main Trading Bot Orchestrator.
    """
    def __init__(self):
        self.market = MarketService()
        self.screener = MarketScreener(self.market)
        self.news_engine = NewsEngine()
        self.tech = Technicals(self.market.data_client)
        self.pm = PositionManager(self.market.trading_client, self.tech)
        
        self.news_client = NewsClient(
            api_key=settings.alpaca_api_key,
            secret_key=settings.alpaca_secret_key
        )
        
        self.scheduler = BackgroundScheduler()
        self.watchlist: Set[str] = set()
        self.last_news_poll = datetime.now() - timedelta(minutes=30) 

    def start(self):
        """Start the bot loops."""
        logger.info("Starting Alpaca Bot...")
        
        # 1. Initial Screen
        self.update_watchlist()
        
        # 2. Schedule Tasks
        self.scheduler.add_job(self.update_watchlist, 'interval', minutes=60)
        self.scheduler.add_job(self.pm.update_trades, 'interval', seconds=60)
        self.scheduler.add_job(self.scan_news, 'interval', minutes=2)
        
        self.scheduler.start()
        
        # Keep alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.scheduler.shutdown()
            logger.info("Bot Stopped")

    def update_watchlist(self):
        """Run screener and update valid candidates."""
        logger.info("Updating Watchlist...")
        try:
            assets = self.screener.run_screen()
            self.watchlist = {a.symbol for a in assets}
            logger.info("Watchlist Updated", count=len(self.watchlist), top_5=list(self.watchlist)[:5])
        except Exception as e:
            logger.error("Screener failed", error=str(e))

    def scan_news(self):
        """Poll for new news articles on watchlist symbols."""
        if not self.watchlist:
            return

        logger.debug("Scanning for news...")
        # Poll news for watchlist symbols
        # Note: API limit on symbols list len is usually 50?? check docs.
        # We'll query ALL news and filter in memory if list is too big, 
        # OR chunk updates. For MVP, querying recent 'all' news and filtering is safer.
        
        try:
            req = NewsRequest(
                limit=50,
                start=self.last_news_poll,
                include_content=True # Need partial content for keywords?
                # symbols=list(self.watchlist) # Optional: filter server side
            )
            data = self.news_client.get_news(req)
            self.last_news_poll = datetime.now() # Reset high watermark

            # Robustly fetch news list from the response object
            news_items = []
            
            # Case 1: Standard Pydantic model with .news
            if hasattr(data, 'news'):
                news_items = data.news
            # Case 2: Nested data attribute (observed in debug: response.data -> dict -> list)
            elif hasattr(data, 'data'):
                inner_data = data.data
                if isinstance(inner_data, dict):
                    news_items = inner_data.get('news', [])
                elif hasattr(inner_data, 'news'):
                     news_items = inner_data.news
            # Case 3: It IS the list (or iterable directly)
            elif isinstance(data, list):
                news_items = data

            if not news_items:
                return

            for item in news_items:
                # Helper to access fields whether item is dict or object
                def get_field(obj, field, default=None):
                    if isinstance(obj, dict):
                        return obj.get(field, default)
                    return getattr(obj, field, default)

                # Convert to our clean model
                # ID might be integer
                raw_id = get_field(item, 'id')
                raw_symbols = get_field(item, 'symbols', [])
                
                article = NewsArticle(
                    id=str(raw_id),
                    headline=get_field(item, 'headline', 'No Headline'),
                    symbol=raw_symbols[0] if raw_symbols else "UNKNOWN", 
                    source=get_field(item, 'source', 'Unknown'),
                    created_at=get_field(item, 'created_at', datetime.now()),
                    summary=get_field(item, 'summary', ''),
                    url=get_field(item, 'url')
                )
                
                # Check Watchlist
                # News API often returns multiple symbols. 
                # We check if ANY of the article's symbols are in our watchlist.
                # Use raw_symbols which we already extracted safely
                relevant_symbols = [s for s in raw_symbols if s in self.watchlist]
                if not relevant_symbols:
                    continue

                # Process
                valid_article = self.news_engine.process_article(article)
                
                if valid_article:
                    logger.info("🔥 Valid Signal Detected!", symbol=valid_article.symbol, headline=valid_article.headline)
                    self.execute_signal(valid_article.symbol)

        except Exception as e:
            logger.error("News Poll Failed", error=str(e))

    def execute_signal(self, symbol: str):
        """Execute buy on valid signal."""
        # 1. Final Tech Check (Trend Up?)
        # Simple VWAP or MA check?
        # MVP: Just check if RSI is not Overbought (>70) already before buying
        rsi = self.tech.get_rsi(symbol)
        if rsi > 70:
            logger.warning("Signal Skipped: RSI too high", symbol=symbol, rsi=rsi)
            return

        logger.info("Executing Buy", symbol=symbol)
        self.pm.open_position(symbol)
