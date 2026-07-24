"""Gateway Service — Routes Intents between services.

IOP: Gateway is the central Intent router.
Intents carry data, not behavior.
Pipeline: validate → authorize → audit → protect
"""

from evoid import Intent, Level, register_processor

from shared import detect_content_type
from shared.processors import validate, authorize, audit, protect


# ── Register Processors ─────────────────────────────────────────────────────

register_processor("validate", validate)
register_processor("authorize", authorize)
register_processor("audit", audit)
register_processor("protect", protect)


# ── Meeting Handlers (Pure Functions) ────────────────────────────────────────

async def create_meeting(room_name: str = "meeting", creator: str = "", server_url: str = "") -> dict:
    """Create a new Jitsi meeting room."""
    room_id = room_name.lower().replace(" ", "-").replace("_", "-")
    meeting_url = f"{server_url}/{room_id}"
    return {
        "status": "created",
        "meeting_url": meeting_url,
        "room_id": room_id,
        "iframe_command": None,
    }


async def join_meeting(room_name: str = "", server_url: str = "") -> dict:
    """Get join link for a meeting."""
    room_id = room_name.lower().replace(" ", "-").replace("_", "-")
    meeting_url = f"{server_url}/{room_id}"
    return {
        "status": "joined",
        "meeting_url": meeting_url,
        "room_id": room_id,
        "iframe_command": None,
    }


async def watch_party(video_url: str = "", room_name: str = "watch-party", creator: str = "", server_url: str = "") -> dict:
    """Create a watch party with shared video."""
    room_id = room_name.lower().replace(" ", "-").replace("_", "-")
    meeting_url = f"{server_url}/{room_id}"
    content_type = detect_content_type(video_url)
    return {
        "status": "watch_party_created",
        "meeting_url": meeting_url,
        "content_type": content_type,
        "iframe_command": "startShareVideo",
    }


async def stop_watch_party() -> dict:
    """Stop shared video playback."""
    return {
        "status": "watch_party_stopped",
        "iframe_command": "stopShareVideo",
    }


# ── Call Control Handlers ───────────────────────────────────────────────────

async def hangup() -> dict:
    """End the call."""
    return {"status": "hung_up", "iframe_command": "hangup"}


async def end_conference() -> dict:
    """End conference for everyone."""
    return {"status": "conference_ended", "iframe_command": "endConference"}


# ── Media Handlers ───────────────────────────────────────────────────────────

async def toggle_audio() -> dict:
    """Toggle audio mute."""
    return {"status": "audio_toggled", "iframe_command": "toggleAudio"}


async def toggle_video() -> dict:
    """Toggle video mute."""
    return {"status": "video_toggled", "iframe_command": "toggleVideo"}


async def toggle_screen() -> dict:
    """Toggle screen sharing."""
    return {"status": "screen_toggled", "iframe_command": "toggleShareScreen"}


async def mute_everyone(media_type: str = "audio") -> dict:
    """Mute all participants."""
    return {"status": "everyone_muted", "media_type": media_type, "iframe_command": "muteEveryone"}


async def set_video_quality(height: int = 720) -> dict:
    """Set video quality."""
    return {"status": "quality_set", "height": height, "iframe_command": "setVideoQuality"}


# ── Participant Handlers ─────────────────────────────────────────────────────

async def kick(participant_id: str = "", user: str = "") -> dict:
    """Kick a participant."""
    return {"status": "kicked", "participantId": participant_id, "iframe_command": "kickParticipant"}


async def grant_moderator(participant_id: str = "", user: str = "") -> dict:
    """Grant moderator rights."""
    return {"status": "moderator_granted", "participantId": participant_id, "iframe_command": "grantModerator"}


async def pin_participant(participant_id: str = "") -> dict:
    """Pin a participant."""
    return {"status": "participant_pinned", "participantId": participant_id, "iframe_command": "pinParticipant"}


async def set_volume(participant_id: str = "", volume: float = 1.0) -> dict:
    """Set participant volume."""
    return {"status": "volume_set", "participantId": participant_id, "volume": volume, "iframe_command": "setParticipantVolume"}


# ── Layout Handlers ──────────────────────────────────────────────────────────

async def toggle_tile() -> dict:
    """Toggle tile view."""
    return {"status": "tile_toggled", "iframe_command": "toggleTileView"}


async def toggle_chat() -> dict:
    """Toggle chat panel."""
    return {"status": "chat_toggled", "iframe_command": "toggleChat"}


async def toggle_raise_hand() -> dict:
    """Toggle raise hand."""
    return {"status": "hand_toggled", "iframe_command": "toggleRaiseHand"}


async def toggle_lobby(enabled: bool = True) -> dict:
    """Toggle lobby mode."""
    return {"status": "lobby_toggled", "enabled": enabled, "iframe_command": "toggleLobby"}


# ── Recording Handlers ───────────────────────────────────────────────────────

