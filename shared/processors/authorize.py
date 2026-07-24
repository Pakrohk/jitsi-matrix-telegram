"""Authorize processor — Permission verification.

IOP: Pure function. Checks user authorization.
"""

from evoid.core import Context


async def authorize(ctx: Context) -> dict:
    """Authorize based on intent level.

    Returns:
        dict: {"authorized": True/False, "reason": str (optional)}
    """
    intent = ctx.intent

    # CRITICAL level requires admin
    if intent.level.value == "critical":
        user = intent.metadata.get("user", "")
        whitelist = intent.metadata.get("admin_whitelist", [])

        # Empty whitelist means everyone is authorized
        if whitelist and user not in whitelist:
            return {
                "authorized": False,
                "reason": f"{user} not authorized for critical operations",
            }

    return {"authorized": True}
