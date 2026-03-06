#!/usr/bin/env python3
"""Send a test Lego card without invoking Claude. For Mini App development.

Usage:
    python tools/test_lego_card.py
    python tools/test_lego_card.py --name "Custom Set" --number 99999 --pieces 100 --image "https://..."
"""

import argparse
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "automations"))
from lib.config import get_webapp_base_url
from lib.telegram import send_message_with_webapp

# Default test data
DEFAULTS = {
    "name": "Lego Technic Bugatti Chiron",
    "number": "42083",
    "pieces": "3599",
    "image": "https://images.brickset.com/sets/large/42083-1.jpg",
}


def main():
    parser = argparse.ArgumentParser(description="Send a test Lego card (no Claude)")
    parser.add_argument("--name", default=DEFAULTS["name"])
    parser.add_argument("--number", default=DEFAULTS["number"])
    parser.add_argument("--pieces", default=DEFAULTS["pieces"])
    parser.add_argument("--image", default=DEFAULTS["image"])
    args = parser.parse_args()

    base_url = get_webapp_base_url()
    params = urllib.parse.urlencode({
        "name": args.name,
        "number": args.number,
        "pieces": args.pieces,
        "image": args.image,
    })
    webapp_url = f"{base_url}/miniapp?{params}"

    print(f"Mini App URL: {webapp_url}")
    print(f"Sending card: {args.name} (#{args.number}, {args.pieces} pcs)")

    text = f"\U0001f9f1 {args.name}\nSet #{args.number} \u2014 {args.pieces} pieces"
    if send_message_with_webapp(text, "View Set Details", webapp_url):
        print("Sent!")
    else:
        print("Failed to send.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
