"""Config handler for Jitsi Maubot plugin."""

from __future__ import annotations

from typing import Any

from evoid_maubot.config import Config as BaseConfig
from mautrix.util.config import ConfigUpdateHelper


class Config(BaseConfig):
    """Configuration for Jitsi Maubot plugin."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.update(
            {
                "service_name": "jitsi-matrix",
                "command_prefix": "jitsi",
                "jitsi": {
                    "server_url": "",
                    "muc_domain": "",
                    "admin_username": "",
                    "admin_password": "",
                },
                "storage": {
                    "db_path": "jitsi-bot.db",
                    "enable_smart_routing": True,
                    "smart_mapping": {
                        "meeting": "storage.sqlite",
                        "user_preference": "storage.sqlite",
                        "watch_party": "storage.sqlite",
                        "moderator_log": "storage.sqlite",
                    },
                    "smart_schemas": {
                        "meeting": ["room_id", "room_name", "creator", "created_at", "url"],
                        "user_preference": ["user_id", "key", "value"],
                        "watch_party": ["room_id", "video_url", "content_type", "creator"],
                    },
                },
                "admin_whitelist": [],
            }
        )

    def do_update(self, helper: ConfigUpdateHelper) -> None:
        """Required by BaseProxyConfig."""
        super().do_update(helper)
        helper.copy("jitsi")
