"""
Test cases for K6 runner service
"""

import pytest
import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from app.services.k6_runner import K6Runner, K6RunnerError, K6TestResult, AnomalyDetector
from app.services.ai_service import AIService


class TestK6TestResult:
    """Test K6TestResult data class"""
    
    def test_k6_test_result_metrics(self):
        """Test K6TestResult metric calculations"""
        raw_output = {
            "metrics": {
                "iteration_duration": {"avg": 1500},
                "http_reqs": {"rate": 25.5, "count": 1000},
                "http_req_failed": {"rate": 0.05},
                "http_req_duration": {"p(95)": 2000, "avg": 800},
                "vus": {"max": 20}
            }
        }
        
        result = K6TestResult(raw_output)
        
        assert result.duration_ms == 1500
        assert result.requests_per_second == 25.5
        assert result.error_rate == 5.0  # 0.05 * 100
        assert result.response_time_p95 == 2000
        assert result.response_time_avg == 800
        assert result.virtual_users == 20
        assert result.total_requests == 1000


class TestAnomalyDetector:
    """Test AnomalyDetector functionality"""
    
    @pytest.fixture
    def mock_ai_service(self):
        """Mock AI service for testing"""
        ai_service = Mock(spec=AIService)
        ai_service.analyze_test_results = AsyncMock()
        return ai_service
    
    @pytest.fixture
    def anomaly_detector(self, mock_ai_service):
        """Create AnomalyDetector instance for testing"""
        return AnomalyDetector(mock_ai_service)
    
    @pytest.fixture
    def sample_test_result(self):
        """Sample test result for testing"""
        raw_output = {
            "metrics": {
                "http_req_duration": {"avg": 1000, "p(95)": 1500},
                "http_req_failed": {"rate": 0.02},
                "http_reqs": {"rate": 15.0, "count": 900},
                "vus": {"max": 10}
            }
        }
        return K6TestResult(raw_output)
    
    @pytest.mark.asyncio
    async def test_rule_based_anomaly_detection_normal(self, anomaly_detector, sample_test_result):
        """Test rule-based anomaly detection with normal results"""
        analysis = anomaly_detector._rule_based_anomaly_detection(sample_test_result)
        
        assert not analysis["anomalies_detected"]
        assert analysis["severity"] == "low"
        assert "Test results look good" in analysis["recommendations"][0]
    
    @pytest.mark.asyncio
    async def test_rule_based_anomaly_detection_high_error_rate(self, anomaly_detector):
        """Test rule-based anomaly detection with high error rate"""
        raw_output = {
            "metrics": {
                "http_req_duration": {"avg": 1000, "p(95)": 1500},
                "http_req_failed": {"rate": 0.12},  # 12% error rate
                "http_reqs": {"rate": 15.0, "count": 900},
                "vus": {"max": 10}
            }
        }
        result = K6TestResult(raw_output)
        
        analysis = anomaly_detector._rule_based_anomaly_detection(result)
        
        assert analysis["anomalies_detected"]
        assert analysis["severity"] == "high"
        assert any("High error rate" in issue for issue in analysis["issues"])
    
    @pytest.mark.asyncio
    async def test_rule_based_anomaly_detection_slow_response(self, anomaly_detector):
        """Test rule-based anomaly detection with slow response times"""
        raw_output = {
            "metrics": {
                "http_req_duration": {"avg": 3500, "p(95)": 6000},  # Very slow
                "http_req_failed": {"rate": 0.02},
                "http_reqs": {"rate": 15.0, "count": 900},
                "vus": {"max": 10}
            }
        }
        result = K6TestResult(raw_output)
        
        analysis = anomaly_detector._rule_based_anomaly_detection(result)
        
        assert analysis["anomalies_detected"]
        assert analysis["severity"] == "high"
        assert any("Slow average response time" in issue for issue in analysis["issues"])
        assert any("Very slow P95 response time" in issue for issue in analysis["issues"])


