"""
database.py: MySQL connection pool for FastAPI
"""

import os
import mysql.connector
from mysql.connector import pooling
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host":     os.getenv("DB_HOST"),
    "port":     int(os.getenv("DB_PORT", 3306)),
    "user":     os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}

# Connection pool: reuses connections instead of opening a new one per request
connection_pool = pooling.MySQLConnectionPool(
    pool_name="dashboard_pool",
    pool_size=5,
    **DB_CONFIG
)

def get_connection():
    """Get a connection from the pool."""
    return connection_pool.get_connection()
