#!/bin/bash
# Setup script for Jarvis
set -e

echo "=== Setting up Jarvis ==="

# Check Python
python3 --version || { echo "Python 3.11+ required"; exit 1; }

# Create virtualenv
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Copy env file
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env from template. Edit it with your settings."
fi

# Start infrastructure
echo "Starting Docker services..."
docker compose up -d postgres redis chromadb

echo ""
echo "=== Setup complete ==="
echo "Run 'docker compose up -d' to start all services"
echo "Run 'jarvis chat' to start chatting"
echo "Run 'jarvis serve' to start the API server"
