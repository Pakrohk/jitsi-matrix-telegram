"""Validation processor — validates incoming Intent metadata."""

from evoid import Intent
from evoid.core.context import Context
from evoid.core.pipeline import ProcessorResult


async def validate(ctx: Context, intent: Intent) -> ProcessorResult:
    """Validate required metadata fields for Jitsi intents."""
    metadata = intent.metadata

    # Required fields for most jitsi commands
    if intent.name.startswith("jitsi:") and not intent.name.startswith("jitsi:health"):
        required = ["user_id", "chat_id"]
        missing = [f for f in required if metadata.get(f) is None]

        if missing:
            return ProcessorResult.fail(f"Missing required fields: {missing}")

    return ProcessorResult.ok()