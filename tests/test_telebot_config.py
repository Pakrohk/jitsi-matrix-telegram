"""Tests for Telegram bot configuration via EVOID config system."""

import pytest
from pathlib import Path
from evoid.config.loader import load as load_config


class TestEvoidConfig:
    def test_load_telebot_config(self):
        config_path = Path(__file__).parent.parent / "services/telebot/evoid.toml"
        config = load_config(config_path)

        assert config.service.name == "telebot"
        assert config.runtime.adapter == "telegram"
        assert config.runtime.port == 8001

    def test_telegram_options(self):
        config_path = Path(__file__).parent.parent / "services/telebot/evoid.toml"
        config = load_config(config_path)

        telegram_cfg = config.engines.options.get("telegram", {})
        assert telegram_cfg.get("parse_mode") == "HTML"

    def test_proxy_options(self):
        config_path = Path(__file__).parent.parent / "services/telebot/evoid.toml"
        config = load_config(config_path)

        proxy_cfg = config.engines.options.get("proxy", {})
        assert proxy_cfg.get("enabled") is False
        assert proxy_cfg.get("type") == "socks5"
        assert proxy_cfg.get("host") == "127.0.0.1"
        assert proxy_cfg.get("port") == 1080

    def test_jitsi_options(self):
        config_path = Path(__file__).parent.parent / "services/telebot/evoid.toml"
        config = load_config(config_path)

        jitsi_cfg = config.engines.options.get("jitsi", {})
        assert "server_url" in jitsi_cfg
        assert "muc_domain" in jitsi_cfg

    def test_admin_options(self):
        config_path = Path(__file__).parent.parent / "services/telebot/evoid.toml"
        config = load_config(config_path)

        admin_cfg = config.engines.options.get("admin", {})
        assert "whitelist" in admin_cfg
        assert admin_cfg.get("require_auth") is False

    def test_pipeline_processors(self):
        config_path = Path(__file__).parent.parent / "services/telebot/evoid.toml"
        config = load_config(config_path)

        assert "validate" in config.pipeline.processors
        assert "authorize" in config.pipeline.processors
