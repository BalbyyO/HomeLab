# One Piece TCG Price Monitor

An automated price monitoring and alert system for One Piece Trading Card Game (TCG) singles listed on TCGplayer.com. Get notified when cards meet your defined buy conditions based on price drops, trends, and availability.

## Features

- **Automated Price Tracking**: Monitors TCGplayer listings every hour (configurable)
- **Smart Alerts**: Get notified when:
  - Price drops below your target
  - Price drops by X% within a timeframe
  - Price reaches 30-day low
  - Inventory falls below threshold (scarcity signal)
- **Anti-FOMO Protection**: Ignores suspicious price spikes to avoid buyout alerts
- **Discord Notifications**: Rich embedded alerts sent directly to Discord
- **Historical Data**: Tracks price history for trend analysis
- **Docker Support**: Easy deployment as a containerized service

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Discord webhook URL (optional but recommended)

### 1. Get Your Discord Webhook URL

1. Open Discord and go to your server
2. Go to Server Settings → Integrations → Webhooks
3. Click "New Webhook" or edit an existing one
4. Copy the webhook URL

### 2. Configure Your Cards and Settings

Edit `config.yaml`:

```yaml
# Add your Discord webhook URL
discord_webhook_url: "https://discord.com/api/webhooks/YOUR_WEBHOOK_HERE"

# Add cards to track
cards:
  - name: "Monkey D. Luffy"
    set: "OP-05"
    number: "119"
    rarity: "Secret Rare"
    condition: "Near Mint"
    language: "English"
    target_price: 150.00
    enabled: true

  - name: "Trafalgar Law"
    set: "ST-10"
    rarity: "Super Rare"
    target_price: 25.00
    enabled: true
```

### 3. Run with Docker

```bash
# Build and start the container
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the monitor
docker-compose down
```

The monitor will now run in the background and check prices every hour.

## Configuration Guide

### Card Configuration

Each card entry supports these fields:

```yaml
- name: "Card Name"          # Required: Full card name
  set: "OP-01"               # Required: Set code
  number: "001"              # Optional: Card number in set
  rarity: "Secret Rare"      # Required: Card rarity
  condition: "Near Mint"     # Optional: Default "Near Mint"
  language: "English"        # Optional: "English" or "Japanese"
  target_price: 50.00        # Optional: Alert when below this price
  enabled: true              # Optional: Enable/disable tracking
```

### Alert Thresholds

Global thresholds (can be customized per card):

```yaml
global_thresholds:
  # Alert when price drops by this percentage
  price_drop_percent: 15

  # Within this timeframe (hours)
  drop_timeframe_hours: 24

  # Alert when listings fall below this number
  low_inventory_threshold: 5

  # Anti-FOMO: Ignore if price spikes this much
  spike_ignore_percent: 30

  # Within this timeframe (hours)
  spike_ignore_hours: 6
```

### Check Frequency

```yaml
# How often to check prices (in minutes)
check_interval_minutes: 60  # Default: 1 hour
```

Recommended values:
- `15`: Every 15 minutes (more responsive, higher request rate)
- `60`: Every hour (balanced, recommended)
- `180`: Every 3 hours (conservative)

### Notifications

```yaml
notifications:
  # Send daily summary even if no alerts
  daily_summary: true

  # What time to send summary (24-hour format)
  daily_summary_hour: 20  # 8 PM

  # Cooldown between duplicate alerts for same card
  alert_cooldown_hours: 6
```

## Usage

### Running Locally (Without Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Run the monitor
python src/main.py

# Test Discord webhook
python src/main.py --test

# Run once and exit (no scheduling)
python src/main.py --once
```

### Command Line Options

```bash
# Use custom config file
python src/main.py --config my-config.yaml

# Test Discord webhook
python src/main.py --test

# Run one price check and exit
python src/main.py --once
```

### Docker Commands

```bash
# Start in background
docker-compose up -d

# View real-time logs
docker-compose logs -f

# Restart after config changes
docker-compose restart

# Stop the monitor
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

## How It Works

### Price Monitoring Flow

1. **Scheduled Check**: Every hour (configurable), the monitor checks all enabled cards
2. **Web Scraping**: Fetches current prices from TCGplayer product pages
3. **Data Storage**: Saves price history to local JSON files in `data/` directory
4. **Alert Checking**: Compares current prices against alert conditions
5. **Notifications**: Sends Discord alerts when conditions are met

### Alert Conditions

