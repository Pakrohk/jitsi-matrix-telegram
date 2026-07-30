"""Authorization processor — checks admin permissions for critical intents."""

from evoid import Intent
from evoid.core.context import Context
from evoid.core.pipeline import ProcessorResult


ADMIN_INTENTS = {
    "jitsi:kick",
    "jitsi:grant_moderator",
    "jitsi:end_conference",
    "jitsi:start_recording",
    "jitsi:stop_recording",
    "jitsi:toggle_lobby",
}


async def authorize(ctx: Context, intent: Intent) -> ProcessorResult:
    """Check if user is authorized for admin intents."""
    if intent.name not in ADMIN_INTENTS:
        return ProcessorResult.ok()

    # Check whitelist from service config
    whitelist = ctx.deps.get("admin_whitelist", [])
    user_id = intent.metadata.get("user_id")

    if whitelist and str(user_id) not in map(str, whitelist):
        return ProcessorResult.fail(f"User {user_id} not authorized for {intent.name}")

    return ProcessorResult.ok()