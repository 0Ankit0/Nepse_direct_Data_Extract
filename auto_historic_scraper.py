#!/usr/bin/env python3
"""
Auto-run historic scraper with predefined options
This script automatically runs the FULL historical scraper:
- Scrapes ALL securities (all 318+ securities)
- Gets up to 1 year of historical data
- No user interaction required
"""

import sys
import os
from nepse_historical_scraper import NepseHistoricalScraper

def main():
    print("Starting NEPSE FULL Historical Data Scraper in AUTO mode")
    print("=" * 70)
    print("This will scrape COMPLETE historical data for ALL securities!")
    print("Expected duration: Several hours")
    print("Data scope:")
    print("  - ALL 318+ securities on NEPSE")
    print("  - Up to 1 year of historical data")
    print("  - 54+ date points per security (weekly intervals)")
    print("  - Expected ~17,000+ API calls")
    print("=" * 70)
    
    # Get configuration from environment variables
    data_folder = os.getenv('DATA_FOLDER', '/app/data')
    delay = float(os.getenv('SCRAPER_DELAY', '1.0'))
    
    # Initialize scraper with container-friendly settings
    scraper = NepseHistoricalScraper(data_folder=data_folder, delay_between_requests=delay)
    
    # Directly call the scrape_all_securities method (bypasses interactive menu)
    scraper.scrape_all_securities()
    
    print("\n🎉 FULL Historical scraping completed!")
    print(f"📁 Data saved to: {data_folder}")

if __name__ == "__main__":
    main()
