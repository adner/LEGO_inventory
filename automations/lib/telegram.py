"""Telegram message sending with automatic Markdown conversion."""

import json
import os
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path

from telegramify_markdown import markdownify

from .config import get_telegram_credentials, LOG_DIR, REPO_DIR

LOG_FILE = str(LOG_DIR / "telegram-messages.log")


MAX_MSG_LENGTH = 4096


def _split_message(text: str, max_length: int = MAX_MSG_LENGTH) -> list[str]:
    """Split a long message into chunks that fit within Telegram's limit.

    Splits on double newlines (paragraph boundaries) when possible,
    falling back to single newlines, then hard-cutting as a last resort.
    """
    if len(text) <= max_length:
        return [text]

    chunks = []
    while text:
        if len(text) <= max_length:
            chunks.append(text)
            break

        # Try splitting at paragraph boundary
        cut = text.rfind("\n\n", 0, max_length)
        if cut == -1:
            # Try single newline
            cut = text.rfind("\n", 0, max_length)
        if cut == -1:
            # Hard cut
            cut = max_length

        chunks.append(text[:cut].rstrip())
        text = text[cut:].lstrip("\n")

    return chunks


def _send_single(text: str, parse_mode: str | None, bot_token: str, chat_id: str) -> bool:
    """Send a single message via Telegram Bot API."""
    data = {
        "chat_id": chat_id,
        "text": text,
    }
    if parse_mode:
        data["parse_mode"] = parse_mode

    reply_to = os.environ.get("TELEGRAM_REPLY_TO_MESSAGE_ID")
    if reply_to:
        data["reply_to_message_id"] = reply_to

    encoded = urllib.parse.urlencode(data).encode()
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    req = urllib.request.Request(url, data=encoded, method="POST")

    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            if result.get("ok"):
                return True
            print(f"Telegram API error: {result}", flush=True)
            return False
    except urllib.error.URLError as e:
        print(f"Failed to send Telegram message: {e}", flush=True)
        return False


def send_message(text: str, convert_markdown: bool = True) -> bool:
    """Send a message via Telegram Bot API.

    Args:
        text: Message text. If convert_markdown is True, standard Markdown
              is automatically converted to Telegram MarkdownV2 format.
        convert_markdown: If True, convert standard Markdown to MarkdownV2.
                         Set to False for plain text messages.

    Returns:
        True if all message chunks were sent successfully.
    """
    bot_token, chat_id = get_telegram_credentials()

    # Split before converting — markdown conversion can change length
    chunks = _split_message(text)

    all_ok = True
    for chunk in chunks:
        if convert_markdown:
            converted = markdownify(chunk)
            parse_mode = "MarkdownV2"
        else:
            converted = chunk
            parse_mode = None

        # Log the message
        with open(LOG_FILE, "a") as f:
            f.write(f"=== {datetime.now():%Y-%m-%d %H:%M:%S} ===\n")
            f.write(f"Parse mode: {parse_mode or 'none'}\n")
            f.write(f"Original: {chunk[:200]}...\n" if len(chunk) > 200 else f"Original: {chunk}\n")
            f.write(f"Converted: {converted[:200]}...\n" if len(converted) > 200 else f"Converted: {converted}\n")
            f.write("---\n")

        if not _send_single(converted, parse_mode, bot_token, chat_id):
            all_ok = False

    return all_ok


def send_plain(text: str) -> bool:
    """Send a plain text message (no Markdown conversion)."""
    return send_message(text, convert_markdown=False)


IMAGES_DIR = REPO_DIR / "telegram_images"
FILES_DIR = REPO_DIR / "telegram_files"


def _download_telegram_file(file_id: str, dest_dir: Path, filename: str | None = None) -> Path | None:
    """Download a file from Telegram by file_id to the given directory."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    bot_token, _ = get_telegram_credentials()
    url = f"https://api.telegram.org/bot{bot_token}/getFile?file_id={file_id}"
    try:
        with urllib.request.urlopen(url) as resp:
            data = json.loads(resp.read())
            if not data.get("ok"):
                return None
            remote_path = data["result"]["file_path"]
    except (urllib.error.URLError, KeyError):
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if filename:
        local_path = dest_dir / f"{timestamp}_{filename}"
    else:
        ext = Path(remote_path).suffix or ".jpg"
        local_path = dest_dir / f"{timestamp}_{file_id}{ext}"

    download_url = f"https://api.telegram.org/file/bot{bot_token}/{remote_path}"
    try:
        urllib.request.urlretrieve(download_url, str(local_path))
        return local_path
    except urllib.error.URLError:
        return None


def download_file(file_id: str) -> Path | None:
    """Download an image from Telegram to telegram_images/."""
    return _download_telegram_file(file_id, IMAGES_DIR)


def download_document(file_id: str, filename: str | None = None) -> Path | None:
    """Download a document from Telegram to telegram_files/."""
    return _download_telegram_file(file_id, FILES_DIR, filename=filename)


def send_typing_action() -> bool:
    """Send a 'typing' chat action. The indicator lasts ~5 seconds."""
    bot_token, chat_id = get_telegram_credentials()
    data = urllib.parse.urlencode({"chat_id": chat_id, "action": "typing"}).encode()
    url = f"https://api.telegram.org/bot{bot_token}/sendChatAction"
    req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read()).get("ok", False)
    except urllib.error.URLError:
        return False
