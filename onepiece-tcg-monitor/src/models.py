"""Data models for TCG price monitoring."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class Card:
    """Represents a One Piece TCG card to track."""
    name: str
    set: str
    rarity: str
    condition: str = "Near Mint"
    language: str = "English"
    number: Optional[str] = None
    target_price: Optional[float] = None
    enabled: bool = True

    def get_identifier(self) -> str:
        """Get unique identifier for this card."""
        parts = [self.name, self.set, self.rarity, self.language]
        if self.number:
            parts.insert(2, self.number)
        return "_".join(p.replace(" ", "_") for p in parts)


@dataclass
class PriceData:
    """Represents price data for a card at a specific time."""
    card_id: str
    timestamp: datetime
    market_price: Optional[float] = None
    lowest_price: Optional[float] = None
    listing_count: int = 0
    tcgplayer_url: Optional[str] = None

    def get_effective_price(self) -> Optional[float]:
        """Get the most relevant price (prefer market_price)."""
        return self.market_price or self.lowest_price


@dataclass
class PriceAlert:
    """Represents a price alert triggered for a card."""
    card: Card
    current_price: PriceData
    previous_price: Optional[PriceData] = None
    alert_reasons: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    def get_price_change_percent(self) -> Optional[float]:
        """Calculate percentage change from previous price."""
        if not self.previous_price:
            return None

        current = self.current_price.get_effective_price()
        previous = self.previous_price.get_effective_price()

        if not current or not previous or previous == 0:
            return None

        return ((current - previous) / previous) * 100


@dataclass
class AlertThresholds:
    """Alert threshold configuration."""
    price_drop_percent: float = 15.0
    drop_timeframe_hours: int = 24
    low_inventory_threshold: int = 5
    spike_ignore_percent: float = 30.0
    spike_ignore_hours: int = 6
