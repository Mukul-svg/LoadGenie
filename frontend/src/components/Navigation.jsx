import { Link, useLocation } from 'react-router-dom'
import './Navigation.css'

function Navigation() {
  const location = useLocation()

  return (
    <nav className="navigation">
      <div className="nav-container">
        <Link to="/" className="nav-brand">
          <h1>🧞‍♂️ LoadGenie</h1>
        </Link>
        
        <div className="nav-links">
          <Link 
            to="/" 
            className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}
          >
            Home
          </Link>
          <Link 
            to="/generate" 
            className={`nav-link ${location.pathname === '/generate' ? 'active' : ''}`}
          >
            Generate Script
          </Link>
          <Link 
            to="/test" 
            className={`nav-link ${location.pathname === '/test' ? 'active' : ''}`}
          >
            Run Test
          </Link>
          <Link 
            to="/results" 
            className={`nav-link ${location.pathname === '/results' ? 'active' : ''}`}
          >
            Results
          </Link>
          <Link 
            to="/history" 
            className={`nav-link ${location.pathname === '/history' ? 'active' : ''}`}
          >
            History
          </Link>
        </div>
      </div>
    </nav>
  )
}

export default Navigation
