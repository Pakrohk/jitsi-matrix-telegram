# AGENTS.md — matrix_jitsi_bot

## Design

Full architecture: [DESIGN.md](./DESIGN.md)

Services: Gateway (8000), TeleBot (8001), MatrixBot (8002), Jitsi (8003). Each service has its own `evoid.toml` + `main.py`. Services communicate via Intents through Gateway.

## What This Is

Matrix + Telegram bot built on the **EVOID runtime** (Intent-Oriented Programming). The bot manages a self-hosted Jitsi server from both platforms.

## Project Structure (EVOID Standard)

```
matrix-jitsi-bot/
├── pyproject.toml           # Project config + [tool.evoid]
├── shared/                  # Shared models (used by all services)
│   └── __init__.py
├── services/
│   ├── gateway/             # Gateway service (routing)
│   │   ├── evoid.toml       # Service config
│   │   └── main.py
│   ├── telebot/             # Telegram bot service
│   │   ├── evoid.toml
│   │   └── main.py
│   ├── matrixbot/           # Matrix bot service (maubot plugin)
│   │   ├── evoid.toml
│   │   └── main.py
│   └── jitsi/               # Jitsi service (shared logic)
│       ├── evoid.toml
│       └── main.py
└── tests/
```

## Key Commands

```bash
# Setup
evo init matrix-jitsi-bot
cd matrix-jitsi-bot

# Add services
evo service new gateway
evo service new telebot
evo service new matrixbot
evo service new jitsi

# Install plugins
evo install sqlite
evo install loguru
evo install telegram

# Run
evo run                      # Run all services
evo service run gateway      # Run single service

# Test
uv run pytest tests/ -v
uv run pytest tests/ --evoid-inspect

# List
evo list-intents
evo list-processors
```

## IOP Pattern

1. **Intents are data** — `Intent(name="create_meeting", level=Level.STANDARD)`
2. **Handlers are pure functions** — `async def handler(intent) -> dict`
3. **Pipelines are processor chains** — Level determines which processors run
4. **Adapters convert events to Intents** — Telegram adapter exists, Matrix adapter (maubot) is custom

## Storage

Uses `evoid[sqlite]` for persistence:
- Meetings: room_id, name, creator, url
- Watch parties: room_id, video_url, content_type
- User preferences: user_id, key, value

## Gotchas

- Each service has its own `evoid.toml` — don't put all config in one place
- Services communicate via Intents through Gateway — don't call each other directly
- CRITICAL level runs full pipeline: validate → authorize → audit → protect
- `evoid[telegram]` depends on `aiogram` — install with `evoid[telegram]`, not bare `aiogram`
- Line length: 120 chars (ruff config in pyproject.toml)
