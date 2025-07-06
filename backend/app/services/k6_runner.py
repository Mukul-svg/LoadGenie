"""
K6 test runner service for executing load tests and analyzing results
"""

import asyncio
import json
import os
import tempfile
import time
import uuid
from pathlib import Path
from typing import Dict, Optional, List, Any
import subprocess
from datetime import datetime

from app.core.config import settings
from app.core.logging import get_logger
from app.services.ai_service import AIService
from app.services.database import db_service

logger = get_logger(__name__)

class K6RunnerError(Exception):
    """Custom exception for K6 runner errors"""
    pass

class K6TestResult:
    """Data class for K6 test results"""
    
    def __init__(self, raw_output: Dict[str, Any]):
        self.raw_output = raw_output
        self.metrics = raw_output.get('metrics', {})
        self.root_group = raw_output.get('root_group', {})
        
    @property
    def duration_ms(self) -> float:
        """Get test duration in milliseconds"""
        return self.metrics.get('iteration_duration', {}).get('avg', 0)
    
    @property
    def requests_per_second(self) -> float:
        """Get requests per second (throughput)"""
        return self.metrics.get('http_reqs', {}).get('rate', 0)
    
    @property
    def error_rate(self) -> float:
        """Get error rate as percentage"""
        failed = self.metrics.get('http_req_failed', {}).get('rate', 0)
        return failed * 100
    
    @property
    def response_time_p95(self) -> float:
        """Get 95th percentile response time"""
        return self.metrics.get('http_req_duration', {}).get('p(95)', 0)
    
    @property
    def response_time_avg(self) -> float:
        """Get average response time"""
        return self.metrics.get('http_req_duration', {}).get('avg', 0)
    
    @property
    def virtual_users(self) -> int:
        """Get number of virtual users"""
        return self.metrics.get('vus', {}).get('max', 0)
    
    @property
    def total_requests(self) -> int:
        """Get total number of requests"""
        return int(self.metrics.get('http_reqs', {}).get('count', 0))

