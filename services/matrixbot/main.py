"""Matrix Bot Service — Maubot plugin for Jitsi management.

Inherits from EvoidMaubot framework. Jitsi-specific commands and intents
registered here. Uses evoid-sqlite for persistence.

Usage:
    1. Install: pip install evoid-maubot evoid-jitsi-maubot
    2. Configure Jitsi server details in plugin config
    3. Upload .mbp to maubot management interface
    4. Create instance with your Matrix client
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from evoid_maubot import EvoidMaubot

try:
    from evoid import Intent, Level
    from evoid.native import on as evoid_on

    HAS_EVOID = True
except ImportError:
    HAS_EVOID = False

try:
    from evoid_smart_storage import SmartStorage
    from evoid_sqlite import create_storage

    HAS_STORAGE = True
except ImportError:
    HAS_STORAGE = False

if TYPE_CHECKING:
    from mautrix.util.config import BaseProxyConfig

from .commands import COMMAND_REGISTRY, CommandDef
from .config import Config


class JitsiMaubot(EvoidMaubot):
    """Maubot plugin for Jitsi Meet management via EVOID pipeline."""

    config: BaseProxyConfig
    _evoid_service: Any = None
    _storage: Any = None
    _smart_storage: Any = None

    @classmethod
    def get_config_class(cls) -> type[BaseProxyConfig]:
        return Config

    def _command_prefix(self) -> str:
        return self.config.get("command_prefix", "jitsi")

    def _intent_prefix(self) -> str:
        return "jitsi"

    def _register_intents(self) -> None:
        """Register all Jitsi command intents with EVOID."""
        if not self._evoid_service or not HAS_EVOID:
            return

        for cmd_name, cmd_def in COMMAND_REGISTRY.items():
            intent = Intent(
                name=f"jitsi:{cmd_name}",
                level=Level.CRITICAL if cmd_def.requires_moderator else Level.STANDARD,
            )
            evoid_on(self._evoid_service, intent, self._make_handler(cmd_name))

    def _make_intent(self, subcommand: str, cmd_def: CommandDef, args: dict, event: Any) -> Intent:
        """Build Intent with Jitsi-specific metadata."""
        intent = super()._make_intent(subcommand, cmd_def, args, event)
        intent.metadata["iframe_command"] = cmd_def.iframe_command
        intent.metadata["server_url"] = self.config.get("jitsi.server_url", "")
        intent.metadata["muc_domain"] = self.config.get("jitsi.muc_domain", "")
        return intent

    async def _on_result(self, command: str, args: dict, event: Any, result: dict) -> None:
        """Persist meeting data for create/watch/mod commands."""
        await self._persist_data(command, args, event, result)

    async def _persist_data(self, command: str, args: dict, event: Any, result: dict) -> None:
        """Persist meeting data to storage."""
        if not HAS_STORAGE or not self._storage:
            return

        if command == "create":
            room_name = args.get("value", "meeting")
            meeting_url = result.get("meeting_url", "")
            await self._storage.write(
                f"meeting:{event.room_id}",
                {
                    "room_id": event.room_id,
                    "room_name": room_name,
                    "creator": event.sender,
                    "url": meeting_url,
                    "created_at": str(event.server_timestamp),
                },
                namespace="meetings",
            )
        elif command == "watch":
            video_url = args.get("url", "")
            room_name = args.get("name", "watch-party")
            await self._storage.write(
                f"watch:{event.room_id}",
                {
                    "room_id": event.room_id,
                    "room_name": room_name,
                    "video_url": video_url,
                    "creator": event.sender,
                },
                namespace="watch_parties",
            )
        elif command == "mod":
            target = args.get("value", "")
            await self._storage.write(
                f"mod:{event.room_id}:{target}",
                {
                    "room_id": event.room_id,
                    "user": target,
                    "granted_by": event.sender,
                },
                namespace="moderators",
            )


def register_plugin() -> type:
    """Entry point for EVOID plugin system."""
    return JitsiMaubot