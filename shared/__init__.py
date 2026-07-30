"""Shared models and utilities — frozen dataclasses for immutability."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class Meeting:
    """A Jitsi meeting room — immutable."""

    room_id: str
    room_name: str
    creator: str
    url: str
    created_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    participants: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WatchParty:
    """A Jitsi watch party with shared video — immutable."""

    room_id: str
    room_name: str
    video_url: str
    content_type: str
    creator: str
    created_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class UserPreference:
    """User preference stored in database — immutable."""

    user_id: str
    key: str
    value: Any
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass(frozen=True)
class ModeratorAction:
    """Log of moderator actions — immutable."""

    room_id: str
    action: str
    target_user: str
    performed_by: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


def detect_content_type(url: str) -> str:
    """Detect media content type from URL."""
    url_lower = url.lower()
    if "youtube.com" in url_lower or "youtu.be" in url_lower:
        return "youtube"
    if "twitch.tv" in url_lower:
        return "twitch"
    if "vimeo.com" in url_lower:
        return "vimeo"
    if any(ext in url_lower for ext in [".mp3", ".wav", ".ogg"]):
        return "audio"
    if any(ext in url_lower for ext in [".mp4", ".webm", ".mkv", ".avi", ".mov"]):
        return "video"
    return "unknown"