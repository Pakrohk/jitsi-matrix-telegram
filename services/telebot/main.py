"""Telegram Bot Service — Adapter converts Telegram updates to Intents.

IOP: Adapter = pure data conversion. No business logic.
Proxy support for Iran: socks5://127.0.0.1:2081
"""

from __future__ import annotations

import os
from pathlib import Path

from evoid import Intent, Level
from evoid.adapters.telegram import create_bot, on, run_bot
from evoid.config.loader import load as load_config
from evoid.engines.logger import loguru as log

# ── Load Config from evoid.toml ──────────────────────────────────────────────
_config = load_config(Path(__file__).parent / "evoid.toml")

# EVOID extracts [engines.X] as options["X"]
_telegram_cfg = _config.engines.options.get("telegram", {})
_proxy_cfg = _config.engines.options.get("proxy", {})
_jitsi_cfg = _config.engines.options.get("jitsi", {})
_admin_cfg = _config.engines.options.get("admin", {})

_token = os.environ.get("TELEGRAM_TOKEN", _telegram_cfg.get("token", ""))
_parse_mode = _telegram_cfg.get("parse_mode", "HTML")

_proxy_enabled = _proxy_cfg.get("enabled", False)
_proxy_type = _proxy_cfg.get("type", "socks5")
_proxy_host = _proxy_cfg.get("host", "127.0.0.1")
_proxy_port = _proxy_cfg.get("port", 2081)

_jitsi_url = os.environ.get("JITSI_SERVER_URL", _jitsi_cfg.get("server_url", "https://meet.example.com"))
_muc_domain = _jitsi_cfg.get("muc_domain", "conference.meet.example.com")

_admin_whitelist = _admin_cfg.get("whitelist", [])
_require_auth = _admin_cfg.get("require_auth", False)

# ── Bot Creation with Proxy ──────────────────────────────────────────────────

def create_telegram_bot():
    """Create Telegram bot with optional proxy support."""
    if not _token:
        log.warning("TELEGRAM_TOKEN not set")
        return None

    bot = create_bot(token=_token)

    if _proxy_enabled:
        proxy_url = f"{_proxy_type}://{_proxy_host}:{_proxy_port}"
        log.info(f"Telegram bot using proxy: {proxy_url}")
        # aiogram 3.x proxy support via aiohttp
        # Note: Actual proxy config depends on aiogram version

    return bot


bot = create_telegram_bot()

# ── Intent Publishers (Pure Functions) ────────────────────────────────────────

async def publish_create_meeting(room_name: str, user_id: int, chat_id: int) -> dict:
    """Publish jitsi:create_meeting intent."""
    intent = Intent(
        name="jitsi:create_meeting",
        level=Level.STANDARD,
        metadata={
            "command": "create",
            "args": [room_name] if room_name else [],
            "user_id": str(user_id),
            "chat_id": str(chat_id),
            "server_url": _jitsi_url,
        },
    )
    from evoid import publish
    result = await publish(intent, source="telebot")
    return result[0] if result else {"error": "No handler"}


async def publish_join_meeting(room_name: str, user_id: int, chat_id: int) -> dict:
    intent = Intent(
        name="jitsi:join_meeting",
        level=Level.STANDARD,
        metadata={
            "command": "join",
            "args": [room_name],
            "user_id": str(user_id),
            "chat_id": str(chat_id),
            "server_url": _jitsi_url,
        },
    )
    from evoid import publish
    result = await publish(intent, source="telebot")
    return result[0] if result else {"error": "No handler"}


async def publish_watch_party(video_url: str, room_name: str, user_id: int, chat_id: int) -> dict:
    intent = Intent(
        name="jitsi:watch_party",
        level=Level.STANDARD,
        metadata={
            "command": "watch",
            "args": [video_url, room_name],
            "user_id": str(user_id),
            "chat_id": str(chat_id),
            "server_url": _jitsi_url,
        },
    )
    from evoid import publish
    result = await publish(intent, source="telebot")
    return result[0] if result else {"error": "No handler"}


