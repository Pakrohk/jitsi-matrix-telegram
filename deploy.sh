#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

# Define ANSI colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Header
echo -e "${CYAN}====================================================${NC}"
echo -e "${CYAN}    Matrix-Jitsi-Bot Automatic Deployment Script    ${NC}"
echo -e "${CYAN}====================================================${NC}"
echo ""

# Check if script is run as root (or has sudo privileges)
IS_ROOT=false
if [ "$EUID" -eq 0 ]; then
    IS_ROOT=true
fi

# Function to check command existence
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 1. Check/Install Docker
echo -e "${BLUE}[1/4] Checking Docker status...${NC}"
if command_exists docker; then
    echo -e "${GREEN}[✔] Docker is already installed.${NC}"
else
    echo -e "${YELLOW}[!] Docker is not installed.${NC}"
    read -p "Would you like to install Docker automatically? (y/n): " install_docker
    if [[ "$install_docker" =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}Installing Docker...${NC}"
        curl -fsSL https://get.docker.com -o get-docker.sh
        if [ "$IS_ROOT" = true ]; then
            sh get-docker.sh
        else
            sudo sh get-docker.sh
        fi
        rm get-docker.sh
        echo -e "${GREEN}[✔] Docker installed successfully.${NC}"
    else
        echo -e "${RED}[✘] Docker is required to run this bot. Exiting.${NC}"
        exit 1
    fi
fi

# 2. Check Docker Compose
echo -e "${BLUE}[2/4] Checking Docker Compose...${NC}"
DOCKER_COMPOSE_CMD=""
if docker compose version >/dev/null 2>&1; then
    DOCKER_COMPOSE_CMD="docker compose"
    echo -e "${GREEN}[✔] Docker Compose V2 is available (docker compose).${NC}"
elif command_exists docker-compose; then
    DOCKER_COMPOSE_CMD="docker-compose"
    echo -e "${GREEN}[✔] Docker Compose V1 is available (docker-compose).${NC}"
else
    echo -e "${YELLOW}[!] Docker Compose is not installed.${NC}"
    if [ "$IS_ROOT" = true ]; then
        apt-get update && apt-get install -y docker-compose-plugin
    else
        sudo apt-get update && sudo apt-get install -y docker-compose-plugin
    fi
    if docker compose version >/dev/null 2>&1; then
        DOCKER_COMPOSE_CMD="docker compose"
        echo -e "${GREEN}[✔] Docker Compose installed successfully.${NC}"
    else
        echo -e "${RED}[✘] Failed to install Docker Compose automatically. Please install it manually.${NC}"
        exit 1
    fi
fi

# 3. Setup Environment Variables (.env)
echo -e "${BLUE}[3/4] Configuring Environment Variables...${NC}"
if [ ! -f .env ]; then
    echo -e "${YELLOW}[!] .env file not found. Creating from .env.example...${NC}"
    cp .env.example .env
fi

read -p "Would you like to configure your Bot settings now? (y/n): " config_env
if [[ "$config_env" =~ ^[Yy]$ ]]; then
    # JITSI_DOMAIN
    read -p "Enter your Jitsi Domain (e.g. meet.yourdomain.com) [default: meet.example.com]: " domain
    if [ ! -z "$domain" ]; then
        # Replace JITSI_DOMAIN
        python3 -c "
with open('.env', 'r') as f:
    lines = f.readlines()
with open('.env', 'w') as f:
    for line in lines:
        if line.startswith('JITSI_DOMAIN='):
            f.write(f'JITSI_DOMAIN={domain}\n')
        else:
            f.write(line)
"
    fi

    # TELEGRAM_TOKEN
    read -p "Enter your Telegram Bot Token: " tg_token
    if [ ! -z "$tg_token" ]; then
        python3 -c "
with open('.env', 'r') as f:
    lines = f.readlines()
with open('.env', 'w') as f:
    for line in lines:
        if line.startswith('TELEGRAM_TOKEN='):
            f.write(f'TELEGRAM_TOKEN={tg_token}\n')
        else:
            f.write(line)
"
    fi

    # Optional Matrix configurations
    read -p "Do you want to configure Matrix Bot as well? (y/n): " config_matrix
    if [[ "$config_matrix" =~ ^[Yy]$ ]]; then
        read -p "Enter Matrix Homeserver (e.g. https://matrix.org): " matrix_hs
        if [ ! -z "$matrix_hs" ]; then
            python3 -c "
with open('.env', 'r') as f:
    lines = f.readlines()
with open('.env', 'w') as f:
    for line in lines:
        if line.startswith('MATRIX_HOMESERVER='):
            f.write(f'MATRIX_HOMESERVER={matrix_hs}\n')
        else:
            f.write(line)
"
        fi

        read -p "Enter Matrix Username (e.g. @your_bot:matrix.org): " matrix_user
        if [ ! -z "$matrix_user" ]; then
            python3 -c "
with open('.env', 'r') as f:
    lines = f.readlines()
with open('.env', 'w') as f:
    for line in lines:
        if line.startswith('MATRIX_USER='):
            f.write(f'MATRIX_USER={matrix_user}\n')
        else:
            f.write(line)
"
        fi

        read -p "Enter Matrix Password: " matrix_pass
        if [ ! -z "$matrix_pass" ]; then
            python3 -c "
with open('.env', 'r') as f:
    lines = f.readlines()
with open('.env', 'w') as f:
    for line in lines:
        if line.startswith('MATRIX_PASSWORD='):
            f.write(f'MATRIX_PASSWORD={matrix_pass}\n')
        else:
            f.write(line)
"
        fi
    fi
    echo -e "${GREEN}[✔] .env file updated successfully.${NC}"
else
    echo -e "${YELLOW}[!] Using default values in .env. Please make sure to edit it later if needed.${NC}"
fi

# 4. Deploy Services
echo -e "${BLUE}[4/4] Starting services via Docker Compose...${NC}"
if [ "$IS_ROOT" = true ]; then
    $DOCKER_COMPOSE_CMD up -d --build
else
    sudo $DOCKER_COMPOSE_CMD up -d --build
fi

echo ""
echo -e "${GREEN}====================================================${NC}"
echo -e "${GREEN}    Deployment completed successfully!              ${NC}"
echo -e "${GREEN}====================================================${NC}"
echo ""
echo -e "You can check the running containers status with:"
echo -e "👉 ${CYAN}$DOCKER_COMPOSE_CMD ps${NC}"
echo ""
echo -e "To watch the logs of the bot services:"
echo -e "👉 ${CYAN}$DOCKER_COMPOSE_CMD logs -f gateway${NC}"
echo -e "👉 ${CYAN}$DOCKER_COMPOSE_CMD logs -f telebot${NC}"
echo -e "👉 ${CYAN}$DOCKER_COMPOSE_CMD logs -f matrixbot${NC}"
echo ""
