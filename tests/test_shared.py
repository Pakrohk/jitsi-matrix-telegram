"""Tests for shared module."""

import pytest
from datetime import datetime

from shared import Meeting, WatchParty, UserPreference, ModeratorAction, detect_content_type


class TestMeeting:
    def test_create(self):
        m = Meeting(room_id="room1", room_name="Room 1", creator="@user:example.com", url="https://meet.example.com/room1")
        assert m.room_id == "room1"
        assert m.is_active is True
        assert isinstance(m.created_at, datetime)

    def test_with_participants(self):
        m = Meeting(room_id="r", room_name="R", creator="@u:e.com", url="http://e.com/r", participants=["@a:e.com", "@b:e.com"])
        assert len(m.participants) == 2


class TestWatchParty:
    def test_create(self):
        p = WatchParty(room_id="movie", room_name="Movie", video_url="https://youtube.com/watch?v=abc", content_type="youtube", creator="@user:example.com")
        assert p.content_type == "youtube"
        assert p.is_active is True


class TestUserPreference:
    def test_create(self):
        pref = UserPreference(user_id="@user:example.com", key="lang", value="fa")
        assert pref.key == "lang"
        assert pref.value == "fa"


class TestModeratorAction:
    def test_create(self):
        action = ModeratorAction(room_id="r1", action="kick", target_user="@u:e.com", performed_by="@admin:e.com")
        assert action.action == "kick"


class TestDetectContentType:
    def test_youtube(self):
        assert detect_content_type("https://youtube.com/watch?v=abc") == "youtube"
        assert detect_content_type("https://youtu.be/abc") == "youtube"

    def test_twitch(self):
        assert detect_content_type("https://twitch.tv/shroud") == "twitch"

    def test_vimeo(self):
        assert detect_content_type("https://vimeo.com/123") == "vimeo"

    def test_video(self):
        assert detect_content_type("https://example.com/movie.mp4") == "video"
        assert detect_content_type("https://example.com/video.webm") == "video"

    def test_audio(self):
        assert detect_content_type("https://example.com/song.mp3") == "audio"

    def test_unknown(self):
        assert detect_content_type("https://example.com/page.html") == "unknown"

    def test_empty(self):
        assert detect_content_type("") == "unknown"