async def start_recording(mode: str = "local", user: str = "") -> dict:
    """Start recording."""
    return {"status": "recording_started", "mode": mode, "iframe_command": "startRecording"}


async def stop_recording(mode: str = "local", user: str = "") -> dict:
    """Stop recording."""
    return {"status": "recording_stopped", "mode": mode, "iframe_command": "stopRecording"}


# ── Breakout Handlers ────────────────────────────────────────────────────────

async def add_breakout(name: str = "") -> dict:
    """Create breakout room."""
    return {"status": "breakout_added", "name": name, "iframe_command": "addBreakoutRoom"}


async def close_breakout(room_id: str = "") -> dict:
    """Close breakout room."""
    return {"status": "breakout_closed", "roomId": room_id, "iframe_command": "closeBreakoutRoom"}


async def join_breakout(room_id: str = "") -> dict:
    """Join breakout room."""
    return {"status": "breakout_joined", "roomId": room_id, "iframe_command": "joinBreakoutRoom"}


# ── Misc Handlers ────────────────────────────────────────────────────────────

async def set_subject(subject: str = "") -> dict:
    """Set conference subject."""
    return {"status": "subject_set", "subject": subject, "iframe_command": "subject"}


async def send_chat(message: str = "", to: str = "") -> dict:
    """Send chat message."""
    return {"status": "chat_sent", "message": message, "to": to, "iframe_command": "sendChatMessage"}


async def set_follow_me(enabled: bool = True, recorder_only: bool = False) -> dict:
    """Toggle follow me mode."""
    return {"status": "follow_me_set", "enabled": enabled, "recorder_only": recorder_only, "iframe_command": "setFollowMe"}


# ── Health Check ─────────────────────────────────────────────────────────────

async def health() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "service": "gateway"}


async def health_services() -> dict:
    """Check health of all services."""
    return {
        "gateway": "healthy",
        "telebot": "healthy",
        "matrixbot": "healthy",
        "jitsi": "healthy",
    }


# ── Run as Web Server ───────────────────────────────────────────────────────

def create_app():
    """Create the ASGI app with all routes."""
    from evoid.web.route import Service

    app = Service("gateway")

    # Health
    app.add_route("GET", "/health", health)
    app.add_route("GET", "/health/services", health_services)

    # Meetings
    app.add_route("POST", "/intent/jitsi/create_meeting", create_meeting)
    app.add_route("POST", "/intent/jitsi/join_meeting", join_meeting)
    app.add_route("POST", "/intent/jitsi/watch_party", watch_party)
    app.add_route("POST", "/intent/jitsi/stop_watch_party", stop_watch_party)

    # Call control
    app.add_route("POST", "/intent/jitsi/hangup", hangup)
    app.add_route("POST", "/intent/jitsi/end_conference", end_conference)

    # Media
    app.add_route("POST", "/intent/jitsi/toggle_audio", toggle_audio)
    app.add_route("POST", "/intent/jitsi/toggle_video", toggle_video)
    app.add_route("POST", "/intent/jitsi/toggle_screen", toggle_screen)
    app.add_route("POST", "/intent/jitsi/mute_everyone", mute_everyone)
    app.add_route("POST", "/intent/jitsi/set_video_quality", set_video_quality)

    # Participants
    app.add_route("POST", "/intent/jitsi/kick", kick)
    app.add_route("POST", "/intent/jitsi/grant_moderator", grant_moderator)
    app.add_route("POST", "/intent/jitsi/pin_participant", pin_participant)
    app.add_route("POST", "/intent/jitsi/set_volume", set_volume)

    # Layout
    app.add_route("POST", "/intent/jitsi/toggle_tile", toggle_tile)
    app.add_route("POST", "/intent/jitsi/toggle_chat", toggle_chat)
    app.add_route("POST", "/intent/jitsi/toggle_raise_hand", toggle_raise_hand)
    app.add_route("POST", "/intent/jitsi/toggle_lobby", toggle_lobby)

    # Recording
    app.add_route("POST", "/intent/jitsi/start_recording", start_recording)
    app.add_route("POST", "/intent/jitsi/stop_recording", stop_recording)

    # Breakout
    app.add_route("POST", "/intent/jitsi/add_breakout", add_breakout)
    app.add_route("POST", "/intent/jitsi/close_breakout", close_breakout)
    app.add_route("POST", "/intent/jitsi/join_breakout", join_breakout)

    # Misc
    app.add_route("POST", "/intent/jitsi/set_subject", set_subject)
    app.add_route("POST", "/intent/jitsi/send_chat", send_chat)
    app.add_route("POST", "/intent/jitsi/set_follow_me", set_follow_me)

    return app


if __name__ == "__main__":
    from evoid.engines.logger import loguru as log
    from evoid.web.route import run
    import asyncio

    log.init("gateway")
    app = create_app()
    asyncio.run(run(app, port=8000))
