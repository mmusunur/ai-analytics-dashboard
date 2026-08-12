import React from 'react';

export default function Navbar() {
  return (
    <header className="navbar">
      <div className="navbar-container">
        <div className="navbar-brand">
          <span className="logo-icon">⚡</span>
          <span className="logo-text">AI Analytics Dashboard</span>
        </div>
        <nav className="navbar-links">
          <a href="#overview" className="nav-link active">Overview</a>
          <a href="#analytics" className="nav-link">ML Analytics</a>
          <a href="#data" className="nav-link">Datasets</a>
          <a href="#agents" className="nav-link">Agent Network</a>
          <a href="#settings" className="nav-link">Settings</a>
        </nav>
        <div className="navbar-actions">
          <span className="status-badge live">● Live Agent Loop</span>
        </div>
      </div>
    </header>
  );
}
