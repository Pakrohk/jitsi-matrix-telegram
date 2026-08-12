# Matrix-Jitsi-Bot

EVOID-based bot for managing Jitsi meetings via Telegram and Matrix.

## Services

- **gateway** (port 8000) — ASGI gateway with AsyncAPI docs
- **telebot** (port 8001) — Telegram adapter with proxy support
- **matrixbot** (port 8002) — Matrix/Maubot adapter
- **jitsi** (port 8003) — Core Jitsi logic with SQLite

## Quick Start

```bash
# Install dependencies
pip install -e .

# Run services
evo service run gateway
evo service run telebot
evo service run matrixbot
evo service run jitsi
```

## Config

Each service has its own `evoid.toml` with engine configs.