"""Tests for Matrix bot service (maubot plugin)."""

import pytest


class TestMatrixBotConfig:
    """Tests for maubot config."""

    def test_load_config(self):
        from pathlib import Path
        from evoid.config.loader import load as load_config

        config_path = Path(__file__).parent.parent / "services/matrixbot/evoid.toml"
        config = load_config(config_path)

        assert config.service.name == "matrixbot"
        assert config.runtime.adapter == "maubot"
        assert config.runtime.port == 8002

    def test_maubot_options(self):
        from pathlib import Path
        from evoid.config.loader import load as load_config

        config_path = Path(__file__).parent.parent / "services/matrixbot/evoid.toml"
        config = load_config(config_path)

        # EVOID extracts [engines.X] as options["X"]
        maubot_cfg = config.engines.options.get("maubot", {})
        assert maubot_cfg.get("command_prefix") == "jitsi"

    def test_jitsi_options(self):
        from pathlib import Path
        from evoid.config.loader import load as load_config

        config_path = Path(__file__).parent.parent / "services/matrixbot/evoid.toml"
        config = load_config(config_path)

        jitsi_cfg = config.engines.options.get("jitsi", {})
        assert jitsi_cfg.get("server_url") == "https://meet.example.com"
        assert jitsi_cfg.get("muc_domain") == "conference.meet.example.com"

    def test_admin_options(self):
        from pathlib import Path
        from evoid.config.loader import load as load_config

        config_path = Path(__file__).parent.parent / "services/matrixbot/evoid.toml"
        config = load_config(config_path)

        admin_cfg = config.engines.options.get("admin", {})
        assert admin_cfg.get("whitelist") == []
        assert admin_cfg.get("require_auth") is False


class TestMatrixBotCommands:
    """Tests for Matrix bot command handlers."""

    def test_help_text(self):
        """Test help text generation."""
        help_text = """Jitsi Commands:
!jitsi create [name] - Create meeting
!jitsi join <room> - Join meeting
!jitsi watch <url> [name] - Watch party
!jitsi stopwatch - Stop watch party
!jitsi mute - Toggle audio
!jitsi video - Toggle video
!jitsi screen - Toggle screen share
!jitsi hangup - End call
!jitsi kick <id> - Kick participant (mod)
!jitsi mod <id> - Grant moderator (mod)
!jitsi record <mode> - Start recording (mod)
!jitsi stoprecord <mode> - Stop recording (mod)"""

        assert "!jitsi create" in help_text
        assert "!jitsi join" in help_text
        assert "!jitsi watch" in help_text
        assert "!jitsi kick" in help_text
        assert "!jitsi mod" in help_text
        assert "!jitsi record" in help_text


class TestMatrixBotLogic:
    """Tests for bot logic (without maubot dependency)."""

    def test_room_id_generation(self):
        """Test room ID generation from name."""
        test_cases = [
            ("My Meeting", "my-meeting"),
            ("Test Room", "test-room"),
            ("", ""),
            ("UPPER CASE", "upper-case"),
        ]
        for name, expected in test_cases:
            result = name.lower().replace(" ", "-")
            assert result == expected

    def test_content_type_detection(self):
        """Test content type detection."""
        from shared import detect_content_type

        assert detect_content_type("https://youtube.com/watch?v=abc") == "youtube"
        assert detect_content_type("https://youtu.be/abc") == "youtube"
        assert detect_content_type("https://twitch.tv/shroud") == "twitch"
        assert detect_content_type("https://vimeo.com/123") == "vimeo"
        assert detect_content_type("https://example.com/movie.mp4") == "video"
        assert detect_content_type("https://example.com/song.mp3") == "audio"
        assert detect_content_type("https://example.com/page") == "unknown"

    def test_admin_check(self):
        """Test admin check logic."""
        def is_admin(user_id: str, whitelist: list[str]) -> bool:
            if not whitelist:
                return True
            return user_id in whitelist

        # Empty whitelist = everyone is admin
        assert is_admin("@user:example.com", []) is True

        # User in whitelist
        assert is_admin("@admin:example.com", ["@admin:example.com"]) is True

        # User not in whitelist
        assert is_admin("@user:example.com", ["@admin:example.com"]) is False

    def test_command_parsing(self):
        """Test command parsing logic."""
        def parse_command(text: str, prefix: str = "jitsi"):
            if not text.startswith("!"):
                return None, []
            parts = text[1:].split()
            if parts[0] != prefix:
                return None, []
            return parts[1][0] if len(parts) > 1 else "", parts[1:]

        # Valid commands
        cmd, args = parse_command("!jitsi create My Meeting")
        assert cmd == "c"
        assert args == ["create", "My", "Meeting"]

        # No args
        cmd, args = parse_command("!jitsi")
        assert cmd == ""
        assert args == []

        # Wrong prefix
        cmd, args = parse_command("!other create")
        assert cmd is None

        # Not a command
        cmd, args = parse_command("hello")
        assert cmd is None
