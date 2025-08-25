import os
import csv
import time
import requests
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
import threading

# Constants
data_folder = 'sharesansarAPI'
api_url = 'https://www.sharesansar.com/ajaxtodayshareprice'
start_date = datetime(2020, 1, 1)
end_date = datetime.now()
max_workers = 3  # Limit concurrent requests to avoid overloading server
delay_between_requests = 2  # seconds

# Ensure output folder exists
os.makedirs(data_folder, exist_ok=True)

# Thread lock for rate limiting
request_lock = threading.Lock()
last_request_time = 0

def rate_limited_request():
    """Ensure minimum delay between requests"""
    global last_request_time
    with request_lock:
        current_time = time.time()
        time_since_last = current_time - last_request_time
        if time_since_last < delay_between_requests:
            time.sleep(delay_between_requests - time_since_last)
        last_request_time = time.time()

def is_weekend(date):
    """Check if date is Friday (4) or Saturday (5) - market closed days in Nepal"""
    return date.weekday() in [4, 5]

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
        # Look for the table in the response
        table = soup.find('table')
        if not table:
            return False
        rows = table.find_all('tr')
        if not rows or len(rows) < 2:
            return False
        # Only save if there is at least one valid data row (not just header, not 'No data found')
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

def scrape_date_api(date_str, csv_path):
    """Scrape data for a specific date using API"""
    try:
        # Rate limiting
        rate_limited_request()
        
        # Get fresh session and token
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

def generate_date_range(start_date, end_date):
    """Generate list of dates to scrape, excluding weekends"""
    dates = []
    current = start_date
    while current <= end_date:
        if not is_weekend(current):
            dates.append(current)
        current += timedelta(days=1)
    return dates

def scrape_date_wrapper(date):
    """Wrapper function for concurrent execution"""
    date_str = date.strftime('%Y-%m-%d')
    csv_filename = f"{date_str.replace('-', '_')}.csv"
    csv_path = os.path.join(data_folder, csv_filename)
    
    # Check if file already exists
    if os.path.exists(csv_path):
        print(f'⏭ Skipping {date_str} - file already exists')
        return True
        
    return scrape_date_api(date_str, csv_path)

def main():
    """Main function to orchestrate the scraping"""
    print(f"Starting ShareSansar API scraping from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"Output folder: {data_folder}")
    print(f"Max concurrent workers: {max_workers}")
    print(f"Delay between requests: {delay_between_requests} seconds")
    print("-" * 60)
    
    # Generate date range
    dates_to_scrape = generate_date_range(start_date, end_date)
    total_dates = len(dates_to_scrape)
    print(f"Total trading days to process: {total_dates}")
    
    if not dates_to_scrape:
        print("No dates to scrape!")
        return
    
    # Test with a single date first
    print("\nTesting with the most recent date...")
    test_date = dates_to_scrape[-1]
    if scrape_date_wrapper(test_date):
        print("✓ Test successful, proceeding with batch processing...\n")
    else:
        print("✗ Test failed, please check the API or token extraction")
        return
    
    # Process dates concurrently
    successful = 0
    failed = 0
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_date = {executor.submit(scrape_date_wrapper, date): date for date in dates_to_scrape}
        
        # Process completed tasks
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
    
    # Summary
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
    print(f"Files saved in: {os.path.abspath(data_folder)}")

if __name__ == "__main__":
    main()
