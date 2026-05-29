import React, { useState, useEffect, useRef } from 'react';
import './App.css';

function App() {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [history, setHistory] = useState([]);
  const [systemTime, setSystemTime] = useState(new Date().toLocaleTimeString());
  const [activeView, setActiveView] = useState('dashboard');
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileAnalysis, setFileAnalysis] = useState(null);
  const [liveLogs, setLiveLogs] = useState([]);
  const [activeSessions, setActiveSessions] = useState(1204);
  const [packetsScanned, setPacketsScanned] = useState(458);
  const [latency, setLatency] = useState(24);
  const [storedLogs, setStoredLogs] = useState([]);
  const logEndRef = useRef(null);

  const fetchStoredLogs = async () => {
    try {
      const response = await fetch('http://localhost:8000/logs');
      const data = await response.json();
      setStoredLogs(data);
    } catch (error) {
      console.error("Error fetching stored logs:", error);
    }
  };

  // System Time & Simulated Live Logs for Monitor
  useEffect(() => {
    const timer = setInterval(() => {
      setSystemTime(new Date().toLocaleTimeString());
      
      // Update Real-time Metrics
      setActiveSessions(prev => prev + Math.floor(Math.random() * 5) - 2);
      setPacketsScanned(450 + Math.floor(Math.random() * 20));
      setLatency(20 + Math.floor(Math.random() * 10));

      // Randomly add system background logs for "Live Monitor"
      if (Math.random() > 0.7) {
        const events = [
          "HEARTBEAT_SIGNAL: Neutral",
          "API_POLL: Connection Stable",
          "NEURAL_CACHE: Optimized",
          "LATENCY_CHECK: 12ms",
          "FIREWALL_STATUS: Active",
          "VECTOR_DB: Synced"
        ];
        const newLog = `[${new Date().toLocaleTimeString()}] ${events[Math.floor(Math.random() * events.length)]}`;
        setLiveLogs(prev => [...prev.slice(-15), newLog]);
      }
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const stats = {
    analyzed: history.length,
    safe: history.filter(h => h.riskLevel === 'SAFE').length,
    flagged: history.filter(h => h.riskLevel === 'SUSPICIOUS').length,
    blocked: history.filter(h => h.riskLevel === 'BLOCKED').length
  };

  const renderSessionLogs = () => (
    <div className="session-logs-view slide-in">
      <section className="card-glass logs-panel" style={{height: '600px'}}>
        <div className="card-header">
          <div className="title">📂 STORED ANALYSIS LOGS</div>
          <div className="header-actions">
             <button className="export-btn" onClick={() => window.open('http://localhost:8000/logs')}>VIEW RAW JSON</button>
          </div>
        </div>
        <div className="logs-container" style={{height: '500px'}}>
          <table className="events-table">
            <thead>
              <tr>
                <th>TIMESTAMP</th>
                <th>PROMPT</th>
                <th>CLASSIFICATION</th>
                <th>RISK</th>
                <th>THREAT TYPE</th>
                <th>RESPONSE</th>
              </tr>
            </thead>
            <tbody>
              {storedLogs.length > 0 ? (
                storedLogs.map((log, index) => (
                  <tr key={index}>
                    <td>{new Date(log.timestamp).toLocaleString()}</td>
                    <td className="prompt-cell">{log.prompt}</td>
                    <td><span className={`type-tag ${log.classification.toLowerCase()}`}>{log.classification}</span></td>
                    <td><span className={`score-tag ${log.risk_score > 70 ? 'blocked' : (log.risk_score > 30 ? 'suspicious' : 'safe')}`}>{log.risk_score}%</span></td>
                    <td>{log.threat_type}</td>
                    <td className="response-cell">{log.response}</td>
                  </tr>
                ))
              ) : (
                <tr><td colSpan="6" style={{textAlign: 'center', padding: '20px'}}>No stored logs found in analysis_tools/</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );

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
      
      if (data && data.analysis) {
        const result = {
          id: Date.now(),
          timestamp: new Date(),
          prompt: input,
          response: data.response, // Capture AI response
          riskScore: data.analysis.score || 0,
          riskLevel: data.analysis.classification === 'SAFE' ? 'SAFE' : (data.analysis.classification === 'WARNING' ? 'SUSPICIOUS' : 'BLOCKED'),
          mlScore: data.analysis.ml_score || 0,
          mlConfidence: data.analysis.ml_confidence || 'LOW',
          mlConfidenceScore: data.analysis.ml_confidence_score || 0,
          ruleScore: data.analysis.rule_score || 0,
          type: data.analysis.threat_type || 'Unknown'
        };
        setAnalysis(result);
        setHistory(prev => [result, ...prev]);
      } else {
        throw new Error("Invalid API response format");
      }
    } catch (error) { 
      console.error("Analysis Error:", error);
      alert("Error: Backend is not responding correctly. Make sure main.py is running.");
    } finally { setLoading(false); }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleAnalyzeFile = async () => {
    if (!selectedFile) return;
    setLoading(true);
    
    const reader = new FileReader();
    reader.onload = async (e) => {
      const content = e.target.result;
      const payload = `Document Analysis: ${selectedFile.name}\n\nContent:\n${content}`;
      
      try {
        const response = await fetch('http://localhost:8000/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: payload }),
        });
        const data = await response.json();
        
        if (data && data.analysis) {
          const result = {
            id: Date.now(),
            timestamp: new Date(),
            prompt: `FILE: ${selectedFile.name}`,
            response: data.response, // Capture AI response for files
            riskScore: data.analysis.score || 0,
            riskLevel: data.analysis.classification === 'SAFE' ? 'SAFE' : (data.analysis.classification === 'WARNING' ? 'SUSPICIOUS' : 'BLOCKED'),
            mlScore: data.analysis.ml_score || 0,
            mlConfidence: data.analysis.ml_confidence || 'LOW',
            mlConfidenceScore: data.analysis.ml_confidence_score || 0,
            ruleScore: data.analysis.rule_score || 0,
            type: data.analysis.threat_type || 'Unknown'
          };
          setFileAnalysis(result);
          setHistory(prev => [result, ...prev]);
        }
      } catch (error) { 
        console.error("File Analysis Error:", error);
      } finally { setLoading(false); }
    };
    
    reader.onerror = () => {
      console.error("File reading error");
      setLoading(false);
    };
    
    reader.readAsText(selectedFile);
  };

  const renderDashboard = () => (
    <>
      <section className="live-stats-bar">
        <div className="stat-item blue">
          <span className="label">ANALYZED</span>
          <span className="value">{stats.analyzed}</span>
          <div className="progress-mini"><div className="fill" style={{width: '100%'}}></div></div>
        </div>
        <div className="stat-item green">
          <span className="label">SAFE</span>
          <span className="value">{stats.safe}</span>
          <div className="progress-mini"><div className="fill" style={{width: stats.analyzed > 0 ? `${(stats.safe/stats.analyzed)*100}%` : '0%'}}></div></div>
        </div>
        <div className="stat-item orange">
          <span className="label">FLAGGED</span>
          <span className="value">{stats.flagged}</span>
          <div className="progress-mini"><div className="fill" style={{width: stats.analyzed > 0 ? `${(stats.flagged/stats.analyzed)*100}%` : '0%'}}></div></div>
        </div>
        <div className="stat-item red">
          <span className="label">BLOCKED</span>
          <span className="value">{stats.blocked}</span>
          <div className="progress-mini"><div className="fill" style={{width: stats.analyzed > 0 ? `${(stats.blocked/stats.analyzed)*100}%` : '0%'}}></div></div>
        </div>
      </section>

      <div className="intelligence-grid">
        <section className="card-glass console-panel">
          <div className="card-header"><div className="title">💬 THREAT INPUT CONSOLE</div><div className="live-tag">LIVE SCANNER</div></div>
          <div className="card-body">
            <div className="textarea-wrapper">
              <textarea placeholder="Paste suspicious LLM prompt here..." value={input} onChange={(e) => setInput(e.target.value)}></textarea>
              {loading && <div className="scan-line"></div>}
            </div>
            <button className={`analyze-trigger ${loading ? 'loading' : ''}`} onClick={handleAnalyze} disabled={loading || !input.trim()}>
              {loading ? 'PROCESSING VECTOR...' : '⚡ ANALYZE THREAT'}
            </button>
            <div className="action-row">
              <button className="btn-secondary orange">🧹 SANITIZE</button>
              <button className="btn-secondary" onClick={() => {setInput(''); setAnalysis(null);}}>✕ CLEAR</button>
            </div>
            <div className="detection-pills">
              <span className="pill green">🟢 Benign</span><span className="pill orange">🟡 Roleplay</span><span className="pill red">🔴 Base64</span><span className="pill purple">🟣 Override</span>
            </div>
          </div>
        </section>

        <section className="card-glass assessment-panel">
          <div className="card-header"><div className="title">📊 THREAT ASSESSMENT ENGINE</div><div className="engine-status">v2.4.0-STABLE</div></div>
          <div className="card-body centered">
            {analysis ? (
              <div className="analysis-results">
                <div className="gauge-wrap">
                  <svg viewBox="0 0 100 50" className="semi-gauge">
                    <path d="M 10 50 A 40 40 0 0 1 90 50" fill="none" stroke="#e0e8f0" strokeWidth="8" />
                    <path className={`gauge-path ${analysis.riskLevel.toLowerCase()}`} d="M 10 50 A 40 40 0 0 1 90 50" fill="none" strokeWidth="8" strokeDasharray="125.6" strokeDashoffset={125.6 * (1 - analysis.riskScore / 100)} />
                  </svg>
                  <div className="gauge-data"><span className={`risk-percent ${analysis.riskLevel.toLowerCase()}`}>{analysis.riskScore.toFixed(0)}%</span><span className="risk-label">INJECTION RISK</span></div>
                </div>
                <div className={`status-badge-large ${analysis.riskLevel.toLowerCase()}`}>{analysis.riskLevel === 'BLOCKED' ? '🚨 BLOCKED' : (analysis.riskLevel === 'SAFE' ? '✅ SAFE' : '⚠️ WARNING')}</div>
                <div className="engine-breakdown">
                  <div className="breakdown-item"><div className="labels"><span>ML Core Prediction</span><span>{analysis.mlScore}%</span></div><div className="bar-track"><div className="bar-fill red" style={{width: `${analysis.mlScore}%`}}></div></div></div>
                  <div className="breakdown-item"><div className="labels"><span>Neural Confidence</span><span className={`confidence-tag ${analysis.mlConfidence.toLowerCase()}`}>{analysis.mlConfidence} ({analysis.mlConfidenceScore}%)</span></div><div className="bar-track"><div className="bar-fill blue" style={{width: `${analysis.mlConfidenceScore}%`}}></div></div></div>
                  <div className="breakdown-item"><div className="labels"><span>Security Rule Match</span><span>{analysis.ruleScore}%</span></div><div className="bar-track"><div className="bar-fill red" style={{width: `${analysis.ruleScore}%`}}></div></div></div>
                </div>
                {analysis.response && (
                  <div className="ai-response-box">
                    <strong>🤖 AI RESPONSE:</strong>
                    <p>{analysis.response}</p>
                  </div>
                )}
                <div className="warning-terminal"><code>{analysis.riskLevel === 'SAFE' ? 'NEURAL_SCAN_CLEAN' : 'INJECTION_VECTOR_DETECTED'} // {analysis.type}</code></div>
              </div>
            ) : (
              <div className="empty-engine"><div className="radar-icon">📡</div><p>Awaiting Threat Vector...</p></div>
            )}
          </div>
        </section>
      </div>
    </>
  );

  const renderFileUpload = () => (
    <div className="intelligence-grid slide-in">
      <section className="card-glass console-panel">
        <div className="card-header"><div className="title">📎 DOCUMENT SECURITY SCANNER</div><div className="live-tag">SECURE UPLOAD</div></div>
        <div className="card-body">
          <div className="file-upload-zone">
            <input type="file" id="fileInput" onChange={handleFileChange} style={{display: 'none'}} />
            <label htmlFor="fileInput" className="upload-label">
              <div className="upload-icon">📁</div>
              {selectedFile ? (
                <div className="file-info">
                  <strong>{selectedFile.name}</strong>
                  <span>{(selectedFile.size / 1024).toFixed(2)} KB</span>
                </div>
              ) : (
                <p>Drag & drop or <span>Browse Files</span></p>
              )}
            </label>
          </div>
          <button className={`analyze-trigger ${loading ? 'loading' : ''}`} onClick={handleAnalyzeFile} disabled={loading || !selectedFile}>
            {loading ? 'SCANNING DOCUMENT...' : '⚡ ANALYZE DOCUMENT'}
          </button>
          <div className="action-row">
            <button className="btn-secondary" onClick={() => {setSelectedFile(null); setFileAnalysis(null);}}>✕ REMOVE FILE</button>
          </div>
          <div className="detection-pills">
            <span className="pill">📄 PDF</span><span className="pill">📝 TXT</span><span className="pill">📊 CSV</span><span className="pill">📓 DOCX</span>
          </div>
        </div>
      </section>

      <section className="card-glass assessment-panel">
        <div className="card-header"><div className="title">🔍 FILE THREAT ASSESSMENT</div></div>
        <div className="card-body centered">
          {fileAnalysis ? (
            <div className="analysis-results">
              <div className="gauge-wrap">
                <svg viewBox="0 0 100 50" className="semi-gauge">
                  <path d="M 10 50 A 40 40 0 0 1 90 50" fill="none" stroke="#e0e8f0" strokeWidth="8" />
                  <path className={`gauge-path ${fileAnalysis.riskLevel.toLowerCase()}`} d="M 10 50 A 40 40 0 0 1 90 50" fill="none" strokeWidth="8" strokeDasharray="125.6" strokeDashoffset={125.6 * (1 - fileAnalysis.riskScore / 100)} />
                </svg>
                <div className="gauge-data"><span className={`risk-percent ${fileAnalysis.riskLevel.toLowerCase()}`}>{fileAnalysis.riskScore.toFixed(0)}%</span><span className="risk-label">INJECTION RISK</span></div>
              </div>
              <div className={`status-badge-large ${fileAnalysis.riskLevel.toLowerCase()}`}>{fileAnalysis.riskLevel}</div>
              <div className="engine-breakdown">
                <div className="breakdown-item"><div className="labels"><span>Document Vector Match</span><span>{fileAnalysis.ruleScore}%</span></div><div className="bar-track"><div className="bar-fill red" style={{width: `${fileAnalysis.ruleScore}%`}}></div></div></div>
              </div>
              {fileAnalysis.response && (
                <div className="ai-response-box">
                  <strong>🤖 AI RESPONSE:</strong>
                  <p>{fileAnalysis.response}</p>
                </div>
              )}
              <div className="warning-terminal"><code>THREAT_TYPE: {fileAnalysis.type}</code></div>
            </div>
          ) : (
            <div className="empty-engine"><div className="radar-icon">📑</div><p>Awaiting File for Security Audit...</p></div>
          )}
        </div>
      </section>
    </div>
  );

  const renderLiveMonitor = () => (
    <div className="monitor-view slide-in">
      <div className="card-glass monitor-terminal">
        <div className="card-header"><div className="title">📡 GLOBAL INTERCEPTION FEED</div><div className="live-tag pulse">REAL-TIME</div></div>
        <div className="terminal-content">
          {liveLogs.map((log, i) => <div key={i} className="log-line">{log}</div>)}
          <div ref={logEndRef} />
        </div>
      </div>
      <div className="monitor-stats-grid">
        <div className="card-glass stat-card-mini">
          <span className="label">ACTIVE SESSIONS</span>
          <span className="value">{activeSessions.toLocaleString()}</span>
        </div>
        <div className="card-glass stat-card-mini">
          <span className="label">PACKETS_SCANNED/S</span>
          <span className="value">{packetsScanned}</span>
        </div>
        <div className="card-glass stat-card-mini">
          <span className="label">AVG_LATENCY</span>
          <span className="value">{latency}ms</span>
        </div>
      </div>
    </div>
  );

  const renderAttackPaths = () => (
    <div className="attack-view slide-in">
      <div className="card-glass path-viz">
        <div className="card-header"><div className="title">🕸️ THREAT PROPAGATION MAP</div></div>
        <div className="path-grid">
          <div className="path-node">
            <div className="node-icon">👤</div>
            <div className="node-label">User Entry</div>
          </div>
          <div className="path-arrow">➔</div>
          <div className="path-node active">
            <div className="node-icon">🛡️</div>
            <div className="node-label">GuardLLM Intercept</div>
            <div className="node-details">3 layers active</div>
          </div>
          <div className="path-arrow">➔</div>
          <div className="path-node blocked">
            <div className="node-icon">🧠</div>
            <div className="node-label">Target LLM</div>
            <div className="node-status">ISOLATED</div>
          </div>
        </div>
      </div>
      <div className="threat-vectors card-glass">
        <div className="card-header"><div className="title">RECENT VECTORS</div></div>
        <div className="vector-list">
          <div className="vector-item"><span className="tag red">CRITICAL</span> Prompt Leakage Vector (Blocked)</div>
          <div className="vector-item"><span className="tag orange">MEDIUM</span> Jailbreak Attempt #442 (Sanitized)</div>
          <div className="vector-item"><span className="tag green">INFO</span> System Instructions Verified</div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="guard-fullscreen-app">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-logo">🛡️</div>
          <div className="brand-text"><strong>GuardLLM</strong><span>Enterprise Security</span></div>
        </div>
        <nav className="sidebar-nav">
          <div className="nav-section">
            <span className="section-title">MAIN MENU</span>
            <button className={`nav-link-btn ${activeView === 'dashboard' ? 'active' : ''}`} onClick={() => setActiveView('dashboard')}>📊 Dashboard</button>
            <button className={`nav-link-btn ${activeView === 'monitor' ? 'active' : ''}`} onClick={() => setActiveView('monitor')}>📡 Live Monitor</button>
            <button className={`nav-link-btn ${activeView === 'attack' ? 'active' : ''}`} onClick={() => setActiveView('attack')}>🕸️ Attack Paths</button>
          </div>
          <div className="nav-section">
            <span className="section-title">ANALYSIS TOOLS</span>
            <button className={`tool-btn ${activeView === 'dashboard' ? 'active' : ''}`} onClick={() => setActiveView('dashboard')}>💬 Input Prompt</button>
            <button className={`tool-btn orange ${activeView === 'file-upload' ? 'active' : ''}`} onClick={() => setActiveView('file-upload')}>📎 Attach File</button>
            <button className={`tool-btn purple ${activeView === 'session-logs' ? 'active' : ''}`} onClick={() => { setActiveView('session-logs'); fetchStoredLogs(); }}>📜 Session Logs</button>
          </div>
        </nav>
        <div className="sidebar-footer">
          <div className="live-clock"><span className="pulse-dot green"></span>{systemTime}</div>
          <div className="status-label">SYSTEM ONLINE</div>
        </div>
      </aside>

      <main className="main-viewport">
        <header className="viewport-header">
          <div className="search-bar"><span>🔍</span><input type="text" placeholder="Search event logs..." /></div>
          <div className="header-actions">
            <div className="notification-icon">🔔<span className="badge">{stats.blocked}</span></div>
            <div className="user-profile"><div className="user-avatar">AD</div><span>Admin</span></div>
          </div>
        </header>

        {activeView === 'dashboard' && renderDashboard()}
        {activeView === 'file-upload' && renderFileUpload()}
        {activeView === 'monitor' && renderLiveMonitor()}
        {activeView === 'attack' && renderAttackPaths()}
        {activeView === 'session-logs' && renderSessionLogs()}

        <section className="card-glass logs-panel">
          <div className="card-header"><div className="title">📋 SESSION EVENT LOGS</div><button className="export-btn">EXPORT CSV</button></div>
          <div className="logs-container">
            <table className="events-table">
              <thead><tr><th>TIME</th><th>PROMPT</th><th>TYPE</th><th>SCORE</th><th>RESPONSE</th><th>ACTION</th></tr></thead>
              <tbody>
                {history.map(log => (
                  <tr key={log.id}>
                    <td>{log.timestamp.toLocaleTimeString()}</td>
                    <td className="prompt-cell">{log.prompt}</td>
                    <td><span className="type-tag">{log.type}</span></td>
                    <td><span className={`score-tag ${log.riskLevel.toLowerCase()}`}>{log.riskScore}%</span></td>
                    <td className="response-cell">{log.response || 'N/A'}</td>
                    <td><span className={`action-badge ${log.riskLevel.toLowerCase()}`}>{log.riskLevel}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
