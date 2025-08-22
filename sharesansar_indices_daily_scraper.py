
import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

BASE_DOWNLOAD_DIR = 'Indices'
INDICES_URL = 'https://www.sharesansar.com/datewise-indices'

def is_weekend(date):
    return date.weekday() in [4, 5]

def save_indices_to_csv(html_content, csv_path):
    soup = BeautifulSoup(html_content, 'html.parser')
    tables = soup.find_all('table')
    if not tables:
        return False
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

def get_most_recent_trading_day():
    today = datetime.now()
    date = today
    while is_weekend(date):
        date -= timedelta(days=1)
    return date

def main():
    os.makedirs(BASE_DOWNLOAD_DIR, exist_ok=True)
    date = get_most_recent_trading_day()
    date_str = date.strftime('%Y-%m-%d')
    csv_filename = f"{date_str.replace('-', '_')}.csv"
    csv_path = os.path.join(BASE_DOWNLOAD_DIR, csv_filename)
    if os.path.exists(csv_path):
        print(f"⏭ Skipping {date_str} - file already exists")
        return
    scrape_indices_for_date(date_str, csv_path)

if __name__ == '__main__':
    main()
