import os
import csv
import time
import requests
from datetime import datetime
from bs4 import BeautifulSoup
 

# Constants
data_folder = 'sharesansarAPI'
api_url = 'https://www.sharesansar.com/ajaxtodayshareprice'
delay_between_requests = 2  # seconds

# Ensure output folder exists
os.makedirs(data_folder, exist_ok=True)





def get_csrf_token():
    """Get CSRF token from the main page"""
    try:
        session = requests.Session()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        response = session.get('https://www.sharesansar.com/today-share-price', headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        token_input = soup.find('input', {'name': '_token'})
        if token_input and token_input.get('value'):
            return session, token_input['value']
        else:
            print("Could not find CSRF token")
            return None, None
    except Exception as e:
        print(f"Error getting CSRF token: {e}")
        return None, None

def save_table_to_csv(html_content, filename):
    """Parse HTML table and save to CSV"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        table = soup.find('table')
        if not table:
            return False
        rows = table.find_all('tr')
        if not rows or len(rows) < 2:
            return False
        # Only save if there is at least one valid data row (not just header, not 'No data found' or 'No Record Found')
        data_rows = [row for row in rows[1:] if row.find_all(['td'])]
        if not data_rows:
            return False
        # Check for 'No data found' or 'No Record Found' in any cell of the only data row
        if len(data_rows) == 1:
            cells = [col.get_text(strip=True).lower() for col in data_rows[0].find_all(['td'])]
            for cell in cells:
                if 'no data found' in cell or 'no record found' in cell:
                    return False
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for row in rows:
                cols = row.find_all(['th', 'td'])
                row_data = [col.get_text().strip() for col in cols]
                if row_data:
                    writer.writerow(row_data)
        return True
    except Exception as e:
        print(f"Error parsing table: {e}")
        return False

def scrape_today():
    today = datetime.now().date()
    date_str = today.strftime('%Y-%m-%d')
    csv_filename = f"{date_str.replace('-', '_')}.csv"
    csv_path = os.path.join(data_folder, csv_filename)
    if os.path.exists(csv_path):
        print(f'⏭ Skipping {date_str} - file already exists')
        return True
    # No rate limiting needed for single daily request
    session, token = get_csrf_token()
    if not session or not token:
        print(f"Failed to get token for {date_str}")
        return False
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest',
        'Connection': 'keep-alive',
        'Referer': 'https://www.sharesansar.com/today-share-price'
    }
    data = {
        '_token': token,
        'sector': 'all_sec',
        'date': date_str
    }
    print(f'Making API request for {date_str}...')
    try:
        response = session.post(api_url, headers=headers, data=data, timeout=30)
        response.raise_for_status()
        if response.text.strip():
            if save_table_to_csv(response.text, csv_path):
                print(f'✓ Saved {csv_path}')
                return True
            else:
                print(f'✗ No valid table data for {date_str}')
                return False
        else:
            print(f'✗ Empty response for {date_str}')
            return False
    except requests.exceptions.RequestException as e:
        print(f'✗ Request error for {date_str}: {e}')
        return False
    except Exception as e:
        print(f'✗ Error processing {date_str}: {e}')
        return False

def main():
    print(f"Starting ShareSansar API daily scraping for today: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"Output folder: {data_folder}")
    print("-" * 60)
    success = scrape_today()
    if success:
        print("✓ Daily scrape successful.")
    else:
        print("✗ Daily scrape failed.")

if __name__ == "__main__":
    main()
