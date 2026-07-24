# Design — matrix_jitsi_bot

## Service Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        EVOID Runtime                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   Gateway   │  │   TeleBot   │  │  MatrixBot  │            │
│  │  (port 8000)│  │  (port 8001)│  │  (port 8002)│            │
│  │  evoid.toml │  │  evoid.toml │  │  evoid.toml │            │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘            │
│         │                │                │                     │
│         └────────────────┼────────────────┘                     │
│                          │                                      │
│                    Intent Bus                                   │
│                          │                                      │
│                    ┌─────┴─────┐                                │
│                    │   Jitsi   │                                │
│                    │  Service  │                                │
│                    │ (8003)    │                                │
│                    └───────────┘                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## EVOID Project Structure

```
matrix-jitsi-bot/
├── pyproject.toml           # Project config + [tool.evoid]
├── shared/                  # Shared models (used by all services)
│   └── __init__.py
├── services/
│   ├── gateway/             # Gateway service (routing)
│   │   ├── evoid.toml       # Service-specific config
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

## Services

### Gateway (port 8000)

Routes Intents between services.

```toml
# services/gateway/evoid.toml
[service]
name = "gateway"

[runtime]
adapter = "asgi"
port = 8000

[pipeline]
processors = ["validate", "authorize", "audit", "protect"]
```

### TeleBot (port 8001)

Converts Telegram messages to Intents.

```toml
# services/telebot/evoid.toml
[service]
name = "telebot"

[runtime]
adapter = "telegram"
port = 8001
```

### MatrixBot (port 8002)

Converts Matrix events to Intents (maubot plugin).

```toml
# services/matrixbot/evoid.toml
[service]
name = "matrixbot"

[runtime]
adapter = "maubot"
port = 8002
```

### Jitsi (port 8003)

Shared Jitsi functionality.

```toml
# services/jitsi/evoid.toml
[service]
name = "jitsi"

[runtime]
adapter = "asgi"
port = 8003

[engines]
storage = "sqlite"
```

## Intent Flow

```
1. User sends "!jitsi create Meeting" in Matrix
2. MatrixBot converts to HTTP POST to Gateway
3. Gateway runs pipeline: validate → authorize
4. Gateway routes to Jitsi service
5. Jitsi service creates meeting, returns URL
6. Gateway returns to MatrixBot
7. MatrixBot replies to Matrix room
```

## EVOID Commands

```bash
# Project setup
evo init matrix-jitsi-bot

# Add services
evo service new gateway
evo service new telebot
evo service new matrixbot
evo service new jitsi

# Run
evo run                      # All services
evo service run gateway      # Single service

# List
evo list-intents
evo list-processors
```
