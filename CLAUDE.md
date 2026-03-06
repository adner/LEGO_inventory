# Lego Inventory Bot

Telegram bot for managing Lego set inventory. Runs on Windows with Microsoft Dev Tunnels for webhook exposure.

## Architecture

- **Webhook server**: `automations/telegram_webhook.py` — HTTP server on port 8443, receives Telegram updates
- **Dev Tunnels**: Provides HTTPS termination and public URL for the webhook
- **Telegram lib**: `automations/lib/telegram.py` — message sending with automatic MarkdownV2 conversion
- **Config**: `automations/lib/config.py` — credentials from `tools/.env`

## Setup

1. Create `tools/.env` with:
   ```
   TELEGRAM_BOT_TOKEN=your-bot-token
   TELEGRAM_CHAT_ID=your-chat-id
   TELEGRAM_WEBHOOK_SECRET=your-secret
   ```
2. Install dependency: `pip install telegramify-markdown`
3. Start webhook server: `python start.py`
4. In another terminal, start Dev Tunnel: `devtunnel host --port 8443`
5. Register webhook: `python automations/register_webhook.py <tunnel-url>`

## Bot Commands

- `/help` — Show available commands
- `/clear` — Clear conversation history
- `/start` — Welcome message

Free-text messages are routed to Claude CLI for processing.

## Tools

- `tools/telegram_send.py` — CLI tool to send Telegram messages with Markdown support
- `tools/telegram_send_lego_card.py` — Send a Telegram Mini App card for a LEGO set (--name, --number, --pieces, --image)

## Dataverse Integration

LEGO set inventory is stored in Microsoft Dataverse. Use the skill in `.claude/skills/dataverse-lego-inventory.md` for managing sets (create, list, get, update, delete) and adding notes with photos. Full CLI docs in `DataverseTool/DataverseTool.md`.
