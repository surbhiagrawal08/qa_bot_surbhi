#!/bin/bash
# Fix langsmith compatibility issue with Python 3.12

echo "🔧 Fixing langsmith compatibility with Python 3.12..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run ./install.sh first"
    exit 1
fi

echo "Upgrading langsmith to a Python 3.12 compatible version..."
venv/bin/pip install --upgrade "langsmith>=0.1.17" --quiet

echo ""
echo "✅ langsmith upgrade complete!"
echo ""
echo "Try running ./run.sh again"