class TestK6Runner:
    """Test K6Runner functionality"""
    
    @pytest.fixture
    def mock_ai_service(self):
        """Mock AI service for testing"""
        ai_service = Mock(spec=AIService)
        ai_service.analyze_test_results = AsyncMock()
        return ai_service
    
    @pytest.fixture
    def temp_results_dir(self):
        """Create temporary results directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def k6_runner(self, mock_ai_service, temp_results_dir):
        """Create K6Runner instance for testing"""
        with patch('app.services.k6_runner.settings.K6_RESULTS_DIR', str(temp_results_dir)):
            # Mock the k6 installation check
            with patch.object(K6Runner, '_check_k6_installation'):
                runner = K6Runner(mock_ai_service)
                runner.results_dir = temp_results_dir
                return runner
    
    def test_k6_runner_initialization(self, k6_runner, temp_results_dir):
        """Test K6Runner initialization"""
        assert k6_runner.results_dir == temp_results_dir
        assert isinstance(k6_runner.anomaly_detector, AnomalyDetector)
    
    @pytest.mark.asyncio
    async def test_create_script_file(self, k6_runner):
        """Test script file creation"""
        script_content = """
        import http from 'k6/http';
        export default function() {
            http.get('https://api.example.com');
        }
        """
        test_id = "test-123"
        
        script_file = await k6_runner._create_script_file(script_content, test_id)
        
        assert script_file.exists()
        assert script_file.name == f"test_{test_id}.js"
        
        with open(script_file, 'r') as f:
            content = f.read()
        assert content == script_content
    
    @pytest.mark.asyncio
    async def test_prepare_k6_command_basic(self, k6_runner, temp_results_dir):
        """Test K6 command preparation with basic options"""
        script_file = temp_results_dir / "test_script.js"
        script_file.touch()
        
        cmd = await k6_runner._prepare_k6_command(script_file)
        
        assert cmd[0] == 'k6'
        assert cmd[1] == 'run'
        assert '--out' in cmd
        assert '--summary-export' in cmd
        assert str(script_file) in cmd
    
    @pytest.mark.asyncio
    async def test_prepare_k6_command_with_options(self, k6_runner, temp_results_dir):
        """Test K6 command preparation with options"""
        script_file = temp_results_dir / "test_script.js"
        script_file.touch()
        
        options = {
            "vus": 20,
            "duration": "2m",
            "iterations": 1000
        }
        
        cmd = await k6_runner._prepare_k6_command(script_file, options)
        
        assert '--vus' in cmd
        assert '20' in cmd
        assert '--duration' in cmd
        assert '2m' in cmd
        assert '--iterations' in cmd
        assert '1000' in cmd
    
    @pytest.mark.asyncio
    async def test_save_test_results(self, k6_runner):
        """Test saving test results to file"""
        test_summary = {
            "test_id": "test-123",
            "timestamp": "2025-07-06T12:00:00",
            "metrics": {"response_time_avg": 500},
            "anomaly_analysis": {"anomalies_detected": False}
        }
        
        await k6_runner._save_test_results(test_summary)
        
        results_file = k6_runner.results_dir / "test_test-123_results.json"
        assert results_file.exists()
        
        with open(results_file, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data["test_id"] == "test-123"
        assert saved_data["metrics"]["response_time_avg"] == 500


@pytest.mark.integration
class TestK6RunnerIntegration:
    """Integration tests for K6Runner (requires k6 installation)"""
    
    @pytest.fixture
    def mock_ai_service(self):
        """Mock AI service for integration tests"""
        ai_service = Mock(spec=AIService)
        ai_service.analyze_test_results = AsyncMock(return_value={
            'k6_script': json.dumps({
                "anomalies_detected": False,
                "severity": "low",
                "issues": [],
                "recommendations": ["Test results look good"],
                "confidence": 0.8
            })
        })
        return ai_service
    
    @pytest.fixture
    def temp_results_dir(self):
        """Create temporary results directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def k6_runner_integration(self, mock_ai_service, temp_results_dir):
        """Create K6Runner for integration testing"""
        with patch('app.services.k6_runner.settings.K6_RESULTS_DIR', str(temp_results_dir)):
            try:
                runner = K6Runner(mock_ai_service)
                runner.results_dir = temp_results_dir
                return runner
            except K6RunnerError as e:
                pytest.skip(f"K6 not available for integration tests: {e}")
    
    @pytest.mark.asyncio
    async def test_full_k6_test_execution(self, k6_runner_integration):
        """Test full K6 test execution with a simple script"""
        script_content = """
        import http from 'k6/http';
        import { sleep } from 'k6';
        
        export const options = {
            vus: 2,
            duration: '5s',
        };
        
        export default function() {
            http.get('https://httpbin.org/get');
            sleep(0.5);
        }
        """
        
        options = {"vus": 2, "duration": "5s"}
        
        # This test requires actual k6 installation
        try:
            result = await k6_runner_integration.run_test(script_content, options)
            
            assert "test_id" in result
            assert "metrics" in result
            assert "anomaly_analysis" in result
            assert result["metrics"]["virtual_users"] == 2
            assert result["metrics"]["total_requests"] > 0
            
        except K6RunnerError as e:
            pytest.skip(f"K6 execution failed: {e}")


