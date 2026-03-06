# Lego Inventory Bot

A Telegram bot for managing Lego set inventory, powered by Claude CLI.

## Prerequisites

- Python 3.12+
- `pip install telegramify-markdown`
- [Microsoft Dev Tunnels CLI](https://learn.microsoft.com/en-us/azure/developer/dev-tunnels/)
- [Claude CLI](https://docs.anthropic.com/en/docs/claude-code) installed and authenticated

## Setup

1. Copy `tools/.env.example` to `tools/.env` and fill in your Telegram bot credentials:
   ```
   TELEGRAM_BOT_TOKEN=your-bot-token
   TELEGRAM_CHAT_ID=your-chat-id
   TELEGRAM_WEBHOOK_SECRET=your-secret
   ```

2. Start the webhook server:
   ```
   python start.py
   ```

3. In a separate terminal, expose the server via Dev Tunnels:
   ```
   devtunnel host --port 8443
   ```

4. Register the webhook with Telegram (first time only):
   ```
   python automations/register_webhook.py https://your-tunnel-id.devtunnels.ms
   ```

5. Send a message to your bot on Telegram.
