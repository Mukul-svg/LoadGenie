import { Link } from 'react-router-dom'
import './Home.css'

function Home() {
  return (
    <div className="home">
      <div className="hero-section">
        <div className="hero-content">
          <h1 className="hero-title">
            🧞‍♂️ LoadGenie
          </h1>
          <p className="hero-subtitle">
            AI-Powered Performance Test Generator
          </p>
          <p className="hero-description">
            Transform your ideas into powerful load tests with the magic of AI. 
            No expertise required - just describe what you want to test!
          </p>
          
          <div className="hero-actions">
            <Link to="/generate" className="btn btn-primary">
              Start Generating Tests ✨
            </Link>
            <Link to="/test" className="btn btn-secondary">
              Run a Test 🚀
            </Link>
          </div>
        </div>
      </div>

      <div className="features-section">
        <h2>What LoadGenie Can Do</h2>
        
        <div className="features-grid">
          <div className="feature-card doodle-border">
            <h3>🎯 Smart Test Generation</h3>
            <p>
              Describe your testing scenario in plain English, and our AI will 
              generate a complete k6 performance test script for you.
            </p>
          </div>
          
          <div className="feature-card doodle-border">
            <h3>🔧 Multi-Framework Support</h3>
            <p>
              Generate tests for k6, Locust, or JMeter formats. Pick the tool 
              that works best for your team.
            </p>
          </div>
          
          <div className="feature-card doodle-border">
            <h3>🤖 AI-Powered Analysis</h3>
            <p>
              Our intelligent system analyzes your test results and identifies 
              performance bottlenecks automatically.
            </p>
          </div>
          
          <div className="feature-card doodle-border">
            <h3>📊 Beautiful Reports</h3>
            <p>
              Get comprehensive, easy-to-understand reports with actionable 
              insights and recommendations.
            </p>
          </div>
        </div>
      </div>

      <div className="getting-started">
        <h2>Getting Started is Easy!</h2>
        
        <div className="steps">
          <div className="step">
            <div className="step-number">1</div>
            <h3>Describe Your Test</h3>
            <p>Tell us what you want to test in plain English</p>
          </div>
          
          <div className="step">
            <div className="step-number">2</div>
            <h3>Generate Script</h3>
            <p>Our AI creates a complete performance test script</p>
          </div>
          
          <div className="step">
            <div className="step-number">3</div>
            <h3>Run & Analyze</h3>
            <p>Execute the test and get intelligent insights</p>
          </div>
        </div>
        
        <div className="cta-section">
          <Link to="/generate" className="btn btn-large">
            Try LoadGenie Now! 🧞‍♂️
          </Link>
        </div>
      </div>
    </div>
  )
}

export default Home
