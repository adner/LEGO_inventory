"""Shared configuration for the Telegram bot."""

import os
import tempfile
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent.parent
TOOLS_DIR = REPO_DIR / "tools"
ENV_FILE = TOOLS_DIR / ".env"
LOG_DIR = Path(tempfile.gettempdir())


def load_env() -> dict[str, str]:
    """Load key=value pairs from tools/.env file."""
    env = {}
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def get_telegram_credentials() -> tuple[str, str]:
    """Return (bot_token, chat_id) from .env file."""
    env = load_env()
    return env["TELEGRAM_BOT_TOKEN"], env["TELEGRAM_CHAT_ID"]


def get_webhook_secret() -> str:
    """Return the webhook secret token from .env file."""
    env = load_env()
    return env["TELEGRAM_WEBHOOK_SECRET"]


def get_webapp_base_url() -> str:
    """Return the base URL for Mini App pages from .env file."""
    env = load_env()
    return env["WEBAPP_BASE_URL"].rstrip("/")


def log(log_file: str, message: str) -> None:
    """Append a timestamped message to a log file."""
    from datetime import datetime
    timestamp = datetime.now().strftime("%a %b %d %I:%M:%S %p %Y")
    with open(log_file, "a") as f:
        f.write(f"{timestamp}: {message}\n")
