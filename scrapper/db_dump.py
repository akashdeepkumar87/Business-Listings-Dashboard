"""
db_dump.py — Export Railway MySQL → listing_master.sql
=======================================================
Since Railway free tier doesn't expose mysqldump directly,
this script exports the full table as a valid .sql file
using Python + mysql-connector.

Output: dump/listing_master.sql

Run:
  python db_dump.py
"""

import os
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import mysql.connector

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

load_dotenv()

DB_CONFIG = {
    "host":     os.getenv("DB_HOST"),
    "port":     int(os.getenv("DB_PORT", 3306)),
    "user":     os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}

TABLE   = "listing_master"
OUT_DIR = Path("dump")


def escape(val) -> str:
    """Safely escape a value for SQL INSERT output."""
    if val is None:
        return "NULL"
    s = str(val).replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n").replace("\r", "\\r")
    return f"'{s}'"


def dump_table(cursor) -> tuple[str, int]:
    """Build the full SQL dump string for listing_master."""

    # ── Table structure ───────────────────────────────────────────────────────
    ddl = f"""-- ============================================================
-- BizDash — Database Dump
-- Table : {TABLE}
-- Generated : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- ============================================================

SET NAMES utf8mb4;
SET foreign_key_checks = 0;
SET sql_mode = 'NO_AUTO_VALUE_ON_ZERO';

-- Drop & recreate table
DROP TABLE IF EXISTS `{TABLE}`;

CREATE TABLE `{TABLE}` (
  `id`            INT          NOT NULL AUTO_INCREMENT,
  `business_name` VARCHAR(255) NOT NULL,
  `category`      VARCHAR(100) NOT NULL,
  `city`          VARCHAR(100) NOT NULL,
  `address`       TEXT,
  `phone`         VARCHAR(50)  DEFAULT NULL,
  `source`        VARCHAR(100) NOT NULL,
  `created_at`    DATETIME     DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `idx_city`     (`city`),
  INDEX `idx_category` (`category`),
  INDEX `idx_source`   (`source`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

"""

    # ── Row data ──────────────────────────────────────────────────────────────
    cursor.execute(f"""
        SELECT id, business_name, category, city, address, phone, source, created_at
        FROM {TABLE}
        ORDER BY id
    """)
    rows = cursor.fetchall()

    if not rows:
        return ddl + f"\n-- No rows found in {TABLE}\n", 0

    # Batch inserts — 100 rows per statement for readability
    BATCH = 100
    insert_lines = [f"\n-- Data for `{TABLE}` ({len(rows)} rows)\n"]
    insert_lines.append(f"LOCK TABLES `{TABLE}` WRITE;\n")

    for i in range(0, len(rows), BATCH):
        batch = rows[i : i + BATCH]
        values = []
        for row in batch:
            vals = ", ".join(escape(v) for v in row)
            values.append(f"  ({vals})")
        stmt = (
            f"INSERT INTO `{TABLE}` "
            f"(`id`, `business_name`, `category`, `city`, `address`, `phone`, `source`, `created_at`) VALUES\n"
            + ",\n".join(values)
            + ";\n"
        )
        insert_lines.append(stmt)

    insert_lines.append(f"\nUNLOCK TABLES;\n")
    insert_lines.append(f"\nSET foreign_key_checks = 1;\n")

    return ddl + "\n".join(insert_lines), len(rows)


def main():
    logger.info("Connecting to Railway MySQL ...")
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as e:
        logger.error(f"Connection failed: {e}")
        logger.error("Check your .env file (DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)")
        raise

    logger.info("Connected ✅")
    cursor = conn.cursor()

    logger.info(f"Dumping table: {TABLE}")
    sql_content, row_count = dump_table(cursor)

    cursor.close()
    conn.close()

    # Write output file
    OUT_DIR.mkdir(exist_ok=True)
    out_file = OUT_DIR / f"{TABLE}.sql"
    out_file.write_text(sql_content, encoding="utf-8")

    logger.info(f"\n✅  Dump complete!")
    logger.info(f"    Rows exported : {row_count}")
    logger.info(f"    Output file   : {out_file}  ({out_file.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()