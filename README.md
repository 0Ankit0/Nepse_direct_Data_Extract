# Nepse Direct Data Extract

This project automates the extraction, processing, and storage of Nepse stock and indices data. It uses Python scripts and a SQLite database, with daily updates managed via GitHub Actions.

## Features
- Scrapes daily stock and indices data from online sources
- Imports CSV data into a SQLite database (`historicdata.sqlite`)
- Maintains company listings and other relevant data
- Automates daily updates and pushes changes to GitHub

## Folder Structure
- `sharesansarAPI/` — Daily stock CSV files
- `Indices/` — Daily indices CSV files
- `historicdata.sqlite` — Main SQLite database
- `import_sharesansar_to_db.py` — Imports stock CSVs to database
- `import_indices_to_db.py` — Imports Indices CSVs to database
- `import_today_data.py` — Imports today's data if files exist
- `scrape_company_listings.py` — Scrapes company listings
- `.github/workflows/daily_scraper.yml` — GitHub Actions workflow for daily automation

## Setup
1. Install Python 3.10 or higher
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   playwright install
   ```
3. Place daily CSV files in `sharesansarAPI/` and `Indices/` folders

## Usage
- To import all stock data:
  ```bash
  python import_sharesansar_to_db.py
  ```
- To import all Indices data:
  ```bash
  python import_indices_to_db.py
  ```
- To import today's data (if files exist):
  ```bash
  python import_today_data.py
  ```
- To scrape company listings:
  ```bash
  python scrape_company_listings.py
  ```

## Automation
- The GitHub Actions workflow (`.github/workflows/daily_scraper.yml`) runs daily:
  - Scrapes new data
  - Imports today's data to the database
  - Commits and pushes all changes to GitHub

## Requirements
- Python 3.10+
- Playwright
- pandas, requests, beautifulsoup4, psycopg2-binary (for legacy support)

