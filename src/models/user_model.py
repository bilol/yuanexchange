from datetime import datetime
from src.models.db import get_db_connection
from src.utils.logging import setup_logging

logger = setup_logging()

def add_user(user_id, first_name, last_name, username, phone_number, user_lang, date_joined, user_status='pending'):
    """Add a new user to the database with a default status of 'pending'."""
    conn = get_db_connection()
    cur = conn.cursor()
    insert_query = """
    INSERT INTO users (user_id, first_name, last_name, username, phone_number, user_lang, date_joined, user_status)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
    """
    cur.execute(insert_query, (user_id, first_name, last_name, username, phone_number, user_lang, date_joined, user_status))
    conn.commit()
    cur.close()
    conn.close()
    logger.info(f"User {user_id} added to the database with status {user_status}.")


def get_user_status(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    select_query = """
    SELECT user_status FROM users WHERE user_id = %s;
    """
    cur.execute(select_query, (user_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result[0] if result else None

def update_user_status(user_id, status):
    conn = get_db_connection()
    cur = conn.cursor()
    update_query = """
    UPDATE users
    SET user_status = %s
    WHERE user_id = %s;
    """
    cur.execute(update_query, (status, user_id))
    conn.commit()
    cur.close()
    conn.close()

def user_exists(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    check_user_query = """
    SELECT EXISTS(SELECT 1 FROM users WHERE user_id = %s);
    """
    cur.execute(check_user_query, (user_id,))
    exists = cur.fetchone()[0]
    cur.close()
    conn.close()
    return exists

def update_user_language(user_id, language):
    conn = get_db_connection()
    cur = conn.cursor()
    update_query = """
    UPDATE users
    SET user_lang = %s
    WHERE user_id = %s;
    """
    cur.execute(update_query, (language, user_id))
    conn.commit()
    cur.close()
    conn.close()
    logger.info(f"Updated language for user {user_id} to {language}.")

def get_user_language(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_lang FROM users WHERE user_id = %s", (user_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    if result:
        return result[0]
    else:
        return 'en'  # Default language

def get_user_info(user_id):
    """Retrieve user information from the database."""
    conn = get_db_connection()
    cur = conn.cursor()
    select_query = """
    SELECT username, first_name, phone_number FROM users WHERE user_id = %s;
    """
    cur.execute(select_query, (user_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result if result else None