class AnomalyDetector:
    """AI-powered anomaly detection for test results"""
    
    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service
        
    async def analyze_results(self, result: K6TestResult, historical_data: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Analyze test results for anomalies using AI"""
        
        # Prepare data for AI analysis
        analysis_data = {
            "current_test": {
                "response_time_avg": result.response_time_avg,
                "response_time_p95": result.response_time_p95,
                "error_rate": result.error_rate,
                "requests_per_second": result.requests_per_second,
                "virtual_users": result.virtual_users,
                "total_requests": result.total_requests
            },
            "historical_averages": self._calculate_historical_averages(historical_data) if historical_data else None
        }
        
        # Create AI prompt for anomaly detection
        prompt = self._create_anomaly_prompt(analysis_data)
        
        try:
            # Use AI service to analyze
            ai_response = await self.ai_service.analyze_test_results(prompt)
            analysis_result = json.loads(ai_response.get('k6_script', '{}'))
            
            return {
                "anomalies_detected": analysis_result.get("anomalies_detected", False),
                "severity": analysis_result.get("severity", "low"),
                "issues": analysis_result.get("issues", []),
                "recommendations": analysis_result.get("recommendations", []),
                "confidence": analysis_result.get("confidence", 0.5)
            }
        except Exception as e:
            logger.error(f"AI anomaly analysis failed: {e}")
            # Fallback to rule-based detection
            return self._rule_based_anomaly_detection(result, historical_data)
    
    def _create_anomaly_prompt(self, data: Dict[str, Any]) -> str:
        """Create AI prompt for anomaly detection"""
        return f"""
        Analyze the following load test results for anomalies and performance issues:
        
        Current Test Results:
        {json.dumps(data['current_test'], indent=2)}
        
        Historical Averages (if available):
        {json.dumps(data.get('historical_averages'), indent=2) if data.get('historical_averages') else 'No historical data available'}
        
        Instructions:
        1. Identify any performance anomalies or concerning patterns
        2. Compare with historical data if available
        3. Assess severity (low, medium, high, critical)
        4. Provide specific issues found
        5. Give actionable recommendations
        
        Return your analysis in JSON format with the following structure:
        {{
            "anomalies_detected": boolean,
            "severity": "low|medium|high|critical",
            "issues": ["list of specific issues found"],
            "recommendations": ["list of actionable recommendations"],
            "confidence": 0.0-1.0
        }}
        
        Focus on:
        - High error rates (>5% is concerning)
        - Slow response times (>2s avg is concerning)
        - Low throughput relative to virtual users
        - Significant deviations from historical patterns
        """
    
    def _calculate_historical_averages(self, historical_data: List[Dict]) -> Dict[str, float]:
        """Calculate averages from historical test data"""
        if not historical_data:
            return {}
        
        totals = {
            "response_time_avg": 0,
            "response_time_p95": 0,
            "error_rate": 0,
            "requests_per_second": 0
        }
        
        for record in historical_data:
            metrics = record.get("metrics", {})
            totals["response_time_avg"] += metrics.get("response_time_avg", 0)
            totals["response_time_p95"] += metrics.get("response_time_p95", 0)
            totals["error_rate"] += metrics.get("error_rate", 0)
            totals["requests_per_second"] += metrics.get("requests_per_second", 0)
        
        count = len(historical_data)
        return {key: value / count for key, value in totals.items()}
    
    def _rule_based_anomaly_detection(self, result: K6TestResult, historical_data: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Fallback rule-based anomaly detection"""
        issues = []
        severity = "low"
        
        # Check error rate
        if result.error_rate > 10:
            issues.append(f"High error rate: {result.error_rate:.1f}%")
            severity = "high"
        elif result.error_rate > 5:
            issues.append(f"Elevated error rate: {result.error_rate:.1f}%")
            severity = "medium"
        
        # Check response time
        if result.response_time_avg > 3000:
            issues.append(f"Slow average response time: {result.response_time_avg:.0f}ms")
            severity = "high"
        elif result.response_time_avg > 2000:
            issues.append(f"Elevated average response time: {result.response_time_avg:.0f}ms")
            if severity == "low":
                severity = "medium"
        
        # Check P95 response time
        if result.response_time_p95 > 5000:
            issues.append(f"Very slow P95 response time: {result.response_time_p95:.0f}ms")
            severity = "high"
        
        # Check throughput efficiency
        if result.virtual_users > 0:
            rps_per_user = result.requests_per_second / result.virtual_users
            if rps_per_user < 0.1:
                issues.append(f"Low throughput efficiency: {rps_per_user:.3f} RPS per VU")
                if severity == "low":
                    severity = "medium"
        
        recommendations = []
        if result.error_rate > 5:
            recommendations.append("Investigate error responses and server logs")
        if result.response_time_avg > 2000:
            recommendations.append("Optimize server performance or increase resources")
        if len(issues) == 0:
            recommendations.append("Test results look good - no immediate concerns")
        
        return {
            "anomalies_detected": len(issues) > 0,
            "severity": severity,
            "issues": issues,
            "recommendations": recommendations,
            "confidence": 0.8
        }

class K6Runner:
    """Service for running K6 load tests and analyzing results"""
    
    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service
        self.anomaly_detector = AnomalyDetector(ai_service)
        self.results_dir = Path(settings.K6_RESULTS_DIR if hasattr(settings, 'K6_RESULTS_DIR') else "/tmp/k6_results")
        self.results_dir.mkdir(exist_ok=True)
        
        # Check if k6 is installed
        self._check_k6_installation()
    
    def _check_k6_installation(self):
        """Check if k6 is installed and accessible"""
        try:
            result = subprocess.run(['k6', 'version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                logger.info(f"K6 detected: {result.stdout.strip()}")
            else:
                logger.warning("K6 installation check failed")
                raise K6RunnerError("K6 is not installed or not accessible")
        except subprocess.TimeoutExpired:
            raise K6RunnerError("K6 installation check timed out")
        except FileNotFoundError:
            raise K6RunnerError("K6 is not installed. Please install k6 from https://k6.io/docs/getting-started/installation/")
    
    async def run_test(self, script_content: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a K6 test script and return results with anomaly analysis
        
        Args:
            script_content: K6 JavaScript test script
            options: Optional test parameters (vus, duration, etc.)
        
        Returns:
            Dictionary containing test results, metrics, and anomaly analysis
        """
        test_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        try:
            # Create temporary script file
            script_file = await self._create_script_file(script_content, test_id)
            
            # Prepare K6 command
            cmd = await self._prepare_k6_command(script_file, options)
            
            # Execute K6 test
            logger.info(f"Starting K6 test {test_id}")
            start_time = time.time()
            
            result = await self._execute_k6_test(cmd, test_id)
            
            execution_time = time.time() - start_time
            logger.info(f"K6 test {test_id} completed in {execution_time:.2f}s")
            
            # Parse results
            k6_result = K6TestResult(result['json_output'])
            
            # Get historical data for anomaly detection
            historical_data = await self._get_historical_data()
            
            # Perform anomaly analysis
            anomaly_analysis = await self.anomaly_detector.analyze_results(k6_result, historical_data)
            
            # Save results
            test_summary = {
                "test_id": test_id,
                "timestamp": timestamp,
                "execution_time": execution_time,
                "script_content": script_content,
                "options": options or {},
                "metrics": {
                    "response_time_avg": k6_result.response_time_avg,
                    "response_time_p95": k6_result.response_time_p95,
                    "error_rate": k6_result.error_rate,
                    "requests_per_second": k6_result.requests_per_second,
                    "virtual_users": k6_result.virtual_users,
                    "total_requests": k6_result.total_requests,
                    "duration_ms": k6_result.duration_ms
                },
                "anomaly_analysis": anomaly_analysis,
                "raw_output": result['json_output'],
                "console_output": result['console_output']
            }
            
            await self._save_test_results(test_summary)
            
            # Cleanup
            await self._cleanup_files(script_file)
            
            return test_summary
            
        except Exception as e:
            logger.error(f"K6 test {test_id} failed: {e}")
            raise K6RunnerError(f"Test execution failed: {str(e)}")
    
    async def _create_script_file(self, script_content: str, test_id: str) -> Path:
        """Create temporary K6 script file"""
        script_file = self.results_dir / f"test_{test_id}.js"
        
        with open(script_file, 'w') as f:
            f.write(script_content)
        
        logger.debug(f"Created script file: {script_file}")
        return script_file
    
    async def _prepare_k6_command(self, script_file: Path, options: Optional[Dict[str, Any]] = None) -> List[str]:
        """Prepare K6 command with options"""
        cmd = ['k6', 'run']
        
        # Add output format for JSON
        json_output_file = script_file.parent / f"{script_file.stem}_results.json"
        cmd.extend(['--out', f'json={json_output_file}'])
        
        # Add summary output
        cmd.extend(['--summary-export', str(script_file.parent / f"{script_file.stem}_summary.json")])
        
        # Apply options
        if options:
            if 'vus' in options:
                cmd.extend(['--vus', str(options['vus'])])
            if 'duration' in options:
                cmd.extend(['--duration', str(options['duration'])])
            if 'iterations' in options:
                cmd.extend(['--iterations', str(options['iterations'])])
        
        cmd.append(str(script_file))
        
        logger.debug(f"K6 command: {' '.join(cmd)}")
        return cmd
    
    async def _execute_k6_test(self, cmd: List[str], test_id: str) -> Dict[str, Any]:
        """Execute K6 test command"""
        try:
            # Run K6 test
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=self.results_dir
            )
            
            stdout, _ = await process.communicate()
            console_output = stdout.decode('utf-8')
            
            if process.returncode != 0:
                raise K6RunnerError(f"K6 test failed with return code {process.returncode}: {console_output}")
            
            # Read JSON summary output
            summary_file = self.results_dir / f"test_{test_id}_summary.json"
            if summary_file.exists():
                with open(summary_file, 'r') as f:
                    json_output = json.load(f)
            else:
                raise K6RunnerError("K6 summary output file not found")
            
            return {
                'json_output': json_output,
                'console_output': console_output
            }
            
        except Exception as e:
            logger.error(f"Failed to execute K6 test: {e}")
            raise K6RunnerError(f"Test execution failed: {str(e)}")
    
    async def _get_historical_data(self, limit: int = 10) -> List[Dict]:
        """Get historical test data for anomaly detection"""
        try:
            return await db_service.get_historical_metrics(days=30, limit=limit)
        except Exception as e:
            logger.warning(f"Failed to get historical data from database: {e}")
            return []
    
    async def _save_test_results(self, test_summary: Dict[str, Any]):
        """Save test results to storage"""
        # Save to JSON file for backup
        results_file = self.results_dir / f"test_{test_summary['test_id']}_results.json"
        
        with open(results_file, 'w') as f:
            json.dump(test_summary, f, indent=2, default=str)
        
        logger.info(f"Test results saved to file: {results_file}")
        
        # Save to SQLite database
        try:
            record_id = await db_service.save_test_result(test_summary)
            logger.info(f"Test results saved to database (ID: {record_id})")
        except Exception as e:
            logger.error(f"Failed to save test results to database: {e}")
            # Continue execution - file backup is available
    
    async def _cleanup_files(self, script_file: Path):
        """Clean up temporary files"""
        try:
            if script_file.exists():
                script_file.unlink()
            
            # Clean up other generated files
            for pattern in [f"{script_file.stem}_*.json", f"{script_file.stem}_*.txt"]:
                for file in script_file.parent.glob(pattern):
                    file.unlink()
                    
        except Exception as e:
            logger.warning(f"Failed to cleanup files: {e}")
    
    async def get_test_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent test execution history"""
        try:
            # Try to get from database first
            history = await db_service.get_test_history(limit=limit)
            if history:
                logger.info(f"Retrieved {len(history)} test records from database")
                return history
        except Exception as e:
            logger.warning(f"Failed to get test history from database: {e}")
        
        # Fallback to JSON files
        history = []
        for results_file in sorted(self.results_dir.glob("test_*_results.json"))[-limit:]:
            try:
                with open(results_file, 'r') as f:
                    test_data = json.load(f)
                    
                # Return summary info only
                history.append({
                    "test_id": test_data.get("test_id"),
                    "timestamp": test_data.get("timestamp"),
                    "execution_time": test_data.get("execution_time"),
                    "metrics": test_data.get("metrics"),
                    "anomaly_analysis": test_data.get("anomaly_analysis")
                })
            except Exception as e:
                logger.warning(f"Failed to read test history from {results_file}: {e}")
        
        logger.info(f"Retrieved {len(history)} test records from files")
        return list(reversed(history))  # Most recent first
