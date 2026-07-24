"""Telegram Bot Service — Converts Telegram messages to EVOID Intents.

IOP: Adapters convert external events to Intents.
Config lives in evoid.toml under [engines.options.telegram].
"""

import asyncio
import os
from pathlib import Path

from evoid import Intent, Level
from evoid.config.loader import load as load_config
from evoid.engines.logger import loguru as log


# ── Load Config from evoid.toml ─────────────────────────────────────────────

_config = load_config(Path(__file__).parent / "evoid.toml")

# EVOID extracts [engines.X] as options["X"]
_token = _config.engines.options.get("telegram", {}).get("token", "")
_token = os.environ.get("TELEGRAM_TOKEN", _token)

_proxy_cfg = _config.engines.options.get("proxy", {})
_proxy_enabled = _proxy_cfg.get("enabled", False)

_jitsi_cfg = _config.engines.options.get("jitsi", {})
_jitsi_url = os.environ.get("JITSI_SERVER_URL", _jitsi_cfg.get("server_url", "https://meet.example.com"))

_admin_cfg = _config.engines.options.get("admin", {})
_admin_whitelist = _admin_cfg.get("whitelist", [])


# ── Bot Creation ────────────────────────────────────────────────────────────

def create_telegram_bot():
    """Create Telegram bot with optional proxy support."""
    from evoid.adapters.telegram import create_bot

    if not _token:
        return None

    # Proxy support
    if _proxy_enabled:
        proxy_type = _proxy_cfg.get("type", "socks5")
        proxy_host = _proxy_cfg.get("host", "127.0.0.1")
        proxy_port = _proxy_cfg.get("port", 1080)
        log.info(f"Using proxy: {proxy_type}://{proxy_host}:{proxy_port}")

    bot = create_bot(token=_token)
    return bot


bot = create_telegram_bot()


# ── Intent Handlers ─────────────────────────────────────────────────────────

async def handle_start(intent: Intent) -> str:
    return "🤖 <b>Jitsi Bot</b>\n\nWelcome! Type /help for commands."


async def handle_help(intent: Intent) -> str:
    return """📋 <b>Commands</b>

<b>Meeting:</b>
/create [name] - Create meeting
/join &lt;room&gt; - Join meeting
/hangup - End call

<b>Watch Party:</b>
/watch &lt;url&gt; [name] - Watch together
/stopwatch - Stop shared video

<b>Media:</b>
/mute - Toggle audio
/video - Toggle video
/screen - Toggle screen share

<b>Moderation:</b>
/kick &lt;id&gt; - Kick participant
/mod &lt;id&gt; - Grant moderator
/record &lt;mode&gt; - Start recording
/stoprecord &lt;mode&gt; - Stop recording"""


async def handle_create(intent: Intent) -> str:
    args = intent.metadata.get("args", [])
    room_name = args[0] if args else "My Meeting"
    room_id = room_name.lower().replace(" ", "-")
    url = f"{_jitsi_url}/{room_id}"
    return f"✅ Meeting created!\n\n🔗 <a href=\"{url}\">{room_name}</a>"


async def handle_join(intent: Intent) -> str:
    args = intent.metadata.get("args", [])
    if not args:
        return "Usage: /join &lt;room_name&gt;"
    room_id = args[0].lower().replace(" ", "-")
    url = f"{_jitsi_url}/{room_id}"
    return f"🔗 <a href=\"{url}\">Join {args[0]}</a>"


async def handle_watch(intent: Intent) -> str:
    args = intent.metadata.get("args", [])
    if not args:
        return "Usage: /watch &lt;url&gt; [name]"
    from shared import detect_content_type
    content_type = detect_content_type(args[0])
    room_name = args[1] if len(args) > 1 else "Watch Party"
    room_id = room_name.lower().replace(" ", "-")
    url = f"{_jitsi_url}/{room_id}"
    return f"🎬 <b>Watch Party</b> ({content_type})\n\n🔗 <a href=\"{url}\">{room_name}</a>\n📺 {args[0]}"


async def handle_stopwatch(intent: Intent) -> str:
    return "⏹️ Watch party stopped"


async def handle_mute(intent: Intent) -> str:
    return "🔇 Audio toggled"


async def handle_video(intent: Intent) -> str:
    return "📹 Video toggled"


async def handle_screen(intent: Intent) -> str:
    return "🖥️ Screen share toggled"


async def handle_hangup(intent: Intent) -> str:
    return "📞 Call ended"


async def handle_kick(intent: Intent) -> str:
    args = intent.metadata.get("args", [])
    if not args:
        return "Usage: /kick &lt;participant_id&gt;"
    return f"👢 Kicked: {args[0]}"


async def handle_mod(intent: Intent) -> str:
    args = intent.metadata.get("args", [])
    if not args:
        return "Usage: /mod &lt;participant_id&gt;"
    return f"👑 Moderator granted: {args[0]}"


async def handle_record(intent: Intent) -> str:
    args = intent.metadata.get("args", [])
    mode = args[0] if args else "local"
    return f"🔴 Recording started ({mode})"


async def handle_stoprecord(intent: Intent) -> str:
    args = intent.metadata.get("args", [])
    mode = args[0] if args else "local"
    return f"⏹️ Recording stopped ({mode})"


# ── Register Handlers ───────────────────────────────────────────────────────

def register_handlers(bot):
    from evoid.adapters.telegram import on

    on(bot, "command:/start", handle_start)
    on(bot, "command:/help", handle_help)
    on(bot, "command:/create", handle_create)
    on(bot, "command:/join", handle_join)
    on(bot, "command:/watch", handle_watch)
    on(bot, "command:/stopwatch", handle_stopwatch)
    on(bot, "command:/mute", handle_mute)
    on(bot, "command:/video", handle_video)
    on(bot, "command:/screen", handle_screen)
    on(bot, "command:/hangup", handle_hangup)
    on(bot, "command:/kick", handle_kick)
    on(bot, "command:/mod", handle_mod)
    on(bot, "command:/record", handle_record)
    on(bot, "command:/stoprecord", handle_stoprecord)


# ── Main ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    log.init("telebot", level="INFO")

    if not bot:
        print("Error: Set token in evoid.toml or TELEGRAM_TOKEN env var")
    else:
        register_handlers(bot)
        print(f"Starting Telegram bot...")
        print(f"Jitsi: {_jitsi_url}")
        if _proxy_enabled:
            print(f"Proxy: {_proxy_cfg.get('type')}://{_proxy_cfg.get('host')}:{_proxy_cfg.get('port')}")
        asyncio.run(run_bot(bot))
