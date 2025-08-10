#!/usr/bin/env python3
"""
Test script to check get_security_detail method
"""

from nepse_scraper import Nepse_scraper
import json

# Initialize scraper
scraper = Nepse_scraper()

try:
    print("Testing get_security_detail()...")
    securities = scraper.get_security_detail()
    
    print(f"Type: {type(securities)}")
    print(f"Keys (if dict): {securities.keys() if isinstance(securities, dict) else 'Not a dict'}")
    
    if isinstance(securities, dict):
        print(f"Content type: {type(securities.get('content', 'No content key'))}")
        if 'content' in securities:
            print(f"Number of securities: {len(securities['content'])}")
            if securities['content']:
                print("Sample security:")
                print(json.dumps(securities['content'][0], indent=2))
    elif isinstance(securities, list):
        print(f"Number of securities: {len(securities)}")
        if securities:
            print("Sample security:")
            print(json.dumps(securities[0], indent=2))
    else:
        print(f"Data: {securities}")

except Exception as e:
    print(f"Error: {e}")
