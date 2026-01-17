"""Alert condition checking and management."""
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from models import Card, PriceData, PriceAlert, AlertThresholds
from price_tracker import PriceTracker

logger = logging.getLogger(__name__)


class AlertSystem:
    """Checks price data against alert conditions."""

    def __init__(self, price_tracker: PriceTracker, thresholds: AlertThresholds):
        self.price_tracker = price_tracker
        self.thresholds = thresholds
        self.last_alert_times = {}  # Track when we last alerted for each card

    def check_alert_conditions(
        self,
        card: Card,
        current_price: PriceData,
        cooldown_hours: int = 6
    ) -> Optional[PriceAlert]:
        """
        Check if current price data triggers any alert conditions.

        Args:
            card: Card being checked
            current_price: Current price data
            cooldown_hours: Hours to wait before re-alerting for same card

        Returns:
            PriceAlert object if conditions met, None otherwise
        """
        # Check alert cooldown
        card_id = card.get_identifier()
        if card_id in self.last_alert_times:
            time_since_last = datetime.now() - self.last_alert_times[card_id]
            if time_since_last < timedelta(hours=cooldown_hours):
                logger.debug(f"Alert cooldown active for {card.name}")
                return None

        current = current_price.get_effective_price()
        if current is None:
            logger.warning(f"No valid price for {card.name}")
            return None

        alert_reasons = []

        # Check 1: Price below target
        if card.target_price and current <= card.target_price:
            alert_reasons.append(
                f"Price ${current:.2f} is at or below target ${card.target_price:.2f}"
            )

        # Check 2: Percentage drop within timeframe
        past_price_data = self.price_tracker.get_price_at_timeframe(
            card,
            self.thresholds.drop_timeframe_hours
        )

        if past_price_data:
            past_price = past_price_data.get_effective_price()
            if past_price:
                drop_percent = ((past_price - current) / past_price) * 100
                if drop_percent >= self.thresholds.price_drop_percent:
                    alert_reasons.append(
                        f"Price dropped {drop_percent:.1f}% "
                        f"(from ${past_price:.2f} to ${current:.2f}) "
                        f"in last {self.thresholds.drop_timeframe_hours} hours"
                    )

        # Check 3: At or below 30-day low
        thirty_day_low = self.price_tracker.get_30_day_low(card)
        if thirty_day_low and current <= thirty_day_low:
            alert_reasons.append(
                f"Price ${current:.2f} matches 30-day low ${thirty_day_low:.2f}"
            )

        # Check 4: Low inventory (scarcity signal)
        if current_price.listing_count > 0 and \
           current_price.listing_count <= self.thresholds.low_inventory_threshold:
            alert_reasons.append(
                f"Low inventory: only {current_price.listing_count} listings available"
            )

        # Anti-FOMO Check: Ignore if recent price spike
        if self._is_price_spike(card, current_price):
            logger.info(
                f"Ignoring alert for {card.name} due to recent price spike (anti-FOMO)"
            )
            return None

        # If any conditions met, create alert
        if alert_reasons:
            previous_price = self.price_tracker.get_latest_price(card)

            alert = PriceAlert(
                card=card,
                current_price=current_price,
                previous_price=previous_price if previous_price != current_price else None,
                alert_reasons=alert_reasons
            )

            # Update last alert time
            self.last_alert_times[card_id] = datetime.now()

            logger.info(f"Alert triggered for {card.name}: {len(alert_reasons)} conditions met")
            return alert

        return None

    def _is_price_spike(self, card: Card, current_price: PriceData) -> bool:
        """
        Check if there's been a recent suspicious price spike.

        Args:
            card: Card to check
            current_price: Current price data

        Returns:
            True if price spiked suspiciously, False otherwise
        """
        current = current_price.get_effective_price()
        if not current:
            return False

        # Get price from X hours ago
        past_price_data = self.price_tracker.get_price_at_timeframe(
            card,
            self.thresholds.spike_ignore_hours
        )

        if not past_price_data:
            return False

        past_price = past_price_data.get_effective_price()
        if not past_price or past_price == 0:
            return False

        # Calculate spike percentage
        spike_percent = ((current - past_price) / past_price) * 100

        if spike_percent >= self.thresholds.spike_ignore_percent:
            logger.warning(
                f"Price spike detected for {card.name}: "
                f"{spike_percent:.1f}% increase in {self.thresholds.spike_ignore_hours} hours"
            )
            return True

        return False

    def get_all_alerts(self, cards: List[Card], cooldown_hours: int = 6) -> List[PriceAlert]:
        """
        Check all cards and return list of alerts.

        Args:
            cards: List of cards to check
            cooldown_hours: Alert cooldown period

        Returns:
            List of PriceAlert objects
        """
        alerts = []

        for card in cards:
            if not card.enabled:
                continue

            # Get latest price from tracker
            latest_price = self.price_tracker.get_latest_price(card)
            if not latest_price:
                logger.debug(f"No price data available for {card.name}")
                continue

            # Check alert conditions
            alert = self.check_alert_conditions(card, latest_price, cooldown_hours)
            if alert:
                alerts.append(alert)

        return alerts
