# matrix-jitsi-bot

Matrix + Telegram bot for Jitsi management, built on the **EVOID runtime** (Intent-Oriented Programming).

## What It Does

Manages a self-hosted Jitsi server from both Matrix and Telegram:
- Create/manage meetings
- Watch parties (YouTube, video, audio)
- Assign moderators
- Control conference state
- 50+ Jitsi iframe commands

## Architecture

```
Telegram/Matrix → Adapter → Intent → Pipeline → Handler → Jitsi
                    ↓                    ↓
               Message Bus         validate → authorize → audit → protect
```

Services communicate through **Intents**, not direct calls. The gateway routes, secures, and orchestrates.

## Quick Start

```bash
# Install EVOID
uv venv && uv pip install -e "evoid[telegram]"

# Install plugins
evo install sqlite
evo install smart-storage
evo plug install evoid-di

# Install Matrix dependencies
uv pip install matrix-nio aiohttp

# Configure
cp .env.example .env
# Edit .env with your tokens

# Run
evo run
```

## Environment Variables

```
TELEGRAM_TOKEN       Telegram bot token
MATRIX_HOMESERVER    Matrix homeserver URL
MATRIX_USER          Bot Matrix user ID
MATRIX_PASSWORD      Bot password
JITSI_SERVER_URL     Jitsi server URL
JITSI_MUC_DOMAIN     Jitsi MUC domain
```

## Commands

### Matrix (maubot plugin)
```
!jitsi create [name]     Create meeting
!jitsi join <room>       Get join link
!jitsi watch <url>       Watch party
!jitsi mute              Toggle audio
!jitsi video             Toggle video
!jitsi kick <id>         Kick participant (mod)
... 50+ commands
```

### Telegram
```
/create [name]     Create meeting
/join <room>       Join meeting
/watch <url>       Watch party
```

## Project Structure

```
src/
├── main.py               # Gateway entry point
├── config/               # Configuration
├── intents/              # Intent definitions (pure data)
├── handlers/             # Handler functions (one per intent)
├── processors/           # Pipeline processors
├── services/
│   ├── gateway.py        # Gateway service (routing)
│   ├── telegram.py       # Telegram bot service
│   ├── matrix.py         # Matrix bot service
│   └── jitsi.py          # Jitsi service (shared)
├── models/               # Data models
evoid.toml                # Runtime config
```

## Development

```bash
# Lint
uv run ruff check src/
uv run ruff format src/

# Test
uv run pytest tests/ -v
uv run pytest tests/ --evoid-inspect

# List intents and processors
evo list-intents
evo list-processors
```

## License

Apache-2.0
