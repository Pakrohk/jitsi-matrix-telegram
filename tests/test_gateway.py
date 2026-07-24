"""Tests for Gateway service — processors and handlers."""

import pytest
from evoid import Intent, Level


# ── Processor Tests ──────────────────────────────────────────────────────────

class TestValidateProcessor:
    """Tests for validate processor."""

    def _make_context(self, intent: Intent):
        """Create a mock context for testing."""
        from dataclasses import dataclass, field

        @dataclass
        class MockState:
            def __init__(self):
                self._data = {}
            def get(self, key, default=None):
                return self._data.get(key, default)
            def __setitem__(self, key, value):
                self._data[key] = value
            def __getitem__(self, key):
                return self._data[key]
            def __contains__(self, key):
                return key in self._data

        @dataclass
        class MockContext:
            intent: Intent
            state: MockState = field(default_factory=MockState)

        return MockContext(intent=intent)

    @pytest.mark.asyncio
    async def test_valid_intent(self):
        from services.gateway.main import validate
        intent = Intent(
            name="jitsi:create_meeting",
            level=Level.STANDARD,
            metadata={"server_url": "https://meet.example.com"},
        )
        ctx = self._make_context(intent)
        result = await validate(ctx)
        assert result["validated"] is True

    @pytest.mark.asyncio
    async def test_empty_intent_name(self):
        from services.gateway.main import validate
        intent = Intent(name="", level=Level.STANDARD, metadata={})
        ctx = self._make_context(intent)
        result = await validate(ctx)
        assert result["validated"] is False
        assert "Intent name required" in result["error"]

    @pytest.mark.asyncio
    async def test_missing_server_url_for_meeting(self):
        from services.gateway.main import validate
        intent = Intent(
            name="jitsi:create_meeting",
            level=Level.STANDARD,
            metadata={},
        )
        ctx = self._make_context(intent)
        result = await validate(ctx)
        assert result["validated"] is False
        assert "server_url" in result["error"]

    @pytest.mark.asyncio
    async def test_missing_server_url_for_watch_party(self):
        from services.gateway.main import validate
        intent = Intent(
            name="jitsi:watch_party",
            level=Level.STANDARD,
            metadata={},
        )
        ctx = self._make_context(intent)
        result = await validate(ctx)
        assert result["validated"] is False

    @pytest.mark.asyncio
    async def test_non_jitsi_intent_skips_url_check(self):
        from services.gateway.main import validate
        intent = Intent(
            name="some:other:intent",
            level=Level.STANDARD,
            metadata={},
        )
        ctx = self._make_context(intent)
        result = await validate(ctx)
        assert result["validated"] is True


class TestAuthorizeProcessor:
    """Tests for authorize processor."""

    def _make_context(self, intent: Intent):
        from dataclasses import dataclass, field

        @dataclass
        class MockState:
            def __init__(self):
                self._data = {}
            def get(self, key, default=None):
                return self._data.get(key, default)

        @dataclass
        class MockContext:
            intent: Intent
            state: MockState = field(default_factory=MockState)

        return MockContext(intent=intent)

    @pytest.mark.asyncio
    async def test_standard_level_authorized(self):
        from services.gateway.main import authorize
        intent = Intent(
            name="jitsi:create_meeting",
            level=Level.STANDARD,
            metadata={"user": "@user:example.com"},
        )
        ctx = self._make_context(intent)
        result = await authorize(ctx)
        assert result["authorized"] is True

    @pytest.mark.asyncio
    async def test_critical_with_admin(self):
        from services.gateway.main import authorize
        intent = Intent(
            name="jitsi:kick",
            level=Level.CRITICAL,
            metadata={
                "user": "@admin:example.com",
                "admin_whitelist": ["@admin:example.com"],
            },
        )
        ctx = self._make_context(intent)
        result = await authorize(ctx)
        assert result["authorized"] is True

    @pytest.mark.asyncio
    async def test_critical_without_admin(self):
        from services.gateway.main import authorize
        intent = Intent(
            name="jitsi:kick",
            level=Level.CRITICAL,
            metadata={
                "user": "@user:example.com",
                "admin_whitelist": ["@admin:example.com"],
            },
        )
        ctx = self._make_context(intent)
        result = await authorize(ctx)
        assert result["authorized"] is False
        assert "not authorized" in result["reason"]

    @pytest.mark.asyncio
    async def test_critical_empty_whitelist(self):
        from services.gateway.main import authorize
        intent = Intent(
            name="jitsi:kick",
            level=Level.CRITICAL,
            metadata={
                "user": "@anyone:example.com",
                "admin_whitelist": [],
            },
        )
        ctx = self._make_context(intent)
        result = await authorize(ctx)
        assert result["authorized"] is True


class TestAuditProcessor:
    """Tests for audit processor."""

    @pytest.mark.asyncio
    async def test_audit_returns_true(self):
        from services.gateway.main import audit
        ctx = type("MockCtx", (), {"intent": Intent(name="test", level=Level.STANDARD)})()
        result = await audit(ctx)
        assert result["audited"] is True


