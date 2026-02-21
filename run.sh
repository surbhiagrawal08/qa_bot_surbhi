#!/bin/bash
# Run script for the QA Bot API

echo "Starting Zania QA Bot API..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "Please run ./setup_env.sh first or create .env manually"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating..."
    python3 -m venv venv
    echo "Installing dependencies..."
    venv/bin/pip install -r requirements.txt
else
    # Use the venv's Python directly instead of sourcing activate
    # This avoids permission issues on macOS
    if [ ! -f "venv/bin/python" ]; then
        echo "❌ Error: Virtual environment appears to be corrupted"
        exit 1
    fi
fi

echo "Starting server..."
echo "API will be available at http://localhost:8000"
echo "API docs at http://localhost:8000/docs"
echo ""

# Use venv's Python directly to avoid activation issues
# Only watch the app directory to avoid reloading on venv changes
# Note: If reloads still occur, try upgrading uvicorn: pip install --upgrade uvicorn[standard]
venv/bin/python -m uvicorn app.main:app --reload --reload-dir app --host 0.0.0.0 --port 8000
