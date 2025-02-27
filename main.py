import argparse
import os
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

def download_files(channel_id, file_format=None, output_dir="."):
    ensure_directory_exists(output_dir)
    
    total_size = 0
    file_count = 0

    with client:
        print(f"Fetching messages from channel: {channel_id}")
        messages = client.iter_messages(channel_id)

        for message in messages:
            if message.media:
                if isinstance(message.media, MessageMediaPhoto):
                    if not file_format or file_format.lower() == "images":
                        filename = f"{message.id}.jpg"
                        file_path = os.path.join(output_dir, filename)
                        if not os.path.exists(file_path):
                            file_path = client.download_media(message, file=file_path)
                            if file_path:
                                total_size += os.path.getsize(file_path)
                                file_count += 1
                                print(f"Downloaded image: {file_path}")
                        else:
                            print(f"Image already exists: {file_path}")

                elif message.file:
                    mime_type = message.file.mime_type
                    extension = guess_extension(mime_type) if mime_type else None
                    filename = message.file.name or str(message.id)
                    if extension and not filename.endswith(extension):
                        filename += extension

                    file_path = os.path.join(output_dir, filename)

                    if (
                        not file_format
                        or (
                            file_format.lower() in SUPPORTED_FILE_TYPES
                            and extension is not None
                            and extension.lstrip(".") in SUPPORTED_FILE_TYPES[file_format.lower()]
                        )
                        or (extension is not None and extension.lstrip(".") == file_format.lower())
                    ):
                        if not os.path.exists(file_path):
                            file_path = client.download_media(message, file=file_path)
                            if file_path:
                                total_size += os.path.getsize(file_path)
                                file_count += 1
                                print(
                                    f"Downloaded {extension if extension else 'file'}: {file_path}"
                                )
                        else:
                            print(f"File already exists: {file_path}")

    print(f"\nSummary:")
    print(f"Total files downloaded: {file_count}")
    print(f"Total size of downloaded files: {total_size / (1024 * 1024):.2f} MB")

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

    args = parser.parse_args()

    # Validate the file format if provided
    if args.format and args.format.lower() not in SUPPORTED_FILE_TYPES.keys():
        valid_extensions = {
            ext for types in SUPPORTED_FILE_TYPES.values() for ext in types
        }
        if args.format.lower() not in valid_extensions:
            print(
                f"Error: Unsupported file format '{args.format}'.\n"
                f"Supported formats are: {', '.join(SUPPORTED_FILE_TYPES.keys())} or specific extensions: {', '.join(valid_extensions)}."
            )
            exit(1)

    try:
        download_files(args.channel, args.format, args.output)
    except Exception as e:
        print(f"An error occurred: {e}")