class TestProtectProcessor:
    """Tests for protect processor."""

    @pytest.mark.asyncio
    async def test_protect_returns_true(self):
        from services.gateway.main import protect
        ctx = type("MockCtx", (), {"intent": Intent(name="test", level=Level.STANDARD)})()
        result = await protect(ctx)
        assert result["protected"] is True


# ── Handler Tests ────────────────────────────────────────────────────────────

class TestMeetingHandlers:
    """Tests for meeting intent handlers."""

    @pytest.mark.asyncio
    async def test_create_meeting(self):
        from services.gateway.main import create_meeting
        result = await create_meeting("My Meeting", "@user:example.com", "https://meet.example.com")
        assert result["status"] == "created"
        assert "my-meeting" in result["meeting_url"]
        assert result["room_id"] == "my-meeting"

    @pytest.mark.asyncio
    async def test_join_meeting(self):
        from services.gateway.main import join_meeting
        result = await join_meeting("Test Room", "https://meet.example.com")
        assert result["status"] == "joined"
        assert "test-room" in result["meeting_url"]

    @pytest.mark.asyncio
    async def test_watch_party_youtube(self):
        from services.gateway.main import watch_party
        result = await watch_party(
            "https://youtube.com/watch?v=abc",
            "Movie Night",
            "@user:example.com",
            "https://meet.example.com",
        )
        assert result["status"] == "watch_party_created"
        assert result["content_type"] == "youtube"
        assert result["iframe_command"] == "startShareVideo"

    @pytest.mark.asyncio
    async def test_watch_party_video(self):
        from services.gateway.main import watch_party
        result = await watch_party(
            "https://example.com/movie.mp4",
            "Movie",
            "@user:example.com",
            "https://meet.example.com",
        )
        assert result["content_type"] == "video"

    @pytest.mark.asyncio
    async def test_stop_watch_party(self):
        from services.gateway.main import stop_watch_party
        result = await stop_watch_party()
        assert result["status"] == "watch_party_stopped"
        assert result["iframe_command"] == "stopShareVideo"


class TestCallControlHandlers:
    """Tests for call control handlers."""

    @pytest.mark.asyncio
    async def test_hangup(self):
        from services.gateway.main import hangup
        result = await hangup()
        assert result["status"] == "hung_up"
        assert result["iframe_command"] == "hangup"

    @pytest.mark.asyncio
    async def test_end_conference(self):
        from services.gateway.main import end_conference
        result = await end_conference()
        assert result["status"] == "conference_ended"
        assert result["iframe_command"] == "endConference"


class TestMediaHandlers:
    """Tests for media control handlers."""

    @pytest.mark.asyncio
    async def test_toggle_audio(self):
        from services.gateway.main import toggle_audio
        result = await toggle_audio()
        assert result["status"] == "audio_toggled"
        assert result["iframe_command"] == "toggleAudio"

    @pytest.mark.asyncio
    async def test_toggle_video(self):
        from services.gateway.main import toggle_video
        result = await toggle_video()
        assert result["status"] == "video_toggled"
        assert result["iframe_command"] == "toggleVideo"

    @pytest.mark.asyncio
    async def test_toggle_screen(self):
        from services.gateway.main import toggle_screen
        result = await toggle_screen()
        assert result["status"] == "screen_toggled"
        assert result["iframe_command"] == "toggleShareScreen"

    @pytest.mark.asyncio
    async def test_mute_everyone_default(self):
        from services.gateway.main import mute_everyone
        result = await mute_everyone()
        assert result["media_type"] == "audio"

    @pytest.mark.asyncio
    async def test_mute_everyone_video(self):
        from services.gateway.main import mute_everyone
        result = await mute_everyone("video")
        assert result["media_type"] == "video"

    @pytest.mark.asyncio
    async def test_set_video_quality(self):
        from services.gateway.main import set_video_quality
        result = await set_video_quality(480)
        assert result["height"] == 480
        assert result["iframe_command"] == "setVideoQuality"


class TestParticipantHandlers:
    """Tests for participant management handlers."""

    @pytest.mark.asyncio
    async def test_kick(self):
        from services.gateway.main import kick
        result = await kick("user123", "@admin:example.com")
        assert result["status"] == "kicked"
        assert result["participantId"] == "user123"

    @pytest.mark.asyncio
    async def test_grant_moderator(self):
        from services.gateway.main import grant_moderator
        result = await grant_moderator("user456", "@admin:example.com")
        assert result["status"] == "moderator_granted"
        assert result["participantId"] == "user456"

    @pytest.mark.asyncio
    async def test_pin_participant(self):
        from services.gateway.main import pin_participant
        result = await pin_participant("user789")
        assert result["status"] == "participant_pinned"
        assert result["participantId"] == "user789"

    @pytest.mark.asyncio
    async def test_set_volume(self):
        from services.gateway.main import set_volume
        result = await set_volume("user123", 0.5)
        assert result["volume"] == 0.5


