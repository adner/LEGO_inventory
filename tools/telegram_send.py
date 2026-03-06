#!/usr/bin/env python3
"""Send a Telegram message with automatic Markdown-to-MarkdownV2 conversion.

Usage:
    telegram_send.py "Your **markdown** message"

This replaces telegram.sh for cases where you want proper Markdown rendering
in Telegram. Standard Markdown is automatically converted to MarkdownV2.
"""

import sys
from pathlib import Path

# Add automations/lib to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "automations"))
from lib.telegram import send_message

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: telegram_send.py \"message\"", file=sys.stderr)
        sys.exit(1)

    text = sys.argv[1]
    if not send_message(text):
        sys.exit(1)
