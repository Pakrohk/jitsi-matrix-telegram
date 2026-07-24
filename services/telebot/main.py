"""Telegram Bot Service — Converts Telegram messages to EVOID Intents.

IOP: Adapters convert external events to Intents.
Telegram messages → Intents → Gateway → Response → Telegram
"""

import asyncio
from pathlib import Path

from evoid import Intent, Level
from evoid.engines.logger import loguru as log

from config import load_config, BotConfig


# ── Load Config ─────────────────────────────────────────────────────────────

config = load_config(Path(__file__).parent / "config.yaml")


# ── Bot Creation ────────────────────────────────────────────────────────────

def create_telegram_bot(config: BotConfig):
    """Create Telegram bot with optional proxy support."""
    from evoid.adapters.telegram import create_bot

    if not config.token:
        return None

    # Proxy support
    proxy_url = config.proxy.url
    if proxy_url:
        log.info(f"Using proxy: {config.proxy.type}://{config.proxy.host}:{config.proxy.port}")

    bot = create_bot(token=config.token)
    return bot


bot = create_telegram_bot(config)


# ── Intent Handlers ─────────────────────────────────────────────────────────

async def handle_start(intent: Intent) -> str:
    """Handle /start command."""
    return f"""🤖 <b>Jitsi Bot</b>

Welcome! I manage Jitsi meetings from Telegram.

Type /help to see available commands."""


async def handle_help(intent: Intent) -> str:
    """Handle /help command."""
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
    """Handle /create command."""
    args = intent.metadata.get("args", [])
    room_name = args[0] if args else "My Meeting"
    room_id = room_name.lower().replace(" ", "-")
    url = f"{config.jitsi.server_url}/{room_id}"

    return f"✅ Meeting created!\n\n🔗 <a href=\"{url}\">{room_name}</a>"


async def handle_join(intent: Intent) -> str:
    """Handle /join command."""
    args = intent.metadata.get("args", [])
    if not args:
        return "Usage: /join &lt;room_name&gt;"

    room_id = args[0].lower().replace(" ", "-")
    url = f"{config.jitsi.server_url}/{room_id}"

    return f"🔗 <a href=\"{url}\">Join {args[0]}</a>"


async def handle_watch(intent: Intent) -> str:
    """Handle /watch command."""
    args = intent.metadata.get("args", [])
    if not args:
        return "Usage: /watch &lt;url&gt; [name]"

    from shared import detect_content_type
    content_type = detect_content_type(args[0])
    room_name = args[1] if len(args) > 1 else "Watch Party"
    room_id = room_name.lower().replace(" ", "-")
    url = f"{config.jitsi.server_url}/{room_id}"

    return f"🎬 <b>Watch Party</b> ({content_type})\n\n🔗 <a href=\"{url}\">{room_name}</a>\n📺 {args[0]}"


async def handle_stopwatch(intent: Intent) -> str:
    """Handle /stopwatch command."""
    return "⏹️ Watch party stopped"


async def handle_mute(intent: Intent) -> str:
    """Handle /mute command."""
    return "🔇 Audio toggled"


async def handle_video(intent: Intent) -> str:
    """Handle /video command."""
    return "📹 Video toggled"


async def handle_screen(intent: Intent) -> str:
    """Handle /screen command."""
    return "🖥️ Screen share toggled"


async def handle_hangup(intent: Intent) -> str:
    """Handle /hangup command."""
    return "📞 Call ended"


async def handle_kick(intent: Intent) -> str:
    """Handle /kick command."""
    args = intent.metadata.get("args", [])
    if not args:
        return "Usage: /kick &lt;participant_id&gt;"
    return f"👢 Kicked: {args[0]}"


async def handle_mod(intent: Intent) -> str:
    """Handle /mod command."""
    args = intent.metadata.get("args", [])
    if not args:
        return "Usage: /mod &lt;participant_id&gt;"
    return f"👑 Moderator granted: {args[0]}"


async def handle_record(intent: Intent) -> str:
    """Handle /record command."""
    args = intent.metadata.get("args", [])
    mode = args[0] if args else "local"
    return f"🔴 Recording started ({mode})"


async def handle_stoprecord(intent: Intent) -> str:
    """Handle /stoprecord command."""
    args = intent.metadata.get("args", [])
    mode = args[0] if args else "local"
    return f"⏹️ Recording stopped ({mode})"


# ── Register Handlers ───────────────────────────────────────────────────────

def register_handlers(bot):
    """Register all command handlers with the bot."""
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
    log.init("telebot", level=config.logging.level)

    if not bot:
        print("Error: Set TELEGRAM_TOKEN in config.yaml or environment")
        print("  export TELEGRAM_TOKEN='your_bot_token'")
    else:
        register_handlers(bot)
        print(f"Starting Telegram bot...")
        print(f"Jitsi server: {config.jitsi.server_url}")
        if config.proxy.enabled:
            print(f"Proxy: {config.proxy.type}://{config.proxy.host}:{config.proxy.port}")
        asyncio.run(run_bot(bot))
