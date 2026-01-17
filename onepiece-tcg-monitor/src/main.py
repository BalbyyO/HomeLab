"""
One Piece TCG Price Monitor
Main entry point with scheduling and orchestration.
"""
import logging
import sys
import yaml
from pathlib import Path
from datetime import datetime, time as dt_time
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from models import Card, AlertThresholds
from scraper import TCGPlayerScraper
from price_tracker import PriceTracker
from alert_system import AlertSystem
from notifier import DiscordNotifier


# Setup logging
def setup_logging(config: dict):
    """Configure logging based on config."""
    log_config = config.get('logging', {})
    log_level = getattr(logging, log_config.get('level', 'INFO'))

    handlers = [logging.StreamHandler(sys.stdout)]

    if log_config.get('log_to_file', True):
        log_file = log_config.get('log_file', 'logs/monitor.log')
        Path(log_file).parent.mkdir(exist_ok=True)
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )


class PriceMonitor:
    """Main price monitoring orchestrator."""

    def __init__(self, config_path: str = "config.yaml"):
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        # Setup logging
        setup_logging(self.config)
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.scraper = TCGPlayerScraper()
        self.price_tracker = PriceTracker(data_dir="data")

        # Load alert thresholds
        threshold_config = self.config.get('global_thresholds', {})
        self.thresholds = AlertThresholds(
            price_drop_percent=threshold_config.get('price_drop_percent', 15.0),
            drop_timeframe_hours=threshold_config.get('drop_timeframe_hours', 24),
            low_inventory_threshold=threshold_config.get('low_inventory_threshold', 5),
            spike_ignore_percent=threshold_config.get('spike_ignore_percent', 30.0),
            spike_ignore_hours=threshold_config.get('spike_ignore_hours', 6)
        )

        self.alert_system = AlertSystem(self.price_tracker, self.thresholds)

        # Initialize Discord notifier
        webhook_url = self.config.get('discord_webhook_url', '')
        self.notifier = DiscordNotifier(webhook_url)

        # Load cards to track
        self.cards = self._load_cards()

        self.logger.info(f"Price Monitor initialized with {len(self.cards)} cards")

    def _load_cards(self) -> list[Card]:
        """Load cards from configuration."""
        cards = []
        card_configs = self.config.get('cards', [])

        for card_config in card_configs:
            card = Card(
                name=card_config['name'],
                set=card_config['set'],
                rarity=card_config['rarity'],
                condition=card_config.get('condition', 'Near Mint'),
                language=card_config.get('language', 'English'),
                number=card_config.get('number'),
                target_price=card_config.get('target_price'),
                enabled=card_config.get('enabled', True)
            )
            cards.append(card)

            # Load historical data
            self.price_tracker.load_history(card)

        return cards

    def check_prices(self):
        """Main price checking routine."""
        self.logger.info("=" * 60)
        self.logger.info("Starting price check cycle")
        self.logger.info("=" * 60)

        alerts_triggered = []

        for card in self.cards:
            if not card.enabled:
                self.logger.debug(f"Skipping disabled card: {card.name}")
                continue

            try:
                self.logger.info(f"Checking price for {card.name} ({card.set})")

                # Fetch current price
                price_data = self.scraper.get_price_data(card)

                if not price_data:
                    self.logger.warning(f"Could not fetch price for {card.name}")
                    continue

                # Save price data
                self.price_tracker.save_price_data(price_data)

                current_price = price_data.get_effective_price()
                self.logger.info(
                    f"  └─ Current price: ${current_price:.2f} "
                    f"({price_data.listing_count} listings)"
                )

                # Check alert conditions
                cooldown = self.config.get('notifications', {}).get('alert_cooldown_hours', 6)
                alert = self.alert_system.check_alert_conditions(card, price_data, cooldown)

                if alert:
                    alerts_triggered.append(alert)
                    self.logger.info(f"  └─ ⚠️  ALERT TRIGGERED! {len(alert.alert_reasons)} conditions met")

            except Exception as e:
                self.logger.error(f"Error checking {card.name}: {e}", exc_info=True)

        # Send alerts
        if alerts_triggered:
            self.logger.info(f"\nSending {len(alerts_triggered)} alert(s) to Discord...")
            sent = self.notifier.send_multiple_alerts(alerts_triggered)
            self.logger.info(f"Sent {sent}/{len(alerts_triggered)} alerts successfully")
        else:
            self.logger.info("\nNo alerts triggered this cycle")

        self.logger.info("=" * 60)
        self.logger.info("Price check cycle complete\n")

    def send_daily_summary(self):
        """Send daily summary of all tracked cards."""
        self.logger.info("Generating daily summary...")

        # Get latest price data for all enabled cards
        price_data = []
        for card in self.cards:
            if card.enabled:
                latest = self.price_tracker.get_latest_price(card)
                if latest:
                    price_data.append(latest)

        # Send summary
        self.notifier.send_daily_summary(self.cards, price_data)
        self.logger.info("Daily summary sent")

    def test_notifications(self):
        """Test Discord webhook configuration."""
        self.logger.info("Testing Discord webhook...")
        if self.notifier.test_webhook():
            self.logger.info("✅ Discord webhook is working!")
        else:
            self.logger.error("❌ Discord webhook test failed")

    def run_once(self):
        """Run a single price check cycle and exit."""
        self.logger.info("Running one-time price check...")
        self.check_prices()
        self.logger.info("One-time check complete")

    def run_scheduler(self):
        """Run the scheduler for continuous monitoring."""
        scheduler = BlockingScheduler()

        # Schedule price checks
        check_interval = self.config.get('check_interval_minutes', 60)
        scheduler.add_job(
            self.check_prices,
            'interval',
            minutes=check_interval,
            id='price_check',
            name='Price Check',
            next_run_time=datetime.now()  # Run immediately on start
        )
        self.logger.info(f"Scheduled price checks every {check_interval} minutes")

        # Schedule daily summary if enabled
        notification_config = self.config.get('notifications', {})
        if notification_config.get('daily_summary', True):
            summary_hour = notification_config.get('daily_summary_hour', 20)
            trigger = CronTrigger(hour=summary_hour, minute=0)
            scheduler.add_job(
                self.send_daily_summary,
                trigger,
                id='daily_summary',
                name='Daily Summary'
            )
            self.logger.info(f"Scheduled daily summary at {summary_hour}:00")

        try:
            self.logger.info("\n" + "=" * 60)
            self.logger.info("🚀 One Piece TCG Price Monitor Started")
            self.logger.info("=" * 60)
            self.logger.info(f"Tracking {len([c for c in self.cards if c.enabled])} cards")
            self.logger.info(f"Check interval: {check_interval} minutes")
            self.logger.info("Press Ctrl+C to stop\n")

            scheduler.start()

        except (KeyboardInterrupt, SystemExit):
            self.logger.info("\n" + "=" * 60)
            self.logger.info("Shutting down Price Monitor...")
            self.logger.info("=" * 60)
            scheduler.shutdown()


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='One Piece TCG Price Monitor')
    parser.add_argument(
        '--config',
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test Discord webhook and exit'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run once and exit (no scheduling)'
    )

    args = parser.parse_args()

    monitor = PriceMonitor(config_path=args.config)

    if args.test:
        monitor.test_notifications()
    elif args.once:
        monitor.run_once()
    else:
        monitor.run_scheduler()


if __name__ == '__main__':
    main()
