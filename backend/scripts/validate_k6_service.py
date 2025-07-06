#!/usr/bin/env python3
"""
LoadGenie K6 Runner Service Validation Script

This script validates that all components of the K6 runner service are working correctly.
It performs comprehensive tests without requiring actual K6 installation.
"""

import asyncio
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.logging import setup_logging, get_logger
from app.services.database import DatabaseService
from app.models.schemas import TestExecutionRequest, K6TestOptions

# Setup logging
setup_logging("INFO")
logger = get_logger(__name__)

async def test_database_service():
    """Test database service functionality"""
    logger.info("🗄️  Testing Database Service...")
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        db_service = DatabaseService(tmp_db.name)
        
        # Test database initialization
        await db_service._ensure_initialized()
        logger.info("   ✅ Database initialization successful")
        
        # Test saving test result
        test_summary = {
            "test_id": "test-validation-123",
            "timestamp": "2025-07-06T12:00:00",
            "execution_time": 30.5,
            "script_content": "test script",
            "options": {"vus": 5, "duration": "30s"},
            "metrics": {
                "response_time_avg": 250.0,
                "response_time_p95": 400.0,
                "error_rate": 2.5,
                "requests_per_second": 10.0,
                "virtual_users": 5,
                "total_requests": 300,
                "duration_ms": 30000.0
            },
            "anomaly_analysis": {
                "anomalies_detected": False,
                "severity": "low",
                "issues": [],
                "recommendations": ["Test results look good"],
                "confidence": 0.8
            },
            "raw_output": {"test": "data"},
            "console_output": "Test output"
        }
        
        record_id = await db_service.save_test_result(test_summary)
        logger.info(f"   ✅ Test result saved (ID: {record_id})")
        
        # Test retrieving test result
        retrieved = await db_service.get_test_result("test-validation-123")
        assert retrieved is not None
        assert retrieved["test_id"] == "test-validation-123"
        logger.info("   ✅ Test result retrieval successful")
        
        # Test getting history
        history = await db_service.get_test_history(limit=5)
        assert len(history) >= 1
        logger.info(f"   ✅ Test history retrieval successful ({len(history)} records)")
        
        # Test statistics
        stats = await db_service.get_anomaly_statistics(days=7)
        assert "total_tests" in stats
        logger.info("   ✅ Statistics calculation successful")
        
        # Cleanup
        Path(tmp_db.name).unlink()
        logger.info("   ✅ Database test completed")

async def test_k6_runner_without_k6():
    """Test K6Runner service without actual K6 installation"""
    logger.info("🏃 Testing K6Runner Service (mocked)...")
    
    from app.services.k6_runner import K6Runner, AnomalyDetector
    from app.services.ai_service import AIService
    
    # Mock AI service
    mock_ai_service = Mock(spec=AIService)
    mock_ai_service.generate_script = AsyncMock(return_value={
        'k6_script': json.dumps({
            "anomalies_detected": False,
            "severity": "low",
            "issues": [],
            "recommendations": ["Test results look good"],
            "confidence": 0.8
        })
    })
    
    # Test anomaly detector
    anomaly_detector = AnomalyDetector(mock_ai_service)
    
    # Create test result
    from app.services.k6_runner import K6TestResult
    raw_output = {
        "metrics": {
            "http_req_duration": {"avg": 500, "p(95)": 800},
            "http_req_failed": {"rate": 0.02},
            "http_reqs": {"rate": 15.0, "count": 900},
            "vus": {"max": 10}
        }
    }
    test_result = K6TestResult(raw_output)
    
    # Test metrics calculation
    assert test_result.response_time_avg == 500
    assert test_result.error_rate == 2.0  # 0.02 * 100
    assert test_result.virtual_users == 10
    logger.info("   ✅ K6TestResult metrics calculation working")
    
    # Test rule-based anomaly detection
    analysis = anomaly_detector._rule_based_anomaly_detection(test_result)
    assert "anomalies_detected" in analysis
    assert "severity" in analysis
    logger.info("   ✅ Rule-based anomaly detection working")
    
    # Test with mock K6Runner (skip installation check)
    with patch.object(K6Runner, '_check_k6_installation'):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('app.services.k6_runner.settings.K6_RESULTS_DIR', temp_dir):
                runner = K6Runner(mock_ai_service)
                runner.results_dir = Path(temp_dir)
                
                # Test script file creation
                script_content = "import http from 'k6/http';"
                test_id = "test-123"
                script_file = await runner._create_script_file(script_content, test_id)
                
                assert script_file.exists()
                logger.info("   ✅ Script file creation working")
                
                # Test command preparation
                cmd = await runner._prepare_k6_command(script_file, {"vus": 5})
                assert "k6" in cmd
                assert "--vus" in cmd
                logger.info("   ✅ K6 command preparation working")
    
    logger.info("   ✅ K6Runner service test completed")

