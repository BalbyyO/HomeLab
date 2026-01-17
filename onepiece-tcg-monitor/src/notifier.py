"""Discord notification system for price alerts."""
import logging
import requests
from typing import List
from datetime import datetime
from models import PriceAlert, Card, PriceData

logger = logging.getLogger(__name__)


class DiscordNotifier:
    """Sends price alerts via Discord webhook."""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.enabled = webhook_url and webhook_url != "YOUR_DISCORD_WEBHOOK_URL_HERE"

        if not self.enabled:
            logger.warning("Discord webhook URL not configured - notifications disabled")

    def send_alert(self, alert: PriceAlert) -> bool:
        """
        Send a single alert to Discord.

        Args:
            alert: PriceAlert object to send

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            logger.info(f"Would send alert for {alert.card.name} (webhook not configured)")
            return False

        try:
            embed = self._create_alert_embed(alert)
            payload = {
                "embeds": [embed]
            }

            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()

            logger.info(f"Alert sent to Discord for {alert.card.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to send Discord alert: {e}")
            return False

    def send_multiple_alerts(self, alerts: List[PriceAlert]) -> int:
        """
        Send multiple alerts to Discord.

        Args:
            alerts: List of PriceAlert objects

        Returns:
            Number of alerts sent successfully
        """
        if not alerts:
            return 0

        sent_count = 0
        for alert in alerts:
            if self.send_alert(alert):
                sent_count += 1

        return sent_count

    def send_daily_summary(self, cards: List[Card], price_data: List[PriceData]) -> bool:
        """
        Send a daily summary of all tracked cards.

        Args:
            cards: List of tracked cards
            price_data: Current price data for each card

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            return False

        try:
            embed = self._create_summary_embed(cards, price_data)
            payload = {
                "embeds": [embed]
            }

            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()

            logger.info("Daily summary sent to Discord")
            return True

        except Exception as e:
            logger.error(f"Failed to send daily summary: {e}")
            return False

    def _create_alert_embed(self, alert: PriceAlert) -> dict:
        """Create Discord embed for an alert."""
        card = alert.card
        current = alert.current_price.get_effective_price()

        # Determine color based on alert type
        # Green for good buying opportunity
        color = 0x00FF00  # Green

        # Build description with alert reasons
        description = "**Alert Conditions Met:**\n"
        for reason in alert.alert_reasons:
            description += f"• {reason}\n"

        # Add price change info if available
        if alert.previous_price:
            prev_price = alert.previous_price.get_effective_price()
            if prev_price and current:
                change = current - prev_price
                change_percent = (change / prev_price) * 100
                change_emoji = "📉" if change < 0 else "📈"
                description += f"\n{change_emoji} **Change:** ${change:+.2f} ({change_percent:+.1f}%)"

        # Build fields
        fields = [
            {
                "name": "Current Price",
                "value": f"${current:.2f}" if current else "N/A",
                "inline": True
            }
        ]

        if alert.current_price.market_price:
            fields.append({
                "name": "Market Price",
                "value": f"${alert.current_price.market_price:.2f}",
                "inline": True
            })

        if alert.current_price.lowest_price:
            fields.append({
                "name": "Lowest Listing",
                "value": f"${alert.current_price.lowest_price:.2f}",
                "inline": True
            })

        if alert.current_price.listing_count > 0:
            fields.append({
                "name": "Available Listings",
                "value": str(alert.current_price.listing_count),
                "inline": True
            })

        if card.target_price:
            fields.append({
                "name": "Your Target",
                "value": f"${card.target_price:.2f}",
                "inline": True
            })

        # Card details
        card_details = f"{card.set}"
        if card.number:
            card_details += f" #{card.number}"
        card_details += f" • {card.rarity} • {card.language}"

        embed = {
            "title": f"🎯 Price Alert: {card.name}",
            "description": description,
            "color": color,
            "fields": fields,
            "footer": {
                "text": card_details
            },
            "timestamp": alert.timestamp.isoformat()
        }

        # Add URL if available
        if alert.current_price.tcgplayer_url:
            embed["url"] = alert.current_price.tcgplayer_url

        return embed

    def _create_summary_embed(self, cards: List[Card], price_data: List[PriceData]) -> dict:
        """Create Discord embed for daily summary."""
        enabled_cards = [c for c in cards if c.enabled]

        description = f"Tracking {len(enabled_cards)} One Piece TCG cards"

        fields = []
        for i, card in enumerate(enabled_cards[:10]):  # Limit to 10 cards
            # Find matching price data
            card_id = card.get_identifier()
            price = next((pd for pd in price_data if pd.card_id == card_id), None)

            if price:
                current = price.get_effective_price()
                value = f"${current:.2f}" if current else "No data"
                if price.listing_count > 0:
                    value += f" • {price.listing_count} listings"
            else:
                value = "No recent data"

            card_name = f"{card.name} ({card.set})"
            fields.append({
                "name": card_name[:256],  # Discord field name limit
                "value": value,
                "inline": False
            })

        if len(enabled_cards) > 10:
            fields.append({
                "name": "...",
                "value": f"+ {len(enabled_cards) - 10} more cards",
                "inline": False
            })

        embed = {
            "title": "📊 Daily Price Summary",
            "description": description,
            "color": 0x3498db,  # Blue
            "fields": fields,
            "timestamp": datetime.now().isoformat(),
            "footer": {
                "text": "One Piece TCG Price Monitor"
            }
        }

        return embed

    def test_webhook(self) -> bool:
        """
        Test the Discord webhook with a simple message.

        Returns:
            True if webhook works, False otherwise
        """
        if not self.enabled:
            logger.warning("Cannot test webhook - URL not configured")
            return False

        try:
            payload = {
                "embeds": [{
                    "title": "✅ Webhook Test",
                    "description": "One Piece TCG Price Monitor is configured correctly!",
                    "color": 0x00FF00,
                    "timestamp": datetime.now().isoformat()
                }]
            }

            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()

            logger.info("Webhook test successful")
            return True

        except Exception as e:
            logger.error(f"Webhook test failed: {e}")
            return False
