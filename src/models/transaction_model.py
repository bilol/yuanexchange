from datetime import datetime
from src.models.db import get_db_connection
from src.utils.logging import setup_logging

logger = setup_logging()

def log_transaction(user_id, exchange_type, amount, rate, received_amount):
    conn = get_db_connection()
    cur = conn.cursor()
    insert_query = """
    INSERT INTO transactions (user_id, timestamp, exchange_type, amount, rate, received_amount)
    VALUES (%s, %s, %s, %s, %s, %s);
    """
    cur.execute(insert_query, (user_id, datetime.now(), exchange_type, amount, rate, received_amount))
    conn.commit()
    cur.close()
    conn.close()
    logger.info(f"Transaction logged: {user_id}, {exchange_type}, {amount}, {rate}, {received_amount}")

def fetch_user_transactions(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    select_query = """
    SELECT timestamp, exchange_type, amount, rate, received_amount
    FROM transactions
    WHERE user_id = %s
    ORDER BY timestamp DESC
    LIMIT 5;
    """
    cur.execute(select_query, (user_id,))
    transactions = cur.fetchall()
    cur.close()
    conn.close()
    return transactions

def fetch_user_transactions_for_today():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT t.timestamp, t.exchange_type, t.amount, t.rate, t.received_amount, u.username, u.phone_number
    FROM transactions t
    JOIN users u ON t.user_id = u.user_id
    WHERE DATE(t.timestamp) = CURRENT_DATE
    """)
    transactions = cur.fetchall()
    cur.close()
    conn.close()
    return transactions

def update_transaction_status(transaction_id, status):
    conn = get_db_connection()
    cur = conn.cursor()
    update_query = """
    UPDATE transactions
    SET status = %s
    WHERE id = %s;
    """
    cur.execute(update_query, (status, transaction_id))
    conn.commit()
    cur.close()
    conn.close()
    logger.info(f"Transaction {transaction_id} status updated to {status}.")
