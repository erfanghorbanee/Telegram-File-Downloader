# Telegram-File-Downloader

A Python script to download files from a given Telegram channel. It supports filtering by file type (e.g., images, PDFs).

## Features

- Download all files from a specified Telegram channel.
- Filter downloads by file type (e.g., images, PDFs, videos).
- Save files to a specific directory.
- Easy setup with environment variables for secure credential management.

## Prerequisites

1. Python 3.12 or higher installed on your system.
2. `telethon` library installed. You can install all the required libraries using:

   ```bash
   pip3 install -r requirements.txt
   ```

3. A Telegram account or bot token.

## Steps to Get Telegram API Credentials

To use this script, you need an **API ID** and **API Hash** from Telegram. Follow these steps:

1. Open your browser and go to [Telegram's My Apps page](https://my.telegram.org/apps).
2. Log in with your Telegram account credentials.
3. Click on **Create New Application**.
4. Fill in the required details.
5. After creating the application, you will see your **API ID** and **API Hash**. Copy these values.

## Setting Up the .env File

To securely store your credentials:

1. In the project directory, create a file named `.env`.
2. Add the following lines to the file:

   ```env
   TELEGRAM_API_ID=your_api_id
   TELEGRAM_API_HASH=your_api_hash
   ```

   Replace `your_api_id` and `your_api_hash` with the actual values obtained from Telegram.

## Why Does Telethon Ask for a Phone Number or Bot Token?

The first time you run the script, Telethon will authenticate your account to create a session. You can authenticate using:

1. **Phone Number**:
   - Telethon sends a code to your Telegram app or via SMS.
   - Enter this code in the terminal when prompted.

2. **Bot Token**:
   - If you're using a bot, you can authenticate with the bot token instead of a phone number.
   - Obtain the bot token from [BotFather](https://t.me/botfather).

Telethon saves this authentication data in a `session_name.session` file in the current directory. This session file allows you to skip authentication on subsequent runs.

### **Example of Running the Script**

```bash
python main.py @channel_name --format images --output ./downloads --limit 100
```

- `@channel_name`: The username or ID of the Telegram channel.
- `--format` or `-f`: The file type to download (e.g., `images`, `pdf`). If omitted, all file types are downloaded.
- `--output` or `-o`: The directory to save the files. Defaults to the current directory.
- `--limit` or `-l`: The maximum number of messages to fetch. Use `0` to fetch **all messages**.

## Security Notes

- Avoid sharing the .env file.
- Avoid sharing the `session_name.session` file, as it contains encrypted data that could potentially be misused to access your account.

## Contributing

If you have suggestions or issues, please open an issue or pull request. All contributions are welcomed.
