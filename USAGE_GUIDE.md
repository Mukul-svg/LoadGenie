# LoadGenie K6 Runner - Usage Guide

LoadGenie is a FastAPI service that allows you to execute K6 load tests and get AI-powered analysis of the results. Here's how to use it:

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.12+
- K6 installed ([Download from k6.io](https://k6.io/docs/getting-started/installation/))
- Google AI API key (optional, for AI analysis)

### 2. Installation & Setup

```bash
# Clone and navigate to the project
cd /home/solo/Documents/Projects/LoadGenie/backend

# Install dependencies
pip install -r requirements.txt

# Set up environment variables (optional)
export GOOGLE_API_KEY="your-gemini-api-key"  # For AI analysis
export LOG_LEVEL="INFO"
export DEBUG="False"

# Start the service
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Verify Installation

```bash
# Check if K6 is installed
k6 version

# Test the service
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/test/health
```

## 📊 Using the API

### 1. Generate K6 Scripts with AI

**The most powerful feature** - Generate K6 test scripts from natural language descriptions:

**Basic Script Generation:**
```bash
curl -X POST "http://localhost:8000/generate-script" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_description": "Test a REST API with 10 users for 30 seconds, checking login endpoint"
  }'
```

**Advanced Script Generation Examples:**
```bash
# E-commerce load test
curl -X POST "http://localhost:8000/generate-script" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_description": "Test an e-commerce site with 50 users browsing products, adding items to cart, and checking out. Include authentication and payment flow simulation."
  }'

# API stress test
curl -X POST "http://localhost:8000/generate-script" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_description": "Stress test a GraphQL API with complex queries, starting with 10 users and ramping up to 100 users over 2 minutes"
  }'

# Database performance test
curl -X POST "http://localhost:8000/generate-script" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_description": "Test database performance with concurrent read/write operations, simulating 25 users performing CRUD operations on user profiles"
  }'
```

### 2. Run a Load Test

**Basic Test:**
```bash
curl -X POST "http://localhost:8000/api/v1/test/run" \
  -H "Content-Type: application/json" \
  -d '{
    "script": "import http from '\''k6/http'\''; export default function() { http.get('\''https://httpbin.org/get'\''); }",
    "options": {
      "vus": 5,
      "duration": "10s"
    }
  }'
```

**Advanced Test with Custom Options:**
```bash
curl -X POST "http://localhost:8000/api/v1/test/run" \
  -H "Content-Type: application/json" \
  -d '{
    "script": "import http from '\''k6/http'\''; import { check } from '\''k6'\''; export const options = { vus: 10, duration: '\''30s'\'' }; export default function() { const res = http.get('\''https://httpbin.org/get'\''); check(res, { '\''status is 200'\'': (r) => r.status === 200 }); }",
    "options": {
      "vus": 10,
      "duration": "30s"
    }
  }'
```

### 3. View Test History

```bash
# Get recent test history
curl "http://localhost:8000/api/v1/test/history?limit=10"

# Get test statistics
curl "http://localhost:8000/api/v1/test/statistics"
```

### 4. Search Tests

```bash
# Search for tests with anomalies
curl "http://localhost:8000/api/v1/test/search?anomalies_only=true"

# Search for tests with high error rates
curl "http://localhost:8000/api/v1/test/search?min_error_rate=5.0"

# Search for tests with slow response times
curl "http://localhost:8000/api/v1/test/search?max_response_time=2000"
```

### 5. Get Detailed Results

```bash
# Get detailed results for a specific test
curl "http://localhost:8000/api/v1/test/results/{test_id}"
```

## 🐍 Using Python Client

### Example Python Script:

```python
import requests
import json

# Service URL
BASE_URL = "http://localhost:8000/api/v1"

def generate_k6_script(description):
    """Generate a K6 script from natural language description"""
    
    payload = {
        "scenario_description": description
    }
    
    response = requests.post("http://localhost:8000/generate-script", json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Script generated successfully!")
        print(f"📝 Description: {result['scenario_description']}")
        print(f"⏰ Generated at: {result['generated_at']}")
        print(f"\n📋 Generated K6 Script:")
        print("=" * 50)
        print(result['script'])
        print("=" * 50)
        return result['script']
    else:
        print(f"❌ Script generation failed: {response.status_code}")
        print(f"   Error: {response.text}")
        return None

def run_load_test(script, vus=5, duration="10s"):
    """Run a K6 load test"""
    
    payload = {
        "script": script,
        "options": {
            "vus": vus,
            "duration": duration
        }
    }
    
    response = requests.post(f"{BASE_URL}/test/run", json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Test completed: {result['test_id']}")
        print(f"📊 Metrics:")
        print(f"   - Response Time: {result['metrics']['response_time_avg']:.0f}ms")
        print(f"   - Error Rate: {result['metrics']['error_rate']:.1f}%")
        print(f"   - Throughput: {result['metrics']['requests_per_second']:.1f} RPS")
        
        # Check for anomalies
        anomaly = result['anomaly_analysis']
        if anomaly['anomalies_detected']:
            print(f"⚠️  Anomalies detected ({anomaly['severity']} severity):")
            for issue in anomaly['issues']:
                print(f"   - {issue}")
        else:
            print("✅ No anomalies detected")
            
        return result
    else:
        print(f"❌ Test failed: {response.text}")
        return None

# Example usage - Complete workflow with AI script generation
description = "Test a REST API for user authentication with 15 users for 45 seconds, including login, profile access, and logout"

# Step 1: Generate the script with AI
script = generate_k6_script(description)

if script:
    # Step 2: Run the generated script
    result = run_load_test(script, vus=15, duration="45s")
    
# Alternative: Use a manual script
manual_script = """
import http from 'k6/http';
import { check } from 'k6';

export default function() {
    const response = http.get('https://httpbin.org/get');
    check(response, {
        'status is 200': (r) => r.status === 200,
        'response time < 2000ms': (r) => r.timings.duration < 2000,
    });
}
"""

# Run the manual test
result = run_load_test(manual_script, vus=10, duration="30s")
```

## 🎯 Example Use Cases

### 1. Complete AI-Powered Workflow

**Step 1: Generate Script from Description**
```bash
curl -X POST "http://localhost:8000/generate-script" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_description": "Test an e-commerce checkout flow with 20 users, including product browsing, cart operations, and payment processing over 60 seconds"
  }'
```

**Step 2: Use Generated Script in Test**
```bash
# Take the generated script and use it in the test run endpoint
curl -X POST "http://localhost:8000/api/v1/test/run" \
  -H "Content-Type: application/json" \
  -d '{
    "script": "[GENERATED_SCRIPT_FROM_STEP_1]",
    "options": {
      "vus": 20,
      "duration": "60s"
    }
  }'
