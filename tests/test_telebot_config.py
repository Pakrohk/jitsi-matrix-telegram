"""Tests for Telegram bot configuration."""

import pytest
import os
import tempfile
from pathlib import Path

from services.telebot.config import load_config, BotConfig, ProxyConfig


class TestProxyConfig:
    def test_default(self):
        p = ProxyConfig()
        assert p.enabled is False
        assert p.url is None

    def test_enabled(self):
        p = ProxyConfig(enabled=True, type="socks5", host="127.0.0.1", port=1080)
        assert p.url == "socks5://127.0.0.1:1080"

    def test_with_auth(self):
        p = ProxyConfig(enabled=True, type="http", host="proxy.com", port=8080, username="user", password="pass")
        assert p.url == "http://user:pass@proxy.com:8080"


class TestBotConfig:
    def test_defaults(self):
        c = BotConfig()
        assert c.token == ""
        assert c.parse_mode == "HTML"
        assert c.proxy.enabled is False

    def test_custom(self):
        c = BotConfig(token="123:ABC", parse_mode="Markdown")
        assert c.token == "123:ABC"
        assert c.parse_mode == "Markdown"


class TestLoadConfig:
    def test_load_from_yaml(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
token: "123:ABC"
bot:
  username: "testbot"
  parse_mode: "Markdown"
proxy:
  enabled: true
  type: "socks5"
  host: "proxy.local"
  port: 1080
jitsi:
  server_url: "https://jitsi.example.com"
  muc_domain: "conference.jitsi.example.com"
""")
        config = load_config(config_file)
        assert config.token == "123:ABC"
        assert config.username == "testbot"
        assert config.proxy.enabled is True
        assert config.proxy.host == "proxy.local"
        assert config.jitsi.server_url == "https://jitsi.example.com"

    def test_env_override(self, tmp_path, monkeypatch):
        config_file = tmp_path / "config.yaml"
        config_file.write_text('token: "old_token"')
        monkeypatch.setenv("TELEGRAM_TOKEN", "new_token")
        config = load_config(config_file)
        assert config.token == "new_token"

    def test_proxy_env(self, tmp_path, monkeypatch):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("proxy:\n  enabled: false")
        monkeypatch.setenv("PROXY_ENABLED", "true")
        monkeypatch.setenv("PROXY_HOST", "myproxy.com")
        monkeypatch.setenv("PROXY_PORT", "9050")
        config = load_config(config_file)
        assert config.proxy.enabled is True
        assert config.proxy.host == "myproxy.com"
        assert config.proxy.port == 9050
