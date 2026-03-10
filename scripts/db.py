"""
Database connection helper for Supabase (PostgreSQL).

Reads credentials from environment variables:
  PGHOST      - Supabase database host (e.g. db.<project>.supabase.co)
  PGPORT      - Database port (default: 5432)
  PGDATABASE  - Database name (default: postgres)
  PGUSER      - Database user (default: postgres)
  PGPASSWORD  - Database password

These are set via GitHub Actions secrets or a local .env file.
"""

# load environment variables from a .env file if present
# (install python-dotenv in requirements.txt or via pip)
from dotenv import load_dotenv
load_dotenv()

import os
import psycopg2


def get_connection():
    """Return a new psycopg2 connection using env-var credentials."""
    return psycopg2.connect(
        os.environ.get('DATABASE_URL', 'localhost')
    )
