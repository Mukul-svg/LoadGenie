import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { useState } from 'react'
import Navigation from './components/Navigation'
import Home from './pages/Home'
import ScriptGenerator from './pages/ScriptGenerator'
import TestRunner from './pages/TestRunner'
import Results from './pages/Results'
import History from './pages/History'
import './App.css'

function App() {
  const [generatedScript, setGeneratedScript] = useState('')
  const [testResults, setTestResults] = useState(null)

  return (
    <Router>
      <div className="app">
        <Navigation />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route 
              path="/generate" 
              element={
                <ScriptGenerator 
                  onScriptGenerated={setGeneratedScript}
                  generatedScript={generatedScript}
                />
              } 
            />
            <Route 
              path="/test" 
              element={
                <TestRunner 
                  script={generatedScript}
                  onTestComplete={setTestResults}
                />
              } 
            />
            <Route 
              path="/results" 
              element={<Results testResults={testResults} />} 
            />
            <Route path="/history" element={<History />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App
