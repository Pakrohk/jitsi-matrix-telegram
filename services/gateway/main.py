"""Gateway — entry point for all external requests.

Routes Intents via message bus. NOT HTTP routes.
Customize: add routes, middleware, auth checks here.
"""

from __future__ import annotations

from evoid import Intent, Level, publish
from evoid.web.route import Service, get, post, run
from evoid.engines.logger import loguru as log

from shared.processors import validate, authorize, audit, protect


# Create the service app
app = Service("gateway")


# ── Health Endpoints ──────────────────────────────────────────────────────────

@get("/health")
async def health() -> dict:
    return {"status": "healthy", "service": "gateway"}


@get("/")
async def index() -> dict:
    return {"service": "gateway", "status": "running", "intent_bus": "active"}


# ── Intent Execution Endpoints ────────────────────────────────────────────────
# These endpoints publish intents to the message bus.
# The actual handlers are registered in each service.

@post("/intent/jitsi/create_meeting")
async def create_meeting_endpoint(body: dict) -> dict:
    intent = Intent(
        name="jitsi:create_meeting",
        level=Level.STANDARD,
        metadata=body,
    )
    result = await publish(intent, source="gateway")
    return result[0] if result else {"error": "No handler"}


@post("/intent/jitsi/join_meeting")
async def join_meeting_endpoint(body: dict) -> dict:
    intent = Intent(
        name="jitsi:join_meeting",
        level=Level.STANDARD,
        metadata=body,
    )
    result = await publish(intent, source="gateway")
    return result[0] if result else {"error": "No handler"}


@post("/intent/jitsi/watch_party")
async def watch_party_endpoint(body: dict) -> dict:
    intent = Intent(
        name="jitsi:watch_party",
        level=Level.STANDARD,
        metadata=body,
    )
    result = await publish(intent, source="gateway")
    return result[0] if result else {"error": "No handler"}


@post("/intent/jitsi/stop_watch_party")
async def stop_watch_party_endpoint(body: dict) -> dict:
    intent = Intent(
        name="jitsi:stop_watch_party",
        level=Level.STANDARD,
        metadata=body,
    )
    result = await publish(intent, source="gateway")
    return result[0] if result else {"error": "No handler"}


@post("/intent/jitsi/hangup")
async def hangup_endpoint(body: dict) -> dict:
    intent = Intent(
        name="jitsi:hangup",
        level=Level.CRITICAL,
        metadata=body,
    )
    result = await publish(intent, source="gateway")
    return result[0] if result else {"error": "No handler"}


@post("/intent/jitsi/toggle_audio")
async def toggle_audio_endpoint(body: dict) -> dict:
    intent = Intent(
        name="jitsi:toggle_audio",
        level=Level.STANDARD,
        metadata=body,
    )
    result = await publish(intent, source="gateway")
    return result[0] if result else {"error": "No handler"}


@post("/intent/jitsi/toggle_video")
async def toggle_video_endpoint(body: dict) -> dict:
    intent = Intent(
        name="jitsi:toggle_video",
        level=Level.STANDARD,
        metadata=body,
    )
    result = await publish(intent, source="gateway")
    return result[0] if result else {"error": "No handler"}


@post("/intent/jitsi/toggle_screen")
async def toggle_screen_endpoint(body: dict) -> dict:
    intent = Intent(
        name="jitsi:toggle_screen",
        level=Level.STANDARD,
        metadata=body,
    )
    result = await publish(intent, source="gateway")
    return result[0] if result else {"error": "No handler"}


@post("/intent/jitsi/kick")
async def kick_endpoint(body: dict) -> dict:
    intent = Intent(
        name="jitsi:kick",
        level=Level.CRITICAL,
        metadata=body,
    )
    result = await publish(intent, source="gateway")
    return result[0] if result else {"error": "No handler"}


@post("/intent/jitsi/grant_moderator")
async def grant_moderator_endpoint(body: dict) -> dict:
    intent = Intent(
        name="jitsi:grant_moderator",
        level=Level.CRITICAL,
        metadata=body,
    )
    result = await publish(intent, source="gateway")
    return result[0] if result else {"error": "No handler"}


@post("/intent/jitsi/start_recording")
async def start_recording_endpoint(body: dict) -> dict:
    intent = Intent(
        name="jitsi:start_recording",
        level=Level.CRITICAL,
        metadata=body,
    )
    result = await publish(intent, source="gateway")
    return result[0] if result else {"error": "No handler"}


@post("/intent/jitsi/stop_recording")
async def stop_recording_endpoint(body: dict) -> dict:
    intent = Intent(
        name="jitsi:stop_recording",
        level=Level.CRITICAL,
        metadata=body,
    )
    result = await publish(intent, source="gateway")
    return result[0] if result else {"error": "No handler"}


# ── AsyncAPI Docs ─────────────────────────────────────────────────────────────

@get("/docs")
async def docs() -> str:
    """AsyncAPI documentation as Markdown."""
    from evoid.adapters.asyncapi import generate_asyncapi_markdown
    return generate_asyncapi_markdown(title="Jitsi Gateway API", version="0.1.0")


@get("/docs/json")
async def docs_json() -> dict:
    """AsyncAPI spec as JSON."""
    from evoid.adapters.asyncapi import generate_asyncapi
    return generate_asyncapi(
        title="Jitsi Gateway API",
        version="0.1.0",
        description="Intent-based API for Jitsi meeting management",
    )


# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    log.init("gateway", level="INFO")
    run(app, port=8000)