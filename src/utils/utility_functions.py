import psycopg2
from src.config.settings import db_params
from decimal import Decimal
from src.utils.logging import setup_logging

logger = setup_logging()

def fetch_current_rates():
    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
        cur.execute("SELECT currency, buy_rate, sell_rate FROM exchange_rates WHERE date = CURRENT_DATE")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        rates = {row[0]: {'buy_rate': row[1], 'sell_rate': row[2]} for row in rows}
        logger.info(f"Fetched rates from database: {rates}")
        return rates
    except Exception as e:
        logger.error(f"Error fetching current rates: {e}")
        return {}

def update_dynamic_spreads():
    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
        cur.execute("""
        WITH transaction_stats AS (
            SELECT
                currency,
                AVG(rate) AS avg_rate,
                STDDEV(rate) AS stddev_rate
            FROM transactions
            GROUP BY currency
        )
        UPDATE spreads
        SET
            buy_spread = avg_rate - (stddev_rate / 2),
            sell_spread = avg_rate + (stddev_rate / 2)
        FROM transaction_stats
        WHERE spreads.currency = transaction_stats.currency;
        """)
        conn.commit()
        cur.close()
        conn.close()
        logger.info("Successfully updated dynamic spreads.")
    except Exception as e:
        logger.error(f"Error updating dynamic spreads: {e}")
