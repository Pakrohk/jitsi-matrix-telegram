"""Gateway Service — Routes Intents between services.

Services don't call each other directly.
They send Intents to the gateway, and the gateway routes them.
"""

from evoid import Intent, Level, register_processor
from evoid.web.route import Service, get, run
from evoid.engines.logger import loguru as log

from shared import detect_content_type


app = Service("gateway")


# ── Processors ──────────────────────────────────────────────────────────────

async def validate(ctx):
    """Validate intent metadata."""
    intent = ctx.intent
    if not intent.name:
        return {"validated": False, "error": "Intent name required"}

    # Jitsi-specific validation
    if intent.name.startswith("jitsi:"):
        server_url = ctx.intent.metadata.get("server_url")
        if intent.name in ("jitsi:create_meeting", "jitsi:join_meeting", "jitsi:watch_party"):
            if not server_url:
                return {"validated": False, "error": "server_url required"}

    return {"validated": True}


async def authorize(ctx):
    """Authorize based on level."""
    intent = ctx.intent
    if intent.level.value == "critical":
        user = intent.metadata.get("user", "")
        whitelist = intent.metadata.get("admin_whitelist", [])
        if whitelist and user not in whitelist:
            return {"authorized": False, "reason": f"{user} not authorized"}
    return {"authorized": True}


async def audit(ctx):
    """Audit log for critical operations."""
    return {"audited": True}


async def protect(ctx):
    """Protection layer."""
    return {"protected": True}


register_processor("validate", validate)
register_processor("authorize", authorize)
register_processor("audit", audit)
register_processor("protect", protect)


# ── Health Check ────────────────────────────────────────────────────────────

@app.get("/health")
async def health() -> dict:
    return {"status": "healthy", "service": "gateway"}


# ── Jitsi Intent Handlers ───────────────────────────────────────────────────

@app.post("/intent/jitsi/create_meeting")
async def create_meeting(room_name: str = "meeting", creator: str = "", server_url: str = "") -> dict:
    room_id = room_name.lower().replace(" ", "-").replace("_", "-")
    meeting_url = f"{server_url}/{room_id}"
    return {"status": "created", "meeting_url": meeting_url, "room_id": room_id}


@app.post("/intent/jitsi/join_meeting")
async def join_meeting(room_name: str = "", server_url: str = "") -> dict:
    room_id = room_name.lower().replace(" ", "-").replace("_", "-")
    meeting_url = f"{server_url}/{room_id}"
    return {"status": "joined", "meeting_url": meeting_url}


@app.post("/intent/jitsi/watch_party")
async def watch_party(video_url: str = "", room_name: str = "watch-party", creator: str = "", server_url: str = "") -> dict:
    room_id = room_name.lower().replace(" ", "-").replace("_", "-")
    meeting_url = f"{server_url}/{room_id}"
    content_type = detect_content_type(video_url)
    return {"status": "watch_party_created", "meeting_url": meeting_url, "content_type": content_type}


@app.post("/intent/jitsi/hangup")
async def hangup() -> dict:
    return {"status": "hung_up", "iframe_command": "hangup"}


@app.post("/intent/jitsi/toggle_audio")
async def toggle_audio() -> dict:
    return {"status": "audio_toggled", "iframe_command": "toggleAudio"}


@app.post("/intent/jitsi/toggle_video")
async def toggle_video() -> dict:
    return {"status": "video_toggled", "iframe_command": "toggleVideo"}


@app.post("/intent/jitsi/kick")
async def kick(participant_id: str = "", user: str = "") -> dict:
    return {"status": "kicked", "participantId": participant_id, "iframe_command": "kickParticipant"}


@app.post("/intent/jitsi/grant_moderator")
async def grant_moderator(participant_id: str = "", user: str = "") -> dict:
    return {"status": "moderator_granted", "participantId": participant_id, "iframe_command": "grantModerator"}


@app.post("/intent/jitsi/start_recording")
async def start_recording(mode: str = "local", user: str = "") -> dict:
    return {"status": "recording_started", "mode": mode, "iframe_command": "startRecording"}


@app.post("/intent/jitsi/stop_recording")
async def stop_recording(mode: str = "local", user: str = "") -> dict:
    return {"status": "recording_stopped", "mode": mode, "iframe_command": "stopRecording"}


if __name__ == "__main__":
    log.init("gateway")
    import asyncio
    asyncio.run(run(app, port=8000))
