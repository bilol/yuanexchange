import psycopg2
from psycopg2 import sql
from src.config.settings import db_params
import logging

logger = logging.getLogger(__name__)

def get_db_connection():
    try:
        conn = psycopg2.connect(**db_params)
        return conn
    except Exception as e:
        logger.error(f"Error connecting to the database: {e}")
        raise

def create_tables():
    """Create necessary tables in the database if they do not exist."""
    create_users_table = """
    CREATE TABLE IF NOT EXISTS users (
        user_id BIGINT PRIMARY KEY,
        first_name VARCHAR(255),
        last_name VARCHAR(255),
        username VARCHAR(255),
        phone_number VARCHAR(255),
        user_lang VARCHAR(10),
        date_joined TIMESTAMP,
        user_status VARCHAR(20)
    );
    """
    create_transactions_table = """
    CREATE TABLE IF NOT EXISTS transactions (
        id SERIAL PRIMARY KEY,
        user_id BIGINT,
        timestamp TIMESTAMP,
        exchange_type VARCHAR(20),
        amount DECIMAL,
        rate DECIMAL,
        received_amount DECIMAL,
        status VARCHAR(20) DEFAULT 'pending'
    );
    """
    create_cbu_rates_table = """
    CREATE TABLE IF NOT EXISTS cbu_rates (
        date DATE,
        currency VARCHAR(3),
        rate DECIMAL,
        PRIMARY KEY (date, currency)
    );
    """
    create_exchange_rates_table = """
    CREATE TABLE IF NOT EXISTS exchange_rates (
        date DATE,
        currency VARCHAR(3),
        buy_rate DECIMAL,
        sell_rate DECIMAL,
        PRIMARY KEY (date, currency)
    );
    """

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(create_users_table)
    cur.execute(create_transactions_table)
    cur.execute(create_cbu_rates_table)
    cur.execute(create_exchange_rates_table)
    conn.commit()
    cur.close()
    conn.close()
    logger.info("Tables created or verified successfully.")
