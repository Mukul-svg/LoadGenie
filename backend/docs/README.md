# LoadGenie Backend

AI-powered k6 load testing script generator using Google's Gemini AI.

## Features

- 🤖 **AI-Powered Script Generation**: Uses Google Gemini AI to generate k6 load testing scripts
- 🔄 **Retry Logic**: Automatic retry with exponential backoff for reliability
- 📊 **Production-Ready**: Comprehensive error handling, logging, and monitoring
- 🚀 **FastAPI**: Modern, fast web framework with automatic API documentation
- 🐳 **Docker Support**: Container-ready with health checks
- 🧪 **Testing**: Built-in integration tests and validation
- 📝 **Comprehensive Logging**: Detailed logging for debugging and monitoring

## Quick Start

### Prerequisites

- Python 3.12+
- Google Gemini API key

### Setup

1. **Clone and navigate to the backend directory**:
   ```bash
   cd backend
   ```

2. **Run the startup script**:
   ```bash
   ./start.sh
   ```

   This script will:
   - Create a virtual environment
   - Install dependencies
   - Set up environment variables
   - Run tests
   - Start the server

3. **Set up your API key**:
   - Copy `.env.example` to `.env`
   - Add your `GEMINI_API_KEY` to the `.env` file

### Manual Setup

1. **Create virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env and add your GEMINI_API_KEY
   ```

4. **Run tests**:
   ```bash
   python test_integration.py
   ```

5. **Start the server**:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

## API Endpoints

### Generate Script (JSON)
```http
POST /generate-script
Content-Type: application/json

{
  "scenario_description": "Create a load test for a REST API with 50 users for 2 minutes"
}
```

### Generate Script (Form Data)
```http
POST /generate-script-form
Content-Type: multipart/form-data

scenario_description=Create a load test for a REST API with 50 users for 2 minutes
```

### Generate Script (Unified - Handles Both)
```http
POST /api/generate-script
Content-Type: application/json OR multipart/form-data

# JSON format:
{
  "scenario_description": "Create a load test for a REST API with 50 users for 2 minutes"
}

# OR Form data format:
scenario_description=Create a load test for a REST API with 50 users for 2 minutes
```

**Response** (All endpoints):
```json
{
  "script": "import http from 'k6/http';\n...",
  "generated_at": "2025-07-06 12:34:56",
  "scenario_description": "..."
}
```

### Health Check
```http
GET /health
```

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-07-06 12:34:56"
}
```

## Frontend Integration

The unified endpoint `/api/generate-script` is recommended for frontend applications as it automatically handles both JSON and form data submissions:

```javascript
// JSON submission
fetch('/api/generate-script', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ scenario_description: 'Your test description' })
})

// Form data submission
const formData = new FormData();
formData.append('scenario_description', 'Your test description');
fetch('/api/generate-script', {
  method: 'POST',
  body: formData
})
```

## API Documentation

Once the server is running, visit:
- **Interactive API docs**: http://localhost:8000/docs
- **ReDoc documentation**: http://localhost:8000/redoc

## Docker Support

### Build and run with Docker:
```bash
# Build the image
docker build -t loadgenie-backend .

# Run the container
docker run -p 8000:8000 --env-file .env loadgenie-backend
```

### Using Docker Compose:
```bash
# From the project root
docker-compose up backend
```

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `GEMINI_API_KEY` | Google Gemini AI API key | Yes | - |
| `DEBUG` | Enable debug mode | No | `False` |
| `LOG_LEVEL` | Logging level | No | `INFO` |

### AI Service Configuration

The AI service can be configured with:
- **Max Retries**: Number of retry attempts (default: 3)
- **Timeout**: Request timeout in seconds (default: 60)
- **Temperature**: AI creativity level (default: 0.8)

## Error Handling

The service includes comprehensive error handling:

- **AI Service Errors** (503): Issues with the AI service
- **Validation Errors** (400): Invalid input data
- **Server Errors** (500): Unexpected server issues

All errors include:
- Error message
- Detailed information
- Timestamp
- Request correlation

## Logging

Logs include:
- Request/response details
- Generation timing
- Error tracking
- AI service interactions

## Testing

### Integration Tests
```bash
python test_integration.py
```

### Test Cases
- Basic script generation
- Empty description handling
- Short description validation
- Mock response format validation

## Production Deployment

### Recommendations

1. **Environment Variables**: Use a secrets management system
2. **API Key Security**: Rotate keys regularly
3. **Rate Limiting**: Implement rate limiting for the API
4. **Monitoring**: Set up health checks and monitoring
5. **Scaling**: Use container orchestration for scaling

### Health Checks

The service includes health check endpoints for:
- Kubernetes liveness/readiness probes
- Load balancer health checks
- Monitoring systems

## Troubleshooting

### Common Issues

1. **API Key Issues**:
   ```
   ValueError: GEMINI_API_KEY environment variable is required
   ```
   - Ensure your `.env` file contains a valid `GEMINI_API_KEY`

2. **Connection Errors**:
   ```
   AIServiceError: Failed to connect to AI service
   ```
   - Check your internet connection
   - Verify API key is valid
   - Check Gemini API service status

3. **Import Errors**:
   ```
   ImportError: No module named 'google.genai'
   ```
   - Ensure all dependencies are installed: `pip install -r requirements.txt`

### Debug Mode

Enable debug mode for detailed logging:
```bash
export DEBUG=True
export LOG_LEVEL=DEBUG
```

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI App   │────│   AI Service     │────│  Google Gemini  │
│                 │    │                  │    │      API        │
│ • Endpoints     │    │ • Retry Logic    │    │                 │
│ • Validation    │    │ • Error Handling │    │ • Script Gen    │
│ • Error Handler │    │ • Logging        │    │ • JSON Response │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

[Your License Here]
