"""Maubot plugin configuration.

IOP: Config is data. Loader is a pure function.

Prerequisites:
- Matrix homeserver URL
- Bot user ID
- Bot password or access token
- Jitsi server URL
- EVOID service name
"""

from typing import Type

from mautrix.util.config import BaseProxyConfig, ConfigUpdateHelper


class Config(BaseProxyConfig):
    """Configuration for Jitsi Bot maubot plugin."""

    def do_update(self, helper: ConfigUpdateHelper) -> None:
        # EVOID service config
        helper.copy("service_name")
        helper.copy("command_prefix")
        helper.copy("max_message_length")

        # Matrix prerequisites
        helper.copy("matrix.homeserver")
        helper.copy("matrix.user")
        helper.copy("matrix.password")
        helper.copy("matrix.access_token")
        helper.copy("matrix.device_id")
        helper.copy("matrix.encryption")

        # Jitsi settings
        helper.copy("jitsi.server_url")
        helper.copy("jitsi.muc_domain")
        helper.copy("jitsi.prosody_modules")
        helper.copy("jitsi.admin_username")
        helper.copy("jitsi.admin_password")

        # Storage settings
        helper.copy("storage.db_path")

        # Admin settings
        helper.copy("admin.whitelist")
        helper.copy("admin.require_auth")

        # Rate limiting
        helper.copy("rate_limit.enabled")
        helper.copy("rate_limit.max_commands")
        helper.copy("rate_limit.window_seconds")

    @classmethod
    def get_config_class(cls) -> Type[BaseProxyConfig]:
        return cls
