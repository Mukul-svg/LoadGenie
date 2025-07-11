import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import './TestRunner.css'

function TestRunner({ script, onTestComplete }) {
  const [currentScript, setCurrentScript] = useState(script || '')
  const [isRunning, setIsRunning] = useState(false)
  const [progress, setProgress] = useState(0)
  const [testOptions, setTestOptions] = useState({
    vus: 10,
    duration: '30s',
    iterations: null
  })
  const [error, setError] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    if (script) {
      setCurrentScript(script)
    }
  }, [script])

  const handleRunTest = async () => {
    if (!currentScript.trim()) {
      setError('Please provide a test script')
      return
    }

    setIsRunning(true)
    setError('')
    setProgress(0)

    // Simulate progress updates
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 90) {
          clearInterval(progressInterval)
          return 90
        }
        return prev + Math.random() * 10
      })
    }, 500)

    try {
      // Try with proxy first, then fallback to direct backend call
      const apiUrl = 'http://localhost:8000/api/v1/test/run'
      const backupUrl = 'http://localhost:8000/api/v1/test/run'
      
      let response;
      try {
        response = await fetch(apiUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            script: currentScript,
            options: testOptions
          }),
        })
      } catch (proxyError) {
        console.log('Proxy failed, trying direct backend call:', proxyError)
        response = await fetch(backupUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            script: currentScript,
            options: testOptions
          }),
        })
      }

      if (!response.ok) {
        throw new Error('Failed to run test')
      }

      const data = await response.json()
      
      clearInterval(progressInterval)
      setProgress(100)
      
      // Pass results to parent and navigate to results page
      onTestComplete(data)
      
      setTimeout(() => {
        navigate('/results')
      }, 1000)
      
    } catch (err) {
      clearInterval(progressInterval)
      setError(err.message || 'Failed to run test')
    } finally {
      setIsRunning(false)
    }
  }

  const handleScriptChange = (e) => {
    setCurrentScript(e.target.value)
  }

  const handleOptionsChange = (field, value) => {
    setTestOptions(prev => ({
      ...prev,
      [field]: value
    }))
  }

  return (
    <div className="test-runner">
      <div className="runner-header">
        <h1>🚀 Test Runner</h1>
        <p>Configure and execute your performance test</p>
      </div>

      <div className="runner-content">
        <div className="script-section">
          <h3>📝 Test Script</h3>
          <div className="script-editor">
            <textarea
              value={currentScript}
              onChange={handleScriptChange}
              placeholder="Paste your k6 test script here..."
              rows="20"
              disabled={isRunning}
            />
          </div>
          
          {!currentScript && (
            <div className="script-help doodle-border">
              <p>
                <strong>No script loaded!</strong> You can either:
              </p>
              <ul>
                <li>Go to the <strong>Generate Script</strong> page to create one</li>
                <li>Paste your existing k6 script in the editor above</li>
              </ul>
              <button 
                onClick={() => navigate('/generate')}
                className="btn btn-primary"
              >
                Generate Script
              </button>
            </div>
          )}
        </div>

        <div className="options-section">
          <h3>⚙️ Test Configuration</h3>
          <div className="options-grid">
            <div className="option-group">
              <label>Virtual Users (VUs)</label>
              <input
                type="number"
                value={testOptions.vus}
                onChange={(e) => handleOptionsChange('vus', parseInt(e.target.value))}
                min="1"
                max="1000"
                disabled={isRunning}
              />
            </div>
            
            <div className="option-group">
              <label>Duration</label>
              <select
                value={testOptions.duration}
                onChange={(e) => handleOptionsChange('duration', e.target.value)}
                disabled={isRunning}
              >
                <option value="30s">30 seconds</option>
                <option value="1m">1 minute</option>
                <option value="2m">2 minutes</option>
                <option value="5m">5 minutes</option>
                <option value="10m">10 minutes</option>
              </select>
            </div>
            
            <div className="option-group">
              <label>Iterations (optional)</label>
              <input
                type="number"
                value={testOptions.iterations || ''}
                onChange={(e) => handleOptionsChange('iterations', e.target.value ? parseInt(e.target.value) : null)}
                min="1"
                placeholder="Leave empty for time-based"
                disabled={isRunning}
              />
            </div>
          </div>
        </div>

        {error && (
          <div className="error-message doodle-border">
            <strong>Test Failed!</strong> {error}
          </div>
        )}

        {isRunning && (
          <div className="progress-section">
            <h3>🔄 Test Running...</h3>
            <div className="progress-bar">
              <div 
                className="progress-fill"
                style={{ width: `${progress}%` }}
              ></div>
            </div>
            <p>Progress: {Math.round(progress)}%</p>
          </div>
        )}

        <div className="action-section">
          <button 
            onClick={handleRunTest}
            disabled={isRunning || !currentScript.trim()}
            className="btn btn-primary btn-large"
          >
            {isRunning ? '🔄 Running Test...' : '🚀 Run Test'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default TestRunner
