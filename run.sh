#!/bin/bash

# BlindBot Discord Bot Startup Script

echo "Starting BlindBot Discord Bot..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    echo "Please copy config.env.example to .env and fill in your tokens."
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed!"
    exit 1
fi

# Check if requirements are installed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/update requirements
echo "Installing/updating requirements..."
pip install -r requirements.txt

# Run the bot
echo "Starting bot..."
python3 bot.py
