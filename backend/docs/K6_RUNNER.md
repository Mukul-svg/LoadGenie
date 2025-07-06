# K6 Test Runner Service

A comprehensive service for executing K6 load tests locally and analyzing results with AI-powered anomaly detection.

## Features

- 🚀 **Local K6 Execution**: Run K6 scripts via Python subprocess
- 📊 **Metrics Capture**: Parse and analyze K6 JSON output
- 🤖 **AI Anomaly Detection**: AI-powered analysis of test results
- 📁 **Result Storage**: SQLite database + JSON file backup
- 🔍 **Search & History**: Query test history and search by criteria
- 📈 **Statistics**: Anomaly rates and performance trends
- 🔄 **REST API**: Complete API for test execution and management

## Quick Start

### Prerequisites

1. **Python 3.8+** with FastAPI and dependencies
2. **K6** installed and accessible in PATH
3. **Gemini API Key** for AI analysis

### Setup

1. **Install K6 (if not already installed):**
   ```bash
   # Run the setup script
   cd backend && ./scripts/setup_k6_runner.sh
   ```

2. **Configure environment:**
   ```bash
   # Update .env file with your Gemini API key
   echo "GEMINI_API_KEY=your_actual_api_key_here" >> .env
   ```

3. **Start the service:**
   ```bash
   cd backend
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Demo

Run the demo script to see the service in action:

```bash
cd backend
python scripts/demo_k6_runner.py
```

## API Endpoints

### Test Execution

#### `POST /api/v1/test/run`
Execute a K6 test script with optional parameters.

**Request:**
```json
{
  "script": "import http from 'k6/http'; export default function() { http.get('https://api.example.com'); }",
  "options": {
    "vus": 10,
    "duration": "30s"
  }
}
```

**Response:**
```json
{
  "test_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-07-06T12:34:56.789Z",
  "execution_time": 32.5,
  "metrics": {
    "response_time_avg": 250.5,
    "response_time_p95": 450.0,
    "error_rate": 2.1,
    "requests_per_second": 15.7,
    "virtual_users": 10,
    "total_requests": 500,
    "duration_ms": 30000.0
  },
  "anomaly_analysis": {
    "anomalies_detected": false,
    "severity": "low",
    "issues": [],
    "recommendations": ["Test results look good"],
    "confidence": 0.85
  },
  "status": "completed"
}
```

### Test History & Results

#### `GET /api/v1/test/history?limit=20`
Get recent test execution history.

#### `GET /api/v1/test/results/{test_id}`
Get detailed results for a specific test execution.

#### `GET /api/v1/test/search?anomalies_only=true&min_error_rate=5.0`
Search tests by criteria (anomalies, error rates, response times).

### Statistics

#### `GET /api/v1/test/statistics?days=7`
Get anomaly detection statistics and trends.

**Response:**
```json
{
  "period_days": 7,
  "total_tests": 45,
  "anomaly_tests": 8,
  "anomaly_rate": 0.178,
  "severity_breakdown": {
    "low": 3,
    "medium": 4,
    "high": 1
  }
}
```

### Health Check

#### `GET /api/v1/test/health`
Check K6 installation and service health.

## K6 Script Examples

### Basic HTTP GET Test
```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
    vus: 10,
    duration: '30s',
};

export default function() {
    const response = http.get('https://api.example.com/users');
    
    check(response, {
        'status is 200': (r) => r.status === 200,
        'response time < 500ms': (r) => r.timings.duration < 500,
    });
    
    sleep(1);
}
```

### API Testing with Authentication
```javascript
import http from 'k6/http';
import { check } from 'k6';

export const options = {
    vus: 5,
    duration: '1m',
};

export default function() {
    // Login and get token
    const loginResponse = http.post('https://api.example.com/auth/login', {
        username: 'testuser',
        password: 'testpass'
    });
    
    const token = loginResponse.json('token');
    
    // Use token for authenticated request
    const headers = { 'Authorization': `Bearer ${token}` };
    const response = http.get('https://api.example.com/protected', { headers });
    
    check(response, {
        'authenticated successfully': (r) => r.status === 200,
        'has user data': (r) => r.json('user') !== null,
    });
}
```

### Load Testing with Stages
```javascript
import http from 'k6/http';
import { check } from 'k6';

export const options = {
    stages: [
        { duration: '2m', target: 10 }, // Ramp up
        { duration: '5m', target: 10 }, // Stay at 10 users
        { duration: '2m', target: 20 }, // Ramp up to 20
        { duration: '5m', target: 20 }, // Stay at 20 users
        { duration: '2m', target: 0 },  // Ramp down
    ],
};

