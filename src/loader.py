"""
Data Loader (ELT)
=================

Loads raw Telegram JSON data from the data lake into PostgreSQL.
It creates the `raw` schema and `telegram_messages` table if they don't exist.

Usage:
    python src/loader.py

Author: Kara Solutions Data Engineering Team
"""

import os
import json
import logging
import glob
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.dialects.postgresql import JSONB

# Load environment variables
load_dotenv()

# Logging Setup
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'loader.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data', 'raw', 'telegram_messages')

def get_db_engine():
    """Creates a SQLAlchemy engine."""
    if not all([DB_NAME, DB_USER, DB_PASSWORD]):
        raise ValueError("Missing DB credentials in .env")
    
    url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(url)

def init_db(engine):
    """Initializes the raw schema and generic table."""
    with engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw;"))
        
        # Create table with raw_payload as JSONB for flexibility
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS raw.telegram_messages (
                message_id BIGINT,
                channel_name TEXT,
                message_date TIMESTAMP,
                message_text TEXT,
                views INTEGER,
                forwards INTEGER,
                has_media BOOLEAN,
                image_path TEXT,
                raw_payload JSONB,
                loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (channel_name, message_id)
            );
        """))
        conn.commit()
    logger.info("Database initialized (raw.telegram_messages).")

def load_data(engine):
    """Iterates over JSON files and loads them into Postgres."""
    json_files = glob.glob(os.path.join(DATA_DIR, '*', '*.json'))
    logger.info(f"Found {len(json_files)} JSON files to process.")
    
    total_loaded = 0
    
    with engine.connect() as conn:
        for file_path in json_files:
            try:
                logger.info(f"Processing file: {file_path}")
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                logger.info(f"Read data type: {type(data)}, length: {len(data) if data else 'None'}")

                if not data:
                    logger.warning(f"Data is empty for {file_path}")
                    continue
                
                # We use ON CONFLICT DO NOTHING to simple idempotency for this raw load
                insert_query = text("""
                    INSERT INTO raw.telegram_messages (
                        message_id, channel_name, message_date, message_text, 
                        views, forwards, has_media, image_path, raw_payload
                    ) VALUES (
                        :message_id, :channel_name, :message_date, :message_text, 
                        :views, :forwards, :has_media, :image_path, :raw_payload
                    )
                    ON CONFLICT (channel_name, message_id) DO NOTHING;
                """)

                # Prepare data for insertion
                prepared_data = []
                for msg in data:
                    msg_copy = msg.copy()
                    # Serialize dictionary to JSON string for JSONB column
                    if isinstance(msg_copy.get('raw_payload'), dict):
                        msg_copy['raw_payload'] = json.dumps(msg_copy['raw_payload'], default=str)
                    
                    # Remove keys not in the table
                    msg_copy.pop('media_type', None)
                    prepared_data.append(msg_copy)

                # Batch insert
                conn.execute(insert_query, prepared_data)
                conn.commit()
                
                count = len(prepared_data)
                total_loaded += count
                logger.info(f"Loaded {count} messages from {os.path.basename(file_path)}")
                
            except Exception as e:
                logger.error(f"Failed to load {file_path}: {e}")

    logger.info(f"Total messages loaded: {total_loaded}")

if __name__ == '__main__':
    try:
        engine = get_db_engine()
        init_db(engine)
        load_data(engine)
    except Exception as e:
        logger.critical(f"Loader failed: {e}", exc_info=True)
