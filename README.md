# Jitsi Matrix Telegram Bot

Matrix + Telegram bot for Jitsi server management, built on the **EVOID runtime** (Intent-Oriented Programming).

## Features

- **Self-hosted Jitsi Server**: Complete Docker-based Jitsi deployment
- **Telegram Bot**: Control Jitsi meetings from Telegram
- **Matrix Bot**: Control Jitsi meetings from Matrix (maubot plugin)
- **Gateway Service**: Central Intent routing between services
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
| Jitsi Web | 8443 | Jitsi Meet web interface |
| Jitsi JVB | 10000 | Videobridge (UDP) |
| Gateway | 9000 | Central Intent router |
| TeleBot | - | Telegram bot |
| MatrixBot | - | Matrix bot (maubot plugin) |
| Jitsi Bot | 8080 | Shared Jitsi functionality |

## Docker Configuration

### 1. Clone and Configure

```bash
git clone https://github.com/Pakrohk/jitsi-matrix-telegram.git
cd jitsi-matrix-telegram
cp .env.example .env
```

### 2. Edit `.env` File

Open `.env` and configure:

```bash
# ═══════════════════════════════════════════════════════════════════════════════
# JITSI SERVER CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

# Your domain name (required)
JITSI_DOMAIN=meet.example.com

# Jitsi server URL (auto-generated from domain if not set)
JITSI_SERVER_URL=https://meet.example.com:8443

# MUC domain for conference rooms
JITSI_MUC_DOMAIN=jitsi-meet.example.com

# ═══════════════════════════════════════════════════════════════════════════════
# JITSI SECRETS (CHANGE THESE!)
# ═══════════════════════════════════════════════════════════════════════════════

# Component secret for Jicofo
JICOFO_COMPONENT_SECRET=your_random_secret_here

# Auth passwords
JICOFO_AUTH_PASSWORD=your_jicofo_password
JVB_AUTH_PASSWORD=your_jvb_password

# Videobridge secret
JVB_SECRET=your_jvb_secret

# ═══════════════════════════════════════════════════════════════════════════════
# TELEGRAM BOT
# ═══════════════════════════════════════════════════════════════════════════════

# Get from @BotFather
TELEGRAM_TOKEN=your_bot_token_here

# ═══════════════════════════════════════════════════════════════════════════════
# MATRIX BOT (optional)
# ═══════════════════════════════════════════════════════════════════════════════

MATRIX_HOMESERVER=https://matrix.example.com
MATRIX_USER=@jitsi-bot:example.com
MATRIX_PASSWORD=your_matrix_password

# ═══════════════════════════════════════════════════════════════════════════════
# PROXY (optional)
# ═══════════════════════════════════════════════════════════════════════════════

PROXY_ENABLED=false
PROXY_TYPE=socks5
PROXY_HOST=127.0.0.1
PROXY_PORT=1080
```

### 3. Generate Secrets

For production, generate secure secrets:

```bash
# Generate random secrets
openssl rand -hex 32
```

### 4. Start Services

```bash
# Start Jitsi server first
docker-compose up -d jitsi-web jitsi-prosody jitsi-jicofo jitsi-jvb

# Wait for Jitsi to start, then start bots
docker-compose up -d gateway telebot matrixbot jitsi-bot

# Or start everything at once
docker-compose up -d
```

### 5. Access Services

| Service | URL |
|---------|-----|
| Jitsi Meet | https://meet.example.com:8443 |
| Gateway API | http://localhost:9000/health |

### 6. View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f jitsi-web
docker-compose logs -f telebot
```

### 7. Stop Services

```bash
docker-compose down

# With volumes
docker-compose down -v
```

## Service Configuration

### Telegram Bot (`services/telebot/evoid.toml`)

```toml
[engines.telegram]
token = ""  # or TELEGRAM_TOKEN env

[engines.proxy]
enabled = false
type = "socks5"
host = "127.0.0.1"
port = 1080

[engines.jitsi]
server_url = "https://meet.example.com:8443"
```

### Matrix Bot (`services/matrixbot/evoid.toml`)

```toml
[engines.matrix]
homeserver = "https://matrix.example.com"
user = "@jitsi-bot:example.com"
access_token = ""

[engines.jitsi]
server_url = "https://meet.example.com:8443"
```

### Gateway (`services/gateway/evoid.toml`)

```toml
[runtime]
adapter = "asgi"
port = 9000

[pipeline]
processors = ["validate", "authorize", "audit", "protect"]
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
│   ├── gateway/            # Gateway service (port 9000)
│   ├── telebot/            # Telegram bot
│   ├── matrixbot/          # Matrix bot (maubot plugin)
│   └── jitsi/              # Jitsi service (port 8080)
├── jitsi/                  # Jitsi server configuration
├── tests/                  # 73 tests
├── Dockerfile
└── docker-compose.yml
```

## License

Apache License 2.0
