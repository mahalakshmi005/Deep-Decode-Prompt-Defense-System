import React, { useState, useEffect, useRef } from 'react';
import './App.css';

function App() {
  const [input, setInput] = useState('');
  const [history, setHistory] = useState([]);
  const [currentAnalysis, setCurrentAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const historyEndRef = useRef(null);

  const handleAnalyze = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: input }),
      });

      const data = await response.json();
      
      // Determine attack type based on analysis data
      let attackType = "None Detected";
      if (data.analysis.base64_detected) {
        attackType = "Encoded Obfuscation (Base64)";
      } else if (data.analysis.ml_score > 60) {
        attackType = "Adversarial NLP Pattern";
      } else if (data.analysis.rule_score > 0) {
        attackType = "Instruction Override / Rule Match";
      }

      const result = {
        id: Date.now(),
        prompt: input,
        riskLevel: data.analysis.classification === 'SAFE' ? 'SAFE' : (data.analysis.classification === 'WARNING' ? 'SUSPICIOUS' : 'BLOCKED'),
        riskScore: data.analysis.score,
        attackType: attackType,
        modelResponse: data.response,
        timestamp: new Date()
      };
      
      setCurrentAnalysis(result);
      setHistory(prev => [result, ...prev]);
      setInput('');
    } catch (error) {
      console.error("Analysis failed", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container soc-theme">
      {/* Header */}
      <header className="soc-header">
        <div className="logo-section">
          <div className="scanner-line"></div>
          <h1><span className="neon-text-blue">AI</span> SECURITY DASHBOARD</h1>
        </div>
        <div className="system-status">
          <div className="status-item">
            <span className="label">SYSTEM:</span>
            <span className="value neon-text-green">OPERATIONAL</span>
          </div>
        </div>
      </header>

      <main className="dashboard-content">
        {/* Top Section: Input and Current Analysis */}
        <div className="analysis-grid">
          {/* Input Panel */}
          <section className="glass-panel input-section">
            <div className="panel-header">
              <span className="icon">📡</span>
              <h2>PROMPT INTERCEPTION</h2>
            </div>
            <form onSubmit={handleAnalyze}>
              <div className="textarea-wrapper">
                <textarea 
                  placeholder="Enter prompt for real-time injection analysis..." 
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  disabled={loading}
                />
                <div className="corner-decor top-left"></div>
                <div className="corner-decor bottom-right"></div>
              </div>
              <button type="submit" className="soc-btn" disabled={loading || !input.trim()}>
                {loading ? 'ANALYZING...' : 'ANALYZE PROMPT'}
                <span className="btn-glow"></span>
              </button>
            </form>
          </section>

          {/* Result Panel */}
          <section className="glass-panel result-section">
            <div className="panel-header">
              <span className="icon">🛡️</span>
              <h2>ANALYSIS RESULT</h2>
            </div>
            {currentAnalysis ? (
              <div className="result-display">
                <div className="metrics-row">
                  <div className="metric-box">
                    <span className="label">RISK LEVEL</span>
                    <span className={`value level-${currentAnalysis.riskLevel.toLowerCase()}`}>
                      {currentAnalysis.riskLevel}
                    </span>
                  </div>
                  <div className="metric-box">
                    <span className="label">RISK SCORE</span>
                    <span className="value neon-text-blue">{currentAnalysis.riskScore.toFixed(1)}%</span>
                  </div>
                </div>
                
                <div className="detail-box">
                  <span className="label">DETECTED ATTACK TYPE</span>
                  <span className="value text-highlight">{currentAnalysis.attackType}</span>
                </div>

                <div className="detail-box response-box">
                  <span className="label">MODEL RESPONSE</span>
                  <div className="response-text">
                    {currentAnalysis.modelResponse}
                  </div>
                </div>
              </div>
            ) : (
              <div className="empty-state">
                <div className="radar"></div>
                <p>Awaiting Input for Analysis...</p>
              </div>
            )}
          </section>
        </div>

        {/* Bottom Section: History Logs */}
        <section className="glass-panel logs-section">
          <div className="panel-header">
            <span className="icon">📋</span>
            <h2>SECURITY EVENT LOGS</h2>
          </div>
          <div className="table-wrapper">
            <table className="soc-table">
              <thead>
                <tr>
                  <th>TIMESTAMP</th>
                  <th>PROMPT (SAMPLED)</th>
                  <th>LEVEL</th>
                  <th>SCORE</th>
                  <th>ATTACK TYPE</th>
                </tr>
              </thead>
              <tbody>
                {history.map((log) => (
                  <tr key={log.id} className={`row-level-${log.riskLevel.toLowerCase()}`}>
                    <td>{log.timestamp.toLocaleTimeString()}</td>
                    <td className="prompt-cell">{log.prompt.substring(0, 40)}{log.prompt.length > 40 ? '...' : ''}</td>
                    <td><span className="level-badge">{log.riskLevel}</span></td>
                    <td>{log.riskScore.toFixed(1)}%</td>
                    <td>{log.attackType}</td>
                  </tr>
                ))}
                {history.length === 0 && (
                  <tr>
                    <td colSpan="5" className="text-center">No security events recorded.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      </main>

      <footer className="soc-footer">
        <div className="scan-id">SCAN_ID: {currentAnalysis ? currentAnalysis.id : 'N/A'}</div>
        <div className="encryption">ENCRYPTION: AES-256-GCM</div>
        <div className="version">v2.4.0-STABLE</div>
      </footer>
    </div>
  );
}

export default App;
