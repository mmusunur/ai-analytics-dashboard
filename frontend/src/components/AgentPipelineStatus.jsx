/**
 * AgentPipelineStatus — Live sprint pipeline tracker visible on every page.
 * Shows: active task, current phase (Pickup → Build → Test → Close → Git), active agent.
 */
import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'
import { Bot, ChevronRight, Activity } from 'lucide-react'

const API = import.meta.env.VITE_API_URL || ''

const PHASES = [
  { key: 'pickup', label: '1. Pickup', agent: 'Sprint Watcher' },
  { key: 'building', label: '2. Building', agent: 'Builder Agent' },
  { key: 'testing', label: '3. Testing', agent: 'Tester Agent' },
  { key: 'closing', label: '4. Close Task', agent: 'Plane Agent' },
  { key: 'git_push', label: '5. Git Push', agent: 'Git Agent' },
  { key: 'done', label: '6. Done', agent: '' },
]

const phaseIndex = (phase) => {
  const i = PHASES.findIndex((p) => p.key === phase)
  return i >= 0 ? i : -1
}

export default function AgentPipelineStatus({ compact = true }) {
  const [data, setData] = useState(null)

  useEffect(() => {
    const fetchStatus = () => {
      axios.get(`${API}/api/agents/status`, { timeout: 5000 })
        .then((res) => setData(res.data))
        .catch(() => {})
    }
    fetchStatus()
    const timer = setInterval(fetchStatus, 4000)
    return () => clearInterval(timer)
  }, [])

  const pipeline = data?.pipeline || {}
  const phase = pipeline.phase || 'idle'
  const taskTitle = pipeline.task_title || data?.agent_working_task || ''
  const activeAgent = pipeline.active_agent || ''
  const message = pipeline.message || ''
  const currentIdx = phaseIndex(phase)
  const isActive = phase !== 'idle' && phase !== 'done' && phase !== 'failed'

  if (compact && !isActive && phase !== 'done' && phase !== 'failed') {
    return (
      <Link
        to="/agents"
        id="agent-pipeline-status-link"
        style={{
          position: 'fixed',
          bottom: '20px',
          right: '20px',
          zIndex: 900,
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          background: 'var(--bg-card)',
          border: '1px solid var(--border-color)',
          borderRadius: '10px',
          padding: '10px 14px',
          fontSize: '12px',
          fontWeight: 600,
          color: 'var(--text-secondary)',
          textDecoration: 'none',
          boxShadow: '0 4px 16px rgba(0,0,0,0.2)',
        }}
        title="View agent fleet status"
      >
        <Bot size={16} color="#7C3AED" />
        Agents idle — view status
        <ChevronRight size={14} />
      </Link>
    )
  }

  return (
    <div
      id="agent-pipeline-status-panel"
      style={{
        position: compact ? 'fixed' : 'relative',
        bottom: compact ? '20px' : undefined,
        right: compact ? '20px' : undefined,
        zIndex: 900,
        width: compact ? '360px' : '100%',
        maxWidth: '100%',
        background: 'linear-gradient(135deg, rgba(30,27,75,0.95) 0%, rgba(15,23,42,0.98) 100%)',
        border: `1px solid ${phase === 'failed' ? 'rgba(239,68,68,0.5)' : phase === 'done' ? 'rgba(16,185,129,0.5)' : 'rgba(124,58,237,0.4)'}`,
        borderRadius: '12px',
        padding: '14px 16px',
        boxShadow: '0 8px 32px rgba(0,0,0,0.35)',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Activity size={16} color={isActive ? '#a78bfa' : '#34d399'} />
          <span style={{ fontSize: '11px', fontWeight: 800, color: '#a78bfa', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Sprint Pipeline
          </span>
        </div>
        <Link to="/agents" style={{ fontSize: '11px', color: '#60a5fa', fontWeight: 600, textDecoration: 'none' }}>
          Full monitor →
        </Link>
      </div>

      {taskTitle && (
        <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '8px', lineHeight: 1.3 }}>
          {taskTitle}
        </div>
      )}

      {activeAgent && isActive && (
        <div style={{
          fontSize: '12px', color: '#c4b5fd', marginBottom: '10px',
          background: 'rgba(124,58,237,0.15)', padding: '6px 10px', borderRadius: '6px',
        }}>
          ⚡ Active: <strong>{activeAgent.replace('_', ' ')}</strong>
          {message && <span style={{ display: 'block', fontSize: '11px', color: '#94a3b8', marginTop: '2px' }}>{message}</span>}
        </div>
      )}

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
        {PHASES.map((p, i) => {
          let bg = 'rgba(255,255,255,0.06)'
          let color = '#64748b'
          let border = '1px solid rgba(255,255,255,0.08)'
          if (phase === 'done' || (currentIdx >= 0 && i < currentIdx)) {
            bg = 'rgba(16,185,129,0.15)'; color = '#34d399'; border = '1px solid rgba(16,185,129,0.3)'
          } else if (p.key === phase) {
            bg = 'rgba(124,58,237,0.25)'; color = '#e9d5ff'; border = '1px solid rgba(124,58,237,0.5)'
          } else if (phase === 'failed' && p.key === 'testing') {
            bg = 'rgba(239,68,68,0.15)'; color = '#fca5a5'; border = '1px solid rgba(239,68,68,0.4)'
          }
          return (
            <span
              key={p.key}
              style={{
                fontSize: '10px', fontWeight: 700, padding: '3px 8px', borderRadius: '6px',
                background: bg, color, border,
              }}
            >
              {p.label}
            </span>
          )
        })}
      </div>

      {phase === 'failed' && (
        <div style={{ marginTop: '8px', fontSize: '11px', color: '#fca5a5' }}>
          Task returned to To Do — check Agent Monitor for details.
        </div>
      )}
      {phase === 'done' && (
        <div style={{ marginTop: '8px', fontSize: '11px', color: '#34d399' }}>
          ✓ Task completed — sprint watcher monitoring for next task.
        </div>
      )}
    </div>
  )
}
