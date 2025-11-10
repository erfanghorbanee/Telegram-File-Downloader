# Telegram-File-Downloader

A Python script to download files from Telegram entities (channels, groups, chats, or saved messages). It supports filtering by file type (e.g., images, PDFs).

## Table of Contents

- [Telegram-File-Downloader](#telegram-file-downloader)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Prerequisites](#prerequisites)
    - [Steps to Get Telegram API Credentials](#steps-to-get-telegram-api-credentials)
    - [Setting Up the .env File](#setting-up-the-env-file)
  - [Usage](#usage)
    - [List All Accessible Dialogs](#list-all-accessible-dialogs)
    - [Download Files](#download-files)
  - [Security Notes](#security-notes)
  - [FAQ](#faq)
    - [What is a Telegram Entity?](#what-is-a-telegram-entity)
    - [How do I find the ID of a private channel or group?](#how-do-i-find-the-id-of-a-private-channel-or-group)
    - [Can I use a bot token instead of my phone number?](#can-i-use-a-bot-token-instead-of-my-phone-number)
    - [What file formats are supported?](#what-file-formats-are-supported)
  - [Contributing](#contributing)

## Features

- Download files from channels, groups, private chats, or your saved messages.
- Filter downloads by file type (e.g., images, PDFs, videos).
- Save files to a specific directory.
- List all channels, groups, and chats you have access to.
- Easy setup with environment variables for secure credential management.

## Prerequisites

1. Python 3.12 or higher installed on your system.
2. `telethon` library installed. You can install all the required libraries using:

   ```bash
   pip3 install -r requirements.txt
   ```

3. A Telegram account or bot token.

### Steps to Get Telegram API Credentials

To use this script, you need an **API ID** and **API Hash** from Telegram. Follow these steps:

1. Open your browser and go to [Telegram's My Apps page](https://my.telegram.org/apps).
2. Log in with your Telegram account credentials.
3. Click on **Create New Application**.
4. Fill in the required details.
5. After creating the application, you will see your **API ID** and **API Hash**. Copy these values.

### Setting Up the .env File

To securely store your credentials:

1. In the project directory, create a file named `.env`.
2. Add the following lines to the file:

   ```env
   TELEGRAM_API_ID=your_api_id
   TELEGRAM_API_HASH=your_api_hash
   ```

   Replace `your_api_id` and `your_api_hash` with the actual values obtained from Telegram.

## Usage

### List All Accessible Dialogs

To see all channels, groups, and chats you have access to:

```shell
python main.py --list
```

This will display a table with:

- **ID**: The numeric identifier of the entity
- **Type**: The type of entity (Channel (public/private), User, Chat, etc.)
- **Name**: The display name
- **Username**: The public username (if available)

### Download Files

**Basic syntax:**

```shell
python main.py <entity_identifier> --format <file_type> --output <directory> --limit <number>
```

**Examples:**

```shell
# Download from a public channel
python main.py @channel_name --format images --output ./downloads --limit 100

# Download from your Saved Messages
python main.py me --format images --output ./downloads --limit 100

# Download from a private channel, private group or user chat using its ID
python main.py -1001234567891 --format images --output ./downloads --limit 100

# Download all media types (no filter)
python main.py @channel_name --output ./downloads --limit 0
```

**Arguments:**

- `<entity>`: The entity to download from. Can be:
  - Public channel username: `@channel_name` or `channel_name`
  - Entity ID: `-1001234567891` (use `--list` to find IDs)
  - Saved Messages: `me` or `self`
- `--format` or `-f`: Filter by file type category or specific extension.
  - **Categories:** `images`, `documents`, `videos`, `audios`, `archives`
  - **Specific extensions:** `pdf`, `jpg`, `png`, `mp4`, `zip`, etc.
  - If omitted, all media types are downloaded.
- `--output` or `-o`: The directory to save downloaded files. Defaults to the current directory.
- `--limit` or `-l`: The maximum number of messages to fetch. Use `0` to fetch **all messages**. Defaults to 100.

**Note:** You can customize supported extensions for each category in the code's `FILE_CATEGORIES` dictionary.

**Note:** The `--limit` parameter specifies how many messages to check, not how many files to download. For example, `--format pdf --limit 10` will check the 10 most recent messages and download any PDFs found among them.

## Security Notes

- Avoid sharing the .env file.
- Avoid sharing the `session_name.session` file, as it contains encrypted data that could potentially be misused to access your account.

## FAQ

### What is a Telegram Entity?

The Telethon library widely uses the concept of “entities”. An entity will refer to any User, Chat or Channel object that the API may return in response to certain methods, such as GetUsersRequest.

**Learn more:** [Telethon Entities Documentation](https://docs.telethon.dev/en/stable/concepts/entities.html)

### How do I find the ID of a private channel or group?

Use the `--list` command to see all your accessible dialogs with their IDs:

```bash
python main.py --list
```

**Note:** You must be a member of the channel/group or have an existing chat with the user to download files.

### Can I use a bot token instead of my phone number?

No. Telegram bots have restricted API access and cannot retrieve message history from channels using the methods this script requires (`iter_messages`). You must use a user account (phone number authentication) for this script to work properly.

### What file formats are supported?

You can filter by category or specific extension:

**Categories:** `images`, `documents`, `videos`, `audios`, `archives`

**Specific extensions:** `pdf`, `jpg`, `png`, `mp4`, `mp3`, `zip`, etc.

**TODO:** there are some bugs for file formats. should be fixed later.

## Contributing

If you have suggestions or issues, please open an issue or pull request. All contributions are welcomed.
