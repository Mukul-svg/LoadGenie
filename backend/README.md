# LoadGenie Backend

> 🚀 **Restructured Backend** - Professional Python project structure with proper separation of concerns

AI-powered k6 load testing script generator using Google's Gemini AI.

## 📁 Project Structure

```
backend/
├── app/                    # Main application package
│   ├── __init__.py
│   ├── main.py            # FastAPI application factory
│   ├── api/               # API routes
│   │   ├── __init__.py
│   │   ├── script_routes.py   # Script generation endpoints
│   │   └── health_routes.py   # Health check endpoints
│   ├── core/              # Core configuration
│   │   ├── __init__.py
│   │   ├── config.py      # Application settings
│   │   └── logging.py     # Logging configuration
│   ├── models/            # Data models
│   │   ├── __init__.py
│   │   └── schemas.py     # Pydantic models
│   └── services/          # Business logic
│       ├── __init__.py
│       └── ai_service.py  # AI service implementation
├── tests/                 # Test suite
│   ├── __init__.py
│   ├── test_integration.py
│   └── test_endpoints.py
├── scripts/               # Utility scripts
│   └── start.sh          # Full startup script with tests
├── docs/                  # Documentation
│   └── README.md         # Detailed documentation
├── main.py               # Application entry point
├── run.sh                # Quick start script
├── requirements.txt      # Dependencies
├── Dockerfile           # Container configuration
├── .env.example         # Environment template
└── .env                 # Environment variables
```

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Google Gemini API key

### Option 1: Quick Start (Recommended for Development)
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# 3. Start the server (with auto-reload)
./run.sh
```

### Option 2: Full Setup with Tests
```bash
# Run the complete startup script with tests
./scripts/start.sh
```

### Option 3: Manual Start
```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env file

# Start with uvicorn (development mode with auto-reload)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Or start with Python (production mode)
python main.py
```

## 📊 API Endpoints

### Generate Script (Unified)
- **POST** `/generate-script` - Handles both JSON and form data
- **POST** `/api/generate-script` - Unified endpoint (recommended)
- **POST** `/generate-script-form` - Form data only

### Health Check
- **GET** `/health` - Service health status

### Documentation
- **GET** `/docs` - Interactive API documentation
- **GET** `/redoc` - ReDoc documentation

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test
python tests/test_integration.py
python tests/test_endpoints.py
```

## ⚙️ Configuration

Environment variables in `.env`:
```bash
# Required
GEMINI_API_KEY=your_api_key_here

# Optional
DEBUG=False
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000
AI_TEMPERATURE=0.8
AI_MAX_RETRIES=3
AI_TIMEOUT=60
CORS_ORIGINS=*
```

## 🐳 Docker

```bash
# Build and run
docker build -t loadgenie-backend .
docker run -p 8000:8000 --env-file .env loadgenie-backend

# Using docker-compose
docker-compose up backend
```

## 📈 Features

- ✅ **Clean Architecture** - Proper separation of concerns
- ✅ **Type Safety** - Full Pydantic model validation
- ✅ **Error Handling** - Comprehensive error management
- ✅ **Logging** - Structured logging with configurable levels
- ✅ **Testing** - Integration and unit tests
- ✅ **Documentation** - Auto-generated API docs
- ✅ **Configuration** - Environment-based configuration
- ✅ **Docker Ready** - Container support
- ✅ **Multi-format Support** - JSON and form data endpoints
- ✅ **Auto-reload** - Development server with hot reloading

## 🔧 Development

### Startup Options

1. **Quick Development** (`./run.sh`):
   - Fast startup
   - Auto-reload on file changes
   - Skip tests for rapid development

2. **Full Testing** (`./scripts/start.sh`):
   - Run all tests first
   - Complete environment validation
   - Production-ready verification

3. **Manual Control**:
   - `uvicorn app.main:app --reload` (development)
   - `python main.py` (production)

### Project Philosophy
- **Single Responsibility** - Each module has a clear purpose
- **Dependency Injection** - Services are properly isolated
- **Configuration Management** - Centralized settings
- **Error Handling** - Consistent error responses
- **Type Safety** - Full type hints and validation

### Adding New Features
1. **Models** - Add to `app/models/schemas.py`
2. **Services** - Add to `app/services/`
3. **Routes** - Add to `app/api/`
4. **Tests** - Add to `tests/`
5. **Configuration** - Update `app/core/config.py`

## 📚 Documentation

For detailed documentation, see [docs/README.md](docs/README.md)

## 🎯 Migration from Old Structure

The old flat structure has been reorganized into a professional Python package:
- `main.py` → `app/main.py` (application factory)
- `ai_service.py` → `app/services/ai_service.py`
- Models extracted to `app/models/schemas.py`
- Configuration centralized in `app/core/config.py`
- Tests moved to `tests/` directory
- Scripts moved to `scripts/` directory

**No API changes** - all endpoints work exactly the same! 🎉

## 🚨 Troubleshooting

### Server Stops Immediately
- Use `./run.sh` or `uvicorn app.main:app --reload` for development
- The `--reload` flag keeps the server running and watching for changes

### Import Errors
- Make sure you're running from the backend root directory
- Ensure virtual environment is activated
- Check that all dependencies are installed: `pip install -r requirements.txt`

### Environment Issues
- Verify `.env` file exists and contains `GEMINI_API_KEY`
- Check that API key is valid and not the placeholder value
