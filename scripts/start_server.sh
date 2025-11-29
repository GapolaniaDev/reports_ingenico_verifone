#!/bin/bash

# Get the directory where this script is located (scripts/)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Get the parent directory (project root)
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

echo "=================================="
echo "Verifone Invoice Management Setup"
echo "=================================="
echo ""

# Change to project root
cd "$PROJECT_ROOT"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✓ Python 3 found"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip."
    exit 1
fi

echo "✓ pip3 found"

# Install dependencies
echo ""
echo "Installing dependencies..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✓ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Create necessary directories
echo ""
echo "Creating necessary directories..."
mkdir -p templates static VerifoneWorkOrders data/logs

echo "✓ Directories created"

# Check if .env exists
if [ ! -f .env ]; then
    echo ""
    echo "⚠️  Warning: .env file not found"
    echo "   Please create a .env file with your credentials"
    echo "   You can update credentials later from the web interface"
fi

# Start the server
echo ""
echo "=================================="
echo "Starting Flask Server..."
echo "=================================="
echo ""
echo "Access the application at:"
echo "  → http://localhost:8080"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 app/app.py
