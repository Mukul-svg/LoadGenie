"""
Database service for storing K6 test results and history
"""

import aiosqlite
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

class DatabaseService:
    """SQLite database service for test results"""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize database service"""
        if db_path:
            self.db_path = db_path
        else:
            # Extract path from DATABASE_URL
            if settings.DATABASE_URL.startswith("sqlite:///"):
                self.db_path = settings.DATABASE_URL[10:]  # Remove "sqlite:///"
            else:
                self.db_path = "./loadgenie.db"
        
        # Ensure directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database on first use
        self._initialized = False
    
    async def _ensure_initialized(self):
        """Ensure database is initialized"""
        if not self._initialized:
            await self._init_database()
            self._initialized = True
    
    async def _init_database(self):
        """Initialize database tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # Create test_runs table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS test_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_id TEXT UNIQUE NOT NULL,
                    timestamp TEXT NOT NULL,
                    execution_time REAL NOT NULL,
                    script_content TEXT NOT NULL,
                    test_options TEXT,
                    response_time_avg REAL,
                    response_time_p95 REAL,
                    error_rate REAL,
                    requests_per_second REAL,
                    virtual_users INTEGER,
                    total_requests INTEGER,
                    duration_ms REAL,
                    anomalies_detected BOOLEAN,
                    severity TEXT,
                    issues TEXT,
                    recommendations TEXT,
                    confidence REAL,
                    raw_output TEXT,
                    console_output TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_test_runs_timestamp 
                ON test_runs(timestamp)
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_test_runs_test_id 
                ON test_runs(test_id)
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_test_runs_anomalies 
                ON test_runs(anomalies_detected, severity)
            """)
            
            await db.commit()
            logger.info(f"Database initialized at: {self.db_path}")
    
    async def save_test_result(self, test_summary: Dict[str, Any]) -> int:
        """
        Save test result to database
        
        Args:
            test_summary: Complete test summary dictionary
            
        Returns:
            Database ID of the inserted record
        """
        await self._ensure_initialized()
        
        async with aiosqlite.connect(self.db_path) as db:
            metrics = test_summary.get("metrics", {})
            anomaly_analysis = test_summary.get("anomaly_analysis", {})
            
            cursor = await db.execute("""
                INSERT INTO test_runs (
                    test_id, timestamp, execution_time, script_content, test_options,
                    response_time_avg, response_time_p95, error_rate, requests_per_second,
                    virtual_users, total_requests, duration_ms,
                    anomalies_detected, severity, issues, recommendations, confidence,
                    raw_output, console_output
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                test_summary["test_id"],
                test_summary["timestamp"],
                test_summary["execution_time"],
                test_summary["script_content"],
                json.dumps(test_summary.get("options", {})),
                metrics.get("response_time_avg"),
                metrics.get("response_time_p95"),
                metrics.get("error_rate"),
                metrics.get("requests_per_second"),
                metrics.get("virtual_users"),
                metrics.get("total_requests"),
                metrics.get("duration_ms"),
                anomaly_analysis.get("anomalies_detected"),
                anomaly_analysis.get("severity"),
                json.dumps(anomaly_analysis.get("issues", [])),
                json.dumps(anomaly_analysis.get("recommendations", [])),
                anomaly_analysis.get("confidence"),
                json.dumps(test_summary.get("raw_output", {})),
                test_summary.get("console_output", "")
            ))
            
            await db.commit()
            record_id = cursor.lastrowid
            
            logger.info(f"Saved test result {test_summary['test_id']} to database (ID: {record_id})")
            return record_id
    
    async def get_test_result(self, test_id: str) -> Optional[Dict[str, Any]]:
        """
        Get test result by test ID
        
        Args:
            test_id: Test execution ID
            
        Returns:
            Complete test result dictionary or None if not found
        """
        await self._ensure_initialized()
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            cursor = await db.execute("""
                SELECT * FROM test_runs WHERE test_id = ?
            """, (test_id,))
            
            row = await cursor.fetchone()
            if not row:
                return None
            
            return self._row_to_dict(row)
    
    async def get_test_history(self, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get test execution history
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of test history records
        """
        await self._ensure_initialized()
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            cursor = await db.execute("""
                SELECT * FROM test_runs 
                ORDER BY timestamp DESC 
                LIMIT ? OFFSET ?
            """, (limit, offset))
            
            rows = await cursor.fetchall()
            return [self._row_to_summary_dict(row) for row in rows]
    
    async def get_historical_metrics(self, days: int = 30, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get historical metrics for anomaly detection
        
        Args:
            days: Number of days to look back
            limit: Maximum number of records
            
        Returns:
            List of historical metrics
        """
        await self._ensure_initialized()
        
        # Calculate cutoff date
        cutoff_date = datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        ).isoformat()
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            cursor = await db.execute("""
                SELECT 
                    response_time_avg,
                    response_time_p95,
                    error_rate,
                    requests_per_second,
                    virtual_users,
                    total_requests
                FROM test_runs 
                WHERE timestamp >= datetime(?, '-{} days')
                AND response_time_avg IS NOT NULL
                ORDER BY timestamp DESC
                LIMIT ?
            """.format(days), (cutoff_date, limit))
            
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_anomaly_statistics(self, days: int = 7) -> Dict[str, Any]:
        """
        Get anomaly detection statistics
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Statistics about anomalies detected
        """
        await self._ensure_initialized()
        
        cutoff_date = datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        ).isoformat()
        
        async with aiosqlite.connect(self.db_path) as db:
            # Total tests
            cursor = await db.execute("""
                SELECT COUNT(*) as total_tests
                FROM test_runs 
                WHERE timestamp >= datetime(?, '-{} days')
            """.format(days), (cutoff_date,))
            total_result = await cursor.fetchone()
            total_tests = total_result[0] if total_result else 0
            
            # Tests with anomalies
            cursor = await db.execute("""
                SELECT COUNT(*) as anomaly_tests
                FROM test_runs 
                WHERE timestamp >= datetime(?, '-{} days')
                AND anomalies_detected = 1
            """.format(days), (cutoff_date,))
            anomaly_result = await cursor.fetchone()
            anomaly_tests = anomaly_result[0] if anomaly_result else 0
            
            # Severity breakdown
            cursor = await db.execute("""
                SELECT severity, COUNT(*) as count
                FROM test_runs 
                WHERE timestamp >= datetime(?, '-{} days')
                AND anomalies_detected = 1
                GROUP BY severity
            """.format(days), (cutoff_date,))
            severity_rows = await cursor.fetchall()
            severity_breakdown = {row[0]: row[1] for row in severity_rows}
            
            return {
                "period_days": days,
                "total_tests": total_tests,
                "anomaly_tests": anomaly_tests,
                "anomaly_rate": anomaly_tests / total_tests if total_tests > 0 else 0,
                "severity_breakdown": severity_breakdown
            }
    
    async def search_tests(
        self, 
        anomalies_only: bool = False,
        min_error_rate: Optional[float] = None,
        max_response_time: Optional[float] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search tests by criteria
        
        Args:
            anomalies_only: Only return tests with anomalies
            min_error_rate: Minimum error rate threshold
            max_response_time: Maximum response time threshold
            limit: Maximum number of results
            
        Returns:
            List of matching test records
        """
        await self._ensure_initialized()
        
        conditions = []
        params = []
        
        if anomalies_only:
            conditions.append("anomalies_detected = 1")
        
        if min_error_rate is not None:
            conditions.append("error_rate >= ?")
            params.append(min_error_rate)
        
        if max_response_time is not None:
            conditions.append("response_time_avg <= ?")
            params.append(max_response_time)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        params.append(limit)
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            cursor = await db.execute(f"""
                SELECT * FROM test_runs 
                WHERE {where_clause}
                ORDER BY timestamp DESC 
                LIMIT ?
            """, params)
            
            rows = await cursor.fetchall()
            return [self._row_to_summary_dict(row) for row in rows]
    
    async def cleanup_old_records(self, days: int = 90) -> int:
        """
        Clean up old test records
        
        Args:
            days: Delete records older than this many days
            
        Returns:
            Number of deleted records
        """
        await self._ensure_initialized()
        
        cutoff_date = datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        ).isoformat()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                DELETE FROM test_runs 
                WHERE timestamp < datetime(?, '-{} days')
            """.format(days), (cutoff_date,))
            
            await db.commit()
            deleted_count = cursor.rowcount
            
            logger.info(f"Cleaned up {deleted_count} old test records (older than {days} days)")
            return deleted_count
    
    def _row_to_dict(self, row: aiosqlite.Row) -> Dict[str, Any]:
        """Convert database row to complete test result dictionary"""
        return {
            "test_id": row["test_id"],
            "timestamp": row["timestamp"],
            "execution_time": row["execution_time"],
            "script_content": row["script_content"],
            "options": json.loads(row["test_options"] or "{}"),
            "metrics": {
                "response_time_avg": row["response_time_avg"],
                "response_time_p95": row["response_time_p95"],
                "error_rate": row["error_rate"],
                "requests_per_second": row["requests_per_second"],
                "virtual_users": row["virtual_users"],
                "total_requests": row["total_requests"],
                "duration_ms": row["duration_ms"]
            },
            "anomaly_analysis": {
                "anomalies_detected": bool(row["anomalies_detected"]),
                "severity": row["severity"],
                "issues": json.loads(row["issues"] or "[]"),
                "recommendations": json.loads(row["recommendations"] or "[]"),
                "confidence": row["confidence"]
            },
            "raw_output": json.loads(row["raw_output"] or "{}"),
            "console_output": row["console_output"]
        }
    
    def _row_to_summary_dict(self, row: aiosqlite.Row) -> Dict[str, Any]:
        """Convert database row to summary dictionary (for history)"""
        return {
            "test_id": row["test_id"],
            "timestamp": row["timestamp"],
            "execution_time": row["execution_time"],
            "metrics": {
                "response_time_avg": row["response_time_avg"],
                "response_time_p95": row["response_time_p95"],
                "error_rate": row["error_rate"],
                "requests_per_second": row["requests_per_second"],
                "virtual_users": row["virtual_users"],
                "total_requests": row["total_requests"],
                "duration_ms": row["duration_ms"]
            },
            "anomaly_analysis": {
                "anomalies_detected": bool(row["anomalies_detected"]),
                "severity": row["severity"],
                "issues": json.loads(row["issues"] or "[]"),
                "recommendations": json.loads(row["recommendations"] or "[]"),
                "confidence": row["confidence"]
            }
        }

# Global database service instance
db_service = DatabaseService()
