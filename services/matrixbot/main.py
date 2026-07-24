"""Matrix Bot Service — Maubot plugin for Matrix.

Converts !jitsi commands to EVOID intents.
Runs as a maubot plugin.
"""

from __future__ import annotations

import os
from typing import Any

from maubot import Plugin, MessageEvent
from maubot.handlers import event
from mautrix.types import EventType

from shared import detect_content_type


class JitsiBotPlugin(Plugin):
    """Maubot plugin for Jitsi management."""

    _server_url: str = ""

    async def start(self) -> None:
        self._server_url = os.environ.get("JITSI_SERVER_URL", "https://meet.example.com")
        self.log.info("Jitsi Bot plugin started")

    @event.on(EventType.ROOM_MESSAGE)
    async def on_message(self, event: MessageEvent) -> None:
        if event.sender == self.client.mxid:
            return

        text = event.body or ""
        if not text.startswith("!"):
            return

        parts = text[1:].split()
        if parts[0] != "jitsi":
            return

        await self._handle_command(event, parts[1:])

    async def _handle_command(self, event: MessageEvent, args: list[str]) -> None:
        if not args:
            await event.reply(self._help())
            return

        cmd = args[0].lower()
        handlers = {
            "create": self._cmd_create,
            "join": self._cmd_join,
            "watch": self._cmd_watch,
            "mute": lambda e, a: "Audio toggled",
            "video": lambda e, a: "Video toggled",
            "hangup": lambda e, a: "Call ended",
        }

        handler = handlers.get(cmd)
        if handler:
            result = handler(event, args[1:])
            if hasattr(result, "__await__"):
                result = await result
            await event.reply(result)
        else:
            await event.reply(f"Unknown command: {cmd}\n\n{self._help()}")

    def _cmd_create(self, event: MessageEvent, args: list[str]) -> str:
        room_name = args[0] if args else "Meeting"
        room_id = room_name.lower().replace(" ", "-")
        return f"Meeting created: {self._server_url}/{room_id}"

    def _cmd_join(self, event: MessageEvent, args: list[str]) -> str:
        if not args:
            return "Usage: !jitsi join <room>"
        room_id = args[0].lower().replace(" ", "-")
        return f"Join: {self._server_url}/{room_id}"

    def _cmd_watch(self, event: MessageEvent, args: list[str]) -> str:
        if not args:
            return "Usage: !jitsi watch <url> [name]"
        content_type = detect_content_type(args[0])
        return f"Watch party ({content_type}): {args[0]}"

    def _help(self) -> str:
        return """Jitsi Commands:
!jitsi create [name] - Create meeting
!jitsi join <room> - Join meeting
!jitsi watch <url> [name] - Watch party
!jitsi mute - Toggle audio
!jitsi video - Toggle video
!jitsi hangup - End call"""
