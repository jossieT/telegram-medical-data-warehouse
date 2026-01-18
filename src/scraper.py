"""
Telegram Data Scraper
=====================

This script extracts messages and metadata from public Telegram channels and stores them
in a raw data lake structure. It separates JSON data and image assets.

Usage:
    python src/scraper.py

Author: Kara Solutions Data Engineering Team
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timezone
import shutil
from typing import Optional, Dict, List, Any

from telethon import TelegramClient, events
from telethon.errors import FloodWaitError, ChannelPrivateError
from telethon.tl.types import MessageMediaPhoto
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
CHANNELS = [
    'https://t.me/CheMed123',
    'https://t.me/lobelia4cosmetics',
    'https://t.me/tikvahpharma',
]

# Paths
# Get the absolute path of the directory containing this script (src/)
SCRAPER_DIR = os.path.dirname(os.path.abspath(__file__))
# Get project root (parent of src/)
PROJECT_ROOT = os.path.dirname(SCRAPER_DIR)

BASE_DATA_DIR = os.path.join(PROJECT_ROOT, 'data', 'raw')
LOG_DIR = os.path.join(PROJECT_ROOT, 'logs')

# Configure Logging
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'scraper.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TelegramScraper:
    """
    Handles scraping of Telegram channels, data extraction, and asset downloading.
    """

    def __init__(self, api_id: str, api_hash: str):
        if not api_id or not api_hash:
            raise ValueError("API_ID and API_HASH must be set in .env file")
        
        self.client = TelegramClient('scraper_session', int(api_id), api_hash)
        self.today_str = datetime.now().strftime('%Y-%m-%d')
        
        # Ensure directories exist
        self.messages_dir = os.path.join(BASE_DATA_DIR, 'telegram_messages', self.today_str)
        self.images_base_dir = os.path.join(BASE_DATA_DIR, 'images')
        
        os.makedirs(self.messages_dir, exist_ok=True)
        os.makedirs(self.images_base_dir, exist_ok=True)

    async def start(self):
        """Starts the Telethon client."""
        await self.client.start()
        logger.info("Telegram client started successfully.")

    async def scrape_channels(self, channels: List[str]):
        """Main loop to scrape a list of channels."""
        logger.info(f"Starting scrape for {len(channels)} channels.")
        
        for channel_url in channels:
            try:
                await self.scrape_single_channel(channel_url)
            except Exception as e:
                logger.error(f"Failed to scrape channel {channel_url}: {e}", exc_info=True)

    async def scrape_single_channel(self, channel_url: str):
        """Scrapes messages from a single channel."""
        channel_name = channel_url.split('/')[-1]
        logger.info(f"Scraping channel: {channel_name}")
        
        os.makedirs(os.path.join(self.images_base_dir, channel_name), exist_ok=True)
        
        messages_data = []
        message_count = 0
        error_count = 0
        
        try:
            entity = await self.client.get_entity(channel_url)
            
            # Iterate through messages history with a limit of 200
            async for message in self.client.iter_messages(entity, limit=200):
                try:
                    data = await self.process_message(message, channel_name)
                    if data:
                        messages_data.append(data)
                        message_count += 1
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error processing message {message.id} in {channel_name}: {e}")
            
            # Save Batch
            if messages_data:
                self.save_json(channel_name, messages_data)
                
            logger.info(f"Finished {channel_name}: Extracted {message_count} messages, {error_count} errors.")
            
        except FloodWaitError as e:
            logger.warning(f"FloodWaitError: Sleeping for {e.seconds} seconds.")
            await asyncio.sleep(e.seconds)
            # Retry logic could be added here, currently just logging and skipping remainder of channel
        except ChannelPrivateError:
            logger.error(f"Channel {channel_name} is private or inaccessible.")
        except Exception as e:
             logger.error(f"Critical error processing channel {channel_name}: {e}")

    async def process_message(self, message, channel_name: str) -> Dict[str, Any]:
        """Extracts fields and downloads media."""
        msg_id = message.id
        
        # Determine media info
        has_media = bool(message.media)
        media_type = 'none'
        image_path = None
        
        if has_media:
            if isinstance(message.media, MessageMediaPhoto):
                media_type = 'photo'
                # Download Image
                filename = f"{msg_id}.jpg"
                save_path = os.path.join(self.images_base_dir, channel_name, filename)
                
                # Check if exists to avoid re-downloading (optional optimization)
                if not os.path.exists(save_path):
                    try:
                        await self.client.download_media(message, file=save_path)
                        image_path = save_path
                    except Exception as e:
                        logger.error(f"Failed to download image for msg {msg_id}: {e}")
                else:
                    image_path = save_path
            elif getattr(message, 'document', None):
                media_type = 'document'
            elif getattr(message, 'video', None):
                media_type = 'video'
            else:
                media_type = 'other'

        # Extract Raw Payload (Telethon object to dict is complex, utilizing to_dict() if available or just str)
        # message.to_dict() gives a full JSON serializable dict
        raw_payload = message.to_dict()

        return {
            "message_id": msg_id,
            "channel_name": channel_name,
            "message_date": message.date.isoformat() if message.date else None,
            "message_text": message.message,
            "views": message.views if message.views else 0,
            "forwards": message.forwards if message.forwards else 0,
            "has_media": has_media,
            "media_type": media_type,
            "image_path": image_path,
            "raw_payload": raw_payload
        }

    def save_json(self, channel_name: str, data: List[Dict[str, Any]]):
        """Saves the extracted data to a JSON file."""
        file_path = os.path.join(self.messages_dir, f"{channel_name}.json")
        try:
            # Custom JSON encoder for datetime objects inside raw_payload if needed
            # to_dict() usually handles standard types, but datetime might remain.
            # We'll use a default converter.
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4, default=str)
            logger.info(f"Saved {len(data)} records to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save JSON for {channel_name}: {e}")

async def main():
    logger.info("Script started.")
    
    if not API_ID or not API_HASH:
        logger.error("API_ID or API_HASH missing. Exiting.")
        return

    scraper = TelegramScraper(API_ID, API_HASH)
    
    try:
        await scraper.start()
        await scraper.scrape_channels(CHANNELS)
    except Exception as e:
        logger.critical(f"Global execution failed: {e}", exc_info=True)
    finally:
        await scraper.client.disconnect()
        logger.info("Script finished.")

if __name__ == '__main__':
    asyncio.run(main())
