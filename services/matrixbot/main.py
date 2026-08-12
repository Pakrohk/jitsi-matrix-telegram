"""Matrix Bot Service — Maubot plugin for Matrix.

IOP: Adapter converts Matrix events to Intents.
Config lives in evoid.toml under [engines.*].
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from maubot import MessageEvent, Plugin
from maubot.handlers import event
from mautrix.types import EventType

try:
    from evoid import Intent, Level, publish
    from evoid.core.extend import add_intent_with_pipeline
    from evoid.native import create_service

    HAS_EVOID = True
except ImportError:
    HAS_EVOID = False

try:
    from evoid_sqlite import create_storage

    HAS_STORAGE = True
except ImportError:
    HAS_STORAGE = False

if TYPE_CHECKING:
    pass


class Config:
    """Configuration from evoid.toml."""

    def __init__(self, config_dict: dict):
        self._config = config_dict

    def get(self, key: str, default=None):
        parts = key.split(".")
        val = self._config
        for part in parts:
            if isinstance(val, dict):
                val = val.get(part)
            else:
                return default
            if val is None:
                return default
        return val


class JitsiBotPlugin(Plugin):
    """Maubot plugin for Jitsi management via EVOID.

    IOP: Intent carries data, not behavior.
    Pipeline: validate → authorize → audit → protect
    """

    config: Config
    _evoid_service = None
    _storage = None
    _command_prefix: str = "jitsi"
    _server_url: str = ""

    @classmethod
    def get_config_class(cls):
        return Config

    async def start(self) -> None:
        """Initialize plugin with config and EVOID service."""
        self.config = Config(self.config)

        # EVOID service
        service_name = self.config.get("service_name", "jitsi-matrix")
        self._server_url = self.config.get("jitsi.server_url", "https://meet.example.com")
        self._command_prefix = self.config.get("command_prefix", "jitsi")

        if HAS_EVOID:
            self._evoid_service = create_service(service_name)
            self._register_jitsi_intents()
            self.log.info(f"EVOID service '{service_name}' initialized")

        # Storage
        if HAS_STORAGE:
            db_path = self.config.get("storage.db_path", "jitsi-bot.db")
            self._storage = create_storage(db_path)
            await self._storage.connect()
            self.log.info(f"SQLite storage connected: {db_path}")

        self.log.info(f"Jitsi Bot started: {self._server_url}")

    async def stop(self) -> None:
        """Cleanup on plugin stop."""
        self.log.info("Stopping Jitsi Bot plugin...")
        if self._storage and hasattr(self._storage, "close"):
            await self._storage.close()
        self._evoid_service = None
        self._storage = None

    def _register_jitsi_intents(self) -> None:
        """Register Jitsi command intents with EVOID.

        IOP: Intent carries data, not behavior.
        Level determines pipeline (STANDARD or CRITICAL).
        """
        if not self._evoid_service or not HAS_EVOID:
            return

        # Standard intents (validate → authorize → handler)
        standard_intents = [
            "create_meeting", "join_meeting", "watch_party", "stop_watch_party",
            "toggle_audio", "toggle_video", "toggle_screen",
            "set_video_quality", "set_subject",
            "toggle_tile", "toggle_chat", "toggle_raise_hand",
        ]

        for intent_name in standard_intents:
            intent = Intent(
                name=f"jitsi:{intent_name}",
                level=Level.STANDARD,
            )
            add_intent_with_pipeline(
                intent,
                processors=["validate", "authorize", self._make_handler(intent_name)],
            )

        # Critical intents (validate → authorize → audit → protect → handler)
        critical_intents = [
            "kick_participant", "grant_moderator",
            "start_recording", "stop_recording",
            "end_conference", "toggle_lobby",
        ]

        for intent_name in critical_intents:
            intent = Intent(
                name=f"jitsi:{intent_name}",
                level=Level.CRITICAL,
            )
            add_intent_with_pipeline(
                intent,
                processors=["validate", "authorize", "audit", "protect", self._make_handler(intent_name)],
            )

    def _make_handler(self, intent_name: str):
        """Create EVOID handler for a Jitsi command.

        IOP: Handler is a pure function.
        It receives Intent (data) and returns result (data).
        """
        async def handler(intent: Intent) -> dict:
            return {
                "status": "executed",
                "intent": intent_name,
                "args": intent.metadata.get("args", {}),
                "iframe_command": intent.metadata.get("iframe_command", ""),
                "room_id": intent.metadata.get("room_id", ""),
            }
        return handler

    # ── Matrix Event Handlers ──────────────────────────────────────────────

    @event.on(EventType.ROOM_MESSAGE)
    async def on_message(self, event: MessageEvent) -> None:
        """Convert Matrix messages to EVOID intents.

        IOP: Adapter converts external events to Intents.
        """
        if event.sender == self.client.mxid:
            return

        text = event.body or ""
        if not text.startswith("!"):
            return

        parts = text[len("!"):].split()
        command_name = parts[0] if parts else ""

        if command_name == self._command_prefix:
            await self._handle_command(event, parts[1:])

    async def _handle_command(self, event: MessageEvent, args: list[str]) -> None:
        """Route commands to EVOID intents.

        IOP: Commands become Intents, Intents flow through pipeline.
        """
        if not args:
            await event.reply(self._help_text())
            return

        subcommand = args[0].lower()

        if subcommand == "help":
            await event.reply(self._help_text())
            return

        # Map commands to intents
        command_map = {
            "create": ("jitsi:create_meeting", Level.STANDARD),
            "join": ("jitsi:join_meeting", Level.STANDARD),
            "watch": ("jitsi:watch_party", Level.STANDARD),
            "stopwatch": ("jitsi:stop_watch_party", Level.STANDARD),
            "mute": ("jitsi:toggle_audio", Level.STANDARD),
            "video": ("jitsi:toggle_video", Level.STANDARD),
            "screen": ("jitsi:toggle_screen", Level.STANDARD),
            "kick": ("jitsi:kick_participant", Level.CRITICAL),
            "mod": ("jitsi:grant_moderator", Level.CRITICAL),
            "record": ("jitsi:start_recording", Level.CRITICAL),
            "stoprecord": ("jitsi:stop_recording", Level.CRITICAL),
        }

        if subcommand not in command_map:
            await event.reply(f"Unknown command: {subcommand}\n\n{self._help_text()}")
            return

        intent_name, level = command_map[subcommand]

        # Check moderator permission for critical intents
        if level == Level.CRITICAL and not self._is_moderator(event.sender):
            await event.reply(f"Command '{subcommand}' requires moderator privileges")
            return

        # Create Intent (pure data)
        if not HAS_EVOID:
            await event.reply("EVOID runtime not available")
            return

        intent = Intent(
            name=intent_name,
            level=level,
            metadata={
                "command": subcommand,
                "args": {"value": " ".join(args[1:]) if len(args) > 1 else ""},
                "user": event.sender,
                "room_id": event.room_id,
                "server_url": self._server_url,
                "iframe_command": self._get_iframe_command(subcommand),
            },
        )

        # Publish Intent (EVOID handles pipeline)
        result = await publish(intent, source="maubot")
        if result:
            response = self._format_response(subcommand, result[0], args)
            await self._persist_data(subcommand, args, event, result[0])
            await event.reply(response)
        else:
            await event.reply(f"Failed to execute: {subcommand}")

    def _get_iframe_command(self, command: str) -> str:
        """Map command to Jitsi iframe command."""
        iframe_map = {
            "create": "createMeeting",
            "join": "joinMeeting",
            "watch": "startShareVideo",
            "stopwatch": "stopShareVideo",
            "mute": "toggleAudio",
            "video": "toggleVideo",
            "screen": "toggleShareScreen",
            "kick": "kickParticipant",
            "mod": "grantModerator",
            "record": "startRecording",
            "stoprecord": "stopRecording",
        }
        return iframe_map.get(command, command)

    def _format_response(self, command: str, result: dict, args: list[str]) -> str:
        """Format EVOID result for Matrix response."""
        status = result.get("status", "executed")

        if command == "create":
            room_name = args[0] if args else "Meeting"
            room_id = room_name.lower().replace(" ", "-")
            url = f"{self._server_url}/{room_id}"
            return f"Meeting created: {url}"

        elif command == "join":
            if not args:
                return "Usage: !jitsi join <room_name>"
            room_id = args[0].lower().replace(" ", "-")
            url = f"{self._server_url}/{room_id}"
            return f"Join: {url}"

        elif command == "watch":
            if not args:
                return "Usage: !jitsi watch <url> [name]"
            room_name = args[1] if len(args) > 1 else "Watch Party"
            room_id = room_name.lower().replace(" ", "-")
            url = f"{self._server_url}/{room_id}"
            return f"Watch party: {url}\nVideo: {args[0]}"

        elif command == "kick":
            return f"Kicked: {args[0]}" if args else "Kicked participant"

        elif command == "mod":
            return f"Moderator granted: {args[0]}" if args else "Granted moderator"

        elif command == "record":
            mode = args[0] if args else "local"
            return f"Recording started ({mode})"

        elif command == "stoprecord":
            mode = args[0] if args else "local"
            return f"Recording stopped ({mode})"

        return f"{command}: {status}"

    async def _persist_data(self, command: str, args: list[str], event: MessageEvent, result: dict) -> None:
        """Persist meeting data to storage."""
        if not HAS_STORAGE or not self._storage:
            return

        if command == "create":
            room_name = args[0] if args else "meeting"
            meeting_url = result.get("meeting_url", "")
            await self._storage.write(
                f"meeting:{event.room_id}",
                {
                    "room_id": event.room_id,
                    "room_name": room_name,
                    "creator": event.sender,
                    "url": meeting_url,
                },
                namespace="meetings",
            )
        elif command == "watch":
            video_url = args[0] if args else ""
            room_name = args[1] if len(args) > 1 else "watch-party"
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

    # ── Helpers ────────────────────────────────────────────────────────────

    def _is_moderator(self, user_id: str) -> bool:
        """Check if user is allowed to run moderator commands."""
        whitelist = self.config.get("admin.whitelist", [])
        if not whitelist:
            return True
        return user_id in whitelist

    def _help_text(self) -> str:
        """Return help text grouped by category."""
        return """Jitsi Commands:

Room:
  !jitsi create [name] — Create meeting
  !jitsi join <room> — Join meeting
  !jitsi hangup — End call

Watch Party:
  !jitsi watch <url> [name] — Watch together
  !jitsi stopwatch — Stop shared video

Media:
  !jitsi mute — Toggle audio
  !jitsi video — Toggle video
  !jitsi screen — Toggle screen share

Moderation (mod only):
  !jitsi kick <id> — Kick participant
  !jitsi mod <id> — Grant moderator
  !jitsi record <mode> — Start recording
  !jitsi stoprecord <mode> — Stop recording"""


# Maubot entry point
def setup():
    return JitsiBotPlugin
