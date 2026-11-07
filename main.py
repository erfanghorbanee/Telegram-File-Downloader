import argparse
import logging
import os
import re
import sys
from mimetypes import guess_extension

from dotenv import load_dotenv

# `sync` looks unused, but importing it switches Telethon to its synchronous
# (non-async) API, which this script relies on. Don't remove it.
from telethon import TelegramClient, sync  # noqa: F401
from telethon.tl.types import MessageMediaPhoto

# Load environment variables from the .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Supported file categories
# Note: These are manually curated based on common use cases.
# Feel free to add or remove extensions as needed.
FILE_CATEGORIES = {
    "images": [
        "jpg",
        "jpeg",
        "png",
        "gif",
        "bmp",
        "webp",
        "svg",
        "heic",
        "raw",
    ],
    "documents": [
        "pdf",
        "doc",
        "docx",
        "odt",
        "rtf",
        "xls",
        "xlsx",
        "csv",
        "ppt",
        "pptx",
        "txt",
        "epub",
        "json",
        "xml",
        "yaml",
        "yml",
        "md",
        "log",
    ],
    "videos": [
        "mp4",
        "mkv",
        "avi",
        "mov",
        "wmv",
        "webm",
        "flv",
        "m4v",
    ],
    "audios": [
        "mp3",
        "wav",
        "aac",
        "flac",
        "ogg",
        "opus",
        "m4a",
        "wma",
    ],
    "archives": [
        "zip",
        "rar",
        "7z",
        "tar",
        "gz",
        "bz2",
        "xz",
    ],
}


def sanitize_filename(filename: str) -> str:
    """
    Remove or replace characters that are invalid across major operating systems
    (Windows, macOS, Linux), preventing filesystem write errors.
    """
    if not filename:
        return "unnamed_file"
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", filename)
    cleaned = cleaned.rstrip(". ")
    if not cleaned or not cleaned.strip("_"):
        return "unnamed_file"
    return cleaned


def determine_file_extension(filename: str, mime_type: str | None = None) -> str:
    """
    Extract the clean extension from the filename if present, or guess from mime_type.
    Returns the extension in lowercase without a leading dot.
    """
    if filename and "." in filename:
        _, ext = os.path.splitext(filename)
        clean_ext = ext.lstrip(".").lower()
        if clean_ext:
            return clean_ext

    if mime_type:
        guessed = guess_extension(mime_type)
        if guessed:
            return guessed.lstrip(".").lower()

    return ""


def create_telegram_client():
    """Create the Telegram client, or exit with a clear message if credentials are missing."""
    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")

    if not api_id or not api_hash:
        sys.exit(
            "Error: TELEGRAM_API_ID and TELEGRAM_API_HASH are not set. "
            "See 'Setting Up the .env File' in README.md."
        )
    if not api_id.isdigit():
        sys.exit("Error: TELEGRAM_API_ID must be a number. Check your .env file.")

    # The session file stores your login, so you only need to sign in once.
    return TelegramClient("session_name", int(api_id), api_hash)


def cleanup_incomplete_files(output_dir):
    """Remove any leftover .tmp files from interrupted downloads."""
    for file in os.listdir(output_dir):
        if file.endswith(".tmp"):
            temp_file_path = os.path.join(output_dir, file)
            logger.warning(f"Removing incomplete file: {temp_file_path}")
            os.remove(temp_file_path)


def create_directory_if_needed(directory):
    """Creates the directory if it does not exist."""
    if not os.path.exists(directory):
        os.makedirs(directory)


def check_and_download_file(telegram_client, message, file_path):
    """Downloads the file with a temporary name and renames it after completion."""
    try:
        # Skip downloading if the file already exists
        if os.path.exists(file_path):
            logger.info(f"File already exists: {file_path}, skipping download.")
            return file_path, os.path.getsize(file_path)

        temp_file_path = file_path + ".tmp"

        # Download the file as a .tmp file first
        downloaded_file = telegram_client.download_media(message, file=temp_file_path)

        # Validate file size before renaming to ensure download was successful
        if (
            downloaded_file
            and os.path.exists(temp_file_path)
            and os.path.getsize(temp_file_path) > 0
        ):
            os.rename(temp_file_path, file_path)
            logger.info(f"Downloaded: {file_path}")
            return file_path, os.path.getsize(file_path)
        else:
            logger.warning(
                f"Downloaded file is incomplete or missing: {temp_file_path}"
            )
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
    # Catch everything so one failed file doesn't stop the whole run.
    except Exception as error:  # noqa: BLE001
        logger.error(f"Failed to download file: {error}")
    return None, 0


