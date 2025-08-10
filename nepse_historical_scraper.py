#!/usr/bin/env python3
"""
NEPSE Historical Data Scraper

This script uses the nepse_scraper package to scrape historical data for all listed securities
from the Nepal Stock Exchange (NEPSE) and saves them as CSV files in a data folder.

Features:
- Fetches all listed securities from NEPSE
- Scrapes historical price data for each security
- Saves data as individual CSV files per security
- Handles date ranges (NEPSE provides data from today to one year prior)
- Includes error handling and logging

Author: Auto-generated script
Date: August 10, 2025
"""

import os
import sys
import csv
import json
import time
import logging
import pandas as pd
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional

try:
    from nepse_scraper import Nepse_scraper
except ImportError:
    print("Error: nepse_scraper package not found. Please install it using:")
    print("pip install nepse-scraper")
    sys.exit(1)


class NepseHistoricalScraper:
    """
    A class to scrape historical data from NEPSE for all listed securities.
    """
    
    def __init__(self, data_folder: str = "data", delay_between_requests: float = 1.0):
        """
        Initialize the scraper.
        
        Args:
            data_folder (str): Folder to save CSV files
            delay_between_requests (float): Delay between API requests in seconds
        """
        self.data_folder = data_folder
        self.delay_between_requests = delay_between_requests
        self.scraper = Nepse_scraper()
        self.logger = self._setup_logging()
        
        # Create data folder if it doesn't exist
        os.makedirs(self.data_folder, exist_ok=True)
        
        self.logger.info(f"Initialized NEPSE Historical Scraper")
        self.logger.info(f"Data will be saved to: {os.path.abspath(self.data_folder)}")
    
    def _setup_logging(self) -> logging.Logger:
        """Set up logging configuration."""
        logger = logging.getLogger('NepseHistoricalScraper')
        logger.setLevel(logging.INFO)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create file handler
        file_handler = logging.FileHandler('nepse_scraper.log')
        file_handler.setLevel(logging.DEBUG)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        # Add handlers to logger
        if not logger.handlers:
            logger.addHandler(console_handler)
            logger.addHandler(file_handler)
        
        return logger
    
    def get_all_securities(self) -> List[Dict[str, Any]]:
        """
        Fetch all listed securities from NEPSE by getting today's price data.
        
        Returns:
            List of dictionaries containing security information
        """
        try:
            self.logger.info("Fetching all listed securities...")
            # Get today's price data which contains all securities
            price_data = self.scraper.get_today_price()
            
            if isinstance(price_data, dict) and 'content' in price_data:
                securities_list = price_data['content']
            elif isinstance(price_data, list):
                securities_list = price_data
            else:
                securities_list = price_data
            
            # Extract unique securities (symbols) from the price data
            unique_securities = []
            seen_symbols = set()
            
            for item in securities_list:
                symbol = item.get('symbol')
                if symbol and symbol not in seen_symbols:
                    seen_symbols.add(symbol)
                    unique_securities.append({
                        'symbol': symbol,
                        'id': item.get('id'),
                        'securityName': item.get('securityName', symbol)
                    })
            
            self.logger.info(f"Found {len(unique_securities)} securities")
            return unique_securities
            
        except Exception as e:
            self.logger.error(f"Error fetching securities: {str(e)}")
            return []
    
    def generate_date_range(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[str]:
        """
        Generate a list of dates for historical data scraping.
        NEPSE only provides data from today to one year prior.
        
        Args:
            start_date (str, optional): Start date in YYYY-MM-DD format
            end_date (str, optional): End date in YYYY-MM-DD format
            
        Returns:
            List of date strings in YYYY-MM-DD format
        """
        if end_date is None:
            end_date = date.today().strftime('%Y-%m-%d')
        
        if start_date is None:
            # NEPSE provides data from one year prior
            start_date = (date.today() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            # Generate weekly intervals to reduce API calls
            dates = []
            current_date = start
            while current_date <= end:
                dates.append(current_date.strftime('%Y-%m-%d'))
                current_date += timedelta(days=7)  # Weekly intervals
            
            # Ensure end date is included
            if dates[-1] != end_date:
                dates.append(end_date)
                
            return dates
            
        except ValueError as e:
            self.logger.error(f"Invalid date format: {str(e)}")
            return []
    
    def scrape_security_data(self, symbol: str, dates: List[str]) -> pd.DataFrame:
        """
        Scrape historical data for a specific security.
        
        Args:
            symbol (str): Security symbol
            dates (List[str]): List of dates to scrape
            
        Returns:
            pandas.DataFrame: Historical data for the security
        """
        all_data = []
        
        self.logger.info(f"Scraping data for {symbol}...")
        
        for date_str in dates:
            try:
                # Add delay between requests to avoid overwhelming the API
                time.sleep(self.delay_between_requests)
                
                # Get today's price data for the specific date
                price_data = self.scraper.get_today_price(date_str)
                
                if isinstance(price_data, dict) and 'content' in price_data:
                    daily_data = price_data['content']
                elif isinstance(price_data, list):
                    daily_data = price_data
                else:
                    daily_data = price_data
                
                # Filter data for the specific symbol
                if isinstance(daily_data, list):
                    symbol_data = [item for item in daily_data if item.get('symbol') == symbol]
                    
                    for item in symbol_data:
                        # Add the date to the record
                        item['date'] = date_str
                        all_data.append(item)
                
            except Exception as e:
                self.logger.warning(f"Error fetching data for {symbol} on {date_str}: {str(e)}")
                continue
        
        if all_data:
            df = pd.DataFrame(all_data)
            # Remove duplicates based on date
            df = df.drop_duplicates(subset=['date'], keep='last')
            # Sort by date
            df = df.sort_values('date')
            return df
        else:
            return pd.DataFrame()
    
    def save_to_csv(self, df: pd.DataFrame, symbol: str) -> bool:
        """
        Save DataFrame to CSV file.
        
        Args:
            df (pd.DataFrame): Data to save
            symbol (str): Security symbol for filename
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            filename = f"{symbol}_historical_data.csv"
            filepath = os.path.join(self.data_folder, filename)
            
            df.to_csv(filepath, index=False)
            self.logger.info(f"Saved {len(df)} records to {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving data for {symbol}: {str(e)}")
            return False
    
    def scrape_all_securities(self, start_date: Optional[str] = None, end_date: Optional[str] = None):
        """
        Main method to scrape historical data for all securities.
        
        Args:
            start_date (str, optional): Start date in YYYY-MM-DD format
            end_date (str, optional): End date in YYYY-MM-DD format
        """
        self.logger.info("Starting historical data scraping for all securities...")
        
        # Get all securities
        securities = self.get_all_securities()
        if not securities:
            self.logger.error("No securities found. Exiting.")
            return
        
        # Generate date range
        dates = self.generate_date_range(start_date, end_date)
        if not dates:
            self.logger.error("No valid dates generated. Exiting.")
            return
        
        self.logger.info(f"Will scrape data for {len(dates)} dates: {dates[0]} to {dates[-1]}")
        
        successful_scrapes = 0
        failed_scrapes = 0
        
        # Process each security
        for i, security in enumerate(securities, 1):
            symbol = security.get('symbol', 'UNKNOWN')
            
            self.logger.info(f"Processing {i}/{len(securities)}: {symbol}")
            
            try:
                # Scrape data for this security
                df = self.scrape_security_data(symbol, dates)
                
                if not df.empty:
                    # Save to CSV
                    if self.save_to_csv(df, symbol):
                        successful_scrapes += 1
                    else:
                        failed_scrapes += 1
                else:
                    self.logger.warning(f"No data found for {symbol}")
                    failed_scrapes += 1
                
            except Exception as e:
                self.logger.error(f"Error processing {symbol}: {str(e)}")
                failed_scrapes += 1
                continue
        
        # Summary
        self.logger.info(f"Scraping completed!")
        self.logger.info(f"Successful: {successful_scrapes}")
        self.logger.info(f"Failed: {failed_scrapes}")
        self.logger.info(f"Total securities processed: {len(securities)}")
    
    def scrape_specific_securities(self, symbols: List[str], start_date: Optional[str] = None, end_date: Optional[str] = None):
        """
        Scrape historical data for specific securities.
        
        Args:
            symbols (List[str]): List of security symbols to scrape
            start_date (str, optional): Start date in YYYY-MM-DD format
            end_date (str, optional): End date in YYYY-MM-DD format
        """
        self.logger.info(f"Starting historical data scraping for {len(symbols)} specific securities...")
        
        # Generate date range
        dates = self.generate_date_range(start_date, end_date)
        if not dates:
            self.logger.error("No valid dates generated. Exiting.")
            return
        
        self.logger.info(f"Will scrape data for {len(dates)} dates: {dates[0]} to {dates[-1]}")
        
        successful_scrapes = 0
        failed_scrapes = 0
        
        # Process each specified security
        for i, symbol in enumerate(symbols, 1):
            self.logger.info(f"Processing {i}/{len(symbols)}: {symbol}")
            
            try:
                # Scrape data for this security
                df = self.scrape_security_data(symbol, dates)
                
                if not df.empty:
                    # Save to CSV
                    if self.save_to_csv(df, symbol):
                        successful_scrapes += 1
                    else:
                        failed_scrapes += 1
                else:
                    self.logger.warning(f"No data found for {symbol}")
                    failed_scrapes += 1
                
            except Exception as e:
                self.logger.error(f"Error processing {symbol}: {str(e)}")
                failed_scrapes += 1
                continue
        
        # Summary
        self.logger.info(f"Scraping completed!")
        self.logger.info(f"Successful: {successful_scrapes}")
        self.logger.info(f"Failed: {failed_scrapes}")
        self.logger.info(f"Total securities processed: {len(symbols)}")


def main():
    """Main function to run the scraper."""
    print("NEPSE Historical Data Scraper")
    print("=" * 50)
    
    # Initialize scraper
    scraper = NepseHistoricalScraper(data_folder="data", delay_between_requests=1.0)
    
    # You can choose one of the following options:
    
    # Option 1: Scrape all securities (this will take a long time!)
    print("\nChoose an option:")
    print("1. Scrape ALL securities (Warning: This will take several hours!)")
    print("2. Scrape specific securities")
    print("3. Test with a few sample securities")
    
    choice = input("\nEnter your choice (1, 2, or 3): ").strip()
    
    if choice == "1":
        # Scrape all securities
        confirm = input("This will scrape ALL securities and may take several hours. Continue? (y/N): ").strip().lower()
        if confirm == 'y':
            scraper.scrape_all_securities()
        else:
            print("Operation cancelled.")
    
    elif choice == "2":
        # Scrape specific securities
        symbols_input = input("Enter security symbols separated by commas (e.g., NABIL,NICA,SCBL): ").strip()
        symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()]
        
        if symbols:
            scraper.scrape_specific_securities(symbols)
        else:
            print("No valid symbols provided.")
    
    elif choice == "3":
        # Test with sample securities
        test_symbols = ["NABIL", "NICA", "SCBL", "SANIMA", "EBL"]
        print(f"Testing with sample securities: {', '.join(test_symbols)}")
        scraper.scrape_specific_securities(test_symbols)
    
    else:
        print("Invalid choice. Exiting.")
        return
    
    print(f"\nData saved to: {os.path.abspath('data')}")
    print("Check the log file 'nepse_scraper.log' for detailed information.")


if __name__ == "__main__":
    main()