An alert is triggered when **any** of these conditions are met:

1. **Target Price**: Current price ≤ your target price
2. **Percentage Drop**: Price dropped ≥ X% within Y hours
3. **30-Day Low**: Current price matches the lowest price in 30 days
4. **Low Inventory**: Available listings ≤ threshold

### Anti-FOMO Protection

Alerts are **blocked** if:
- Price spiked ≥ 30% in the last 6 hours (configurable)
- Helps avoid alerts during buyouts or price manipulation

### Alert Cooldown

- After an alert is sent for a card, no new alerts for that card for 6 hours (configurable)
- Prevents spam from minor price fluctuations

## File Structure

```
onepiece-tcg-monitor/
├── config.yaml              # Main configuration
├── docker-compose.yml       # Docker setup
├── Dockerfile              # Container definition
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── data/                  # Price history (auto-created)
│   └── *_history.json    # Per-card price data
├── logs/                  # Application logs (auto-created)
│   └── monitor.log       # Main log file
└── src/                   # Source code
    ├── main.py           # Entry point & scheduler
    ├── models.py         # Data classes
    ├── scraper.py        # TCGplayer web scraper
    ├── price_tracker.py  # Price history management
    ├── alert_system.py   # Alert condition logic
    └── notifier.py       # Discord notifications
```

## Troubleshooting

### Discord notifications not working

1. Check webhook URL in `config.yaml`
2. Test webhook: `docker-compose exec tcg-monitor python src/main.py --test`
3. Check logs: `docker-compose logs -f`

### Cards not being found

1. Verify card name, set, and rarity match TCGplayer exactly
2. Check logs for search errors: `docker-compose logs -f`
3. Try searching on TCGplayer.com manually to verify the card exists
4. The scraper may need updates if TCGplayer changes their site structure

### Price data not updating

1. Check if container is running: `docker ps`
2. View logs for errors: `docker-compose logs -f`
3. Verify check interval in config: `check_interval_minutes`
4. TCGplayer may be blocking requests (add delays or reduce frequency)

### Container won't start

1. Check Docker logs: `docker-compose logs`
2. Verify `config.yaml` syntax (YAML is indent-sensitive)
3. Ensure ports aren't in use
4. Try rebuilding: `docker-compose up -d --build`

## Advanced Configuration

### Setting Timezone

Edit `docker-compose.yml`:

```yaml
environment:
  - TZ=America/New_York  # Change to your timezone
```

### Per-Card Custom Thresholds

Override global thresholds for specific cards:

```yaml
cards:
  - name: "High Value Card"
    set: "OP-01"
    rarity: "Secret Rare"
    target_price: 500.00
    # Custom thresholds for this card only
    price_drop_percent: 10  # More sensitive for expensive cards
    drop_timeframe_hours: 48
```

### Multiple Conditions Cards

You can track the same card in different conditions:

```yaml
cards:
  - name: "Monkey D. Luffy"
    set: "OP-05"
    rarity: "Secret Rare"
    condition: "Near Mint"
    target_price: 150.00
    enabled: true

  - name: "Monkey D. Luffy"
    set: "OP-05"
    rarity: "Secret Rare"
    condition: "Lightly Played"
    target_price: 120.00
    enabled: true
```

## Limitations

- **Web Scraping**: Relies on TCGplayer's website structure. May break if they update their site.
- **Rate Limiting**: Too frequent requests may get blocked. Recommended: 60+ minute intervals.
- **No API**: Uses web scraping instead of official API (which requires approval).
- **Single Market**: Only monitors TCGplayer.com (not eBay, CardMarket, etc.).

## Future Enhancements

Potential features for future versions:
- Support for multiple marketplaces (eBay, CardMarket)
- Price trend graphs in Discord embeds
- Email/SMS notification options
- Web dashboard for viewing price history
- Machine learning for price prediction
- Multiple language support for cards

## Contributing

Feel free to submit issues or pull requests for:
- Bug fixes
- TCGplayer scraper improvements
- New features
- Documentation improvements

## Disclaimer

This tool is for personal use only. Please:
- Respect TCGplayer's Terms of Service
- Use reasonable check intervals (60+ minutes recommended)
- Don't overload their servers with requests

This is an unofficial tool and is not affiliated with or endorsed by TCGplayer or Bandai (One Piece TCG publisher).

## License

MIT License - Feel free to modify and use as needed.

---

**Happy card hunting! May your pulls be legendary and your prices be low!** 🏴‍☠️💰
