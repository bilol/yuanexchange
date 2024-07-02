import requests
import csv
import logging
from datetime import date
import psycopg2
from decimal import Decimal
from src.config.settings import db_params
from src.utils.logging import setup_logging

logger = setup_logging()

def fetch_cbu_rates():
    try:
        url = "https://cbu.uz/oz/services/open_data/rates/csv/"
        response = requests.get(url)
        response.raise_for_status()
        csv_data = response.text

        exchange_rates = []
        reader = csv.DictReader(csv_data.splitlines(), delimiter=';')

        for row in reader:
            if row['G1'] in ['USD', 'CNY']:
                exchange_rates.append({
                    'date': date.today().strftime('%Y-%m-%d'),
                    'currency': row['G1'],
                    'rate': Decimal(row['G4'])
                })

        logger.info("Fetched exchange rates: %s", exchange_rates)
        return exchange_rates
    except Exception as e:
        logger.error(f"Error fetching exchange rates: {e}")
        raise RuntimeError(f"Error fetching exchange rates: {e}")

def update_cbu_rates(exchange_rates):
    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
        for rate in exchange_rates:
            currency = rate['currency']
            base_rate = rate['rate']
            upsert_query = """
            INSERT INTO cbu_rates (date, currency, rate)
            VALUES (%s, %s, %s)
            ON CONFLICT (date, currency)
            DO UPDATE SET rate = EXCLUDED.rate;
            """
            cur.execute(upsert_query, (rate['date'], currency, base_rate))
            logger.info(f"Upserted CBU rates: {rate['date']} - {currency} - Rate: {base_rate}")
        
        conn.commit()
        cur.close()
        conn.close()
        logger.info("Successfully upserted all CBU rates.")
    except Exception as e:
        logger.error(f"Error upserting CBU rates: {e}")
        raise RuntimeError(f"Error upserting CBU rates: {e}")

def update_exchange_rates():
    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
        cur.execute("SELECT currency, rate FROM cbu_rates WHERE date = CURRENT_DATE")
        cbu_rates = cur.fetchall()
        if not cbu_rates:
            raise RuntimeError("No CBU rates found for today.")
        rates_dict = {rate[0]: rate[1] for rate in cbu_rates}
        usd_to_cny = rates_dict['USD'] / rates_dict['CNY']
        cny_to_usd = rates_dict['CNY'] / rates_dict['USD']

        rates_to_insert = [
            {'currency': 'USD', 'buy_rate': rates_dict['USD'] - 5, 'sell_rate': rates_dict['USD'] + 40},
            {'currency': 'CNY', 'buy_rate': rates_dict['CNY'] - 10, 'sell_rate': rates_dict['CNY'] + 50}
        ]

        for rate in rates_to_insert:
            upsert_query = """
            INSERT INTO exchange_rates (date, currency, buy_rate, sell_rate)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (date, currency)
            DO UPDATE SET buy_rate = EXCLUDED.buy_rate, sell_rate = EXCLUDED.sell_rate;
            """
            cur.execute(upsert_query, (date.today(), rate['currency'], rate['buy_rate'], rate['sell_rate']))
            logger.info(f"Upserted exchange rates: {date.today()} - {rate['currency']} - BUY: {rate['buy_rate']}, SELL: {rate['sell_rate']}")
        
        conn.commit()
        cur.close()
        conn.close()
        logger.info("Successfully upserted all exchange rates.")
    except Exception as e:
        logger.error(f"Error updating exchange rates: {e}")
        raise RuntimeError(f"Error updating exchange rates: {e}")
