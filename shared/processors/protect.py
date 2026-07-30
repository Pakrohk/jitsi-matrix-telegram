"""Protection processor — rate limiting, spam protection for critical intents."""

from evoid import Intent
from evoid.core.context import Context
from evoid.core.pipeline import ProcessorResult
from collections import defaultdict
import time


# In-memory rate limiter (use Redis in production)
_rate_limits: dict[str, list[float]] = defaultdict(list)


async def protect(ctx: Context, intent: Intent) -> ProcessorResult:
    """Rate limit critical intents."""
    # Only rate limit critical intents
    if intent.level.name != "CRITICAL":
        return ProcessorResult.ok()

    user_id = intent.metadata.get("user_id")
    if not user_id:
        return ProcessorResult.ok()

    key = f"{intent.name}:{user_id}"
    now = time.time()
    window = ctx.deps.get("rate_limit_window", 60)  # seconds
    max_requests = ctx.deps.get("rate_limit_max", 10)

    # Clean old entries
    _rate_limits[key] = [t for t in _rate_limits[key] if now - t < window]

    if len(_rate_limits[key]) >= max_requests:
        return ProcessorResult.fail(f"Rate limit exceeded for {intent.name}")

    _rate_limits[key].append(now)
    return ProcessorResult.ok()