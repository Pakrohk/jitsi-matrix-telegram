"""Telegram Bot Service — Converts Telegram messages to EVOID Intents."""

import asyncio
import os

from evoid import Intent, Level
from evoid.adapters.telegram import create_bot, on, run_bot
from evoid.engines.logger import loguru as log


token = os.environ.get("TELEGRAM_TOKEN", "")
bot = create_bot(token=token) if token else None


# ── Handlers ────────────────────────────────────────────────────────────────

async def handle_start(intent: Intent) -> str:
    return "Jitsi Bot ready! Use /help for commands."


async def handle_help(intent: Intent) -> str:
    return """Jitsi Bot Commands:
/create [name] - Create meeting
/join <room> - Join meeting
/watch <url> [name] - Watch party
/stopwatch - Stop watch party
/hangup - End call
/mute - Toggle audio
/video - Toggle video
/screen - Toggle screen share
/kick <id> - Kick participant (mod)
/mod <id> - Grant moderator (mod)
/record <mode> - Start recording (mod)
/stoprecord <mode> - Stop recording (mod)"""


async def handle_create(intent: Intent) -> str:
    args = intent.metadata.get("args", [])
    room_name = args[0] if args else "My Meeting"
    room_id = room_name.lower().replace(" ", "-")
    server_url = os.environ.get("JITSI_SERVER_URL", "https://meet.example.com")
    return f"Meeting created: {server_url}/{room_id}"


async def handle_join(intent: Intent) -> str:
    args = intent.metadata.get("args", [])
    if not args:
        return "Usage: /join <room_name>"
    room_id = args[0].lower().replace(" ", "-")
    server_url = os.environ.get("JITSI_SERVER_URL", "https://meet.example.com")
    return f"Join: {server_url}/{room_id}"


async def handle_watch(intent: Intent) -> str:
    args = intent.metadata.get("args", [])
    if not args:
        return "Usage: /watch <url> [name]"
    from shared import detect_content_type
    content_type = detect_content_type(args[0])
    return f"Watch party ({content_type}): {args[0]}"


async def handle_mute(intent: Intent) -> str:
    return "Audio toggled"


async def handle_video(intent: Intent) -> str:
    return "Video toggled"


async def handle_hangup(intent: Intent) -> str:
    return "Call ended"


# ── Register & Run ──────────────────────────────────────────────────────────

if bot:
    on(bot, "command:/start", handle_start)
    on(bot, "command:/help", handle_help)
    on(bot, "command:/create", handle_create)
    on(bot, "command:/join", handle_join)
    on(bot, "command:/watch", handle_watch)
    on(bot, "command:/mute", handle_mute)
    on(bot, "command:/video", handle_video)
    on(bot, "command:/hangup", handle_hangup)


if __name__ == "__main__":
    log.init("telebot")
    if bot:
        asyncio.run(run_bot(bot))
    else:
        print("Set TELEGRAM_TOKEN environment variable")
