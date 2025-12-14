from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict

class Asset(BaseModel):
    """Represents a tradeable asset with relevant metadata."""
    model_config = ConfigDict(frozen=True)

    symbol: str
    name: Optional[str] = None
    exchange: str
    price: Decimal
    volume: int
    market_cap: Optional[float] = None
    
    @property
    def is_valid_candidate(self) -> bool:
        """Check if asset meets basic validation criteria."""
        return (
            self.price > 0 
            and self.volume > 0
        )
