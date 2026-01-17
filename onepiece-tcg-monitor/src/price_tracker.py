"""Price tracking and historical data management."""
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from models import Card, PriceData

logger = logging.getLogger(__name__)


class PriceTracker:
    """Manages historical price data for tracked cards."""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.price_history: Dict[str, List[PriceData]] = {}

    def get_history_file(self, card_id: str) -> Path:
        """Get the history file path for a card."""
        return self.data_dir / f"{card_id}_history.json"

    def load_history(self, card: Card) -> List[PriceData]:
        """
        Load price history for a card from disk.

        Args:
            card: Card to load history for

        Returns:
            List of PriceData objects, newest first
        """
        card_id = card.get_identifier()
        history_file = self.get_history_file(card_id)

        if not history_file.exists():
            return []

        try:
            with open(history_file, 'r') as f:
                data = json.load(f)

            history = []
            for item in data:
                price_data = PriceData(
                    card_id=item['card_id'],
                    timestamp=datetime.fromisoformat(item['timestamp']),
                    market_price=item.get('market_price'),
                    lowest_price=item.get('lowest_price'),
                    listing_count=item.get('listing_count', 0),
                    tcgplayer_url=item.get('tcgplayer_url')
                )
                history.append(price_data)

            # Sort by timestamp, newest first
            history.sort(key=lambda x: x.timestamp, reverse=True)
            self.price_history[card_id] = history

            logger.info(f"Loaded {len(history)} price records for {card.name}")
            return history

        except Exception as e:
            logger.error(f"Error loading history for {card.name}: {e}")
            return []

    def save_price_data(self, price_data: PriceData):
        """
        Save new price data for a card.

        Args:
            price_data: PriceData object to save
        """
        try:
            # Load existing history
            history_file = self.get_history_file(price_data.card_id)

            if history_file.exists():
                with open(history_file, 'r') as f:
                    data = json.load(f)
            else:
                data = []

            # Add new price data
            new_entry = {
                'card_id': price_data.card_id,
                'timestamp': price_data.timestamp.isoformat(),
                'market_price': price_data.market_price,
                'lowest_price': price_data.lowest_price,
                'listing_count': price_data.listing_count,
                'tcgplayer_url': price_data.tcgplayer_url
            }
            data.append(new_entry)

            # Keep only last 90 days of data to prevent files from growing too large
            cutoff_date = datetime.now() - timedelta(days=90)
            data = [
                entry for entry in data
                if datetime.fromisoformat(entry['timestamp']) > cutoff_date
            ]

            # Save back to file
            with open(history_file, 'w') as f:
                json.dump(data, f, indent=2)

            # Update in-memory cache
            if price_data.card_id not in self.price_history:
                self.price_history[price_data.card_id] = []
            self.price_history[price_data.card_id].insert(0, price_data)

            logger.debug(f"Saved price data for {price_data.card_id}")

        except Exception as e:
            logger.error(f"Error saving price data: {e}")

    def get_latest_price(self, card: Card) -> Optional[PriceData]:
        """
        Get the most recent price data for a card.

        Args:
            card: Card to get latest price for

        Returns:
            Latest PriceData object, or None if no history
        """
        card_id = card.get_identifier()

        # Check in-memory cache first
        if card_id in self.price_history and self.price_history[card_id]:
            return self.price_history[card_id][0]

        # Load from disk
        history = self.load_history(card)
        return history[0] if history else None

    def get_price_at_timeframe(self, card: Card, hours_ago: int) -> Optional[PriceData]:
        """
        Get price data from X hours ago.

        Args:
            card: Card to get price for
            hours_ago: Number of hours in the past

        Returns:
            PriceData closest to the specified time, or None
        """
        card_id = card.get_identifier()

        if card_id not in self.price_history:
            self.load_history(card)

        if card_id not in self.price_history or not self.price_history[card_id]:
            return None

        target_time = datetime.now() - timedelta(hours=hours_ago)
        history = self.price_history[card_id]

        # Find closest price data to target time
        closest = min(
            history,
            key=lambda x: abs((x.timestamp - target_time).total_seconds())
        )

        return closest

    def get_30_day_low(self, card: Card) -> Optional[float]:
        """
        Get the lowest price in the last 30 days.

        Args:
            card: Card to check

        Returns:
            Lowest price as float, or None if no data
        """
        card_id = card.get_identifier()

        if card_id not in self.price_history:
            self.load_history(card)

        if card_id not in self.price_history or not self.price_history[card_id]:
            return None

        cutoff_date = datetime.now() - timedelta(days=30)
        recent_prices = [
            pd.get_effective_price()
            for pd in self.price_history[card_id]
            if pd.timestamp > cutoff_date and pd.get_effective_price() is not None
        ]

        return min(recent_prices) if recent_prices else None

    def get_highest_price_in_period(self, card: Card, hours: int) -> Optional[float]:
        """
        Get the highest price within a time period.

        Args:
            card: Card to check
            hours: Number of hours to look back

        Returns:
            Highest price as float, or None if no data
        """
        card_id = card.get_identifier()

        if card_id not in self.price_history:
            self.load_history(card)

        if card_id not in self.price_history or not self.price_history[card_id]:
            return None

        cutoff_date = datetime.now() - timedelta(hours=hours)
        recent_prices = [
            pd.get_effective_price()
            for pd in self.price_history[card_id]
            if pd.timestamp > cutoff_date and pd.get_effective_price() is not None
        ]

        return max(recent_prices) if recent_prices else None
