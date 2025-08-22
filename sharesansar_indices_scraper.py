

import os
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DOWNLOAD_DIR = 'Indices'
INDICES_URL = 'https://www.sharesansar.com/datewise-indices'
START_DATE = datetime(2020, 1, 1)
END_DATE = datetime.now()
MAX_WORKERS = 3
DELAY_BETWEEN_REQUESTS = 2  # seconds

os.makedirs(BASE_DOWNLOAD_DIR, exist_ok=True)

def is_weekend(date):
    return date.weekday() in [4, 5]


def save_indices_to_csv(html_content, csv_path):
    soup = BeautifulSoup(html_content, 'html.parser')
    tables = soup.find_all('table')
    if not tables:
        return False
    # Assume all tables have the same header structure
    headers = None
    all_data = []
    for table in tables:
        thead = table.find('thead')
        if not thead:
            continue
        current_headers = [th.get_text(strip=True) for th in thead.find_all('th')]
        if not headers:
            headers = current_headers
        elif headers != current_headers:
            # If headers differ, skip this table
            continue
        tbody = table.find('tbody')
        if not tbody:
            continue
        for row in tbody.find_all('tr'):
            cells = [td.get_text(strip=True) for td in row.find_all('td')]
            if len(cells) == len(headers):
                all_data.append(cells)
    if not all_data:
        return False
    df = pd.DataFrame(all_data, columns=headers)
    df.to_csv(csv_path, index=False)
    return True

def scrape_indices_for_date(date_str, csv_path):
    try:
        params = {'date': date_str}
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
        }
        resp = requests.get(INDICES_URL, params=params, headers=headers, timeout=30)
        if resp.status_code != 200:
            print(f"✗ Failed to fetch data for {date_str}: HTTP {resp.status_code}")
            return False
        if save_indices_to_csv(resp.text, csv_path):
            print(f"✓ Saved {csv_path}")
            return True
        else:
            print(f"✗ No valid table data for {date_str}")
            return False
    except Exception as e:
        print(f"✗ Error for {date_str}: {e}")
        return False

def generate_date_range(start_date, end_date):
    dates = []
    current = end_date
    while current >= start_date:
        if not is_weekend(current):
            dates.append(current)
        current -= timedelta(days=1)
    return dates

def scrape_date_wrapper(date):
    date_str = date.strftime('%Y-%m-%d')
    csv_filename = f"{date_str.replace('-', '_')}.csv"
    csv_path = os.path.join(BASE_DOWNLOAD_DIR, csv_filename)
    if os.path.exists(csv_path):
        print(f"⏭ Skipping {date_str} - file already exists")
        return True
    # Rate limiting between requests
    time.sleep(DELAY_BETWEEN_REQUESTS)
    return scrape_indices_for_date(date_str, csv_path)

def main():
    print(f"Starting Sharesansar Indices scraping from {START_DATE.strftime('%Y-%m-%d')} to {END_DATE.strftime('%Y-%m-%d')}")
    print(f"Output folder: {BASE_DOWNLOAD_DIR}")
    print(f"Max concurrent workers: {MAX_WORKERS}")
    print(f"Delay between requests: {DELAY_BETWEEN_REQUESTS} seconds")
    print("-" * 60)

    dates_to_scrape = generate_date_range(START_DATE, END_DATE)
    total_dates = len(dates_to_scrape)
    print(f"Total trading days to process: {total_dates}")

    if not dates_to_scrape:
        print("No dates to scrape!")
        return

    # Test with the most recent date first
    print("\nTesting with the most recent date...")
    test_date = dates_to_scrape[0]
    if scrape_date_wrapper(test_date):
        print("✓ Test successful, proceeding with batch processing...\n")
    else:
        print("✗ Test failed, please check the site or scraping logic")
        return

    successful = 0
    failed = 0
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_date = {executor.submit(scrape_date_wrapper, date): date for date in dates_to_scrape}
        for future in as_completed(future_to_date):
            date = future_to_date[future]
            try:
                success = future.result()
                if success:
                    successful += 1
                else:
                    failed += 1
            except Exception as e:
                print(f'✗ Exception for {date.strftime("%Y-%m-%d")}: {e}')
                failed += 1

    end_time = time.time()
    duration = end_time - start_time
    print("\n" + "="*60)
    print("SCRAPING SUMMARY")
    print("="*60)
    print(f"Total dates processed: {successful + failed}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Duration: {duration:.2f} seconds")
    print(f"Average time per request: {duration/total_dates:.2f} seconds")
    print(f"Files saved in: {os.path.abspath(BASE_DOWNLOAD_DIR)}")

if __name__ == '__main__':
    main()