class TestLayoutHandlers:
    """Tests for layout control handlers."""

    @pytest.mark.asyncio
    async def test_toggle_tile(self):
        from services.gateway.main import toggle_tile
        result = await toggle_tile()
        assert result["iframe_command"] == "toggleTileView"

    @pytest.mark.asyncio
    async def test_toggle_chat(self):
        from services.gateway.main import toggle_chat
        result = await toggle_chat()
        assert result["iframe_command"] == "toggleChat"

    @pytest.mark.asyncio
    async def test_toggle_raise_hand(self):
        from services.gateway.main import toggle_raise_hand
        result = await toggle_raise_hand()
        assert result["iframe_command"] == "toggleRaiseHand"

    @pytest.mark.asyncio
    async def test_toggle_lobby(self):
        from services.gateway.main import toggle_lobby
        result = await toggle_lobby(True)
        assert result["enabled"] is True
        assert result["iframe_command"] == "toggleLobby"


class TestRecordingHandlers:
    """Tests for recording handlers."""

    @pytest.mark.asyncio
    async def test_start_recording_local(self):
        from services.gateway.main import start_recording
        result = await start_recording("local", "@user:example.com")
        assert result["mode"] == "local"
        assert result["iframe_command"] == "startRecording"

    @pytest.mark.asyncio
    async def test_start_recording_stream(self):
        from services.gateway.main import start_recording
        result = await start_recording("stream", "@user:example.com")
        assert result["mode"] == "stream"

    @pytest.mark.asyncio
    async def test_stop_recording(self):
        from services.gateway.main import stop_recording
        result = await stop_recording("local")
        assert result["status"] == "recording_stopped"


class TestBreakoutHandlers:
    """Tests for breakout room handlers."""

    @pytest.mark.asyncio
    async def test_add_breakout(self):
        from services.gateway.main import add_breakout
        result = await add_breakout("Room A")
        assert result["name"] == "Room A"
        assert result["iframe_command"] == "addBreakoutRoom"

    @pytest.mark.asyncio
    async def test_close_breakout(self):
        from services.gateway.main import close_breakout
        result = await close_breakout("room-1")
        assert result["roomId"] == "room-1"
        assert result["iframe_command"] == "closeBreakoutRoom"

    @pytest.mark.asyncio
    async def test_join_breakout(self):
        from services.gateway.main import join_breakout
        result = await join_breakout("room-2")
        assert result["roomId"] == "room-2"
        assert result["iframe_command"] == "joinBreakoutRoom"


class TestMiscHandlers:
    """Tests for misc handlers."""

    @pytest.mark.asyncio
    async def test_set_subject(self):
        from services.gateway.main import set_subject
        result = await set_subject("New Subject")
        assert result["subject"] == "New Subject"
        assert result["iframe_command"] == "subject"

    @pytest.mark.asyncio
    async def test_send_chat(self):
        from services.gateway.main import send_chat
        result = await send_chat("Hello!", "user123")
        assert result["message"] == "Hello!"
        assert result["to"] == "user123"
        assert result["iframe_command"] == "sendChatMessage"

    @pytest.mark.asyncio
    async def test_set_follow_me(self):
        from services.gateway.main import set_follow_me
        result = await set_follow_me(True, False)
        assert result["enabled"] is True
        assert result["recorder_only"] is False
        assert result["iframe_command"] == "setFollowMe"


# ── Edge Case Tests ──────────────────────────────────────────────────────────

class TestEdgeCases:
    """Tests for edge cases."""

    @pytest.mark.asyncio
    async def test_create_meeting_empty_name(self):
        from services.gateway.main import create_meeting
        result = await create_meeting("", "@user:example.com", "https://meet.example.com")
        assert result["room_id"] == ""

    @pytest.mark.asyncio
    async def test_create_meeting_special_chars(self):
        from services.gateway.main import create_meeting
        result = await create_meeting("Room @#$", "@user:example.com", "https://meet.example.com")
        assert result["room_id"] == "room-@#$"

    @pytest.mark.asyncio
    async def test_join_meeting_empty_room(self):
        from services.gateway.main import join_meeting
        result = await join_meeting("", "https://meet.example.com")
        assert result["room_id"] == ""

    @pytest.mark.asyncio
    async def test_watch_party_unknown_url(self):
        from services.gateway.main import watch_party
        result = await watch_party(
            "https://example.com/page",
            "Test",
            "@user:example.com",
            "https://meet.example.com",
        )
        assert result["content_type"] == "unknown"

    @pytest.mark.asyncio
    async def test_watch_party_empty_url(self):
        from services.gateway.main import watch_party
        result = await watch_party(
            "",
            "Test",
            "@user:example.com",
            "https://meet.example.com",
        )
        assert result["content_type"] == "unknown"
