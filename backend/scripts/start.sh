#!/bin/bash

# LoadGenie Backend Startup Script

set -e

echo "🚀 Starting LoadGenie Backend..."

# Change to backend directory (script is in scripts/ subdirectory)
cd "$(dirname "$0")/.."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Copying from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env file and add your GEMINI_API_KEY"
    echo "   Then run this script again."
    exit 1
fi

# Load environment variables
source .env

# Check if GEMINI_API_KEY is set
if [ -z "$GEMINI_API_KEY" ] || [ "$GEMINI_API_KEY" = "your_gemini_api_key_here" ]; then
    echo "❌ GEMINI_API_KEY is not set properly in .env file"
    echo "   Please add your actual Gemini API key to the .env file"
    exit 1
fi

echo "✅ Environment configured successfully"

# Run tests
echo "🧪 Running integration tests..."
python -m pytest tests/ -v

if [ $? -eq 0 ]; then
    echo "✅ All tests passed!"
    
    # Start the server
    echo "🌟 Starting LoadGenie API server..."
    echo "   API will be available at: http://localhost:8000"
    echo "   API docs will be available at: http://localhost:8000/docs"
    echo "   Press Ctrl+C to stop"
    echo ""
    
    # Use uvicorn with reload for development
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
else
    echo "❌ Tests failed. Please check the configuration."
    exit 1
fi
