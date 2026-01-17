"""TCGplayer web scraper for One Piece TCG cards."""
import logging
import re
import time
from typing import Optional
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from models import Card, PriceData

logger = logging.getLogger(__name__)


class TCGPlayerScraper:
    """Scrapes price data from TCGplayer for One Piece TCG cards."""

    BASE_URL = "https://www.tcgplayer.com"
    SEARCH_URL = f"{BASE_URL}/search/onepiece/product"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

    def search_card(self, card: Card) -> Optional[str]:
        """
        Search for a card and return its TCGplayer product URL.

        Args:
            card: Card object to search for

        Returns:
            URL of the card's product page, or None if not found
        """
        try:
            # Build search query
            query_parts = [card.name]
            if card.number and card.set:
                query_parts.append(f"{card.set}-{card.number}")
            elif card.set:
                query_parts.append(card.set)

            search_query = " ".join(query_parts)

            params = {
                'q': search_query,
                'view': 'grid'
            }

            logger.debug(f"Searching for: {search_query}")
            response = self.session.get(self.SEARCH_URL, params=params, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'lxml')

            # Find product links in search results
            # TCGplayer structure may vary, this is a common pattern
            product_links = soup.find_all('a', class_=re.compile(r'product-card__link|search-result__product'))

            if not product_links:
                # Try alternative selector
                product_links = soup.select('a[href*="/product/"]')

            for link in product_links:
                href = link.get('href')
                if href and '/product/' in href:
                    # Verify this matches our card criteria
                    title = link.get_text(strip=True).lower()
                    if card.name.lower() in title:
                        full_url = href if href.startswith('http') else f"{self.BASE_URL}{href}"
                        logger.info(f"Found card URL: {full_url}")
                        return full_url

            logger.warning(f"No product found for {card.name} ({card.set})")
            return None

        except Exception as e:
            logger.error(f"Error searching for card {card.name}: {e}")
            return None

    def get_price_data(self, card: Card, product_url: Optional[str] = None) -> Optional[PriceData]:
        """
        Get current price data for a card.

        Args:
            card: Card object to get price for
            product_url: Direct product URL (if None, will search for card)

        Returns:
            PriceData object with current pricing, or None if failed
        """
        try:
            # If no URL provided, search for the card
            if not product_url:
                product_url = self.search_card(card)
                if not product_url:
                    return None

            # Add small delay to be respectful to the server
            time.sleep(1)

            logger.debug(f"Fetching price data from: {product_url}")
            response = self.session.get(product_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'lxml')

            # Initialize price data
            price_data = PriceData(
                card_id=card.get_identifier(),
                timestamp=datetime.now(),
                tcgplayer_url=product_url
            )

            # Try to extract market price
            # Common selectors for TCGplayer (may need adjustment)
            market_price_elem = soup.find('div', class_=re.compile(r'market-price|spotlight__price'))
            if not market_price_elem:
                market_price_elem = soup.find('span', string=re.compile(r'Market Price'))
                if market_price_elem:
                    market_price_elem = market_price_elem.find_next('span', class_=re.compile(r'price'))

            if market_price_elem:
                price_text = market_price_elem.get_text(strip=True)
                price_data.market_price = self._parse_price(price_text)
                logger.debug(f"Market price: ${price_data.market_price}")

            # Try to extract lowest listing price
            lowest_price_elem = soup.find('div', class_=re.compile(r'listing-item__price|lowest-price'))
            if not lowest_price_elem:
                # Look for price in listings table
                listings = soup.find_all('div', class_=re.compile(r'listing-item'))
                if listings:
                    for listing in listings:
                        # Check condition matches
                        condition_elem = listing.find(string=re.compile(card.condition, re.IGNORECASE))
                        if condition_elem:
                            price_elem = listing.find('span', class_=re.compile(r'listing-item__price'))
                            if price_elem:
                                lowest_price_elem = price_elem
                                break

            if lowest_price_elem:
                price_text = lowest_price_elem.get_text(strip=True)
                price_data.lowest_price = self._parse_price(price_text)
                logger.debug(f"Lowest price: ${price_data.lowest_price}")

            # Count available listings
            listing_count_elem = soup.find(string=re.compile(r'(\d+)\s*sellers?', re.IGNORECASE))
            if listing_count_elem:
                match = re.search(r'(\d+)', listing_count_elem)
                if match:
                    price_data.listing_count = int(match.group(1))
                    logger.debug(f"Listing count: {price_data.listing_count}")

            # Validate we got at least one price
            if price_data.get_effective_price() is None:
                logger.warning(f"No price data found for {card.name}")
                return None

            return price_data

        except Exception as e:
            logger.error(f"Error fetching price data for {card.name}: {e}")
            return None

    def _parse_price(self, price_text: str) -> Optional[float]:
        """
        Parse price from text string.

        Args:
            price_text: String containing price (e.g., "$49.99", "49.99")

        Returns:
            Float price value, or None if parsing failed
        """
        try:
            # Remove currency symbols and whitespace
            clean_text = re.sub(r'[^\d.]', '', price_text)
            return float(clean_text) if clean_text else None
        except (ValueError, AttributeError):
            return None
