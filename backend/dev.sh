#!/bin/bash

# Development server with detailed logging
echo "🚀 LoadGenie Development Server"
echo "==============================="
echo ""
echo "Features enabled:"
echo "  ✅ Auto-reload on file changes"
echo "  ✅ Debug logging"
echo "  ✅ CORS enabled for development"
echo ""
echo "Available endpoints:"
echo "  🌐 API: http://localhost:8000"
echo "  📖 Docs: http://localhost:8000/docs"
echo "  📚 ReDoc: http://localhost:8000/redoc"
echo "  ❤️  Health: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo "==============================="
echo ""

# Start with verbose logging and reload
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --reload-dir app \
    --log-level info \
    --access-log
