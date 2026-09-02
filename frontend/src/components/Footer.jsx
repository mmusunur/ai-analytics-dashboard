import React from 'react'

export default function Footer() {
  const currentYear = new Date().getFullYear()
  return (
    <footer id="app-footer" style={{
      padding: '20px 32px',
      borderTop: '1px solid var(--border-color, rgba(255,255,255,0.08))',
      background: 'var(--bg-card)',
      marginTop: 'auto',
      display: 'flex',
      justify: 'space-between',
      alignItems: 'center',
      flexWrap: 'wrap',
      gap: '12px',
      fontSize: '12px',
      color: 'var(--text-secondary)'
    }}>
      <div>
        © {currentYear} <strong>AI Analytics Dashboard</strong>. All rights reserved.
      </div>
      <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
        <span>Powered by ⚡ Autonomous AI Agent Fleet</span>
        <span>•</span>
        <a href="#privacy" style={{ color: 'var(--text-secondary, #9ca3af)', textDecoration: 'none' }}>Privacy Policy</a>
        <span>•</span>
        <a href="#terms" style={{ color: 'var(--text-secondary, #9ca3af)', textDecoration: 'none' }}>Terms of Service</a>
      </div>
    </footer>
  )
}
