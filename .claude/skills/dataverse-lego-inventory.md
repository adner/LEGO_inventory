# Dataverse LEGO Inventory

Manage LEGO set inventory stored in Microsoft Dataverse using the DataverseTool CLI.

## Instructions

Run commands from the repository root using:

```bash
dotnet run --project DataverseTool -- <command> [options]
```

### Available Commands

**list-legosets** — List all LEGO sets in the inventory.

```bash
dotnet run --project DataverseTool -- list-legosets
```

**get-legoset** — Look up a specific set by number.

```bash
dotnet run --project DataverseTool -- get-legoset --number <number>
```

**create-legoset** — Add a new set to the inventory. All parameters required.

```bash
dotnet run --project DataverseTool -- create-legoset --name "<name>" --number <number> --pieces <count> --image <path>
```

**update-legoset** — Update an existing set. Only --number is required; include only the fields to change.

```bash
dotnet run --project DataverseTool -- update-legoset --number <number> [--name "<name>"] [--pieces <count>] [--image <path>]
```

**delete-legoset** — Remove a set from the inventory.

```bash
dotnet run --project DataverseTool -- delete-legoset --number <number>
```

**add-note** — Attach a note to a set, optionally with an inline image.

```bash
dotnet run --project DataverseTool -- add-note --number <number> --subject "<subject>" --text "<text>" [--image <path>]
```

### When to Use

- User asks to add a LEGO set to their inventory/collection
- User asks what sets they own or to list their inventory
- User asks to look up, update, or remove a set from inventory
- User wants to attach a note or photo to a set they own
- After identifying a set from a photo, use create-legoset to add it (download box image first and pass as --image)

### Important Notes

- The --number parameter is always the official LEGO set number (e.g., 42083 for Bugatti Chiron)
- The --image parameter takes a local file path, not a URL — download images first if needed
- Exit code 0 means success, exit code 1 means error (missing params, set not found, etc.)
- For add-note with --image, the image is embedded inline in the note's rich text content
- After creating a set, send confirmation to the user via tools/telegram_send.py or tools/telegram_send_lego_card.py
