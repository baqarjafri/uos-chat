"""Quick test to scrape MSc AI page with JS and tab clicking to get fee data"""
import os
import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
from firecrawl import Firecrawl

load_dotenv()

client = Firecrawl(api_key=os.getenv('FIRECRAWL_API_KEY'))

print("Scraping MSc AI page with JS rendering + TAB CLICKING...")
print("This will click on the Fees tab (#tab_1_4) to reveal the fee data...")

# Actions to click on all tabs, especially the Fees tab
actions = [
    {"type": "wait", "milliseconds": 2000},
    {"type": "click", "selector": "#tab_1_4"},  # Fees and funding tab
    {"type": "wait", "milliseconds": 2000},  # Wait for fee data to load
    {"type": "scrape"},
]

result = client.scrape(
    "https://www.stir.ac.uk/courses/pg-taught/artificial-intelligence",
    formats=['markdown'],
    wait_for=5000,
    only_main_content=True,
    timeout=90000,
    actions=actions,
)

markdown = result.markdown if hasattr(result, 'markdown') else ''
print(f"\nContent length: {len(markdown)} chars")

# Check for fee amounts
amounts = re.findall(r'£[\d,]+(?:\.\d{2})?', markdown)
print(f"\n£ amounts found: {amounts}")

# Check for the specific fee £24,300
if '24,300' in markdown or '24300' in markdown:
    print("\n[SUCCESS] Found £24,300 - the international fee!")
else:
    print("\n[CHECK] £24,300 not found - checking for other tuition fees...")

# Check for tuition fee specifically (usually > £10,000)
tuition_fees = [a for a in amounts if int(a.replace('£', '').replace(',', '')) > 10000]
print(f"Likely tuition fees (>£10,000): {tuition_fees}")

# Save content to file for inspection
with open('msc_ai_content.txt', 'w', encoding='utf-8') as f:
    f.write(markdown)
print("\n[SAVED] Full content saved to msc_ai_content.txt for inspection")
