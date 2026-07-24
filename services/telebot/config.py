"""Telegram Bot Configuration Loader.

IOP: Config is data. Loader is a pure function.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None


@dataclass
class ProxyConfig:
    """Proxy configuration."""
    enabled: bool = False
    type: str = "socks5"
    host: str = "127.0.0.1"
    port: int = 1080
    username: str = ""
    password: str = ""

    @property
    def url(self) -> str | None:
        """Get proxy URL for aiogram."""
        if not self.enabled:
            return None
        auth = ""
        if self.username:
            auth = f"{self.username}:{self.password}@"
        return f"{self.type}://{auth}{self.host}:{self.port}"


@dataclass
class JitsiConfig:
    """Jitsi server configuration."""
    server_url: str = "https://meet.example.com"
    muc_domain: str = "conference.meet.example.com"


@dataclass
class AdminConfig:
    """Admin configuration."""
    whitelist: list[str] = field(default_factory=list)
    require_auth: bool = False


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    enabled: bool = True
    max_requests: int = 30
    window_seconds: int = 60


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    file: str = "telebot.log"


@dataclass
class BotConfig:
    """Complete Telegram bot configuration."""
    token: str = ""
    username: str = ""
    parse_mode: str = "HTML"
    proxy: ProxyConfig = field(default_factory=ProxyConfig)
    jitsi: JitsiConfig = field(default_factory=JitsiConfig)
    admin: AdminConfig = field(default_factory=AdminConfig)
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)


def load_config(path: str | Path = "config.yaml") -> BotConfig:
    """Load configuration from YAML file.

    IOP: Pure function. Returns config data.
    Priority: environment variables > config file > defaults
    """
    config = BotConfig()

    # Load from file if exists
    path = Path(path)
    if path.exists():
        config = _load_yaml(path)

    # Override with environment variables
    config.token = os.environ.get("TELEGRAM_TOKEN", config.token)
    config.jitsi.server_url = os.environ.get("JITSI_SERVER_URL", config.jitsi.server_url)
    config.jitsi.muc_domain = os.environ.get("JITSI_MUC_DOMAIN", config.jitsi.muc_domain)

    # Proxy from env
    if os.environ.get("PROXY_ENABLED", "").lower() in ("true", "1", "yes"):
        config.proxy.enabled = True
        config.proxy.type = os.environ.get("PROXY_TYPE", config.proxy.type)
        config.proxy.host = os.environ.get("PROXY_HOST", config.proxy.host)
        config.proxy.port = int(os.environ.get("PROXY_PORT", str(config.proxy.port)))
        config.proxy.username = os.environ.get("PROXY_USERNAME", config.proxy.username)
        config.proxy.password = os.environ.get("PROXY_PASSWORD", config.proxy.password)

    return config


def _load_yaml(path: Path) -> BotConfig:
    """Load config from YAML file."""
    try:
        import yaml
        with open(path) as f:
            data = yaml.safe_load(f) or {}
    except ImportError:
        # Fallback: parse simple YAML manually
        data = _parse_simple_yaml(path)

    return BotConfig(
        token=data.get("token", ""),
        username=data.get("bot", {}).get("username", ""),
        parse_mode=data.get("bot", {}).get("parse_mode", "HTML"),
        proxy=ProxyConfig(
            enabled=data.get("proxy", {}).get("enabled", False),
            type=data.get("proxy", {}).get("type", "socks5"),
            host=data.get("proxy", {}).get("host", "127.0.0.1"),
            port=data.get("proxy", {}).get("port", 1080),
            username=data.get("proxy", {}).get("username", ""),
            password=data.get("proxy", {}).get("password", ""),
        ),
        jitsi=JitsiConfig(
            server_url=data.get("jitsi", {}).get("server_url", "https://meet.example.com"),
            muc_domain=data.get("jitsi", {}).get("muc_domain", "conference.meet.example.com"),
        ),
        admin=AdminConfig(
            whitelist=data.get("admin", {}).get("whitelist", []),
            require_auth=data.get("admin", {}).get("require_auth", False),
        ),
        rate_limit=RateLimitConfig(
            enabled=data.get("rate_limit", {}).get("enabled", True),
            max_requests=data.get("rate_limit", {}).get("max_requests", 30),
            window_seconds=data.get("rate_limit", {}).get("window_seconds", 60),
        ),
        logging=LoggingConfig(
            level=data.get("logging", {}).get("level", "INFO"),
            file=data.get("logging", {}).get("file", "telebot.log"),
        ),
    )


def _parse_simple_yaml(path: Path) -> dict:
    """Simple YAML parser for config files."""
    data: dict[str, Any] = {}
    current_section = data

    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()

                if not value:
                    # Section header
                    current_section = {}
                    data[key] = current_section
                elif value.startswith("["):
                    # List
                    current_section[key] = []
                else:
                    # Simple value
                    if value.lower() in ("true", "yes"):
                        value = True
                    elif value.lower() in ("false", "no"):
                        value = False
                    elif value.isdigit():
                        value = int(value)
                    current_section[key] = value

    return data
