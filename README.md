# Jitsi Matrix Telegram Bot

Matrix + Telegram bot for Jitsi server management, built on the **EVOID runtime** (Intent-Oriented Programming).

## Features

- **Telegram Bot**: Control Jitsi meetings from Telegram
- **Matrix Bot**: Control Jitsi meetings from Matrix (maubot plugin)
- **Gateway Service**: Central Intent routing between services
- **Jitsi Service**: Shared Jitsi functionality
- **50+ Commands**: Full Jitsi iframe API support
- **Proxy Support**: SOCKS5/SOCKS4/HTTP proxy for Telegram
- **Storage**: SQLite for meeting persistence

## Architecture

```
Telegram/Matrix → Adapter → Intent → Pipeline → Handler → Jitsi
                    ↓                    ↓
               Message Bus         validate → authorize → audit → protect
```

Services communicate through **Intents**, not direct calls. The gateway routes, secures, and orchestrates.

## Services

| Service | Port | Description |
|---------|------|-------------|
| Gateway | 8000 | Central Intent router |
| TeleBot | 8001 | Telegram bot |
| MatrixBot | 8002 | Matrix bot (maubot plugin) |
| Jitsi | 8003 | Shared Jitsi functionality |

## Quick Start

### Using Docker Compose

```bash
# Clone the repository
git clone https://github.com/Pakrohk/jitsi-matrix-telegram.git
cd jitsi-matrix-telegram

# Configure
cp .env.example .env
# Edit .env with your tokens

# Run all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### Manual Setup

```bash
# Install EVOID
uv venv && uv pip install -e "evoid[telegram,asgi,sqlite,loguru]"

# Install plugins
evo install sqlite
evo install loguru

# Run services
evo run
# Or run individual service
evo service run gateway
```

## Configuration

### Environment Variables

```bash
# Telegram Bot
TELEGRAM_TOKEN=your_bot_token

# Matrix Bot
MATRIX_HOMESERVER=https://matrix.example.com
MATRIX_USER=@jitsi-bot:example.com
MATRIX_PASSWORD=your_password

# Jitsi Server
JITSI_SERVER_URL=https://meet.example.com
JITSI_MUC_DOMAIN=conference.meet.example.com

# Proxy (optional)
PROXY_ENABLED=false
PROXY_TYPE=socks5
PROXY_HOST=127.0.0.1
PROXY_PORT=1080
```

### Service Configuration

Each service has its own `evoid.toml`:

```toml
[service]
name = "telebot"

[runtime]
adapter = "telegram"
port = 8001

[engines.telegram]
token = ""  # or TELEGRAM_TOKEN env

[engines.proxy]
enabled = false
type = "socks5"
host = "127.0.0.1"
port = 1080

[engines.jitsi]
server_url = "https://meet.example.com"
```

## Commands

### Telegram

| Command | Description |
|---------|-------------|
| `/start` | Welcome message |
| `/help` | Show help |
| `/create [name]` | Create meeting |
| `/join <room>` | Join meeting |
| `/watch <url> [name]` | Watch party |
| `/stopwatch` | Stop watch party |
| `/mute` | Toggle audio |
| `/video` | Toggle video |
| `/screen` | Toggle screen share |
| `/hangup` | End call |
| `/kick <id>` | Kick participant (mod) |
| `/mod <id>` | Grant moderator (mod) |
| `/record <mode>` | Start recording (mod) |
| `/stoprecord <mode>` | Stop recording (mod) |

### Matrix (maubot)

| Command | Description |
|---------|-------------|
| `!jitsi create [name]` | Create meeting |
| `!jitsi join <room>` | Join meeting |
| `!jitsi watch <url> [name]` | Watch party |
| `!jitsi stopwatch` | Stop watch party |
| `!jitsi mute` | Toggle audio |
| `!jitsi video` | Toggle video |
| `!jitsi screen` | Toggle screen share |
| `!jitsi hangup` | End call |
| `!jitsi kick <id>` | Kick participant (mod) |
| `!jitsi mod <id>` | Grant moderator (mod) |
| `!jitsi record <mode>` | Start recording (mod) |
| `!jitsi stoprecord <mode>` | Stop recording (mod) |

## Development

```bash
# Run tests
uv run pytest tests/ -v

# Lint
uv run ruff check src/
uv run ruff format src/

# Build maubot plugin
cd services/matrixbot
zip -9r jitsi-bot.mbp *
```

## Project Structure

```
jitsi-matrix-telegram/
├── shared/                 # Shared models and processors
│   ├── __init__.py
│   └── processors/         # IOP pipeline processors
├── services/
│   ├── gateway/            # Gateway service (port 8000)
│   ├── telebot/            # Telegram bot (port 8001)
│   ├── matrixbot/          # Matrix bot (port 8002)
│   └── jitsi/              # Jitsi service (port 8003)
├── tests/                  # 73 tests
├── Dockerfile
└── docker-compose.yml
```

## License

Apache License 2.0
