"""Pipeline processors for all services.

IOP: Processors are pure functions.
They validate, authorize, audit, and protect intents.
"""

from .validate import validate
from .authorize import authorize
from .audit import audit
from .protect import protect

__all__ = ["validate", "authorize", "audit", "protect"]