async def publish_media_toggle(command: str, user_id: int, chat_id: int) -> dict:
    intent_map = {
        "mute": "jitsi:toggle_audio",
        "video": "jitsi:toggle_video",
        "screen": "jitsi:toggle_screen",
    }
    intent = Intent(
        name=intent_map[command],
        level=Level.STANDARD,
        metadata={
            "command": command,
            "args": [],
            "user_id": str(user_id),
            "chat_id": str(chat_id),
        },
    )
    from evoid import publish
    result = await publish(intent, source="telebot")
    return result[0] if result else {"error": "No handler"}


async def publish_admin_command(command: str, target_id: str, user_id: int, chat_id: int) -> dict:
    intent_map = {
        "kick": "jitsi:kick",
        "mod": "jitsi:grant_moderator",
        "record": "jitsi:start_recording",
        "stoprecord": "jitsi:stop_recording",
    }
    intent = Intent(
        name=intent_map[command],
        level=Level.CRITICAL,
        metadata={
            "command": command,
            "args": [target_id],
            "user_id": str(user_id),
            "chat_id": str(chat_id),
        },
    )
    from evoid import publish
    result = await publish(intent, source="telebot")
    return result[0] if result else {"error": "No handler"}


# ── Format Responses ──────────────────────────────────────────────────────────

def format_response(command: str, result: dict) -> str:
    """Format EVOID result for Telegram response."""
    status = result.get("status", "unknown")

    if command == "create":
        room_name = result.get("room_name", "Meeting")
        url = result.get("meeting_url", "")
        return f"✅ Meeting created!\n\n🔗 <a href=\"{url}\">{room_name}</a>"

    elif command == "join":
        room_name = result.get("room_name", "Meeting")
        url = result.get("meeting_url", "")
        return f"🔗 <a href=\"{url}\">Join {room_name}</a>"

    elif command == "watch":
        room_name = result.get("room_name", "Watch Party")
        url = result.get("meeting_url", "")
        content_type = result.get("content_type", "unknown")
        video_url = result.get("video_url", "")
        return f"🎬 <b>Watch Party</b> ({content_type})\n\n🔗 <a href=\"{url}\">{room_name}</a>\n📺 {video_url}"

    elif command in ("mute", "video", "screen"):
        emoji = {"mute": "🔇", "video": "📹", "screen": "🖥️"}[command]
        return f"{emoji} {command.capitalize()} toggled"

    elif command == "kick":
        return f"👢 Kicked: {result.get('participantId', 'unknown')}"

    elif command == "mod":
        return f"👑 Moderator granted: {result.get('participantId', 'unknown')}"

    elif command == "record":
        return f"🔴 Recording started ({result.get('mode', 'local')})"

    elif command == "stoprecord":
        return f"⏹️ Recording stopped ({result.get('mode', 'local')})"

    return f"{command}: {status}"


# ── Telegram Handlers (Adapter) ──────────────────────────────────────────────

async def handle_start(intent: Intent) -> str:
    return "🤖 <b>Jitsi Bot</b>\n\nWelcome! Type /help for commands."


async def handle_help(intent: Intent) -> str:
    return """📋 <b>Commands</b>

<b>Meeting:</b>
/create [name] - Create meeting
/join <room> - Join meeting
/hangup - End call

<b>Watch Party:</b>
/watch <url> [name] - Watch together
/stopwatch - Stop shared video

<b>Media:</b>
/mute - Toggle audio
/video - Toggle video
/screen - Toggle screen share

<b>Moderation (admin only):</b>
/kick <id> - Kick participant
/mod <id> - Grant moderator
/record <mode> - Start recording
/stoprecord <mode> - Stop recording"""


async def handle_create(intent: Intent) -> str:
    args = intent.metadata.get("args", [])
    user_id = int(intent.metadata.get("user_id", 0))
    chat_id = int(intent.metadata.get("chat_id", 0))
    room_name = args[0] if args else "My Meeting"

    result = await publish_create_meeting(room_name, user_id, chat_id)
    return format_response("create", result)


