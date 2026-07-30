"""Jitsi Service — Core Jitsi logic with SQLite persistence.

IOP: Service handles intent execution, not HTTP routing.
Uses evoid-sqlite for storage.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from evoid import Intent, Level, register_processor
from evoid.core.extend import add_intent_with_pipeline
from evoid.engines.logger import loguru as log

# Import shared models
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from shared import Meeting, WatchParty, detect_content_type, ModeratorAction


# ── Storage (SQLite) ──────────────────────────────────────────────────────────

_storage = None


def init_storage(config: dict) -> None:
    """Initialize SQLite storage from config."""
    global _storage
    db_path = config.get("sqlite", {}).get("db_path", "jitsi.db")
    try:
        from evoid_sqlite import create_storage
        _storage = create_storage(db_path)
        log.info(f"Jitsi SQLite storage: {db_path}")
    except ImportError:
        log.warning("evoid-sqlite not installed, using in-memory")


async def storage_connect() -> None:
    if _storage and hasattr(_storage, "connect"):
        await _storage.connect()


async def storage_close() -> None:
    if _storage and hasattr(_storage, "close"):
        await _storage.close()


# ── Pure Handler Functions (IOP: data in, data out) ──────────────────────────

async def create_meeting(intent: Intent) -> dict:
    """Create a new Jitsi meeting room."""
    room_name = intent.metadata.get("args", [""])[0] if intent.metadata.get("args") else "meeting"
    creator = intent.metadata.get("user_id", "")
    server_url = intent.metadata.get("server_url", "")
    room_id = room_name.lower().replace(" ", "-").replace("_", "-")
    meeting_url = f"{server_url}/{room_id}"

    meeting = Meeting(
        room_id=room_id,
        room_name=room_name,
        creator=creator,
        url=meeting_url,
        is_active=True,
    )

    # Persist
    if _storage:
        await _storage.write(
            f"meeting:{room_id}",
            {
                "room_id": room_id,
                "room_name": room_name,
                "creator": creator,
                "url": meeting_url,
                "is_active": True,
            },
            namespace="meetings",
        )

    return {
        "status": "created",
        "meeting_url": meeting_url,
        "room_id": room_id,
        "room_name": room_name,
    }


async def join_meeting(intent: Intent) -> dict:
    """Get join link for a meeting."""
    room_name = intent.metadata.get("args", [""])[0] if intent.metadata.get("args") else ""
    server_url = intent.metadata.get("server_url", "")
    room_id = room_name.lower().replace(" ", "-").replace("_", "-")
    meeting_url = f"{server_url}/{room_id}"

    # Check if exists
    meeting_data = None
    if _storage:
        meeting_data = await _storage.read(f"meeting:{room_id}", namespace="meetings")

    return {
        "status": "joined" if meeting_data else "created",
        "meeting_url": meeting_url,
        "room_id": room_id,
        "room_name": room_name,
    }


async def watch_party(intent: Intent) -> dict:
    """Create a watch party with shared video."""
    args = intent.metadata.get("args", [])
    video_url = args[0] if len(args) > 0 else ""
    room_name = args[1] if len(args) > 1 else "watch-party"
    creator = intent.metadata.get("user_id", "")
    server_url = intent.metadata.get("server_url", "")
    room_id = room_name.lower().replace(" ", "-").replace("_", "-")
    meeting_url = f"{server_url}/{room_id}"
    content_type = detect_content_type(video_url)

    party = WatchParty(
        room_id=room_id,
        room_name=room_name,
        video_url=video_url,
        content_type=content_type,
        creator=creator,
        is_active=True,
    )

    if _storage:
        await _storage.write(
            f"watch:{room_id}",
            {
                "room_id": room_id,
                "room_name": room_name,
                "video_url": video_url,
                "content_type": content_type,
                "creator": creator,
                "is_active": True,
            },
            namespace="watch_parties",
        )

    return {
        "status": "watch_party_created",
        "meeting_url": meeting_url,
        "room_id": room_id,
        "content_type": content_type,
    }


async def stop_watch_party(intent: Intent) -> dict:
    """Stop shared video playback."""
    room_id = intent.metadata.get("room_id", "")
    if _storage and room_id:
        await _storage.update(
            f"watch:{room_id}",
            {"is_active": False},
            namespace="watch_parties",
        )
    return {"status": "watch_party_stopped", "iframe_command": "stopShareVideo"}


# ── Call Control ──────────────────────────────────────────────────────────────

async def hangup(intent: Intent) -> dict:
    return {"status": "hung_up", "iframe_command": "hangup"}


async def end_conference(intent: Intent) -> dict:
    room_id = intent.metadata.get("room_id", "")
    if _storage and room_id:
        await _storage.update(
            f"meeting:{room_id}",
            {"is_active": False},
            namespace="meetings",
        )
    return {"status": "conference_ended", "iframe_command": "endConference"}


# ── Media ─────────────────────────────────────────────────────────────────────

async def toggle_audio(intent: Intent) -> dict:
    return {"status": "audio_toggled", "iframe_command": "toggleAudio"}


async def toggle_video(intent: Intent) -> dict:
    return {"status": "video_toggled", "iframe_command": "toggleVideo"}


async def toggle_screen(intent: Intent) -> dict:
    return {"status": "screen_toggled", "iframe_command": "toggleShareScreen"}


async def mute_everyone(intent: Intent) -> dict:
    media_type = intent.metadata.get("media_type", "audio")
    return {"status": "everyone_muted", "media_type": media_type, "iframe_command": "muteEveryone"}


async def set_video_quality(intent: Intent) -> dict:
    height = intent.metadata.get("height", 720)
    return {"status": "quality_set", "height": height, "iframe_command": "setVideoQuality"}


# ── Participants ──────────────────────────────────────────────────────────────

async def kick(intent: Intent) -> dict:
    participant_id = intent.metadata.get("args", [""])[0] if intent.metadata.get("args") else ""
    user = intent.metadata.get("user_id", "")
    room_id = intent.metadata.get("room_id", "")
    if _storage and room_id:
        await _storage.write(
            f"action:{room_id}:{participant_id}",
            {
                "room_id": room_id,
                "action": "kick",
                "target_user": participant_id,
                "performed_by": user,
            },
            namespace="moderator_actions",
        )
    return {"status": "kicked", "participantId": participant_id, "iframe_command": "kickParticipant"}


async def grant_moderator(intent: Intent) -> dict:
    participant_id = intent.metadata.get("args", [""])[0] if intent.metadata.get("args") else ""
    user = intent.metadata.get("user_id", "")
    room_id = intent.metadata.get("room_id", "")
    if _storage and room_id:
        await _storage.write(
            f"action:{room_id}:{participant_id}",
            {
                "room_id": room_id,
                "action": "grant_moderator",
                "target_user": participant_id,
                "performed_by": user,
            },
            namespace="moderator_actions",
        )
    return {"status": "moderator_granted", "participantId": participant_id, "iframe_command": "grantModerator"}


async def pin_participant(intent: Intent) -> dict:
    participant_id = intent.metadata.get("participant_id", "")
    room_id = intent.metadata.get("room_id", "")
    return {"status": "participant_pinned", "participantId": participant_id, "iframe_command": "pinParticipant"}


async def set_volume(intent: Intent) -> dict:
    participant_id = intent.metadata.get("participant_id", "")
    volume = intent.metadata.get("volume", 1.0)
    room_id = intent.metadata.get("room_id", "")
    return {"status": "volume_set", "participantId": participant_id, "volume": volume, "iframe_command": "setParticipantVolume"}


# ── Layout ────────────────────────────────────────────────────────────────────

async def toggle_tile(intent: Intent) -> dict:
    return {"status": "tile_toggled", "iframe_command": "toggleTileView"}


async def toggle_chat(intent: Intent) -> dict:
    return {"status": "chat_toggled", "iframe_command": "toggleChat"}


async def toggle_raise_hand(intent: Intent) -> dict:
    return {"status": "hand_toggled", "iframe_command": "toggleRaiseHand"}


async def toggle_lobby(intent: Intent) -> dict:
    enabled = intent.metadata.get("enabled", True)
    room_id = intent.metadata.get("room_id", "")
    return {"status": "lobby_toggled", "enabled": enabled, "iframe_command": "toggleLobby"}


# ── Recording ─────────────────────────────────────────────────────────────────

async def start_recording(intent: Intent) -> dict:
    mode = intent.metadata.get("args", ["local"])[0] if intent.metadata.get("args") else "local"
    user = intent.metadata.get("user_id", "")
    room_id = intent.metadata.get("room_id", "")
    if _storage and room_id:
        await _storage.write(
            f"action:{room_id}:recording",
            {
                "room_id": room_id,
                "action": "start_recording",
                "mode": mode,
                "performed_by": user,
            },
            namespace="moderator_actions",
        )
    return {"status": "recording_started", "mode": mode, "iframe_command": "startRecording"}


async def stop_recording(intent: Intent) -> dict:
    mode = intent.metadata.get("args", ["local"])[0] if intent.metadata.get("args") else "local"
    user = intent.metadata.get("user_id", "")
    room_id = intent.metadata.get("room_id", "")
    if _storage and room_id:
        await _storage.write(
            f"action:{room_id}:recording",
            {
                "room_id": room_id,
                "action": "stop_recording",
                "mode": mode,
                "performed_by": user,
            },
            namespace="moderator_actions",
        )
    return {"status": "recording_stopped", "mode": mode, "iframe_command": "stopRecording"}


# ── Breakout ──────────────────────────────────────────────────────────────────

async def add_breakout(intent: Intent) -> dict:
    name = intent.metadata.get("args", [""])[0] if intent.metadata.get("args") else ""
    room_id = intent.metadata.get("room_id", "")
    return {"status": "breakout_added", "name": name, "iframe_command": "addBreakoutRoom"}


async def close_breakout(intent: Intent) -> dict:
    room_id = intent.metadata.get("room_id", "")
    return {"status": "breakout_closed", "roomId": room_id, "iframe_command": "closeBreakoutRoom"}


async def join_breakout(intent: Intent) -> dict:
    room_id = intent.metadata.get("room_id", "")
    return {"status": "breakout_joined", "roomId": room_id, "iframe_command": "joinBreakoutRoom"}


# ── Misc ──────────────────────────────────────────────────────────────────────

async def set_subject(intent: Intent) -> dict:
    subject = intent.metadata.get("args", [""])[0] if intent.metadata.get("args") else ""
    room_id = intent.metadata.get("room_id", "")
    return {"status": "subject_set", "subject": subject, "iframe_command": "subject"}


async def send_chat(intent: Intent) -> dict:
    message = intent.metadata.get("args", [""])[0] if intent.metadata.get("args") else ""
    to = intent.metadata.get("to", "")
    room_id = intent.metadata.get("room_id", "")
    return {"status": "chat_sent", "message": message, "to": to, "iframe_command": "sendChatMessage"}


async def set_follow_me(intent: Intent) -> dict:
    enabled = intent.metadata.get("enabled", True)
    recorder_only = intent.metadata.get("recorder_only", False)
    room_id = intent.metadata.get("room_id", "")
    return {"status": "follow_me_set", "enabled": enabled, "recorder_only": recorder_only, "iframe_command": "setFollowMe"}


# ── Health ────────────────────────────────────────────────────────────────────

async def health(intent: Intent) -> dict:
    return {"status": "healthy", "service": "jitsi", "storage": "sqlite" if _storage else "memory"}


# ── Register Processors ───────────────────────────────────────────────────────

from shared.processors import validate, authorize, audit, protect

register_processor("validate", validate)
register_processor("authorize", authorize)
register_processor("audit", audit)
register_processor("protect", protect)


# ── Create Service & Register Handlers ────────────────────────────────────────

from evoid.core.service import Service, on

jitsi_service = Service("jitsi")

# Standard: validate → authorize → handler
standard_intents = [
    ("jitsi:create_meeting", create_meeting),
    ("jitsi:join_meeting", join_meeting),
    ("jitsi:watch_party", watch_party),
    ("jitsi:stop_watch_party", stop_watch_party),
    ("jitsi:toggle_audio", toggle_audio),
    ("jitsi:toggle_video", toggle_video),
    ("jitsi:toggle_screen", toggle_screen),
    ("jitsi:mute_everyone", mute_everyone),
    ("jitsi:set_video_quality", set_video_quality),
    ("jitsi:pin_participant", pin_participant),
    ("jitsi:set_volume", set_volume),
    ("jitsi:toggle_tile", toggle_tile),
    ("jitsi:toggle_chat", toggle_chat),
    ("jitsi:toggle_raise_hand", toggle_raise_hand),
    ("jitsi:toggle_lobby", toggle_lobby),
    ("jitsi:set_subject", set_subject),
    ("jitsi:send_chat", send_chat),
    ("jitsi:set_follow_me", set_follow_me),
]

for name, handler in standard_intents:
    add_intent_with_pipeline(
        Intent(name=name, level=Level.STANDARD),
        processors=["validate", "authorize", handler],
    )
    on(jitsi_service, name, handler)

# Critical: validate → authorize → audit → protect → handler
critical_intents = [
    ("jitsi:kick", kick),
    ("jitsi:grant_moderator", grant_moderator),
    ("jitsi:hangup", hangup),
    ("jitsi:end_conference", end_conference),
    ("jitsi:start_recording", start_recording),
    ("jitsi:stop_recording", stop_recording),
    ("jitsi:add_breakout", add_breakout),
    ("jitsi:close_breakout", close_breakout),
    ("jitsi:join_breakout", join_breakout),
]

for name, handler in critical_intents:
    add_intent_with_pipeline(
        Intent(name=name, level=Level.CRITICAL),
        processors=["validate", "authorize", "audit", "protect", handler],
    )
    on(jitsi_service, name, handler)

# Health: EPHEMERAL
add_intent_with_pipeline(
    Intent(name="health", level=Level.EPHEMERAL),
    processors=["validate", health],
)
on(jitsi_service, "health", health)


# ── Run as Service ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import asyncio
    from evoid.core import start
    from evoid.config.loader import load
    from pathlib import Path

    # Load config & init storage
    config = load(Path(__file__).parent / "evoid.toml")
    init_storage(config.engines.options)

    # Start service (subscribes handlers to message bus)
    start(jitsi_service)

    async def run_service():
        await storage_connect()
        log.init("jitsi")
        print("Jitsi service running (intent handlers registered + message bus subscribed)")
        await asyncio.Event().wait()

    asyncio.run(run_service())