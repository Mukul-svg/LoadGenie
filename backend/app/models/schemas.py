"""
Pydantic models for request/response schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any

class ScenarioRequest(BaseModel):
    """Request model for script generation"""
    scenario_description: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Description of the load testing scenario",
        example="Create a k6 load test for a REST API with 50 users for 2 minutes"
    )

class ScriptResponse(BaseModel):
    """Response model for generated script"""
    script: str = Field(
        ..., 
        description="Generated k6 JavaScript script",
        example="import http from 'k6/http'; ..."
    )
    generated_at: str = Field(
        ..., 
        description="Timestamp when script was generated",
        example="2025-07-06 12:34:56"
    )
    scenario_description: str = Field(
        ..., 
        description="Original scenario description",
        example="Create a k6 load test for a REST API"
    )

# New schemas for K6 test execution
class K6TestOptions(BaseModel):
    """Options for K6 test execution"""
    vus: Optional[int] = Field(
        None,
        ge=1,
        le=1000,
        description="Number of virtual users",
        example=10
    )
    duration: Optional[str] = Field(
        None,
        description="Test duration (e.g., '30s', '1m', '5m')",
        example="1m"
    )
    iterations: Optional[int] = Field(
        None,
        ge=1,
        description="Number of iterations to run",
        example=100
    )

class TestExecutionRequest(BaseModel):
    """Request model for test execution"""
    script: str = Field(
        ...,
        min_length=10,
        description="K6 JavaScript test script to execute",
        example="import http from 'k6/http'; export default function() { http.get('https://api.example.com'); }"
    )
    options: Optional[K6TestOptions] = Field(
        None,
        description="Test execution options"
    )

class TestMetrics(BaseModel):
    """Test execution metrics"""
    response_time_avg: float = Field(
        ...,
        description="Average response time in milliseconds",
        example=250.5
    )
    response_time_p95: float = Field(
        ...,
        description="95th percentile response time in milliseconds",
        example=450.0
    )
    error_rate: float = Field(
        ...,
        description="Error rate as percentage",
        example=2.1
    )
    requests_per_second: float = Field(
        ...,
        description="Throughput in requests per second",
        example=15.7
    )
    virtual_users: int = Field(
        ...,
        description="Number of virtual users used",
        example=10
    )
    total_requests: int = Field(
        ...,
        description="Total number of requests made",
        example=1000
    )
    duration_ms: float = Field(
        ...,
        description="Test duration in milliseconds",
        example=60000.0
    )

class AnomalyAnalysis(BaseModel):
    """Anomaly analysis results"""
    anomalies_detected: bool = Field(
        ...,
        description="Whether anomalies were detected",
        example=True
    )
    severity: str = Field(
        ...,
        description="Severity level of detected issues",
        example="medium"
    )
    issues: List[str] = Field(
        ...,
        description="List of specific issues found",
        example=["High error rate: 5.2%", "Elevated response time: 2.1s"]
    )
    recommendations: List[str] = Field(
        ...,
        description="List of actionable recommendations",
        example=["Investigate error responses", "Optimize server performance"]
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence level of the analysis",
        example=0.85
    )

class TestExecutionResponse(BaseModel):
    """Response model for test execution"""
    test_id: str = Field(
        ...,
        description="Unique test execution ID",
        example="550e8400-e29b-41d4-a716-446655440000"
    )
    timestamp: str = Field(
        ...,
        description="Test execution timestamp",
        example="2025-07-06T12:34:56.789Z"
    )
    execution_time: float = Field(
        ...,
        description="Test execution time in seconds",
        example=65.2
    )
    metrics: TestMetrics = Field(
        ...,
        description="Test execution metrics"
    )
    anomaly_analysis: AnomalyAnalysis = Field(
        ...,
        description="AI-powered anomaly analysis results"
    )
    status: str = Field(
        default="completed",
        description="Test execution status",
        example="completed"
    )

class TestHistoryItem(BaseModel):
    """Test history item"""
    test_id: str = Field(
        ...,
        description="Test execution ID",
        example="550e8400-e29b-41d4-a716-446655440000"
    )
    timestamp: str = Field(
        ...,
        description="Test execution timestamp",
        example="2025-07-06T12:34:56.789Z"
    )
    execution_time: float = Field(
        ...,
        description="Test execution time in seconds",
        example=65.2
    )
    metrics: TestMetrics = Field(
        ...,
        description="Test execution metrics"
    )
    anomaly_analysis: AnomalyAnalysis = Field(
        ...,
        description="Anomaly analysis summary"
    )

class TestHistoryResponse(BaseModel):
    """Response model for test history"""
    tests: List[TestHistoryItem] = Field(
        ...,
        description="List of recent test executions"
    )
    total_count: int = Field(
        ...,
        description="Total number of tests in history",
        example=25
    )

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(
        ..., 
        description="Error message",
        example="AI service error"
    )
    detail: Optional[str] = Field(
        None, 
        description="Detailed error information",
        example="Failed to connect to AI service"
    )
    timestamp: str = Field(
        ..., 
        description="Error timestamp",
        example="2025-07-06 12:34:56"
    )

class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(
        ..., 
        description="Service status",
        example="healthy"
    )
    timestamp: str = Field(
        ..., 
        description="Check timestamp",
        example="2025-07-06 12:34:56"
    )