def list_dialogs(telegram_client):
    """List all accessible dialogs (channels, groups, chats) with their details."""
    with telegram_client:
        logger.info("Fetching your dialogs...")
        print(f"\n{'ID':<15} {'Type':<25} {'Name':<30} {'Username':<20}")
        print("-" * 90)
        for dialog in telegram_client.iter_dialogs():
            dialog_id = dialog.id
            dialog_type = type(dialog.entity).__name__
            dialog_name = dialog.name or "(No name)"
            dialog_username = getattr(dialog.entity, "username", "") or "(No username)"

            # Check if it's a channel and whether it's public or private
            if dialog_type == "Channel":
                if hasattr(dialog.entity, "username") and dialog.entity.username:
                    dialog_type = "Channel (public)"
                else:
                    dialog_type = "Channel (private)"

            print(
                f"{dialog_id:<15} {dialog_type:<25} {dialog_name:<30} {dialog_username:<20}"
            )


def resolve_entity(entity_identifier):
    """
    Convert entity identifier to proper format for Telethon.
    Converts numeric strings to integers, keeps usernames and keywords as strings.

    Args:
        entity_identifier: Channel name, username, or numeric ID as string

    Returns:
        Integer for numeric IDs, string for usernames/keywords
    """
    try:
        return int(entity_identifier)
    except (ValueError, TypeError):
        # Keep as string for usernames like '@channel' or 'me'
        return entity_identifier


def download_files_from_entity(
    telegram_client,
    entity_identifier,
    file_type=None,
    save_directory=".",
    message_limit=100,
):
    create_directory_if_needed(save_directory)
    cleanup_incomplete_files(save_directory)

    total_file_size = 0
    total_files_downloaded = 0
    message_limit = None if message_limit == 0 else message_limit

    # Resolve the entity (convert to int if numeric, keep as string otherwise)
    entity = resolve_entity(entity_identifier)

    with telegram_client:
        logger.info(f"Fetching messages from: {entity_identifier}")
        messages = telegram_client.iter_messages(entity, limit=message_limit)

        for message in messages:
            if message.media:
                if isinstance(message.media, MessageMediaPhoto):
                    if not file_type or file_type.lower() == "images":
                        file_name = f"{message.id}.jpg"
                        file_path = os.path.join(save_directory, file_name)
                        downloaded_file, file_size = check_and_download_file(
                            telegram_client, message, file_path
                        )
                        if downloaded_file:
                            total_file_size += file_size
                            total_files_downloaded += 1

                elif message.file:
                    raw_name = message.file.name or str(message.id)
                    mime_type = message.file.mime_type
                    file_extension = determine_file_extension(raw_name, mime_type)

                    file_name = sanitize_filename(raw_name)
                    if file_extension and not file_name.lower().endswith(
                        f".{file_extension}"
                    ):
                        file_name += f".{file_extension}"

                    file_path = os.path.join(save_directory, file_name)

                    if (
                        not file_type
                        or (
                            file_type.lower() in FILE_CATEGORIES
                            and file_extension
                            in FILE_CATEGORIES.get(file_type.lower(), [])
                        )
                        or (file_extension == file_type.lower().lstrip("."))
                    ):
                        downloaded_file, file_size = check_and_download_file(
                            telegram_client, message, file_path
                        )
                        if downloaded_file:
                            total_file_size += file_size
                            total_files_downloaded += 1

    logger.info(
        f"\nSummary: Total files downloaded: {total_files_downloaded}, Total size: {total_file_size / (1024 * 1024):.2f} MB"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download files from a Telegram entity (channel, group, chat, or user)."
    )
    parser.add_argument(
        "entity",
        nargs="?",
        type=str,
        help="The username or ID of the Telegram entity (channel, group, chat, or 'me' for saved messages).",
    )
    parser.add_argument(
        "-f",
        "--format",
        type=str,
        help=f"Filter by file type category or specific extension. "
        f"Categories: {', '.join(FILE_CATEGORIES.keys())}. "
        f"Or use specific extensions (e.g., pdf, jpg, mp4). "
        f"If omitted, all media types are downloaded.",
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
        help="Maximum number of messages to check (not files to download). Use 0 for no limit. Defaults to 100.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all accessible dialogs (channels, groups, chats) and exit.",
    )

    args = parser.parse_args()

    if not args.list and not args.entity:
        parser.error(
            "Please specify an entity or use --list to view available dialogs (channels, groups, chats)."
        )

    # Created after parsing arguments, so `--help` works without credentials.
    telegram_client = create_telegram_client()

    try:
        if args.list:
            list_dialogs(telegram_client)
        else:
            download_files_from_entity(
                telegram_client, args.entity, args.format, args.output, args.limit
            )
    # Show a one-line message instead of a long traceback.
    except Exception as error:  # noqa: BLE001
        logger.error(f"An error occurred: {error}")
