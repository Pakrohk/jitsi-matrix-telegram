# Jitsi Server Configuration

This directory contains configuration for the self-hosted Jitsi server.

## Quick Start

```bash
# Start Jitsi server
docker-compose up -d jitsi-web jitsi-prosody jitsi-jicofo jitsi-jvb

# Start bot services
docker-compose up -d gateway telebot matrixbot jitsi-bot
```

## Configuration

Edit `.env` file to configure:

- `JITSI_DOMAIN` - Your domain name
- `JICOFO_COMPONENT_SECRET` - Component secret
- `JICOFO_AUTH_PASSWORD` - Focus auth password
- `JVB_AUTH_PASSWORD` - Videobridge auth password
- `JVB_SECRET` - Videobridge secret

## Ports

| Port | Service | Protocol |
|------|---------|----------|
| 8443 | Jitsi Meet Web | HTTPS |
| 8000 | Jitsi Meet Web | HTTP |
| 10000 | Jitsi Videobridge | UDP |
| 4443 | Jitsi Videobridge | TCP |
| 9000 | Gateway Bot | HTTP |
| 8080 | Jitsi Bot | HTTP |

## HTTPS

For production, use Let's Encrypt with Traefik:

```yaml
# Add to docker-compose.yml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.jitsi.rule=Host(`meet.example.com`)"
  - "traefik.http.routers.jitsi.tls.certresolver=letsencrypt"
```