```

### 2. API Performance Testing

```javascript
// K6 script for API testing
import http from 'k6/http';
import { check } from 'k6';

export const options = {
    vus: 50,
    duration: '2m',
};

export default function() {
    const response = http.get('https://your-api.com/endpoint');
    
    check(response, {
        'status is 200': (r) => r.status === 200,
        'response time < 500ms': (r) => r.timings.duration < 500,
    });
}
```

### 2. Load Testing with Ramp-up

```javascript
import http from 'k6/http';

export const options = {
    stages: [
        { duration: '1m', target: 10 },  // Ramp up
        { duration: '3m', target: 50 },  // Stay at 50 users
        { duration: '1m', target: 0 },   // Ramp down
    ],
};

export default function() {
    http.get('https://your-app.com');
}
```

### 3. Stress Testing

```javascript
import http from 'k6/http';

export const options = {
    vus: 100,
    duration: '5m',
    thresholds: {
        http_req_duration: ['p(95)<2000'], // 95% under 2s
        http_req_failed: ['rate<0.05'],    // Error rate under 5%
    },
};

export default function() {
    http.get('https://your-app.com/heavy-endpoint');
}
```

## 🔧 Configuration

### Environment Variables

```bash
# Required for AI analysis
export GOOGLE_API_KEY="your-gemini-api-key"

# Optional configuration
export LOG_LEVEL="INFO"          # DEBUG, INFO, WARNING, ERROR
export DEBUG="False"             # True for development
export K6_RESULTS_DIR="/tmp/k6"  # Where to store results
```

### API Response Format

```json
{
    "test_id": "uuid",
    "timestamp": "2025-07-06T13:00:00",
    "status": "completed",
    "execution_time": 12.34,
    "metrics": {
        "response_time_avg": 250.5,
        "response_time_p95": 450.2,
        "error_rate": 2.1,
        "requests_per_second": 45.3,
        "virtual_users": 10,
        "total_requests": 453
    },
    "anomaly_analysis": {
        "anomalies_detected": false,
        "severity": "low",
        "issues": [],
        "recommendations": ["Test results look good"],
        "confidence": 0.85
    }
}
```

## 🧪 Testing & Validation

### Run Demo Scripts

```bash
# Run the demo script
python scripts/demo_k6_runner.py

# Validate the service
python scripts/validate_k6_service.py

# Test API endpoints
python scripts/test_api.py
```

### Run Test Suite

```bash
# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/test_k6_runner.py -v          # Unit tests
pytest tests/test_integration_k6.py -v     # Integration tests
```

## 📈 Monitoring & Analysis

The service provides built-in monitoring and analysis:

1. **Real-time Metrics**: Response times, error rates, throughput
2. **AI-Powered Anomaly Detection**: Automatic issue identification
3. **Historical Analysis**: Trend analysis and comparisons
4. **Persistent Storage**: SQLite database for long-term storage
5. **Search & Filtering**: Find tests by criteria

## 🚨 Troubleshooting

### Common Issues

1. **K6 not found**: Make sure K6 is installed and in PATH
2. **Permission errors**: Check file permissions in results directory
3. **Network timeouts**: Tests may timeout on slow networks
4. **AI analysis fails**: Check Google API key or rely on rule-based fallback

### Health Checks

```bash
# Check service health
curl http://localhost:8000/api/v1/health

# Check K6 runner health
curl http://localhost:8000/api/v1/test/health
```

## 🎉 Next Steps

1. **Customize Scripts**: Create your own K6 scripts for your specific use case
2. **Set up Monitoring**: Use the history and search APIs to monitor trends
3. **Integrate with CI/CD**: Add load testing to your deployment pipeline
4. **Scale Up**: Run more complex scenarios with multiple stages

For more examples and advanced usage, check the `scripts/` directory and test files.
