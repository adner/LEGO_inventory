# DataverseTool

A CLI tool for managing LEGO set inventory in Microsoft Dataverse.

## Prerequisites

- .NET 8.0 SDK installed
- `appsettings.json` configured with Dataverse credentials (Url, ClientId, ClientSecret)

## Usage

```
dotnet run --project DataverseTool -- <command> [options]
```

## Commands

### create-legoset

Creates a new LEGO set record in Dataverse.

```
dotnet run --project DataverseTool -- create-legoset --name <name> --number <number> --pieces <count> --image <path>
```

**Parameters (all required):**

| Parameter  | Description                        |
|------------|------------------------------------|
| `--name`   | Name of the LEGO set               |
| `--number` | Official LEGO set number (integer) |
| `--pieces` | Number of pieces (integer)         |
| `--image`  | Path to box image file             |

**Example:**

```
dotnet run --project DataverseTool -- create-legoset --name "Bugatti Chiron" --number 42083 --pieces 3599 --image box.jpg
```

**Output:** `LEGO set created: Bugatti Chiron (#42083). ID: <guid>`

### get-legoset

Retrieves a LEGO set by its set number.

```
dotnet run --project DataverseTool -- get-legoset --number <number>
```

**Output:**

```
Name:   Bugatti Chiron
Number: 42083
Pieces: 3599
```

### list-legosets

Lists all LEGO sets in the inventory.

```
dotnet run --project DataverseTool -- list-legosets
```

**Output:**

```
  [42083] Bugatti Chiron - 3599 pieces
  [10300] Back to the Future Time Machine - 1872 pieces

Total: 2 set(s)
```

### update-legoset

Updates an existing LEGO set. Only provided fields are updated.

```
dotnet run --project DataverseTool -- update-legoset --number <number> [--name <name>] [--pieces <count>] [--image <path>]
```

| Parameter  | Required | Description                        |
|------------|----------|------------------------------------|
| `--number` | Yes      | Set number to find the record      |
| `--name`   | No       | New name                           |
| `--pieces` | No       | New piece count                    |
| `--image`  | No       | New box image file path            |

**Output:** `LEGO set #42083 updated.`

### delete-legoset

Deletes a LEGO set by its set number.

```
dotnet run --project DataverseTool -- delete-legoset --number <number>
```

**Output:** `LEGO set #42083 deleted.`

### add-note

Adds a note (annotation) to a LEGO set. Optionally includes an inline image.

```
dotnet run --project DataverseTool -- add-note --number <number> --subject <subject> --text <text> [--image <path>]
```

| Parameter   | Required | Description                              |
|-------------|----------|------------------------------------------|
| `--number`  | Yes      | Set number to attach the note to         |
| `--subject` | Yes      | Note subject line                        |
| `--text`    | Yes      | Note body text                           |
| `--image`   | No       | Path to image file (displayed inline)    |

**Output:** `Note added. ID: <guid>`

When an image is provided, it is uploaded as a `msdyn_richtextfile` and embedded inline in the note's rich text content.

## Exit Codes

| Code | Meaning                                      |
|------|----------------------------------------------|
| 0    | Command completed successfully               |
| 1    | Error (missing parameters, not found, etc.)  |
