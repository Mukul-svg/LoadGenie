#!/bin/bash

# Quick start script for LoadGenie Backend
# This script starts the server directly without running tests

set -e

echo "🚀 LoadGenie Quick Start..."

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Copying from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env file and add your GEMINI_API_KEY"
    exit 1
fi

# Check if GEMINI_API_KEY is set
source .env
if [ -z "$GEMINI_API_KEY" ] || [ "$GEMINI_API_KEY" = "your_gemini_api_key_here" ]; then
    echo "❌ GEMINI_API_KEY is not set properly in .env file"
    echo "   Please add your actual Gemini API key to the .env file"
    exit 1
fi

echo "✅ Environment configured"
echo "🌟 Starting LoadGenie API server..."
echo "   API will be available at: http://localhost:8000"
echo "   API docs will be available at: http://localhost:8000/docs"
echo "   Press Ctrl+C to stop"
echo ""

# Start with uvicorn and reload
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
