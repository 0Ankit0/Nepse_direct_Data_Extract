#!/usr/bin/env python3
"""
Test the fixed get_all_securities method
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from nepse_historical_scraper import NepseHistoricalScraper

# Initialize scraper
scraper = NepseHistoricalScraper()

# Test getting securities
securities = scraper.get_all_securities()
print(f"Found {len(securities)} securities")

if securities:
    print("First 5 securities:")
    for i, security in enumerate(securities[:5]):
        print(f"  {i+1}. {security}")
else:
    print("No securities found!")
