#!/usr/bin/env python3
"""
Test script to check available methods in nepse_scraper
"""

from nepse_scraper import Nepse_scraper

# Initialize scraper
scraper = Nepse_scraper()

# Print all available methods
print("Available methods in Nepse_scraper:")
methods = [method for method in dir(scraper) if not method.startswith('_')]
for method in sorted(methods):
    print(f"  - {method}")

print("\nAll methods (including private):")
all_methods = [method for method in dir(scraper)]
for method in sorted(all_methods):
    print(f"  - {method}")
