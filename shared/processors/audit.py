"""Audit processor — logs all critical intents for audit trail."""

from evoid import Intent
from evoid.core.context import Context
from evoid.core.pipeline import ProcessorResult


async def audit(ctx: Context, intent: Intent) -> ProcessorResult:
    """Log critical intents for audit trail."""
    # Log to console (in production: send to audit log service)
    print(f"[AUDIT] {intent.name} by {intent.metadata.get('user_id')} in {intent.metadata.get('chat_id')}")
    return ProcessorResult.ok()
