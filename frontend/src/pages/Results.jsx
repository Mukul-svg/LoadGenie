import { useEffect, useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import './Results.css'

function Results({ testResults }) {
  const [results, setResults] = useState(testResults)
  const navigate = useNavigate()
  const location = useLocation()

  useEffect(() => {
    // Check for results from props first, then from location state
    const resultsData = testResults || location.state?.testResults
    if (resultsData) {
      setResults(resultsData)
      console.log('Test results received:', resultsData) // Debug log
      console.log('Available metrics:', resultsData.metrics) // Debug log
    }
  }, [testResults, location.state])

  const formatDuration = (seconds) => {
    if (seconds < 60) return `${seconds.toFixed(2)}s`
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    return `${minutes}m ${remainingSeconds.toFixed(2)}s`
  }

  const formatNumber = (num) => {
    return new Intl.NumberFormat().format(num)
  }

  const getStatusColor = (status) => {
    if (!status) return '#95a5a6'
    switch (status.toLowerCase()) {
      case 'passed': return '#27ae60'
      case 'failed': return '#e74c3c'
      case 'warning': return '#f39c12'
      case 'completed': return '#27ae60'
      default: return '#95a5a6'
    }
  }

  const getAnomalyIcon = (type) => {
    switch (type.toLowerCase()) {
      case 'high_response_time': return '🐌'
      case 'high_error_rate': return '❌'
      case 'memory_spike': return '📈'
      case 'cpu_spike': return '🔥'
      default: return '⚠️'
    }
  }

  const getTotalRequests = () => {
    if (!results.metrics) return 0
    
    // Try various possible field names for total requests
    const possibleFields = ['http_reqs', 'requests', 'total_requests', 'http_requests', 'reqs']
    for (const field of possibleFields) {
      if (results.metrics[field] !== undefined) {
        return results.metrics[field]
      }
    }
    return 0
  }

  const getRequestRate = () => {
    if (!results.metrics) return 0
    
    // Try various possible field names for request rate
    const possibleFields = ['requests_per_second', 'http_req_rate', 'req_rate', 'requests_per_sec', 'rps', 'rate']
    for (const field of possibleFields) {
      if (results.metrics[field] !== undefined) {
        return results.metrics[field]
      }
    }
    return 0
  }

  if (!results) {
    return (
      <div className="results no-results">
        <div className="no-results-content">
          <h1>📊 Test Results</h1>
          <div className="empty-state doodle-border">
            <h3>No test results yet!</h3>
            <p>Run a test to see the results here.</p>
            <button 
              onClick={() => navigate('/test')}
              className="btn btn-primary"
            >
              Run a Test
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="results">
      <div className="results-header">
        <h1>📊 Test Results</h1>
        <p>Test executed on {new Date(results.timestamp).toLocaleString()}</p>
        <p className="test-id">Test ID: {results.test_id}</p>
      </div>

      <div className="results-content">
        {/* Summary Cards */}
        <div className="summary-section">
          <div className="summary-card doodle-border">
            <h3>⏱️ Duration</h3>
            <div className="metric-value">
              {formatDuration(results.execution_time)}
            </div>
          </div>
          
          <div className="summary-card doodle-border">
            <h3>✅ Status</h3>
            <div 
              className="metric-value"
              style={{ color: getStatusColor(results.status) }}
            >
              {results.status ? results.status.toUpperCase() : 'UNKNOWN'}
            </div>
          </div>
          
          <div className="summary-card doodle-border">
            <h3>🔢 Total Requests</h3>
            <div className="metric-value">
              {formatNumber(getTotalRequests())}
            </div>
          </div>
          
          <div className="summary-card doodle-border">
            <h3>📈 Req/sec</h3>
            <div className="metric-value">
              {getRequestRate().toFixed(2)}
            </div>
          </div>
        </div>

        {/* Detailed Metrics */}
        <div className="metrics-section">
          <h2>📋 Detailed Metrics</h2>
          <div className="metrics-grid">
            {results.metrics && Object.entries(results.metrics).map(([key, value]) => (
              <div key={key} className="metric-item doodle-border">
                <div className="metric-name">{key.replace(/_/g, ' ').toUpperCase()}</div>
                <div className="metric-value">
                  {typeof value === 'number' ? 
                    (key.includes('rate') ? value.toFixed(2) : formatNumber(value)) : 
                    value
                  }
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Anomaly Analysis */}
        {results.anomaly_analysis && (
          <div className="anomaly-section">
            <h2>🔍 AI Anomaly Analysis</h2>
            
            <div className="anomaly-summary doodle-border">
              <div className="anomaly-header">
                <h3>Overall Assessment</h3>
                <div 
                  className="anomaly-status"
                  style={{ 
                    color: results.anomaly_analysis.anomalies_detected ? '#e74c3c' : '#27ae60' 
                  }}
                >
                  {results.anomaly_analysis.anomalies_detected ? 
                    `Issues Detected (${results.anomaly_analysis.severity?.toUpperCase()} severity)` : 
                    'No Issues Detected'
                  }
                </div>
              </div>
              
              {results.anomaly_analysis.summary && (
                <p className="anomaly-summary-text">
                  {results.anomaly_analysis.summary}
                </p>
              )}
            </div>

            {results.anomaly_analysis.issues && results.anomaly_analysis.issues.length > 0 && (
              <div className="anomalies-list">
                <h4>⚠️ Detected Issues</h4>
                {results.anomaly_analysis.issues.map((issue, index) => (
                  <div key={index} className="anomaly-item doodle-border">
                    <div className="anomaly-icon">
                      ⚠️
                    </div>
                    <div className="anomaly-content">
                      <div className="anomaly-description">{issue}</div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {results.anomaly_analysis.recommendations && results.anomaly_analysis.recommendations.length > 0 && (
              <div className="recommendations-section">
                <h4>💡 AI Recommendations</h4>
                <div className="recommendations-list">
                  {results.anomaly_analysis.recommendations.map((rec, index) => (
                    <div key={index} className="recommendation-item doodle-border">
                      {rec}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="actions-section">
          <button 
            onClick={() => navigate('/test')}
            className="btn btn-primary"
          >
            🔄 Run Another Test
          </button>
          
          <button 
            onClick={() => navigate('/history')}
            className="btn btn-secondary"
          >
            📚 View History
          </button>
          
          <button 
            onClick={() => {
              const dataStr = JSON.stringify(results, null, 2)
              const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr)
              const exportFileDefaultName = `loadgenie-test-${results.test_id}.json`
              const linkElement = document.createElement('a')
              linkElement.setAttribute('href', dataUri)
              linkElement.setAttribute('download', exportFileDefaultName)
              linkElement.click()
            }}
            className="btn btn-tertiary"
          >
            💾 Export Results
          </button>
        </div>
      </div>
    </div>
  )
}

export default Results
