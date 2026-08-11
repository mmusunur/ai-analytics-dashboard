/**
 * AgentPipelineTracker — visual 6-stage pipeline (embedded in monitor pages).
 */
import { Activity } from 'lucide-react'

const PHASES = [
  { key: 'pickup', label: '1. Pickup', short: 'Pickup', agent: 'Sprint Watcher' },
  { key: 'building', label: '2. Building', short: 'Build', agent: 'Builder Agent' },
  { key: 'testing', label: '3. Testing', short: 'Test', agent: 'Tester Agent' },
  { key: 'closing', label: '4. Close', short: 'Close', agent: 'Plane Agent' },
  { key: 'git_push', label: '5. Git Push', short: 'Git', agent: 'Git Agent' },
  { key: 'done', label: '6. Done', short: 'Done', agent: '' },
]

function phaseIndex(phase) {
  const i = PHASES.findIndex((p) => p.key === phase)
  return i >= 0 ? i : -1
}

export default function AgentPipelineTracker({ pipeline, agentWorking, agentWorkingTask }) {
  const phase = pipeline?.phase || 'idle'
  const taskTitle = pipeline?.task_title || agentWorkingTask || ''
  const activeAgent = pipeline?.active_agent || ''
  const message = pipeline?.message || ''
  const currentIdx = phaseIndex(phase)
  const isActive = !['idle', 'done', 'failed'].includes(phase)

  return (
    <div
      id="agent-pipeline-tracker"
      style={{
        background: 'linear-gradient(135deg, rgba(30,27,75,0.6) 0%, rgba(15,23,42,0.9) 100%)',
        border: `1px solid ${phase === 'failed' ? 'rgba(239,68,68,0.45)' : phase === 'done' ? 'rgba(16,185,129,0.45)' : 'rgba(124,58,237,0.35)'}`,
        borderRadius: '12px',
        padding: '18px 20px',
        marginBottom: '20px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
        <Activity size={18} color={isActive ? '#a78bfa' : '#64748b'} />
        <span style={{ fontSize: '14px', fontWeight: 800, color: 'var(--text-primary)' }}>
          Sprint Task Pipeline
        </span>
        <span style={{
          marginLeft: 'auto', fontSize: '11px', fontWeight: 700, textTransform: 'uppercase',
          color: phase === 'idle' ? '#94a3b8' : phase === 'done' ? '#34d399' : phase === 'failed' ? '#f87171' : '#c4b5fd',
        }}>
          {phase === 'idle' ? 'Monitoring — waiting for next task' : phase.replace('_', ' ')}
        </span>
      </div>

      {taskTitle ? (
        <div style={{
          fontSize: '15px', fontWeight: 700, color: '#e2e8f0', marginBottom: '10px',
          padding: '10px 14px', background: 'rgba(0,0,0,0.25)', borderRadius: '8px',
        }}>
          📋 {taskTitle}
        </div>
      ) : (
        <div style={{ fontSize: '13px', color: '#64748b', marginBottom: '12px', fontStyle: 'italic' }}>
          No active sprint task — add a task in Plane (To Do / Unstarted) to trigger the agent pipeline.
        </div>
      )}

      {activeAgent && isActive && (
        <div style={{
          fontSize: '13px', color: '#c4b5fd', marginBottom: '14px',
          display: 'flex', alignItems: 'center', gap: '8px',
        }}>
          <span style={{
            background: 'rgba(124,58,237,0.3)', padding: '4px 12px', borderRadius: '20px',
            fontWeight: 800, fontSize: '11px', animation: 'pulse 1.5s ease-in-out infinite',
          }}>
            ⚡ {activeAgent.replace(/_/g, ' ').toUpperCase()} WORKING
          </span>
          {message && <span style={{ color: '#94a3b8', fontSize: '12px' }}>{message}</span>}
        </div>
      )}

      {isActive && (pipeline?.progress_pct > 0) && (
        <div style={{ marginBottom: '14px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: '#64748b', marginBottom: '4px' }}>
            <span>Progress</span>
            <span>{pipeline.progress_pct}%</span>
          </div>
          <div style={{ height: '8px', background: 'rgba(255,255,255,0.08)', borderRadius: '4px', overflow: 'hidden' }}>
            <div style={{
              width: `${pipeline.progress_pct}%`, height: '100%',
              background: phase === 'failed' ? '#ef4444' : 'linear-gradient(90deg, #7c3aed, #34d399)',
              transition: 'width 0.4s ease',
            }} />
          </div>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(100px, 1fr))', gap: '8px' }}>
        {PHASES.map((p, i) => {
          let bg = 'rgba(255,255,255,0.04)'
          let color = '#64748b'
          let border = '1px solid rgba(255,255,255,0.06)'
          let icon = '○'

          if (phase === 'done' || (currentIdx >= 0 && i < currentIdx)) {
            bg = 'rgba(16,185,129,0.12)'; color = '#34d399'; border = '1px solid rgba(16,185,129,0.35)'; icon = '✓'
          } else if (p.key === phase) {
            bg = 'rgba(124,58,237,0.22)'; color = '#e9d5ff'; border = '2px solid rgba(167,139,250,0.6)'; icon = '●'
          } else if (phase === 'failed' && p.key === 'testing') {
            bg = 'rgba(239,68,68,0.12)'; color = '#fca5a5'; border = '1px solid rgba(239,68,68,0.4)'; icon = '✕'
          }

          return (
            <div
              key={p.key}
              style={{
                textAlign: 'center', padding: '10px 8px', borderRadius: '8px',
                background: bg, border, transition: 'all 0.2s ease',
              }}
            >
              <div style={{ fontSize: '16px', marginBottom: '4px' }}>{icon}</div>
              <div style={{ fontSize: '11px', fontWeight: 800, color }}>{p.short}</div>
              <div style={{ fontSize: '9px', color: '#64748b', marginTop: '2px' }}>{p.agent}</div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export { PHASES, phaseIndex }