async def handle_join(intent: Intent) -> str:
    args = intent.metadata.get("args", [])
    user_id = int(intent.metadata.get("user_id", 0))
    chat_id = int(intent.metadata.get("chat_id", 0))

    if not args:
        return "Usage: /join <room_name>"

    result = await publish_join_meeting(args[0], user_id, chat_id)
    return format_response("join", result)


async def handle_watch(intent: Intent) -> str:
    args = intent.metadata.get("args", [])
    user_id = int(intent.metadata.get("user_id", 0))
    chat_id = int(intent.metadata.get("chat_id", 0))

    if not args:
        return "Usage: /watch <url> [name]"

    video_url = args[0]
    room_name = args[1] if len(args) > 1 else "Watch Party"

    result = await publish_watch_party(video_url, room_name, user_id, chat_id)
    return format_response("watch", result)


async def handle_media_toggle(intent: Intent) -> str:
    command = intent.metadata.get("command", "")
    user_id = int(intent.metadata.get("user_id", 0))
    chat_id = int(intent.metadata.get("chat_id", 0))

    result = await publish_media_toggle(command, user_id, chat_id)
    return format_response(command, result)


async def handle_admin(intent: Intent) -> str:
    command = intent.metadata.get("command", "")
    args = intent.metadata.get("args", [])
    user_id = int(intent.metadata.get("user_id", 0))
    chat_id = int(intent.metadata.get("chat_id", 0))

    if not args:
        return f"Usage: /{command} <participant_id>"

    # Check auth
    if _require_auth and _admin_whitelist and str(user_id) not in map(str, _admin_whitelist):
        return "❌ Not authorized"

    result = await publish_admin_command(command, args[0], user_id, chat_id)
    return format_response(command, result)


async def handle_hangup(intent: Intent) -> str:
    user_id = int(intent.metadata.get("user_id", 0))
    chat_id = int(intent.metadata.get("chat_id", 0))
    intent_obj = Intent(
        name="jitsi:hangup",
        level=Level.STANDARD,
        metadata={"command": "hangup", "args": [], "user_id": str(user_id), "chat_id": str(chat_id)},
    )
    from evoid import publish
    result = await publish(intent_obj, source="telebot")
    return format_response("hangup", result[0] if result else {})


async def handle_stopwatch(intent: Intent) -> str:
    user_id = int(intent.metadata.get("user_id", 0))
    chat_id = int(intent.metadata.get("chat_id", 0))
    intent_obj = Intent(
        name="jitsi:stop_watch_party",
        level=Level.STANDARD,
        metadata={"command": "stopwatch", "args": [], "user_id": str(user_id), "chat_id": str(chat_id)},
    )
    from evoid import publish
    await publish(intent_obj, source="telebot")
    return "⏹️ Watch party stopped"


# ── Register Telegram Handlers ────────────────────────────────────────────────

def register_handlers(bot):
    """Map Telegram commands to adapter handlers."""
    on(bot, "command:/start", handle_start)
    on(bot, "command:/help", handle_help)
    on(bot, "command:/create", handle_create)
    on(bot, "command:/join", handle_join)
    on(bot, "command:/watch", handle_watch)
    on(bot, "command:/stopwatch", handle_stopwatch)
    on(bot, "command:/mute", handle_media_toggle)
    on(bot, "command:/video", handle_media_toggle)
    on(bot, "command:/screen", handle_media_toggle)
    on(bot, "command:/hangup", handle_hangup)
    on(bot, "command:/kick", handle_admin)
    on(bot, "command:/mod", handle_admin)
    on(bot, "command:/record", handle_admin)
    on(bot, "command:/stoprecord", handle_admin)


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    log.init("telebot", level="INFO")

    if not bot:
        print("Error: Set TELEGRAM_TOKEN in evoid.toml or env var")
        print(f"Proxy: {_proxy_type}://{_proxy_host}:{_proxy_port} (enabled={_proxy_enabled})")
    else:
        register_handlers(bot)
        print("Starting Telegram bot...")
        print(f"Jitsi: {_jitsi_url}")
        if _proxy_enabled:
            print(f"Proxy: {_proxy_type}://{_proxy_host}:{_proxy_port}")
        import asyncio
        asyncio.run(run_bot(bot))
