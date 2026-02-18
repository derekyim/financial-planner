"""Scraper for business knowledge sources.

Downloads content from URLs listed in rag_requirements.md and saves as text files
for RAG ingestion.
"""

import os
import re
import time
import requests
from bs4 import BeautifulSoup
import html2text
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse


# Configuration
DATA_DIR = Path(__file__).parent.parent / "data"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
REQUEST_DELAY = 2  # Seconds between requests to be polite


# Knowledge sources from rag_requirements.md organized by category
KNOWLEDGE_SOURCES = {
    "financial_glossary": [
        {
            "name": "sba_glossary",
            "url": "https://www.sba.gov/document/support--glossary-business-financial-terms",
            "description": "SBA Glossary of Business Financial Terms",
        },
        {
            "name": "investopedia_dictionary",
            "url": "https://www.investopedia.com/financial-term-dictionary-4769738",
            "description": "Investopedia Financial Term Dictionary",
        },
    ],
    "amazon_selling": [
        {
            "name": "amazon_seller_guide",
            "url": "https://sell.amazon.com/sell-online",
            "description": "Amazon Seller Resources & New Seller Guide",
        },
        {
            "name": "ecommerce_fastlane_amazon",
            "url": "https://ecommercefastlane.com/a-complete-beginners-guide-to-selling-on-amazon/",
            "description": "Complete Beginner's Guide to Selling On Amazon",
        },
    ],
    "shopify_strategy": [
        {
            "name": "shopify_enterprise_blog",
            "url": "https://www.shopify.com/enterprise/blog/resources-to-help-merchants-get-online-fast-optimize-stores-and-scale",
            "description": "Shopify Enterprise Blog: Ecommerce Optimization Resources",
        },
        {
            "name": "shopify_profitable_store",
            "url": "https://ecommbreakthrough.com/the-ultimate-guide-to-building-a-profitable-shopify-store-for-amazon-sellers-with-kurt-elster/",
            "description": "Ultimate Guide to Building a Profitable Shopify Store",
        },
    ],
    "advertising": [
        {
            "name": "shopify_google_shopping",
            "url": "https://www.shopify.com/enterprise/blog/the-master-guide-to-google-shopping",
            "description": "Shopify's Master Guide to Google Shopping",
        },
    ],
    "tiktok_shop": [
        {
            "name": "tiktok_shop_guide",
            "url": "https://akselera.tech/en/insights/guides/tiktok-shop-ecommerce-complete-guide",
            "description": "TikTok Shop Guide - fees, optimization tactics, pricing",
        },
    ],
    "retail_expansion": [
        {
            "name": "entrepreneur_retail_guide",
            "url": "https://www.entrepreneur.com/growing-a-business/the-sellers-guide-to-ecommerce-success-on-amazon/368092",
            "description": "Seller's Guide to Ecommerce Success on Target & Amazon",
        },
    ],
}


def create_html_to_text_converter() -> html2text.HTML2Text:
    """Create an HTML to text converter with appropriate settings."""
    converter = html2text.HTML2Text()
    converter.ignore_links = False
    converter.ignore_images = True
    converter.ignore_emphasis = False
    converter.body_width = 0  # Don't wrap lines
    return converter


def fetch_page(url: str) -> Optional[str]:
    """Fetch a web page and return its HTML content.
    
    Args:
        url: The URL to fetch.
        
    Returns:
        The HTML content or None if fetch failed.
    """
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"  Error fetching {url}: {e}")
        return None


def extract_main_content(html: str, url: str) -> str:
    """Extract the main content from HTML, removing navigation and footers.
    
    Args:
        html: The HTML content.
        url: The URL (for context in extraction).
        
    Returns:
        The extracted text content.
    """
    soup = BeautifulSoup(html, "html.parser")
    
    # Remove unwanted elements
    for element in soup.find_all(["nav", "header", "footer", "aside", "script", "style", "noscript"]):
        element.decompose()
    
    # Try to find main content area
    main_content = None
    for selector in ["main", "article", '[role="main"]', ".main-content", "#main-content", ".content", "#content"]:
        main_content = soup.select_one(selector)
        if main_content:
            break
    
    if main_content is None:
        main_content = soup.body if soup.body else soup
    
    # Convert to text
    converter = create_html_to_text_converter()
    text = converter.handle(str(main_content))
    
    # Clean up excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()
    
    return text


def scrape_source(source: dict, category: str) -> bool:
    """Scrape a single source and save to file.
    
    Args:
        source: Source dictionary with name, url, description.
        category: The category this source belongs to.
        
    Returns:
        True if successful, False otherwise.
    """
    name = source["name"]
    url = source["url"]
    description = source["description"]
    
    print(f"  Scraping: {name}")
    print(f"    URL: {url}")
    
    html = fetch_page(url)
    if html is None:
        return False
    
    text = extract_main_content(html, url)
    
    if len(text) < 100:
        print(f"    Warning: Very little content extracted ({len(text)} chars)")
    
    # Create output file
    output_file = DATA_DIR / category / f"{name}.txt"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Add metadata header
    content = f"""# {description}
Source: {url}
Category: {category}

---

{text}
"""
    
    output_file.write_text(content, encoding="utf-8")
    print(f"    Saved: {output_file} ({len(text)} chars)")
    
    return True


