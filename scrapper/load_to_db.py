"""
DB Loader: Bulk Insert listings.csv → Railway MySQL
=====================================================
Reads listings.csv produced by scraper.py and inserts
all rows into listing_master using batch inserts (1000 rows/batch).

Setup:
  pip install mysql-connector-python pandas python-dotenv

Usage:
  1. Copy your Railway credentials into .env (see .env.example)
  2. Run:  python load_to_db.py
"""

import os
import math
import logging
import pandas as pd
import mysql.connector
from dotenv import load_dotenv

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ─── Config ───────────────────────────────────────────────────────────────────
load_dotenv()

DB_CONFIG = {
    "host":     os.getenv("DB_HOST"),
    "port":     int(os.getenv("DB_PORT", 3306)),
    "user":     os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}

CSV_FILE   = "../Scrapper/listings.csv"
BATCH_SIZE = 500   # rows per INSERT statement


# ─── Insert Logic ─────────────────────────────────────────────────────────────
INSERT_SQL = """
    INSERT INTO listing_master
        (business_name, category, city, address, phone, source, created_at)
    VALUES
        (%s, %s, %s, %s, %s, %s, %s)
"""

def clean_row(row) -> tuple:
    """Convert a DataFrame row to a DB-ready tuple."""
    phone = row.get("phone")
    # treat float NaN / string "nan" / "None" as NULL
    if pd.isna(phone) or str(phone).strip().lower() in ("nan", "none", ""):
        phone = None

    return (
        str(row["business_name"]).strip()[:255],
        str(row["category"]).strip()[:100],
        str(row["city"]).strip()[:100],
        str(row["address"]).strip() if row.get("address") else None,
        phone,
        str(row["source"]).strip()[:100],
        str(row["created_at"]),
    )


def load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} rows from {path}")
    required = {"business_name", "category", "city", "source"}
    missing  = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV is missing columns: {missing}")
    return df


def bulk_insert(df: pd.DataFrame, cursor) -> int:
    rows       = [clean_row(row) for _, row in df.iterrows()]
    total      = len(rows)
    batches    = math.ceil(total / BATCH_SIZE)
    inserted   = 0

    for i in range(batches):
        batch = rows[i * BATCH_SIZE : (i + 1) * BATCH_SIZE]
        cursor.executemany(INSERT_SQL, batch)
        inserted += len(batch)
        logger.info(f"  Batch {i+1}/{batches} → {inserted}/{total} rows inserted")

    return inserted


def main():
    # ── 1. Load CSV ───────────────────────────────────────────────────────────
    df = load_csv(CSV_FILE)

    # ── 2. Connect to Railway MySQL ───────────────────────────────────────────
    logger.info(f"Connecting to MySQL at {DB_CONFIG['host']}:{DB_CONFIG['port']} ...")
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as e:
        logger.error(f"Connection failed: {e}")
        logger.error("Check your .env file: see .env.example for the required keys")
        raise

    logger.info("Connected ✅")
    cursor = conn.cursor()

    # ── 3. Create table if it doesn't exist ───────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS listing_master (
            id            INT AUTO_INCREMENT PRIMARY KEY,
            business_name VARCHAR(255)  NOT NULL,
            category      VARCHAR(100)  NOT NULL,
            city          VARCHAR(100)  NOT NULL,
            address       TEXT,
            phone         VARCHAR(50)   DEFAULT NULL,
            source        VARCHAR(100)  NOT NULL,
            created_at    DATETIME      DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_city     (city),
            INDEX idx_category (category),
            INDEX idx_source   (source)
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    """)
    conn.commit()
    logger.info("Table listing_master ready")

    # ── 4. Optional: clear existing data before fresh insert ─────────────────
    cursor.execute("SELECT COUNT(*) FROM listing_master")
    existing = cursor.fetchone()[0]
    if existing > 0:
        logger.info(f"Table already has {existing} rows: clearing before re-insert")
        cursor.execute("TRUNCATE TABLE listing_master")
        conn.commit()

    # ── 5. Bulk insert ────────────────────────────────────────────────────────
    logger.info(f"Inserting {len(df)} rows in batches of {BATCH_SIZE} ...")
    inserted = bulk_insert(df, cursor)
    conn.commit()

    # ── 6. Verify ─────────────────────────────────────────────────────────────
    cursor.execute("SELECT COUNT(*) FROM listing_master")
    count = cursor.fetchone()[0]
    logger.info(f"\n✅  Insert complete: {count} rows now in listing_master")

    # Quick sanity check
    cursor.execute("SELECT city, COUNT(*) as cnt FROM listing_master GROUP BY city ORDER BY cnt DESC")
    logger.info("\n📊  City distribution in DB:")
    for city, cnt in cursor.fetchall():
        logger.info(f"    {city:<15} {cnt}")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    main()
