from typing import List, Optional
from decimal import Decimal
import structlog
from alpaca_trader.core.market import MarketService
from alpaca_trader.models.asset import Asset

logger = structlog.get_logger()

class MarketScreener:
    """Filters the market for tradeable candidates."""

    def __init__(self, market_service: MarketService):
        self.market = market_service

    def run_screen(self) -> List[Asset]:
        """
        Execute the screening process:
        1. Fetch all US Equities.
        2. Filter by Price ($2 - $20).
        3. Filter by Volume (> 500k).
        """
        logger.info("Starting market screen...")
        
        # 1. Fetch Universe
        all_assets = self.market.get_all_assets()
        tradable_symbols = [
            a.symbol for a in all_assets 
            if a.tradable and a.marginable
        ]
        logger.info("Universe size", count=len(tradable_symbols))

        # 2 & 3. Price & Liquidity Filter (using Alpaca Snapshots for speed)
        candidates: List[Asset] = []
        
        # Process in chunks of 500 to avoid URL length limits
        chunk_size = 500
        for i in range(0, len(tradable_symbols), chunk_size):
            chunk = tradable_symbols[i:i + chunk_size]
            try:
                snapshots = self.market.get_snapshots(chunk)
                
                for symbol, snapshot in snapshots.items():
                    # Latest Trade Price
                    if not snapshot.latest_trade:
                        continue
                        
                    price = snapshot.latest_trade.price
                    
                    if not snapshot.daily_bar:
                        continue
                        
                    volume = snapshot.daily_bar.volume
                    
                    # ---------------------------------------------
                    # ⚡ LEVEL 1 FILTER: Price $2-$20 & Vol Check
                    # ---------------------------------------------
                    if 2.0 <= price <= 20.0 and volume > 100_000:
                        candidates.append(Asset(
                            symbol=symbol,
                            exchange="Unknown",
                            price=Decimal(str(price)),
                            volume=int(volume)
                        ))
            except Exception as e:
                logger.error("Error processing chunk", error=str(e), chunk_index=i)

        logger.info("Candidates after Price/Vol filter", count=len(candidates))

        # 4. Market Cap Filter (Simplified/Skipped for MVP)
        final_list = self._filter_by_market_cap(candidates)
        
        logger.info("Final Screen Results", count=len(final_list))
        return final_list

    def _filter_by_market_cap(self, assets: List[Asset]) -> List[Asset]:
        """
        Placeholder for Market Cap filter.
        In MVP (Alpaca-only), we skip this or need a paid data subscription.
        Passing all candidates for now.
        """
        return assets
