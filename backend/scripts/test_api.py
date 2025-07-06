#!/usr/bin/env python3
"""
Simple API test script for K6 Runner Service
"""

import requests
import json
import time
import sys
from pathlib import Path

def test_api_endpoints():
    """Test the K6 runner API endpoints"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing K6 Runner API Endpoints")
    print("=" * 40)
    
    # Test 1: Health endpoint
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/api/v1/test/health", timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {data.get('status', 'unknown')}")
        else:
            print(f"   Error: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Connection failed: {e}")
        print("   Make sure the server is running: python -m uvicorn app.main:app --reload")
        return False
    
    # Test 2: History endpoint
    print("\n2. Testing history endpoint...")
    try:
        response = requests.get(f"{base_url}/api/v1/test/history?limit=3", timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Found {data.get('total_count', 0)} tests in history")
            if data.get('tests'):
                latest = data['tests'][0]
                print(f"   Latest test: {latest['test_id'][:8]}... ({latest['metrics']['response_time_avg']:.1f}ms avg)")
        else:
            print(f"   Error: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request failed: {e}")
    
    # Test 3: Statistics endpoint
    print("\n3. Testing statistics endpoint...")
    try:
        response = requests.get(f"{base_url}/api/v1/test/statistics?days=7", timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Stats: {data.get('total_tests', 0)} tests, {data.get('anomaly_tests', 0)} with anomalies")
            if data.get('total_tests', 0) > 0:
                anomaly_rate = data.get('anomaly_rate', 0) * 100
                print(f"   Anomaly rate: {anomaly_rate:.1f}%")
        else:
            print(f"   Error: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request failed: {e}")
    
    # Test 4: Run a simple K6 test (optional - only if user wants to test execution)
    print("\n4. Testing K6 script execution (optional)...")
    run_test = input("   Run a test K6 script? (y/N): ").lower().strip()
    
    if run_test in ['y', 'yes']:
        simple_script = '''
import http from 'k6/http';
import { check } from 'k6';

export const options = {
    vus: 2,
    duration: '5s',
};

export default function() {
    const response = http.get('https://httpbin.org/get');
    check(response, {
        'status is 200': (r) => r.status === 200,
    });
}
'''
        
        test_payload = {
            "script": simple_script,
            "options": {
                "vus": 2,
                "duration": "5s"
            }
        }
        
        print("   Executing test script...")
        try:
            response = requests.post(
                f"{base_url}/api/v1/test/run", 
                json=test_payload, 
                timeout=30
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Test ID: {data['test_id'][:8]}...")
                print(f"   Execution time: {data['execution_time']:.1f}s")
                metrics = data['metrics']
                print(f"   Results: {metrics['total_requests']} requests, {metrics['response_time_avg']:.1f}ms avg")
                anomaly = data['anomaly_analysis']
                print(f"   Anomalies: {anomaly['anomalies_detected']} (severity: {anomaly['severity']})")
            else:
                print(f"   Error: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Test execution failed: {e}")
    
    print("\n✅ API endpoint testing completed!")
    return True

def check_server_status():
    """Check if the server is running"""
    try:
        response = requests.get("http://localhost:8000/docs", timeout=2)
        return response.status_code == 200
    except:
        return False

def main():
    """Main function"""
    print("🔍 K6 Runner API Test")
    print("=" * 30)
    
    # Check if server is running
    if not check_server_status():
        print("❌ Server not running on localhost:8000")
        print("\nTo start the server:")
        print("cd /home/solo/Documents/Projects/LoadGenie/backend")
        print("python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        print("\nThen run this script again.")
        return
    
    print("✅ Server is running")
    print("📚 API docs available at: http://localhost:8000/docs")
    print()
    
    # Run tests
    success = test_api_endpoints()
    
    if success:
        print("\n🎉 All tests completed successfully!")
        print("\nNext steps:")
        print("1. Check the API documentation: http://localhost:8000/docs")
        print("2. Run more demo tests: python scripts/demo_k6_runner.py")
        print("3. Explore test history and results in the database")
    else:
        print("\n❌ Some tests failed - check the server logs")

if __name__ == "__main__":
    main()
