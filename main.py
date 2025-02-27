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
client = TelegramClient("session_name", API_ID, API_HASH)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Supported file types
SUPPORTED_FILE_TYPES = {
    "images": ["jpg", "jpeg", "png", "gif", "bmp"],
    "documents": ["pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx"],
    "videos": ["mp4", "mkv", "avi", "mov", "wmv"],
    "audios": ["mp3", "wav", "aac", "flac", "ogg"],
    "archives": ["zip", "rar", "7z", "tar", "gz"],
}

def ensure_directory_exists(directory):
    """Creates the directory if it does not exist."""
    if not os.path.exists(directory):
        os.makedirs(directory)

def check_and_download_file(message, file_path):
    """Checks if the file exists and downloads it if not, with logging and error handling."""
    try:
        if not os.path.exists(file_path):
            file_path = client.download_media(message, file=file_path)
            if file_path:
                logging.info(f"Downloaded: {file_path}")
                return file_path, os.path.getsize(file_path)
        else:
            logging.info(f"File already exists: {file_path}")
    except Exception as e:
        logging.error(f"Failed to download file: {e}")
    return None, 0

def download_files(channel_id, file_format=None, output_dir=".", message_limit=100):
    ensure_directory_exists(output_dir)
    
    total_size = 0
    file_count = 0
    # Setting message_limit to None fetches all messages if 0 is provided
    message_limit = None if message_limit == 0 else message_limit

    with client:
        logging.info(f"Fetching messages from channel: {channel_id}")
        messages = client.iter_messages(channel_id, limit=message_limit)

        for message in messages:
            if message.media:
                if isinstance(message.media, MessageMediaPhoto):
                    if not file_format or file_format.lower() == "images":
                        filename = f"{message.id}.jpg"
                        file_path = os.path.join(output_dir, filename)
                        downloaded_file, size = check_and_download_file(message, file_path)
                        if downloaded_file:
                            total_size += size
                            file_count += 1

                elif message.file:
                    mime_type = message.file.mime_type
                    extension = guess_extension(mime_type) if mime_type else None
                    # Ensure `guess_extension()` does not return None before appending
                    if extension is None:
                        extension = ""
                    
                    filename = message.file.name or str(message.id)
                    if extension and not filename.endswith(extension):
                        filename += extension

                    file_path = os.path.join(output_dir, filename)

                    if (
                        not file_format
                        or (
                            file_format.lower() in SUPPORTED_FILE_TYPES
                            and extension.lstrip(".") in SUPPORTED_FILE_TYPES.get(file_format.lower(), [])
                        )
                        or (extension.lstrip(".") == file_format.lower())
                    ):
                        downloaded_file, size = check_and_download_file(message, file_path)
                        if downloaded_file:
                            total_size += size
                            file_count += 1

    logging.info(f"\nSummary: Total files downloaded: {file_count}, Total size: {total_size / (1024 * 1024):.2f} MB")

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
        help=f"The type of files to download. Supported types: {', '.join(SUPPORTED_FILE_TYPES.keys())} "
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

    # Validate the file format if provided
    if args.format and args.format.lower() not in SUPPORTED_FILE_TYPES.keys():
        valid_extensions = {
            ext for types in SUPPORTED_FILE_TYPES.values() for ext in types
        }
        if args.format.lower() not in valid_extensions:
            logging.error(
                f"Error: Unsupported file format '{args.format}'.\n"
                f"Supported formats are: {', '.join(SUPPORTED_FILE_TYPES.keys())} or specific extensions: {', '.join(valid_extensions)}."
            )
            exit(1)

    try:
        download_files(args.channel, args.format, args.output, args.limit)
    except Exception as e:
        logging.error(f"An error occurred: {e}")
