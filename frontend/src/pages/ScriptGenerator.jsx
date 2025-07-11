import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './ScriptGenerator.css'

function ScriptGenerator({ onScriptGenerated, generatedScript }) {
  const [scenario, setScenario] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const handleGenerate = async () => {
    if (!scenario.trim()) {
      setError('Please describe your testing scenario')
      return
    }

    setIsGenerating(true)
    setError('')

    try {
      const response = await fetch('http://localhost:8000/generate-script', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          scenario_description: scenario
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to generate script')
      }

      const data = await response.json()
      console.log('Backend response:', data) // Debug log
      
      // Check if the response has the expected structure
      const script = data.k6_script || data.script || data.code || data
      console.log('Extracted script:', script) // Debug log
      
      onScriptGenerated(script)
      
      // Add a small delay to ensure state is updated
      setTimeout(() => {
        navigate('/test')
      }, 100)
      
    } catch (err) {
      setError(err.message || 'Failed to generate script')
    } finally {
      setIsGenerating(false)
    }
  }

  const handleExampleClick = (example) => {
    setScenario(example)
  }

  const examples = [
    "Test an e-commerce website with 100 users browsing products and making purchases over 5 minutes",
    "Simulate 500 concurrent users hitting a REST API endpoint with authentication",
    "Load test a login system with 200 users over 10 minutes with 2-second think time",
    "Test a search functionality with 50 users performing various searches for 3 minutes",
    "Stress test a file upload endpoint with 25 users uploading 1MB files simultaneously"
  ]

  return (
    <div className="script-generator">
      <div className="generator-header">
        <h1>🎯 AI Script Generator</h1>
        <p>Describe your testing scenario in plain English, and our AI will generate a complete k6 performance test script for you!</p>
      </div>

      <div className="generator-content">
        <div className="input-section">
          <div className="form-group">
            <label htmlFor="scenario">Testing Scenario Description</label>
            <textarea
              id="scenario"
              value={scenario}
              onChange={(e) => setScenario(e.target.value)}
              placeholder="Example: Test an e-commerce website with 100 users browsing products and making purchases over 5 minutes..."
              rows="6"
              disabled={isGenerating}
            />
          </div>

          {error && (
            <div className="error-message doodle-border">
              <strong>Oops!</strong> {error}
            </div>
          )}

          <div className="action-buttons">
            <button 
              onClick={handleGenerate}
              disabled={isGenerating || !scenario.trim()}
              className="btn btn-primary"
            >
              {isGenerating ? '🔮 Generating Magic...' : '✨ Generate Script'}
            </button>
            
            {generatedScript && (
              <button 
                onClick={() => navigate('/test')}
                className="btn btn-secondary"
              >
                🚀 Run Test
              </button>
            )}
          </div>
        </div>

        <div className="examples-section">
          <h3>🎭 Try These Examples</h3>
          <div className="examples-grid">
            {examples.map((example, index) => (
              <div 
                key={index}
                className="example-card doodle-border"
                onClick={() => handleExampleClick(example)}
              >
                <p>{example}</p>
              </div>
            ))}
          </div>
        </div>

        {generatedScript && (
          <div className="script-preview">
            <h3>🎉 Generated Script</h3>
            <div className="script-container">
              <pre className="script-code">{generatedScript}</pre>
            </div>
            <div className="script-actions">
              <button 
                onClick={() => navigator.clipboard.writeText(generatedScript)}
                className="btn btn-small"
              >
                📋 Copy Script
              </button>
              <button 
                onClick={() => navigate('/test')}
                className="btn btn-primary"
              >
                🚀 Run This Test
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default ScriptGenerator
