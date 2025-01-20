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

# Initialize the Telegram client
client = TelegramClient("session_name", API_ID, API_HASH)


# Function to download files
def download_files(channel_id, file_format=None, output_dir="."):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with client:
        print(f"Fetching messages from channel: {channel_id}")
        messages = client.iter_messages(channel_id)

        for message in messages:
            if message.media:
                if isinstance(message.media, MessageMediaPhoto):
                    if not file_format or file_format.lower() in ["image", "images"]:
                        file_path = client.download_media(message, file=output_dir)
                        print(f"Downloaded image: {file_path}")

                elif message.file:
                    mime_type = message.file.mime_type
                    extension = guess_extension(mime_type) if mime_type else ""

                    if not file_format or (
                        extension and file_format.lower() in extension.lower()
                    ):
                        file_path = client.download_media(message, file=output_dir)
                        print(
                            f"Downloaded {extension if extension else 'file'}: {file_path}"
                        )


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
        help="The type of files to download (e.g., images, pdf, etc.). If not specified, downloads all media.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=".",
        help="The directory to save downloaded files. Defaults to the current directory.",
    )

    args = parser.parse_args()

    try:
        download_files(args.channel, args.format, args.output)
    except Exception as e:
        print(f"An error occurred: {e}")
