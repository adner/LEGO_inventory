#!/usr/bin/env python3
"""Telegram webhook server — receives bot updates via HTTP and processes them.

Designed to run behind Microsoft Dev Tunnels which provides HTTPS termination.
"""

import json
import os
import queue
import subprocess
import threading
from datetime import date
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent))
from lib.config import REPO_DIR, LOG_DIR, get_telegram_credentials, get_webhook_secret, log
from lib.telegram import download_document, download_file, send_message, send_plain, send_typing_action

LOG = str(LOG_DIR / "telegram-webhook.log")
SESSION_FILE = Path(__file__).parent / "telegram_session_id"
PORT = 8443

# Load config at startup
_, CHAT_ID = get_telegram_credentials()
SECRET_TOKEN = get_webhook_secret()

# Sequential message processing queue
msg_queue = queue.Queue()

# Track seen update IDs to prevent duplicate processing
seen_updates = set()
MAX_SEEN = 1000


# --- Session management ---

def read_session_id() -> str | None:
    if SESSION_FILE.exists():
        sid = SESSION_FILE.read_text().strip()
        return sid if sid else None
    return None


def write_session_id(session_id: str) -> None:
    SESSION_FILE.write_text(session_id)


def clear_session() -> None:
    if SESSION_FILE.exists():
        SESSION_FILE.unlink()
        log(LOG, "Session cleared")


# --- Message processing ---

def process_message(text: str, message_id: int | None = None,
                    image_path: str | None = None, doc_path: str | None = None) -> None:
    """Execute a user message via Claude CLI, resuming the session if possible."""
    prompt = (
        f"The user sent this message via Telegram. Today is {date.today()}. "
        "Respond to their request. When done, send your response via Telegram "
        "using tools/telegram_send.py (pass the message as the first argument). "
        "Write your message in standard Markdown — it will be automatically "
        "converted for Telegram. "
        "Keep each message under 3000 characters; split into multiple messages if needed.\n\n"
    )
    if image_path:
        prompt += f"The user sent an image saved at {image_path}. Use the Read tool to view it.\n"
        prompt += (
            "This is a Lego Inventory Bot. Analyze the image to identify the Lego set. "
            "Respond with:\n"
            "- **Set name**\n"
            "- **Set number**\n"
            "- **Number of pieces**\n"
            "If you can't identify the exact set, give your best guess and say so. "
            "If the image is not a Lego set, let the user know.\n\n"
        )
    if doc_path:
        prompt += f"The user also sent a document saved at {doc_path}. Use the Read tool to view it.\n\n"
    if text:
        prompt += f"User message: {text}"
    elif image_path or doc_path:
        prompt += "The user sent the file without any additional text."
    else:
        prompt += "The user sent an empty message."

    env = {**os.environ}
    env.pop("CLAUDECODE", None)
    if message_id:
        env["TELEGRAM_REPLY_TO_MESSAGE_ID"] = str(message_id)

    session_id = read_session_id()

    cmd = [
        "claude", "-p",
        "--model", "sonnet",
        "--permission-mode", "bypassPermissions",
        "--allowedTools", "Read Glob Grep Edit Write Bash",
        "--output-format", "json",
    ]
    if session_id:
        cmd.extend(["--resume", session_id])
        log(LOG, f"Resuming session {session_id}")

    # Show typing indicator while Claude processes
    stop_typing = threading.Event()

    def typing_loop():
        while not stop_typing.wait(4):
            send_typing_action()

    send_typing_action()
    typing_thread = threading.Thread(target=typing_loop, daemon=True)
    typing_thread.start()

    try:
        result = subprocess.run(cmd, input=prompt, text=True, capture_output=True, env=env)
    finally:
        stop_typing.set()
        typing_thread.join(timeout=1)

    if result.returncode != 0 and session_id:
        log(LOG, f"Resume failed (exit {result.returncode}), retrying with fresh session")
        cmd = [c for c in cmd if c not in ("--resume", session_id)]
        stop_typing.clear()
        send_typing_action()
        typing_thread = threading.Thread(target=typing_loop, daemon=True)
        typing_thread.start()
        try:
            result = subprocess.run(cmd, input=prompt, text=True, capture_output=True, env=env)
        finally:
            stop_typing.set()
            typing_thread.join(timeout=1)

    if result.returncode != 0:
        log(LOG, f"Claude exited with code {result.returncode}")
        log(LOG, f"Claude stderr: {result.stderr[-500:]}")
        return

    # Extract and persist session ID from JSON output
    try:
        output = json.loads(result.stdout)
        new_session_id = output.get("session_id", "")
        if new_session_id:
            write_session_id(new_session_id)
            log(LOG, f"Session ID saved: {new_session_id}")
    except (json.JSONDecodeError, KeyError):
        log(LOG, "Could not parse session ID from Claude output")


