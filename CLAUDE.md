# Lego Inventory Bot

Telegram bot for managing LEGO set inventory using Claude Code as the AI backend, with Microsoft Dataverse as the data store.

## Architecture

- **Webhook server**: `automations/telegram_webhook.py` — HTTP server on port 8443, receives Telegram updates
- **Dev Tunnels**: Provides HTTPS termination and public URL for the webhook
- **Telegram lib**: `automations/lib/telegram.py` — message sending with automatic MarkdownV2 conversion
- **Config**: `automations/lib/config.py` — credentials from `tools/.env`
- **DataverseTool**: `DataverseTool/` — .NET CLI for Dataverse CRUD operations

## Setup

1. Create `tools/.env` from `tools/.env.example` with Telegram bot credentials and tunnel URL
2. Create `DataverseTool/appsettings.json` from `DataverseTool/appsettings.example.json` with Dataverse credentials
3. Install dependency: `pip install telegramify-markdown`
4. Start webhook server: `python start.py`
5. In another terminal, start Dev Tunnel: `devtunnel host --port 8443`
6. Register webhook: `python automations/register_webhook.py <tunnel-url>`

## Bot Commands

- `/inventory` — List all LEGO sets in inventory (queries Dataverse directly, no Claude needed)
- `/clear` — Clear conversation history
- `/help` — Show available commands
- `/start` — Welcome message

Free-text messages and photos are routed to Claude CLI for processing.

## Photo Flow

When a user sends a photo:
1. Claude identifies the LEGO set from the image
2. Claude sends a Mini App card via `tools/telegram_send_lego_card.py` with `--user-image` pointing to the saved photo
3. The Mini App shows set details with an "Add to Inventory" button
4. Tapping the button POSTs to `/add-to-inventory` on the webhook server
5. The webhook downloads the box image, runs `DataverseTool create-legoset`, then `add-note` with the user's photo

## Tools

- `tools/telegram_send.py` — Send Telegram messages with Markdown support
- `tools/telegram_send_lego_card.py` — Send a Mini App card for a LEGO set (--name, --number, --pieces, --image, --user-image)
- `tools/test_lego_card.py` — Test harness for Mini App development without using Claude

## Dataverse Integration

LEGO set inventory is stored in Microsoft Dataverse. Use the skill in `.claude/skills/dataverse-lego-inventory.md` for managing sets (create, list, get, update, delete) and adding notes with photos. Full CLI docs in `DataverseTool/DataverseTool.md`.