export default function() {
    const response = http.get('https://api.example.com/heavy-endpoint');
    
    check(response, {
        'status is 200': (r) => r.status === 200,
        'response time < 2000ms': (r) => r.timings.duration < 2000,
    });
}
```

## Anomaly Detection

The AI-powered anomaly detection analyzes test results for:

### Performance Issues
- **High Error Rates**: >5% error rate triggers warnings
- **Slow Response Times**: >2s average response time
- **Low Throughput**: Poor requests/second relative to virtual users
- **Response Time Spikes**: High P95 response times

### AI Analysis
The service uses Google Gemini to analyze results and provide:
- **Severity Assessment**: low/medium/high/critical
- **Specific Issues**: Detailed problem identification
- **Recommendations**: Actionable next steps
- **Confidence Score**: Analysis reliability (0.0-1.0)

### Rule-based Fallback
If AI analysis fails, rule-based detection provides:
- Error rate thresholds (5%, 10%)
- Response time limits (2s, 3s)
- Throughput efficiency checks

## Data Storage

### SQLite Database
- Complete test results and metrics
- Searchable history with indexes
- Anomaly statistics and trends
- Automatic cleanup of old records

### JSON Backup Files
- Local file backup in `K6_RESULTS_DIR`
- Human-readable test results
- Fallback if database is unavailable

## Configuration

Environment variables in `.env`:

```bash
# K6 Runner settings
K6_RESULTS_DIR=/tmp/k6_results
K6_TIMEOUT=300

# AI Service
GEMINI_API_KEY=your_api_key_here
AI_MODEL=gemini-2.0-flash-exp
AI_TEMPERATURE=0.8

# Database
DATABASE_URL=sqlite:///./loadgenie.db

# Server
DEBUG=true
HOST=0.0.0.0
PORT=8000
```

## Testing

### Unit Tests
```bash
cd backend
python -m pytest tests/test_k6_runner.py -v
```

### Integration Tests
```bash
# Requires K6 installation
cd backend
python tests/test_integration_k6.py
```

### Sample Tests
Run predefined test scenarios:
```bash
cd backend
python scripts/demo_k6_runner.py
```

## Error Handling

### K6 Installation Issues
- **Missing K6**: Returns 503 status with installation instructions
- **K6 Execution Failure**: Captures stderr and returns detailed error

### Script Validation
- **Syntax Errors**: Captured during K6 execution
- **Runtime Errors**: Logged with full console output
- **Timeout**: Configurable execution timeout

### AI Service Failures
- **API Errors**: Falls back to rule-based anomaly detection
- **Rate Limits**: Exponential backoff with retries
- **Invalid Responses**: Graceful degradation to heuristics

## Performance Considerations

### Resource Usage
- **Memory**: ~50MB base + K6 execution overhead
- **CPU**: Subprocess execution for K6 tests
- **Disk**: JSON results + SQLite database storage

### Scalability
- **Concurrent Tests**: Limited by system resources
- **History Storage**: Automatic cleanup of old records
- **Database**: SQLite suitable for development/small teams

### Optimization Tips
- Use shorter test durations for development
- Clean up old test results regularly
- Monitor K6_RESULTS_DIR disk usage
- Set appropriate K6_TIMEOUT values

## Troubleshooting

### Common Issues

**K6 not found:**
```bash
# Install K6 first
./scripts/setup_k6_runner.sh
```

**Permission denied:**
```bash
# Check K6 executable permissions
which k6
ls -la $(which k6)
```

**Database errors:**
```bash
# Check SQLite database permissions
ls -la loadgenie.db
# Reset database if needed
rm loadgenie.db
```

**AI service errors:**
```bash
# Check API key
echo $GEMINI_API_KEY
# Verify AI service connectivity
curl -H "Authorization: Bearer $GEMINI_API_KEY" https://api.gemini.com/v1/models
```

### Debug Mode
Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python -m uvicorn app.main:app --reload
```

### Log Files
Check application logs:
```bash
# Application logs
tail -f logs/loadgenie.log

# K6 execution logs (in test results)
cat /tmp/k6_results/test_*_results.json | jq .console_output
```

## Contributing

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Add tests**: Ensure new features have test coverage
4. **Run tests**: `python -m pytest tests/ -v`
5. **Submit pull request**

## License

This project is part of LoadGenie - see main project LICENSE for details.

---

🚀 **Happy Load Testing!**

For more information, visit the main LoadGenie documentation or open an issue on GitHub.
