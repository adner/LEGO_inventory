# LEGO Inventory Bot

A Telegram bot that identifies LEGO sets from photos and manages your collection in Microsoft Dataverse — powered by [Claude Code](https://docs.anthropic.com/en/docs/claude-code) as the AI backend.

## What It Does

1. **Snap a photo** of a LEGO set in Telegram
2. **AI identifies** the set (name, number, piece count)
3. **A Mini App card** pops up with the set details and box image
4. **Tap "Add to Inventory"** to save it to Dataverse — no manual data entry

You can also use `/inventory` to list your collection, or chat freely with the bot for anything LEGO-related.

## Architecture

```
Telegram  -->  Dev Tunnel (HTTPS)  -->  Python webhook server (HTTP :8443)
                                            |
                                            +--> Claude Code CLI (set identification)
                                            +--> DataverseTool CLI (inventory CRUD)
                                            +--> Telegram Mini App (set detail cards)
```

- **Webhook server** (`automations/telegram_webhook.py`) — Receives Telegram updates, routes to Claude or handles directly
- **Claude Code CLI** — Identifies LEGO sets from photos, responds to free-text messages
- **Agent skill** (`.claude/skills/dataverse-lego-inventory.md`) — Teaches Claude how to manage inventory via DataverseTool
- **DataverseTool** (`DataverseTool/`) — .NET CLI for Dataverse CRUD operations on LEGO sets
- **Telegram Mini App** — Inline card UI with "Add to Inventory" button
- **Dev Tunnels** — Provides HTTPS termination for the local webhook server

## Prerequisites

- Python 3.12+
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) installed and authenticated
- [Microsoft Dev Tunnels CLI](https://learn.microsoft.com/en-us/azure/developer/dev-tunnels/)
- [.NET 8.0 SDK](https://dotnet.microsoft.com/download/dotnet/8.0) (for the DataverseTool)
- A [Telegram Bot](https://core.telegram.org/bots#how-do-i-create-a-bot) (via BotFather)
- A [Microsoft Dataverse](https://learn.microsoft.com/en-us/power-apps/maker/data-platform/) environment with a LEGO set table (see [Dataverse Setup](#dataverse-setup))

## Setup

### 1. Clone and install dependencies

```bash
git clone https://github.com/adner/LEGO_inventory.git
cd LEGO_inventory
pip install telegramify-markdown
```

### 2. Configure Telegram credentials

```bash
cp tools/.env.example tools/.env
```

Edit `tools/.env` with your values:

```
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id
TELEGRAM_WEBHOOK_SECRET=any-random-secret-string
WEBAPP_BASE_URL=https://your-tunnel-id.euw.devtunnels.ms
```

To get your chat ID, send a message to your bot, then run:
```bash
curl https://api.telegram.org/bot<your-token>/getUpdates
```

### 3. Configure Dataverse credentials

```bash
cp DataverseTool/appsettings.example.json DataverseTool/appsettings.json
```

Edit `DataverseTool/appsettings.json` with your Dataverse environment URL and app registration credentials.

### 4. Start the bot

Terminal 1 — Start the webhook server:
```bash
python start.py
```

Terminal 2 — Expose via Dev Tunnel:
```bash
devtunnel host --port 8443
```

### 5. Register the webhook (first time only)

```bash
python automations/register_webhook.py https://your-tunnel-id.devtunnels.ms
```

This also registers the bot commands (`/inventory`, `/clear`, `/help`).

### 6. Update WEBAPP_BASE_URL

Set `WEBAPP_BASE_URL` in `tools/.env` to your Dev Tunnel URL. This is used to generate Mini App links.

### 7. Send a photo to your bot!

## Bot Commands

| Command      | Description                          |
|--------------|--------------------------------------|
| `/inventory` | List all LEGO sets in your inventory |
| `/clear`     | Clear conversation history           |
| `/help`      | Show available commands              |

Send a photo of a LEGO set to identify it, or send any text message to chat with the AI assistant.

## Dataverse Setup

The DataverseTool expects a custom table `cr19f_legoset` with these columns:

| Column                  | Type         | Description            |
|-------------------------|--------------|------------------------|
| `cr19f_legosetname`     | Text         | Name of the LEGO set   |
| `cr19f_legosetnumber`   | Whole Number | Official set number    |
| `cr19f_numberofpieces`  | Whole Number | Piece count            |
| `cr19f_boximage`        | Image        | Box image              |

Notes must be enabled on the table for the `add-note` command to work.

> **Note:** The `cr19f_` prefix is specific to this Dataverse environment. If you create your own table, update the column names in `DataverseTool/Program.cs` to match your publisher prefix.

## Project Structure

```
.claude/skills/          # Agent skills (Dataverse inventory)
automations/
  lib/config.py          # Configuration and credentials
  lib/telegram.py        # Telegram messaging helpers
  register_webhook.py    # Webhook + bot command registration
  telegram_webhook.py    # Main webhook server + Mini App
DataverseTool/
  Program.cs             # .NET CLI for Dataverse CRUD
  DataverseTool.md       # Detailed CLI documentation
tools/
  telegram_send.py       # Send messages via Telegram
  telegram_send_lego_card.py  # Send Mini App set cards
  test_lego_card.py      # Test harness for Mini App dev
start.py                 # Entry point
CLAUDE.md                # Agent instructions
```