def create_sample_documents():
    """Create sample documents for testing when scraping isn't possible.
    
    This provides a fallback with curated content based on the topics.
    """
    sample_docs = {
        "financial_glossary/business_terms.txt": """# Business Financial Terms Glossary
Source: Curated from industry standards
Category: financial_glossary

---

## Revenue and Sales Terms

**Gross Sales**: The total amount of sales before any deductions (returns, discounts, allowances).

**Net Revenue**: Gross sales minus returns, discounts, and allowances. This is the actual revenue recognized.

**Average Order Value (AOV)**: Total revenue divided by number of orders. A key metric for ecommerce.

**Customer Acquisition Cost (CAC)**: Total cost of acquiring a new customer, including marketing and sales expenses.

**Lifetime Value (LTV)**: The predicted total revenue a customer will generate over their relationship with the business.

**LTV:CAC Ratio**: The ratio of customer lifetime value to acquisition cost. A healthy ratio is typically 3:1 or higher.

## Profitability Terms

**Gross Profit**: Revenue minus Cost of Goods Sold (COGS). Shows profitability before operating expenses.

**Gross Margin**: Gross Profit divided by Revenue, expressed as a percentage.

**Contribution Margin**: Revenue minus variable costs. Shows how much each sale contributes to fixed costs and profit.

**EBITDA**: Earnings Before Interest, Taxes, Depreciation, and Amortization. A measure of operating performance.

**EBIT (Operating Income)**: Earnings Before Interest and Taxes. Shows profitability from core operations.

**Net Income**: The bottom line profit after all expenses, interest, and taxes.

## Cash Flow Terms

**Operating Cash Flow**: Cash generated from normal business operations.

**Free Cash Flow**: Operating cash flow minus capital expenditures. Cash available for dividends, debt repayment, or reinvestment.

**Working Capital**: Current assets minus current liabilities. Measures short-term liquidity.

**Burn Rate**: The rate at which a company spends its cash reserves, typically monthly.

**Runway**: How long a company can operate before running out of cash, based on current burn rate.

## Ecommerce Metrics

**Conversion Rate**: Percentage of visitors who make a purchase.

**Cart Abandonment Rate**: Percentage of shoppers who add items to cart but don't complete purchase.

**Return Rate**: Percentage of products returned by customers.

**Repeat Purchase Rate**: Percentage of customers who make more than one purchase.

**Churn Rate**: Percentage of customers who stop buying over a given period.
""",
        "amazon_selling/amazon_strategy.txt": """# Amazon Selling Strategy Guide
Source: Best practices compilation
Category: amazon_selling

---

## Getting Started on Amazon

### Account Types
- **Individual**: For sellers with fewer than 40 items/month. $0.99 per item sold.
- **Professional**: For serious sellers. $39.99/month flat fee, access to advanced tools.

### Fulfillment Options

**FBA (Fulfillment by Amazon)**:
- Amazon stores, packs, and ships your products
- Products eligible for Prime shipping
- Higher fees but less operational burden
- Best for: products with good margins, high volume items

**FBM (Fulfillment by Merchant)**:
- You handle storage and shipping
- Lower fees, more control
- Best for: large/heavy items, low volume, custom products

### Listing Optimization

**Title**: Include main keywords, brand, key features. Max 200 characters.

**Bullet Points**: Highlight 5 key benefits and features. Use keywords naturally.

**Images**: 
- Main image on white background
- Lifestyle images showing product in use
- Infographics highlighting features
- Minimum 1000x1000 pixels for zoom

**Backend Keywords**: Use all 250 bytes for search terms not in visible listing.

### Amazon PPC Strategy

**Sponsored Products**: Target specific keywords or ASINs. Start with automatic campaigns to discover keywords.

**ACoS (Advertising Cost of Sales)**: Ad spend divided by attributed sales. Target 15-30% depending on margins.

**TACOS (Total ACoS)**: Ad spend divided by total sales. Shows true advertising efficiency.

### Pricing Strategy

- Use repricing tools for competitive markets
- Consider MAP (Minimum Advertised Price) policies
- Factor in all fees: referral (8-15%), FBA fees, storage
- Maintain at least 30% profit margin after all costs
""",
        "shopify_strategy/shopify_optimization.txt": """# Shopify Store Optimization Guide
Source: Best practices compilation
Category: shopify_strategy

---

## Store Setup Best Practices

### Theme Selection
- Choose mobile-first themes (70%+ of traffic is mobile)
- Prioritize page speed over flashy features
- Use themes with built-in SEO features

### Conversion Optimization

**Homepage**:
- Clear value proposition above the fold
- Featured products or collections
- Social proof (reviews, press mentions)
- Trust badges and guarantees

**Product Pages**:
- High-quality images with zoom
- Detailed descriptions with benefits focus
- Size guides and specifications
- Customer reviews and ratings
- Clear add-to-cart button
- Cross-sell and upsell widgets

**Checkout**:
- Enable Shop Pay for faster checkout
- Offer multiple payment options
- Display security badges
- Show shipping costs early
- Enable guest checkout

### Apps and Integrations

**Essential Apps**:
- Email marketing (Klaviyo, Omnisend)
- Reviews (Judge.me, Loox)
- SMS marketing (Postscript, Attentive)
- Subscriptions (Recharge, Bold)
- Analytics (Triple Whale, Lifetimely)

### Marketing Channels

**Email Marketing**:
- Welcome series (3-5 emails)
- Abandoned cart recovery
- Post-purchase follow-up
- Win-back campaigns

**Retention Strategies**:
- Loyalty programs
- Subscription options
- VIP customer tiers
- Referral programs
""",
        "advertising/digital_ads_strategy.txt": """# Digital Advertising Strategy
Source: Best practices compilation
Category: advertising

---

## Meta (Facebook/Instagram) Ads

### Campaign Structure

**Top of Funnel (Prospecting)**:
- Broad audiences or lookalikes
- Video content performs best
- Focus on awareness and engagement
- Budget: 60-70% of ad spend

**Middle of Funnel (Consideration)**:
- Retarget website visitors
- Engaged social followers
- Email subscribers
- Budget: 20-30% of ad spend

**Bottom of Funnel (Conversion)**:
- Cart abandoners
- Product page viewers
- High-intent audiences
- Budget: 10-20% of ad spend

### Key Metrics
- **ROAS (Return on Ad Spend)**: Revenue / Ad Spend. Target 3x+ for profitability
- **CPM (Cost per 1000 impressions)**: Monitor for audience saturation
- **CTR (Click-through rate)**: Benchmark 1-2% for ecommerce
- **CPA (Cost per acquisition)**: Should be well below customer LTV

## Google Ads

### Campaign Types

**Shopping Campaigns**:
- Product listing ads in search results
- Requires Google Merchant Center
- Use Performance Max for AI optimization

**Search Campaigns**:
- Text ads for branded and non-branded keywords
- Use negative keywords to reduce waste
- Implement RLSA for remarketing

**Display/YouTube**:
- Awareness and remarketing
- Lower intent but broader reach
- Use for brand building

### Optimization Tips
- Segment campaigns by product category
- Use bid adjustments for devices and locations
- Test ad copy continuously
- Monitor search terms report weekly
""",
        "operations/warehouse_optimization.txt": """# Warehouse and Fulfillment Optimization
Source: Best practices compilation
Category: operations

---

## Reducing Warehouse Costs

### Inventory Management

**Demand Forecasting**:
- Analyze historical sales data
- Account for seasonality
- Factor in marketing calendar
- Use 80/20 rule: focus on top SKUs

**Safety Stock Formula**:
Safety Stock = (Max Daily Sales × Max Lead Time) - (Avg Daily Sales × Avg Lead Time)

**Inventory Turnover**:
- Target 4-6x per year for most products
- Slow movers (<2x): liquidate or reduce orders
- Fast movers (>8x): may need more safety stock

### Warehouse Layout

**ABC Analysis**:
- A items (top 20% by volume): prime picking locations
- B items (next 30%): secondary locations
- C items (bottom 50%): back of warehouse

**Pick Path Optimization**:
- Zone picking for large warehouses
- Batch picking for similar orders
- Wave picking during peak times

### Labor Efficiency

- Cross-train staff for flexibility
- Use pick-to-light or voice picking
- Implement quality checkpoints
- Track picks per hour metrics

## Reducing Shipping Costs

### Carrier Negotiation
- Get quotes from multiple carriers
- Negotiate based on volume commitments
- Consider regional carriers for specific zones

### Packaging Optimization
- Right-size boxes to reduce DIM weight
- Use poly mailers when possible
- Negotiate custom box sizes with suppliers

### Zone Optimization
- Distribute inventory to multiple locations
- Use zone-skipping for high-volume zones
- Consider 3PL partners in key regions
"""
    }
    
    print("\nCreating sample documents...")
    for filepath, content in sample_docs.items():
        full_path = DATA_DIR / filepath
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        print(f"  Created: {full_path}")
    
    print(f"\nCreated {len(sample_docs)} sample documents")


def scrape_all_sources(use_samples: bool = True):
    """Scrape all knowledge sources.
    
    Args:
        use_samples: If True, create sample documents instead of scraping
                    (useful when sites block scraping).
    """
    print("=" * 60)
    print("Business Knowledge Scraper")
    print("=" * 60)
    
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    if use_samples:
        create_sample_documents()
        return
    
    total = 0
    success = 0
    
    for category, sources in KNOWLEDGE_SOURCES.items():
        print(f"\n[{category}]")
        
        for source in sources:
            total += 1
            if scrape_source(source, category):
                success += 1
            time.sleep(REQUEST_DELAY)
    
    print("\n" + "=" * 60)
    print(f"Scraping complete: {success}/{total} sources successful")
    print("=" * 60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Scrape business knowledge sources")
    parser.add_argument(
        "--scrape", 
        action="store_true", 
        help="Actually scrape URLs (default: create sample documents)"
    )
    args = parser.parse_args()
    
    scrape_all_sources(use_samples=not args.scrape)
