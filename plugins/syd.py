import logging
import re
import asyncio
from utils import temp
from info import ADMINS
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait
from pyrogram.errors.exceptions.bad_request_400 import ChannelInvalid, ChatAdminRequired, UsernameInvalid, UsernameNotModified
from database.ia_filterdb import save_file
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
lock = asyncio.Lock()

# Channel ID as an integer
INDEX_CHANNEL = [-1002498086501, -1003164435604, -1002901811032, -1003183027276, -1003137700522]

@Client.on_message(filters.document | filters.audio | filters.video)
async def auto(bot, message):
    # Check if the message is from the specified channel
    if message.chat.id in INDEX_CHANNEL:
        # Log the received media for tracking purposes
        logger.info(f"Received {message.media.value} from {message.chat.title or message.chat.id}")

        # Check if the media attribute exists
        if message.media:
            # Extract the media type
            media_type = message.media.value
            media = getattr(message, media_type, None)

            if media:
                media.file_type = media_type
                media.caption = message.caption
                
                # Save the media file
                try:
                    aynav, vnay = await save_file(media, 4)
                    if aynav:
                        logger.info("File successfully indexed and saved.")
                    elif vnay == 0:
                        logger.info("Duplicate file was skipped.")
                    elif vnay == 2:
                        logger.error("Error(index) occurred")
                    
                except Exception as e:
                    logger.exception("Failed to save file: %s", e)
                    await message.reply(f"An error occurred while processing the file. {e}")
            else:
                logger.warning("No media found in the message.")
        else:
            logger.warning("Message does not contain media.")
