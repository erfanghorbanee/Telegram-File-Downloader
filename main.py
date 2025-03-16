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

def cleanup_incomplete_files(output_dir):
    """Remove any leftover .tmp files from interrupted downloads."""
    for file in os.listdir(output_dir):
        if file.endswith(".tmp"):
            temp_file_path = os.path.join(output_dir, file)
            logging.warning(f"Removing incomplete file: {temp_file_path}")
            os.remove(temp_file_path)

def create_directory_if_needed(directory):
    """Creates the directory if it does not exist."""
    if not os.path.exists(directory):
        os.makedirs(directory)

def check_and_download_file(message, file_path):
    """Downloads the file with a temporary name and renames it after completion."""
    try:
        # Skip downloading if the file already exists
        if os.path.exists(file_path):
            logging.info(f"File already exists: {file_path}, skipping download.")
            return file_path, os.path.getsize(file_path)

        temp_file_path = file_path + ".tmp"

        # Download the file as a .tmp file first
        downloaded_file = telegram_client.download_media(message, file=temp_file_path)

        if downloaded_file:
            os.rename(temp_file_path, file_path)  # Rename only if download is successful
            logging.info(f"Downloaded: {file_path}")
            return file_path, os.path.getsize(file_path)
    except Exception as error:
        logging.error(f"Failed to download file: {error}")
    return None, 0

def download_channel_files(channel_name, file_type=None, save_directory=".", message_limit=100):
    create_directory_if_needed(save_directory)
    cleanup_incomplete_files(save_directory)
    
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
                        downloaded_file, file_size = check_and_download_file(message, file_path)
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
                        downloaded_file, file_size = check_and_download_file(message, file_path)
                        if downloaded_file:
                            total_file_size += file_size
                            total_files_downloaded += 1

    logging.info(f"\nSummary: Total files downloaded: {total_files_downloaded}, Total size: {total_file_size / (1024 * 1024):.2f} MB")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download files from a Telegram channel."
    )
    parser.add_argument("channel", type=str, help="The username or ID of the Telegram channel.")
    parser.add_argument("-f", "--format", type=str, help=f"The type of files to download. Supported types: {', '.join(FILE_CATEGORIES.keys())} "
        f"or specific extensions (e.g., pdf, jpg). If not specified, downloads all media.")
    parser.add_argument("-o", "--output", type=str, default=".", help="The directory to save downloaded files. Defaults to the current directory.")
    parser.add_argument("-l", "--limit", type=int, default=100, help="The maximum number of messages to fetch. Use 0 for no limit. Defaults to 100.")

    args = parser.parse_args()

    try:
        download_channel_files(args.channel, args.format, args.output, args.limit)
    except Exception as error:
        logging.error(f"An error occurred: {error}")
