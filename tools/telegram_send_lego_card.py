#!/usr/bin/env python3
"""Send a Lego set card with a Mini App button via Telegram.

Usage:
    telegram_send_lego_card.py --name "Set Name" --number 12345 --pieces 500 --image "https://..."
"""

import argparse
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "automations"))
from lib.config import get_webapp_base_url
from lib.telegram import send_message_with_webapp


def main():
    parser = argparse.ArgumentParser(description="Send a Lego set card via Telegram")
    parser.add_argument("--name", required=True, help="Lego set name")
    parser.add_argument("--number", required=True, help="Lego set number")
    parser.add_argument("--pieces", required=True, help="Number of pieces")
    parser.add_argument("--image", required=True, help="URL of the box image")
    args = parser.parse_args()

    base_url = get_webapp_base_url()
    params = urllib.parse.urlencode({
        "name": args.name,
        "number": args.number,
        "pieces": args.pieces,
        "image": args.image,
    })
    webapp_url = f"{base_url}/miniapp?{params}"

    text = f"🧱 {args.name}\nSet #{args.number} — {args.pieces} pieces"

    if not send_message_with_webapp(text, "View Set Details", webapp_url):
        sys.exit(1)


if __name__ == "__main__":
    main()
