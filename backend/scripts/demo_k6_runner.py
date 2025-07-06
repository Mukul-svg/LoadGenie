#!/usr/bin/env python3
"""
Sample script to demonstrate K6 runner functionality
"""

import asyncio
import json
from pathlib import Path
import sys

# Add the parent directory to the path so we can import the app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.ai_service import AIService
from app.services.k6_runner import K6Runner
from app.core.logging import setup_logging, get_logger

# Sample K6 scripts for testing
SAMPLE_SCRIPTS = [
    {
        "name": "Basic HTTP GET Test",
        "script": """
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
    vus: 5,
    duration: '15s',
};

export default function() {
    const response = http.get('https://httpbin.org/get');
    
    check(response, {
        'status is 200': (r) => r.status === 200,
        'response time < 1000ms': (r) => r.timings.duration < 1000,
    });
    
    sleep(0.5);
}
""",
        "options": {"vus": 5, "duration": "15s"}
    },
    {
        "name": "API POST Test",
        "script": """
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
    vus: 3,
    duration: '20s',
};

export default function() {
    const payload = JSON.stringify({
        name: 'Load Test User',
        email: 'loadtest@example.com',
        timestamp: new Date().toISOString()
    });
    
    const params = {
        headers: {
            'Content-Type': 'application/json',
        },
    };
    
    const response = http.post('https://httpbin.org/post', payload, params);
    
    check(response, {
        'status is 200': (r) => r.status === 200,
        'has correct email': (r) => r.json().json.email === 'loadtest@example.com',
        'response time < 2000ms': (r) => r.timings.duration < 2000,
    });
    
    sleep(1);
}
""",
        "options": {"vus": 3, "duration": "20s"}
    },
    {
        "name": "Mixed Scenario Test (with errors)",
        "script": """
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
    vus: 4,
    duration: '10s',
};

const scenarios = [
    'https://httpbin.org/get',
    'https://httpbin.org/status/404',  // Will cause errors
    'https://httpbin.org/delay/2',     // Slow response
    'https://httpbin.org/status/500',  // Server error
];

export default function() {
    // Randomly pick a scenario (including error-prone ones)
    const url = scenarios[Math.floor(Math.random() * scenarios.length)];
    const response = http.get(url);
    
    check(response, {
        'request completed': (r) => r.status !== 0,
        'not too slow': (r) => r.timings.duration < 3000,
    });
    
    sleep(0.3);
}
""",
        "options": {"vus": 4, "duration": "10s"}
    }
]

async def run_sample_tests():
    """Run sample K6 tests to demonstrate the service"""
    
    # Setup logging
    setup_logging("INFO")
    logger = get_logger(__name__)
    
    logger.info("🚀 Starting K6 Runner demonstration")
    
    try:
        # Initialize services
        ai_service = AIService()
        k6_runner = K6Runner(ai_service)
        
        logger.info("✅ Services initialized successfully")
        
        # Run each sample test
        results = []
        
        for i, sample in enumerate(SAMPLE_SCRIPTS, 1):
            logger.info(f"\n📊 Running test {i}/{len(SAMPLE_SCRIPTS)}: {sample['name']}")
            
            try:
                result = await k6_runner.run_test(
                    script_content=sample['script'],
                    options=sample.get('options')
                )
                
                results.append(result)
                
                # Log key metrics
                metrics = result['metrics']
                anomaly = result['anomaly_analysis']
                
                logger.info(f"  ✅ Test completed in {result['execution_time']:.1f}s")
                logger.info(f"  📈 Metrics:")
                logger.info(f"    - Virtual Users: {metrics['virtual_users']}")
                logger.info(f"    - Total Requests: {metrics['total_requests']}")
                logger.info(f"    - Avg Response Time: {metrics['response_time_avg']:.1f}ms")
                logger.info(f"    - P95 Response Time: {metrics['response_time_p95']:.1f}ms")
                logger.info(f"    - Error Rate: {metrics['error_rate']:.1f}%")
                logger.info(f"    - Throughput: {metrics['requests_per_second']:.1f} RPS")
                
                logger.info(f"  🔍 Anomaly Analysis:")
                logger.info(f"    - Anomalies Detected: {anomaly['anomalies_detected']}")
                logger.info(f"    - Severity: {anomaly['severity']}")
                logger.info(f"    - Confidence: {anomaly['confidence']:.2f}")
                
                if anomaly['issues']:
                    logger.info(f"    - Issues: {', '.join(anomaly['issues'])}")
                
                if anomaly['recommendations']:
                    logger.info(f"    - Recommendations: {', '.join(anomaly['recommendations'])}")
                
            except Exception as e:
                logger.error(f"  ❌ Test failed: {e}")
                continue
        
        # Summary
        logger.info(f"\n📋 Test Summary:")
        logger.info(f"  - Total tests run: {len(results)}")
        
        anomaly_count = sum(1 for r in results if r['anomaly_analysis']['anomalies_detected'])
        logger.info(f"  - Tests with anomalies: {anomaly_count}")
        
        if results:
            avg_response_time = sum(r['metrics']['response_time_avg'] for r in results) / len(results)
            avg_error_rate = sum(r['metrics']['error_rate'] for r in results) / len(results)
            
            logger.info(f"  - Average response time: {avg_response_time:.1f}ms")
            logger.info(f"  - Average error rate: {avg_error_rate:.1f}%")
        
        # Get test history
        logger.info(f"\n📚 Recent test history:")
        history = await k6_runner.get_test_history(limit=5)
        
        for i, test in enumerate(history[:3], 1):  # Show last 3
            logger.info(f"  {i}. {test['test_id'][:8]}... - "
                       f"{test['metrics']['response_time_avg']:.0f}ms avg, "
                       f"{test['metrics']['error_rate']:.1f}% errors")
        
        logger.info(f"\n🎉 Demonstration completed successfully!")
        logger.info(f"📁 Results saved to: {k6_runner.results_dir}")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Demonstration failed: {e}")
        raise

async def main():
    """Main function"""
    try:
        results = await run_sample_tests()
        
        # Save summary to file
        summary_file = Path(__file__).parent / "sample_test_results.json"
        with open(summary_file, 'w') as f:
            json.dump({
                "total_tests": len(results),
                "tests": [
                    {
                        "test_id": r["test_id"],
                        "timestamp": r["timestamp"],
                        "metrics": r["metrics"],
                        "anomaly_analysis": r["anomaly_analysis"]
                    }
                    for r in results
                ]
            }, f, indent=2, default=str)
        
        print(f"\n📄 Summary saved to: {summary_file}")
        
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
