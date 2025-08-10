# NEPSE Historical Data Scraper

A Python project to scrape historical stock market data from the Nepal Stock Exchange (NEPSE) using the [nepse_scraper](https://github.com/polymorphisma/nepse_scraper/) package.

## 🚀 Features

- **Comprehensive Data Scraping**: Download historical data for all listed securities on NEPSE
- **Flexible Date Ranges**: Scrape data from today to one year prior (NEPSE API limitation)
- **Multiple Scraping Options**:
  - All securities at once
  - Specific securities only
  - Sample securities for testing
- **CSV Output**: Data saved as individual CSV files per security
- **Error Handling**: Robust error handling with detailed logging
- **Rate Limiting**: Built-in delays to avoid overwhelming the API
- **🐳 Docker Support**: Containerized deployment for consistent, scalable scraping

## 📁 Files

1. **`nepse_historical_scraper.py`** - Full-featured scraper with comprehensive historical data collection
2. **`simple_nepse_scraper.py`** - Simplified version for quick data retrieval
3. **`container_scraper.py`** - Container-optimized scraper with environment variable configuration
4. **`Dockerfile`** - Docker container definition
5. **`docker-compose.yml`** - Multi-container orchestration
6. **`requirements.txt`** - Python dependencies
7. **`data/`** - Directory where CSV files are saved

## 📦 Installation

### Option 1: Local Installation

1. Clone or download this project
2. Install the required packages:

```bash
pip install -r requirements.txt
```

Or install manually:

```bash
pip install nepse-scraper pandas
```

### Option 2: Docker Installation

1. **Build the Docker image:**
   ```bash
   # Linux/Mac
   ./docker-run.sh build
   
   # Windows
   docker-run.bat build
   
   # Or manually
   docker build -t nepse-scraper:latest .
   ```

2. **Quick start with Docker:**
   ```bash
   # Get latest data once
   ./docker-run.sh latest
   
   # Run continuously every 60 minutes
   ./docker-run.sh continuous
   
   # Interactive mode
   ./docker-run.sh interactive
   ```

## 🔧 Usage

### 🐳 Docker Usage (Recommended)

Docker provides consistent, isolated environments and easier deployment:

#### Quick Docker Commands
```bash
# Build the image
./docker-run.sh build

# Get latest market data (one-time)
./docker-run.sh latest

# Run continuous scraping every 30 minutes
./docker-run.sh continuous 30

# Scrape specific securities
./docker-run.sh specific "NABIL,NICA,SCBL,EBL"

# Interactive mode
./docker-run.sh interactive

# View logs of running container
./docker-run.sh logs

# Stop all containers
./docker-run.sh stop
```

#### Docker Compose
```bash
# Start continuous scraper service
docker-compose up -d nepse-scraper

# View logs
docker-compose logs -f nepse-scraper

# Stop service
docker-compose down
```

📖 **For detailed Docker usage, see [DOCKER_README.md](DOCKER_README.md)**

### 💻 Local Usage

#### Option 1: Full Historical Scraper

Run the comprehensive scraper:

```bash
python nepse_historical_scraper.py
```

This script offers three options:

1. **Scrape ALL securities** (Warning: Takes several hours!)
2. **Scrape specific securities** (Enter comma-separated symbols)
3. **Test with sample securities** (NABIL, NICA, SCBL, SANIMA, EBL)

#### Option 2: Simple Scraper

Run the simple scraper for quick data:

```bash
python simple_nepse_scraper.py
```

This script offers:

1. Get latest trading data for all securities
2. Get data for specific securities (with recent history)
3. Get market summary
4. Exit

## Data Format

The scraped data includes the following fields:

- `symbol` - Security symbol (e.g., NABIL, NICA)
- `openPrice` - Opening price
- `highPrice` - Highest price of the day
- `lowPrice` - Lowest price of the day
- `lastTradedPrice` - Last traded price
- `totalTradedQuantity` - Total quantity traded
- `totalTradedValue` - Total value traded
- `date` - Trading date
- Additional market data fields

## Important Notes

### NEPSE API Limitations

- **Date Range**: NEPSE only provides data from today to one year prior
- **Trading Days Only**: Data is only available for trading days (weekdays when market is open)
- **Rate Limiting**: The script includes delays between requests to avoid overloading the API

### Data Accuracy

- Data comes directly from NEPSE's official API
- Historical data may have gaps for non-trading days
- Always verify important data with official NEPSE sources

### Performance Considerations

- Scraping all securities can take several hours
- Use the simple scraper for quick data needs
- Consider scraping specific securities rather than all at once

## Example Usage

### Scrape Specific Securities

```python
from nepse_scraper import Nepse_scraper
import pandas as pd

# Initialize scraper
scraper = Nepse_scraper()

# Get today's data
data = scraper.get_today_price()

# Get specific date data
data = scraper.get_today_price('2024-08-01')

# Get all securities list
securities = scraper.get_all_security()
```

### Sample Output Files

```
data/
├── NABIL_historical_data.csv
├── NICA_historical_data.csv
├── SCBL_historical_data.csv
├── market_summary_20250810_143022.json
└── nepse_latest_data_20250810_143022.csv
```

## Troubleshooting

### Common Issues

1. **Import Error**: Make sure `nepse-scraper` is installed

   ```bash
   pip install nepse-scraper
   ```

2. **No Data Found**: Check if the market is open or if the date is a trading day

3. **API Errors**: The script includes retry logic, but if you get persistent errors:

   - Check your internet connection
   - Try again later (API might be temporarily unavailable)
   - Reduce the frequency of requests by increasing delay

4. **Date Format Errors**: Use YYYY-MM-DD format for dates

### Logging

- Check `nepse_scraper.log` for detailed error logs
- The script provides console output for progress tracking

## Dependencies

- **nepse-scraper**: The main package for NEPSE API access
- **pandas**: For data manipulation and CSV output
- **requests**: HTTP requests (dependency of nepse-scraper)
- **retrying**: Retry logic for failed requests

## Legal and Ethical Usage

- This script uses the official NEPSE API through the nepse_scraper package
- Respect the API rate limits and don't overload the servers
- Use the data responsibly and in accordance with NEPSE's terms of service
- The data is for informational purposes only

## Contributing

Feel free to improve this script by:

- Adding more data validation
- Implementing additional data formats (JSON, Excel)
- Adding more sophisticated error handling
- Optimizing performance

## License

This project is provided as-is for educational and research purposes. Please ensure compliance with NEPSE's terms of service when using this tool.

## Acknowledgments

- Thanks to the developers of the [nepse_scraper](https://github.com/polymorphisma/nepse_scraper/) package
- Nepal Stock Exchange (NEPSE) for providing the API
