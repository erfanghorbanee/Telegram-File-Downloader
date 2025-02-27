import argparse
import os
import logging
from mimetypes import guess_extension

from dotenv import load_dotenv
from telethon import TelegramClient, sync
from telethon.tl.types import MessageMediaPhoto

# Load environment variables from the .env file
load_dotenv()

API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")

# Initialize the Telegram client with a session name to save the session data
telegram_client = TelegramClient("session_name", API_ID, API_HASH)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Supported file categories
FILE_CATEGORIES = {
    "images": ["jpg", "jpeg", "png", "gif", "bmp"],
    "documents": ["pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx"],
    "videos": ["mp4", "mkv", "avi", "mov", "wmv"],
    "audios": ["mp3", "wav", "aac", "flac", "ogg"],
    "archives": ["zip", "rar", "7z", "tar", "gz"],
}

def create_directory_if_needed(directory):
    """Creates the directory if it does not exist."""
    if not os.path.exists(directory):
        os.makedirs(directory)

def fetch_and_save_file(message, destination_path):
    """Checks if the file exists and downloads it if not, with logging and error handling."""
    try:
        if not os.path.exists(destination_path):
            destination_path = telegram_client.download_media(message, file=destination_path)
            if destination_path:
                logging.info(f"Downloaded: {destination_path}")
                return destination_path, os.path.getsize(destination_path)
        else:
            logging.info(f"File already exists: {destination_path}")
    except Exception as error:
        logging.error(f"Failed to download file: {error}")
    return None, 0

def download_channel_files(channel_name, file_type=None, save_directory=".", message_limit=100):
    create_directory_if_needed(save_directory)
    
    total_file_size = 0
    total_files_downloaded = 0
    message_limit = None if message_limit == 0 else message_limit

    with telegram_client:
        logging.info(f"Fetching messages from channel: {channel_name}")
        messages = telegram_client.iter_messages(channel_name, limit=message_limit)

        for message in messages:
            if message.media:
                if isinstance(message.media, MessageMediaPhoto):
                    if not file_type or file_type.lower() == "images":
                        file_name = f"{message.id}.jpg"
                        file_path = os.path.join(save_directory, file_name)
                        downloaded_file, file_size = fetch_and_save_file(message, file_path)
                        if downloaded_file:
                            total_file_size += file_size
                            total_files_downloaded += 1

                elif message.file:
                    mime_type = message.file.mime_type
                    file_extension = guess_extension(mime_type) if mime_type else None
                    if file_extension is None:
                        file_extension = ""
                    
                    file_name = message.file.name or str(message.id)
                    if file_extension and not file_name.endswith(file_extension):
                        file_name += file_extension

                    file_path = os.path.join(save_directory, file_name)

                    if (
                        not file_type
                        or (
                            file_type.lower() in FILE_CATEGORIES
                            and file_extension.lstrip(".") in FILE_CATEGORIES.get(file_type.lower(), [])
                        )
                        or (file_extension.lstrip(".") == file_type.lower())
                    ):
                        downloaded_file, file_size = fetch_and_save_file(message, file_path)
                        if downloaded_file:
                            total_file_size += file_size
                            total_files_downloaded += 1

    logging.info(f"\nSummary: Total files downloaded: {total_files_downloaded}, Total size: {total_file_size / (1024 * 1024):.2f} MB")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download files from a Telegram channel."
    )
    parser.add_argument(
        "channel", type=str, help="The username or ID of the Telegram channel."
    )
    parser.add_argument(
        "-f",
        "--format",
        type=str,
        help=f"The type of files to download. Supported types: {', '.join(FILE_CATEGORIES.keys())} "
        f"or specific extensions (e.g., pdf, jpg). If not specified, downloads all media.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=".",
        help="The directory to save downloaded files. Defaults to the current directory.",
    )
    parser.add_argument(
        "-l",
        "--limit",
        type=int,
        default=100,
        help="The maximum number of messages to fetch. Use 0 for no limit. Defaults to 100."
    )

    args = parser.parse_args()

    if args.format and args.format.lower() not in FILE_CATEGORIES.keys():
        valid_extensions = {
            ext for types in FILE_CATEGORIES.values() for ext in types
        }
        if args.format.lower() not in valid_extensions:
            logging.error(
                f"Error: Unsupported file format '{args.format}'.\n"
                f"Supported formats are: {', '.join(FILE_CATEGORIES.keys())} or specific extensions: {', '.join(valid_extensions)}."
            )
            exit(1)

    try:
        download_channel_files(args.channel, args.format, args.output, args.limit)
    except Exception as error:
        logging.error(f"An error occurred: {error}")
