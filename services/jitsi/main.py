"""Jitsi Service — Shared Jitsi functionality for all platforms.

Handles meeting creation, watch parties, recording commands.
"""

from evoid.web.route import Service, get, post, run
from evoid.engines.logger import loguru as log

from shared import Meeting, WatchParty, detect_content_type


app = Service("jitsi")

# In-memory storage (use SQLite in production)
_meetings: dict[str, Meeting] = {}
_watch_parties: dict[str, WatchParty] = {}


# ── Meeting Endpoints ───────────────────────────────────────────────────────

@app.post("/meetings")
async def create_meeting(room_name: str = "meeting", creator: str = "", server_url: str = "") -> dict:
    room_id = room_name.lower().replace(" ", "-").replace("_", "-")
    meeting_url = f"{server_url}/{room_id}"

    meeting = Meeting(room_id=room_id, room_name=room_name, creator=creator, url=meeting_url)
    _meetings[room_id] = meeting

    return {"status": "created", "meeting_url": meeting_url, "room_id": room_id}


@app.get("/meetings/{room_id}")
async def get_meeting(room_id: str) -> dict:
    meeting = _meetings.get(room_id)
    if not meeting:
        return {"error": "Meeting not found"}
    return {"room_id": meeting.room_id, "room_name": meeting.room_name, "url": meeting.url}


@app.get("/meetings")
async def list_meetings() -> dict:
    return {"meetings": [{"room_id": m.room_id, "room_name": m.room_name} for m in _meetings.values()]}


# ── Watch Party Endpoints ───────────────────────────────────────────────────

@app.post("/watch-parties")
async def create_watch_party(video_url: str = "", room_name: str = "watch-party", creator: str = "", server_url: str = "") -> dict:
    room_id = room_name.lower().replace(" ", "-").replace("_", "-")
    meeting_url = f"{server_url}/{room_id}"
    content_type = detect_content_type(video_url)

    party = WatchParty(room_id=room_id, room_name=room_name, video_url=video_url, content_type=content_type, creator=creator)
    _watch_parties[room_id] = party

    return {"status": "created", "meeting_url": meeting_url, "content_type": content_type}


@app.get("/watch-parties")
async def list_watch_parties() -> dict:
    return {"parties": [{"room_id": p.room_id, "video_url": p.video_url} for p in _watch_parties.values()]}


# ── Health ──────────────────────────────────────────────────────────────────

@app.get("/health")
async def health() -> dict:
    return {"status": "healthy", "service": "jitsi"}


if __name__ == "__main__":
    log.init("jitsi")
    import asyncio
    asyncio.run(run(app, port=8003))