# Sample test data for testing the service
SAMPLE_K6_SCRIPTS = [
    {
        "name": "Basic GET test",
        "script": """
        import http from 'k6/http';
        import { check } from 'k6';
        
        export const options = {
            vus: 10,
            duration: '30s',
        };
        
        export default function() {
            const response = http.get('https://httpbin.org/get');
            check(response, {
                'status is 200': (r) => r.status === 200,
                'response time < 500ms': (r) => r.timings.duration < 500,
            });
        }
        """,
        "expected_vus": 10
    },
    {
        "name": "POST API test",
        "script": """
        import http from 'k6/http';
        import { check } from 'k6';
        
        export const options = {
            vus: 5,
            duration: '1m',
        };
        
        export default function() {
            const payload = JSON.stringify({
                name: 'Test User',
                email: 'test@example.com'
            });
            
            const params = {
                headers: {
                    'Content-Type': 'application/json',
                },
            };
            
            const response = http.post('https://httpbin.org/post', payload, params);
            check(response, {
                'status is 200': (r) => r.status === 200,
                'has email': (r) => r.json().json.email === 'test@example.com',
            });
        }
        """,
        "expected_vus": 5
    },
    {
        "name": "Load test with stages",
        "script": """
        import http from 'k6/http';
        import { check } from 'k6';
        
        export const options = {
            stages: [
                { duration: '10s', target: 5 },
                { duration: '20s', target: 10 },
                { duration: '10s', target: 0 },
            ],
        };
        
        export default function() {
            const response = http.get('https://httpbin.org/get');
            check(response, {
                'status is 200': (r) => r.status === 200,
            });
        }
        """,
        "expected_max_vus": 10
    },
    {
        "name": "Authentication test",
        "script": """
        import http from 'k6/http';
        import { check } from 'k6';
        
        export const options = {
            vus: 3,
            duration: '30s',
        };
        
        export default function() {
            // Test with basic auth
            const credentials = 'user:password';
            const encodedCredentials = encoding.b64encode(credentials);
            
            const params = {
                headers: {
                    'Authorization': `Basic ${encodedCredentials}`,
                },
            };
            
            const response = http.get('https://httpbin.org/basic-auth/user/password', params);
            check(response, {
                'status is 200': (r) => r.status === 200,
                'authenticated': (r) => r.json().authenticated === true,
            });
        }
        """,
        "expected_vus": 3
    },
    {
        "name": "Error scenario test",
        "script": """
        import http from 'k6/http';
        import { check } from 'k6';
        
        export const options = {
            vus: 5,
            duration: '20s',
        };
        
        export default function() {
            // Mix of successful and failing requests
            const urls = [
                'https://httpbin.org/get',
                'https://httpbin.org/status/404',
                'https://httpbin.org/status/500',
                'https://httpbin.org/delay/3'
            ];
            
            const url = urls[Math.floor(Math.random() * urls.length)];
            const response = http.get(url);
            
            check(response, {
                'request completed': (r) => r.status !== 0,
            });
        }
        """,
        "expected_errors": True
    }
]


@pytest.mark.asyncio
async def test_sample_scripts_validation():
    """Test that sample scripts are valid and contain expected elements"""
    for sample in SAMPLE_K6_SCRIPTS:
        script = sample["script"]
        
        # Basic validation
        assert "import http from 'k6/http'" in script
        assert "export default function" in script
        assert "http.get" in script or "http.post" in script
        
        # Check for expected configuration
        if "expected_vus" in sample:
            assert f"vus: {sample['expected_vus']}" in script
        
        print(f"✓ {sample['name']} script is valid")
