import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import './History.css'

function History() {
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    fetchHistory()
  }, [])

  const fetchHistory = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/test/history')
      
      if (!response.ok) {
        const errorText = await response.text()
        console.error('API Error:', response.status, errorText)
        throw new Error(`HTTP ${response.status}: ${errorText}`)
      }
      
      const contentType = response.headers.get('content-type')
      if (!contentType || !contentType.includes('application/json')) {
        const textResponse = await response.text()
        console.error('Non-JSON response:', textResponse)
        throw new Error('Server returned non-JSON response')
      }
      
      const data = await response.json()
      console.log('History data received:', data) // Debug log
      setHistory(data.tests || [])
    } catch (err) {
      console.error('History fetch error:', err)
      setError(err.message || 'Failed to load history')
    } finally {
      setLoading(false)
    }
  }

  const formatDuration = (seconds) => {
    if (seconds < 60) return `${seconds.toFixed(1)}s`
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    return `${minutes}m ${remainingSeconds.toFixed(1)}s`
  }

  const formatDate = (timestamp) => {
    return new Date(timestamp).toLocaleString()
  }

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'completed': return '#27ae60'
      case 'failed': return '#e74c3c'
      case 'running': return '#f39c12'
      default: return '#95a5a6'
    }
  }

  const getStatusIcon = (status) => {
    switch (status?.toLowerCase()) {
      case 'completed': return '✅'
      case 'failed': return '❌'
      case 'running': return '🔄'
      default: return '❓'
    }
  }

  const handleViewResults = (testData) => {
    // Navigate to results page with test data
    navigate('/results', { state: { testResults: testData } })
  }

  if (loading) {
    return (
      <div className="history loading">
        <div className="loading-content">
          <h1>📚 Test History</h1>
          <div className="loading-spinner">🔄 Loading history...</div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="history error">
        <div className="error-content">
          <h1>📚 Test History</h1>
          <div className="error-message doodle-border">
            <h3>Failed to load history</h3>
            <p>{error}</p>
            <button 
              onClick={fetchHistory}
              className="btn btn-primary"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="history">
      <div className="history-header">
        <h1>📚 Test History</h1>
        <p>View and analyze your past performance tests</p>
      </div>

      <div className="history-content">
        {history.length === 0 ? (
          <div className="empty-history">
            <div className="empty-state doodle-border">
              <h3>No test history yet!</h3>
              <p>Run some tests to see them appear here.</p>
              <button 
                onClick={() => navigate('/generate')}
                className="btn btn-primary"
              >
                Generate Your First Test
              </button>
            </div>
          </div>
        ) : (
          <>
            <div className="history-stats">
              <div className="stat-card doodle-border">
                <h3>Total Tests</h3>
                <div className="stat-value">{history.length}</div>
              </div>
              
              <div className="stat-card doodle-border">
                <h3>Successful</h3>
                <div className="stat-value" style={{ color: '#27ae60' }}>
                  {history.filter(test => test.status === 'completed').length}
                </div>
              </div>
              
              <div className="stat-card doodle-border">
                <h3>Failed</h3>
                <div className="stat-value" style={{ color: '#e74c3c' }}>
                  {history.filter(test => test.status === 'failed').length}
                </div>
              </div>
              
              <div className="stat-card doodle-border">
                <h3>Avg Duration</h3>
                <div className="stat-value">
                  {formatDuration(
                    history.reduce((sum, test) => sum + (test.execution_time || 0), 0) / history.length
                  )}
                </div>
              </div>
            </div>

            <div className="history-list">
              <h2>Recent Tests</h2>
              <div className="test-list">
                {history.map((test) => (
                  <div key={test.test_id} className="test-item doodle-border">
                    <div className="test-header">
                      <div className="test-id">
                        <span className="test-icon">🧪</span>
                        <span className="test-id-text">{test.test_id}</span>
                      </div>
                      <div className="test-status">
                        <span className="status-icon">
                          {getStatusIcon(test.status)}
                        </span>
                        <span 
                          className="status-text"
                          style={{ color: getStatusColor(test.status) }}
                        >
                          {test.status || 'Unknown'}
                        </span>
                      </div>
                    </div>
                    
                    <div className="test-meta">
                      <div className="meta-item">
                        <span className="meta-label">📅 Date:</span>
                        <span className="meta-value">{formatDate(test.timestamp)}</span>
                      </div>
                      <div className="meta-item">
                        <span className="meta-label">⏱️ Duration:</span>
                        <span className="meta-value">{formatDuration(test.execution_time || 0)}</span>
                      </div>
                      {test.metrics && (
                        <>
                          <div className="meta-item">
                            <span className="meta-label">📊 Requests:</span>
                            <span className="meta-value">{test.metrics.total_requests || 0}</span>
                          </div>
                          <div className="meta-item">
                            <span className="meta-label">📈 Req/sec:</span>
                            <span className="meta-value">{(test.metrics.requests_per_second || 0).toFixed(2)}</span>
                          </div>
                        </>
                      )}
                    </div>

                    {test.anomaly_analysis && (
                      <div className="test-anomalies">
                        <div className="anomaly-summary">
                          {test.anomaly_analysis.anomalies_detected ? (
                            <span className="anomaly-warning">
                              ⚠️ Issues Detected ({test.anomaly_analysis.severity?.toUpperCase()} severity)
                            </span>
                          ) : (
                            <span className="anomaly-success">
                              ✅ No Issues Detected
                            </span>
                          )}
                        </div>
                      </div>
                    )}

                    <div className="test-actions">
                      <button 
                        onClick={() => handleViewResults(test)}
                        className="btn btn-small btn-primary"
                      >
                        View Results
                      </button>
                      <button 
                        onClick={() => {
                          const dataStr = JSON.stringify(test, null, 2)
                          const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr)
                          const exportFileDefaultName = `test-${test.test_id}.json`
                          const linkElement = document.createElement('a')
                          linkElement.setAttribute('href', dataUri)
                          linkElement.setAttribute('download', exportFileDefaultName)
                          linkElement.click()
                        }}
                        className="btn btn-small btn-secondary"
                      >
                        Export
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default History