# --- Worker thread ---

def worker():
    """Process messages from the queue one at a time."""
    while True:
        text, message_id, image_path, doc_path = msg_queue.get()
        try:
            cmd = text.strip().lower() if text else ""

            if cmd == "/clear":
                clear_session()
                send_plain("Conversation cleared.")
                log(LOG, "Session cleared via /clear")
            elif cmd == "/start":
                send_plain("Lego Inventory Bot is running. Send /help for available commands.")
                log(LOG, "Sent /start response")
            elif cmd == "/help":
                help_text = (
                    "**Available commands:**\n\n"
                    "/clear — Clear conversation history\n"
                    "/help — Show this help message\n"
                    "/start — Welcome message\n\n"
                    "Send any other message to chat with the AI assistant."
                )
                send_message(help_text)
                log(LOG, "Sent help")
            else:
                log(LOG, f"Processing: {(text or 'file')[:100]}")
                process_message(text or "", message_id=message_id,
                                image_path=image_path, doc_path=doc_path)
                log(LOG, f"Done processing: {(text or 'file')[:100]}")
        except Exception as e:
            log(LOG, f"Error processing message: {e}")
        finally:
            msg_queue.task_done()


# --- HTTP handler ---

class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Verify secret token
        token = self.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if token != SECRET_TOKEN:
            self.send_response(403)
            self.end_headers()
            log(LOG, "Rejected request: invalid secret token")
            return

        # Read body
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        # Respond 200 immediately so Telegram doesn't retry
        self.send_response(200)
        self.end_headers()

        try:
            update = json.loads(body)
            update_id = update.get("update_id")

            # Deduplicate
            if update_id in seen_updates:
                log(LOG, f"Skipping duplicate update {update_id}")
                return
            seen_updates.add(update_id)
            if len(seen_updates) > MAX_SEEN:
                seen_updates.clear()

            msg = update.get("message", {})
            msg_chat_id = str(msg.get("chat", {}).get("id", ""))
            text = msg.get("text") or msg.get("caption") or ""
            photos = msg.get("photo")
            document = msg.get("document")

            if msg_chat_id != CHAT_ID or (not text and not photos and not document):
                return

            # Download photo if present (last element = largest size)
            image_path = None
            if photos:
                file_id = photos[-1]["file_id"]
                local = download_file(file_id)
                if local:
                    image_path = str(local)
                    log(LOG, f"Downloaded image: {image_path}")

            # Download document if present
            doc_path = None
            if document:
                file_id = document["file_id"]
                filename = document.get("file_name")
                local = download_document(file_id, filename=filename)
                if local:
                    doc_path = str(local)
                    log(LOG, f"Downloaded document: {doc_path}")

            message_id = msg.get("message_id")
            log(LOG, f"Queued message: {(text or 'file')[:100]}")
            msg_queue.put((text, message_id, image_path, doc_path))
        except Exception as e:
            log(LOG, f"Error parsing update: {e}")

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Telegram webhook server is running.\n")

    def log_message(self, format, *args):
        """Suppress default stderr logging."""
        pass


def main():
    os.chdir(REPO_DIR)

    # Start worker thread
    t = threading.Thread(target=worker, daemon=True)
    t.start()

    server = HTTPServer(("0.0.0.0", PORT), WebhookHandler)

    log(LOG, f"Webhook server starting on port {PORT}")
    print(f"Listening on http://0.0.0.0:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
