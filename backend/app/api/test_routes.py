"""
API routes for K6 test execution and management
"""

import time
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse

from app.core.logging import get_logger
from app.models.schemas import (
    TestExecutionRequest, 
    TestExecutionResponse, 
    TestHistoryResponse,
    ErrorResponse
)
from app.services.k6_runner import K6Runner, K6RunnerError
from app.services.ai_service import AIService
from app.services.database import db_service
from app.services.database import db_service

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/test")

# Dependency to get K6Runner instance
def get_k6_runner() -> K6Runner:
    """Get K6Runner instance with AI service"""
    ai_service = AIService()
    return K6Runner(ai_service)

@router.post("/run", response_model=TestExecutionResponse)
async def run_test(
    request: TestExecutionRequest,
    k6_runner: K6Runner = Depends(get_k6_runner)
):
    """
    Execute a K6 load test script and return results with anomaly analysis
    
    This endpoint accepts a K6 JavaScript script and optional test parameters,
    executes the test locally using subprocess, captures the results,
    and performs AI-powered anomaly detection on the metrics.
    """
    try:
        logger.info("Starting K6 test execution")
        logger.debug(f"Script length: {len(request.script)} characters")
        
        # Convert options to dict if provided
        options = request.options.dict(exclude_none=True) if request.options else None
        
        # Execute the test
        result = await k6_runner.run_test(request.script, options)
        
        # Convert to response model
        response = TestExecutionResponse(
            test_id=result["test_id"],
            timestamp=result["timestamp"],
            execution_time=result["execution_time"],
            metrics=result["metrics"],
            anomaly_analysis=result["anomaly_analysis"],
            status="completed"
        )
        
        logger.info(f"Test {result['test_id']} completed successfully")
        return response
        
    except K6RunnerError as e:
        logger.error(f"K6 runner error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during test execution: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during test execution"
        )

@router.get("/history", response_model=TestHistoryResponse)
async def get_test_history(
    limit: int = 20,
    k6_runner: K6Runner = Depends(get_k6_runner)
):
    """
    Get recent test execution history
    
    Returns a list of recent test executions with their metrics and anomaly analysis.
    Useful for tracking test trends and identifying patterns over time.
    """
    try:
        logger.info(f"Fetching test history (limit: {limit})")
        
        history = await k6_runner.get_test_history(limit)
        
        response = TestHistoryResponse(
            tests=history,
            total_count=len(history)
        )
        
        logger.info(f"Retrieved {len(history)} test history records")
        return response
        
    except Exception as e:
        logger.error(f"Error fetching test history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve test history"
        )

@router.get("/health")
async def check_k6_health():
    """
    Check K6 installation and runner service health
    
    Verifies that K6 is properly installed and accessible for test execution.
    """
    try:
        logger.info("Checking K6 runner health")
        
        # Try to create a K6Runner instance to check installation
        ai_service = AIService()
        k6_runner = K6Runner(ai_service)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "healthy",
                "message": "K6 runner is ready",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        )
        
    except K6RunnerError as e:
        logger.error(f"K6 runner health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=ErrorResponse(
                error="K6 runner not available",
                detail=str(e),
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
            ).dict()
        )
    except Exception as e:
        logger.error(f"Unexpected error during health check: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                error="Health check failed",
                detail="Internal server error",
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
            ).dict()
        )

@router.get("/results/{test_id}")
async def get_test_results(
    test_id: str,
    k6_runner: K6Runner = Depends(get_k6_runner)
):
    """
    Get detailed results for a specific test execution
    
    Returns the complete test results including raw K6 output,
    console logs, and full anomaly analysis for the specified test ID.
    """
    try:
        logger.info(f"Fetching results for test {test_id}")
        
        # Try to get from database first
        test_data = await db_service.get_test_result(test_id)
        
        if not test_data:
            # Fallback to file system
            results_file = k6_runner.results_dir / f"test_{test_id}_results.json"
            
            if not results_file.exists():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Test results not found for ID: {test_id}"
                )
            
            import json
            with open(results_file, 'r') as f:
                test_data = json.load(f)
        
        logger.info(f"Retrieved results for test {test_id}")
        return test_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching test results: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve test results"
        )

@router.get("/statistics")
async def get_test_statistics(days: int = 7):
    """
    Get test execution statistics and anomaly detection metrics
    
    Returns statistics about recent test executions including anomaly rates,
    severity breakdowns, and performance trends.
    """
    try:
        logger.info(f"Fetching test statistics for {days} days")
        
        stats = await db_service.get_anomaly_statistics(days=days)
        
        logger.info(f"Retrieved statistics: {stats['total_tests']} tests, {stats['anomaly_tests']} with anomalies")
        return stats
        
    except Exception as e:
        logger.error(f"Error fetching test statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve test statistics"
        )

@router.get("/search")
async def search_tests(
    anomalies_only: bool = False,
    min_error_rate: Optional[float] = None,
    max_response_time: Optional[float] = None,
    limit: int = 50
):
    """
    Search test executions by criteria
    
    Allows filtering tests by various performance criteria such as
    presence of anomalies, error rates, and response times.
    """
    try:
        logger.info(f"Searching tests with criteria: anomalies_only={anomalies_only}, "
                   f"min_error_rate={min_error_rate}, max_response_time={max_response_time}")
        
        results = await db_service.search_tests(
            anomalies_only=anomalies_only,
            min_error_rate=min_error_rate,
            max_response_time=max_response_time,
            limit=limit
        )
        
        response = TestHistoryResponse(
            tests=results,
            total_count=len(results)
        )
        
        logger.info(f"Found {len(results)} tests matching criteria")
        return response
        
    except Exception as e:
        logger.error(f"Error searching tests: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search tests"
        )
