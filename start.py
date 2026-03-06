#!/usr/bin/env python3
"""Start the Telegram webhook server.

After starting, open a separate terminal and run:
    devtunnel host --port 8443

Then register the webhook (one-time):
    python automations/register_webhook.py <tunnel-url>
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "automations"))
from telegram_webhook import main

if __name__ == "__main__":
    print("=" * 50)
    print("  Lego Inventory Bot — Webhook Server")
    print("=" * 50)
    print()
    print("Next steps:")
    print("  1. Open another terminal and run:")
    print("     devtunnel host --port 8443")
    print()
    print("  2. Register webhook (first time only):")
    print("     python automations/register_webhook.py <tunnel-url>")
    print()
    main()
