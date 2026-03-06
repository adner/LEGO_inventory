#!/usr/bin/env python3
"""Register the Telegram webhook using a Dev Tunnel URL.

Usage:
    python register_webhook.py <tunnel-url>

Example:
    python register_webhook.py https://abc123.devtunnels.ms
"""

import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lib.config import get_telegram_credentials, get_webhook_secret


def main():
    if len(sys.argv) < 2:
        print("Usage: python register_webhook.py <tunnel-url>")
        print("Example: python register_webhook.py https://abc123.devtunnels.ms")
        sys.exit(1)

    tunnel_url = sys.argv[1].rstrip("/")
    webhook_url = f"{tunnel_url}/webhook"

    bot_token, _ = get_telegram_credentials()
    secret = get_webhook_secret()

    print(f"Registering webhook: {webhook_url}")

    data = urllib.parse.urlencode({
        "url": webhook_url,
        "secret_token": secret,
        "allowed_updates": '["message"]',
    }).encode()

    url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
    req = urllib.request.Request(url, data=data, method="POST")

    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())

    if result.get("ok"):
        print(f"Webhook registered successfully: {result.get('description')}")
    else:
        print(f"Failed: {result}")
        sys.exit(1)

    # Register bot commands
    commands = json.dumps([
        {"command": "inventory", "description": "List all LEGO sets in inventory"},
        {"command": "clear", "description": "Clear conversation history"},
        {"command": "help", "description": "Show available commands"},
    ])
    cmd_data = urllib.parse.urlencode({"commands": commands}).encode()
    cmd_url = f"https://api.telegram.org/bot{bot_token}/setMyCommands"
    cmd_req = urllib.request.Request(cmd_url, data=cmd_data, method="POST")

    with urllib.request.urlopen(cmd_req) as resp:
        cmd_result = json.loads(resp.read())

    if cmd_result.get("ok"):
        print("Bot commands registered successfully.")
    else:
        print(f"Failed to register commands: {cmd_result}")


if __name__ == "__main__":
    main()
