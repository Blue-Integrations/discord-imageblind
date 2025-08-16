@echo off
echo Starting BlindBot Discord Bot...

REM Check if .env file exists
if not exist .env (
    echo Error: .env file not found!
    echo Please copy config.env.example to .env and fill in your tokens.
    pause
    exit /b 1
)

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH!
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install/update requirements
echo Installing/updating requirements...
pip install -r requirements.txt

REM Run the bot
echo Starting bot...
python bot.py

pause
