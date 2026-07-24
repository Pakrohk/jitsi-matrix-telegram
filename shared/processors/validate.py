"""Validate processor — Input validation.

IOP: Pure function. Validates intent metadata.
"""

from evoid.core import Context


async def validate(ctx: Context) -> dict:
    """Validate intent metadata.

    Returns:
        dict: {"validated": True/False, "error": str (optional)}
    """
    intent = ctx.intent

    # Check intent name exists
    if not intent.name:
        return {"validated": False, "error": "Intent name required"}

    # Jitsi-specific validation
    if intent.name.startswith("jitsi:"):
        server_url = intent.metadata.get("server_url")

        # Meeting creation requires server_url
        if intent.name in ("jitsi:create_meeting", "jitsi:join_meeting", "jitsi:watch_party"):
            if not server_url:
                return {"validated": False, "error": "server_url required"}

        # Watch party requires video_url
        if intent.name == "jitsi:watch_party":
            video_url = intent.metadata.get("video_url")
            if not video_url:
                return {"validated": False, "error": "video_url required"}

        # Kick/Mod requires participant_id
        if intent.name in ("jitsi:kick", "jitsi:grant_moderator"):
            participant_id = intent.metadata.get("participant_id")
            if not participant_id:
                return {"validated": False, "error": "participant_id required"}

    return {"validated": True}
