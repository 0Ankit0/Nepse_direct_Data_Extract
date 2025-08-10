#!/usr/bin/env python3
"""
Simple NEPSE Data Scraper

A simplified script to scrape current and recent historical data from NEPSE
using the nepse_scraper package.

This version focuses on efficiency and gets the most recent trading data.
"""

import os
import json
import pandas as pd
from datetime import datetime, timedelta, date
from typing import List, Dict, Any

try:
    from nepse_scraper import Nepse_scraper
except ImportError:
    print("Error: nepse_scraper package not found. Please install it using:")
    print("pip install nepse-scraper")
    exit(1)


def get_recent_trading_dates(days_back: int = 30) -> List[str]:
    """Get a list of recent dates for data scraping."""
    dates = []
    current_date = date.today()
    
    for i in range(days_back):
        check_date = current_date - timedelta(days=i)
        # Skip weekends (Saturday=5, Sunday=6)
        if check_date.weekday() < 5:  # Monday=0 to Friday=4
            dates.append(check_date.strftime('%Y-%m-%d'))
    
    return dates[:10]  # Limit to last 10 trading days


def scrape_latest_data():
    """Scrape the latest trading data for all securities."""
    print("NEPSE Simple Data Scraper")
    print("=" * 40)
    
    # Initialize scraper
    scraper = Nepse_scraper()
    data_folder = "data"
    os.makedirs(data_folder, exist_ok=True)
    
    try:
        print("Fetching latest trading data...")
        
        # Get today's price data (latest trading day)
        latest_data = scraper.get_today_price()
        
        if isinstance(latest_data, dict) and 'content' in latest_data:
            securities_data = latest_data['content']
        elif isinstance(latest_data, list):
            securities_data = latest_data
        else:
            securities_data = latest_data
        
        if not securities_data:
            print("No data found for today. The market might be closed.")
            return
        
        # Convert to DataFrame
        df = pd.DataFrame(securities_data)
        
        # Add timestamp
        df['scraped_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Save to CSV
        filename = f"nepse_latest_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join(data_folder, filename)
        df.to_csv(filepath, index=False)
        
        print(f"Successfully scraped data for {len(securities_data)} securities")
        print(f"Data saved to: {filepath}")
        
        # Display summary
        print(f"\nSample data (first 5 securities):")
        print(df[['symbol', 'openPrice', 'highPrice', 'lowPrice', 'lastTradedPrice', 'totalTradedQuantity']].head())
        
        return df
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return None


def scrape_specific_securities(symbols: List[str]):
    """Scrape data for specific securities with recent historical data."""
    print(f"Scraping data for: {', '.join(symbols)}")
    
    scraper = Nepse_scraper()
    data_folder = "data"
    os.makedirs(data_folder, exist_ok=True)
    
    # Get recent trading dates
    recent_dates = get_recent_trading_dates(30)
    
    all_data = []
    
    for date_str in recent_dates[:5]:  # Limit to 5 recent dates
        try:
            print(f"Fetching data for {date_str}...")
            
            daily_data = scraper.get_today_price(date_str)
            
            if isinstance(daily_data, dict) and 'content' in daily_data:
                securities_list = daily_data['content']
            elif isinstance(daily_data, list):
                securities_list = daily_data
            else:
                securities_list = daily_data
            
            # Filter for requested symbols
            for security in securities_list:
                if security.get('symbol') in symbols:
                    security['date'] = date_str
                    all_data.append(security)
        
        except Exception as e:
            print(f"Error fetching data for {date_str}: {str(e)}")
            continue
    
    if all_data:
        df = pd.DataFrame(all_data)
        
        # Save combined data
        filename = f"nepse_specific_securities_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join(data_folder, filename)
        df.to_csv(filepath, index=False)
        
        print(f"Successfully scraped {len(all_data)} records")
        print(f"Data saved to: {filepath}")
        
        # Save individual files for each security
        for symbol in symbols:
            symbol_data = df[df['symbol'] == symbol]
            if not symbol_data.empty:
                symbol_file = os.path.join(data_folder, f"{symbol}_data.csv")
                symbol_data.to_csv(symbol_file, index=False)
                print(f"Saved {len(symbol_data)} records for {symbol}")
        
        return df
    else:
        print("No data found for the specified securities.")
        return None


def get_market_summary():
    """Get current market summary."""
    print("Fetching market summary...")
    
    scraper = Nepse_scraper()
    
    try:
        # Get market summary
        market_summary = scraper.get_market_summary()
        
        # Get today's market summary
        today_summary = scraper.get_today_market_summary()
        
        print("Market Summary:")
        print(json.dumps(market_summary, indent=2))
        
        print("\nToday's Market Summary:")
        print(json.dumps(today_summary, indent=2))
        
        # Save to file
        data_folder = "data"
        os.makedirs(data_folder, exist_ok=True)
        
        summary_file = os.path.join(data_folder, f"market_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(summary_file, 'w') as f:
            json.dump({
                'market_summary': market_summary,
                'today_summary': today_summary,
                'timestamp': datetime.now().isoformat()
            }, f, indent=2)
        
        print(f"\nMarket summary saved to: {summary_file}")
        
    except Exception as e:
        print(f"Error fetching market summary: {str(e)}")


def main():
    """Main function with user menu."""
    while True:
        print("\n" + "="*50)
        print("NEPSE Data Scraper - Simple Version")
        print("="*50)
        print("1. Get latest trading data for all securities")
        print("2. Get data for specific securities")
        print("3. Get market summary")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            scrape_latest_data()
        
        elif choice == "2":
            symbols_input = input("Enter security symbols separated by commas (e.g., NABIL,NICA,SCBL): ").strip()
            symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()]
            
            if symbols:
                scrape_specific_securities(symbols)
            else:
                print("No valid symbols provided.")
        
        elif choice == "3":
            get_market_summary()
        
        elif choice == "4":
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