def test_api_schemas():
    """Test API schema validation"""
    logger.info("📋 Testing API Schemas...")
    
    # Test TestExecutionRequest
    request_data = {
        "script": "import http from 'k6/http'; export default function() { http.get('https://example.com'); }",
        "options": {
            "vus": 10,
            "duration": "30s"
        }
    }
    
    request = TestExecutionRequest(**request_data)
    assert request.script == request_data["script"]
    assert request.options.vus == 10
    assert request.options.duration == "30s"
    logger.info("   ✅ TestExecutionRequest schema validation working")
    
    # Test with minimal data
    minimal_request = TestExecutionRequest(script="test script")
    assert minimal_request.options is None
    logger.info("   ✅ Minimal request validation working")
    
    # Test K6TestOptions validation
    options = K6TestOptions(vus=5, duration="1m", iterations=100)
    assert options.vus == 5
    assert options.duration == "1m"
    assert options.iterations == 100
    logger.info("   ✅ K6TestOptions schema validation working")
    
    logger.info("   ✅ API schemas test completed")

def test_configuration():
    """Test configuration loading"""
    logger.info("⚙️  Testing Configuration...")
    
    from app.core.config import settings
    
    # Test basic settings
    assert settings.APP_NAME == "LoadGenie API"
    assert settings.APP_VERSION == "1.0.0"
    logger.info("   ✅ Basic settings loaded")
    
    # Test K6 settings
    assert hasattr(settings, 'K6_RESULTS_DIR')
    assert hasattr(settings, 'K6_TIMEOUT')
    logger.info("   ✅ K6 settings available")
    
    # Test database settings
    assert hasattr(settings, 'DATABASE_URL')
    logger.info("   ✅ Database settings available")
    
    logger.info("   ✅ Configuration test completed")

async def test_api_imports():
    """Test that API routes can be imported without errors"""
    logger.info("🌐 Testing API Imports...")
    
    try:
        from app.api.test_routes import router
        assert router is not None
        logger.info("   ✅ Test routes imported successfully")
        
        from app.main import app
        assert app is not None
        logger.info("   ✅ Main app imported successfully")
        
        # Test that routes are included
        route_paths = [route.path for route in app.routes]
        test_routes = [path for path in route_paths if path.startswith('/api/v1/test')]
        assert len(test_routes) > 0
        logger.info(f"   ✅ Test routes registered ({len(test_routes)} routes)")
        
    except Exception as e:
        logger.error(f"   ❌ API import failed: {e}")
        raise
    
    logger.info("   ✅ API imports test completed")

def test_file_structure():
    """Test that all required files exist"""
    logger.info("📁 Testing File Structure...")
    
    backend_dir = Path(__file__).parent.parent
    
    required_files = [
        "app/main.py",
        "app/services/k6_runner.py",
        "app/services/database.py",
        "app/api/test_routes.py",
        "app/models/schemas.py",
        "requirements.txt",
        "scripts/demo_k6_runner.py",
        "scripts/setup_k6_runner.sh",
        "tests/test_k6_runner.py",
        "tests/test_integration_k6.py",
        "docs/K6_RUNNER.md"
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = backend_dir / file_path
        if not full_path.exists():
            missing_files.append(file_path)
        else:
            logger.info(f"   ✅ {file_path}")
    
    if missing_files:
        logger.error(f"   ❌ Missing files: {missing_files}")
        return False
    
    logger.info("   ✅ All required files present")
    return True

async def main():
    """Run all validation tests"""
    logger.info("🔍 LoadGenie K6 Runner Service Validation")
    logger.info("=" * 50)
    
    tests_passed = 0
    tests_total = 6
    
    try:
        # Test 1: File structure
        if test_file_structure():
            tests_passed += 1
        
        # Test 2: Configuration
        test_configuration()
        tests_passed += 1
        
        # Test 3: API schemas
        test_api_schemas()
        tests_passed += 1
        
        # Test 4: API imports
        await test_api_imports()
        tests_passed += 1
        
        # Test 5: Database service
        await test_database_service()
        tests_passed += 1
        
        # Test 6: K6Runner service (mocked)
        await test_k6_runner_without_k6()
        tests_passed += 1
        
    except Exception as e:
        logger.error(f"❌ Validation failed: {e}")
        sys.exit(1)
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info(f"🎉 Validation Summary: {tests_passed}/{tests_total} tests passed")
    
    if tests_passed == tests_total:
        logger.info("✅ All components validated successfully!")
        logger.info("\n🚀 K6 Runner Service is ready to use!")
        logger.info("\nNext steps:")
        logger.info("1. Install K6: ./scripts/setup_k6_runner.sh")
        logger.info("2. Set GEMINI_API_KEY in .env file")
        logger.info("3. Start the service: python -m uvicorn app.main:app --reload")
        logger.info("4. Run demo: python scripts/demo_k6_runner.py")
    else:
        logger.error(f"❌ {tests_total - tests_passed} tests failed")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
