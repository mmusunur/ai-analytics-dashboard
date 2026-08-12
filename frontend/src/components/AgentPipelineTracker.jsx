/**
 * AgentPipelineTracker — visual 6-stage pipeline (embedded in monitor pages).
 */
import { useState, useEffect } from 'react'
import { Activity } from 'lucide-react'

const PHASES = [
  { key: 'pickup', label: '1. Pickup', short: 'Pickup', agent: 'Sprint Watcher' },
  { key: 'building', label: '2. Building', short: 'Build', agent: 'Builder Agent' },
  { key: 'testing', label: '3. Testing', short: 'Test', agent: 'Tester Agent' },
  { key: 'closing', label: '4. Close', short: 'Close', agent: 'Plane Agent' },
  { key: 'git_push', label: '5. Git Push', short: 'Git', agent: 'Git Agent' },
  { key: 'done', label: '6. Done', short: 'Done', agent: '' },
]

const TEST_SUBPHASE_LABELS = {
  starting: 'Preparing suite',
  sprint_cases: 'Registering sprint cases',
  unit: 'Unit tests (pytest)',
  browser: 'Browser tests (Playwright)',
  excel: 'Updating TEST_CASES.xlsx',
  done: 'Finishing',
}

function normalizePhase(phase) {
  return phase === 'retry' ? 'building' : phase
}

function phaseIndex(phase) {
  const i = PHASES.findIndex((p) => p.key === normalizePhase(phase))
  return i >= 0 ? i : -1
}

function formatElapsed(isoStart) {
  if (!isoStart) return null
  const sec = Math.max(0, Math.floor((Date.now() - new Date(isoStart).getTime()) / 1000))
  if (sec < 60) return `${sec}s`
  const m = Math.floor(sec / 60)
  return `${m}m ${sec % 60}s`
}

export default function AgentPipelineTracker({ pipeline, agentWorking, agentWorkingTask }) {
  const [, tick] = useState(0)
  const phase = pipeline?.phase || 'idle'
  const taskTitle = pipeline?.task_title || agentWorkingTask || ''
  const activeAgent = pipeline?.active_agent || ''
  const message = pipeline?.message || ''
  const testSubphase = pipeline?.test_subphase || ''
  const testStartedAt = pipeline?.test_started_at || ''
  const currentIdx = phaseIndex(phase)
  const completedSteps = new Set(pipeline?.completed_steps || [])
  const isActive = !['idle', 'done', 'failed'].includes(phase)
  const isFailed = phase === 'failed'
  const isTesting = phase === 'testing'
  const isVerifyWaiting = phase === 'idle' && taskTitle && message.includes('Verify-close failed')

  useEffect(() => {
    if (!isTesting && !testStartedAt) return undefined
    const id = setInterval(() => tick((n) => n + 1), 1000)
    return () => clearInterval(id)
  }, [isTesting, testStartedAt])

  const elapsed = formatElapsed(testStartedAt)

  const isStepComplete = (key) => {
    if (phase === 'done') return true
    return completedSteps.has(key)
  }

  return (
    <div
      id="agent-pipeline-tracker"
      style={{
        background: 'linear-gradient(135deg, rgba(30,27,75,0.6) 0%, rgba(15,23,42,0.9) 100%)',
        border: `1px solid ${phase === 'failed' ? 'rgba(239,68,68,0.45)' : phase === 'done' ? 'rgba(16,185,129,0.45)' : isVerifyWaiting ? 'rgba(245,158,11,0.4)' : 'rgba(124,58,237,0.35)'}`,
        borderRadius: '12px',
        padding: '18px 20px',
        marginBottom: '20px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
        <Activity size={18} color={isActive || isVerifyWaiting ? '#a78bfa' : '#64748b'} />
        <span style={{ fontSize: '14px', fontWeight: 800, color: 'var(--text-primary)' }}>
          Sprint Task Pipeline
        </span>
        <span style={{
          marginLeft: 'auto', fontSize: '11px', fontWeight: 700, textTransform: 'uppercase',
          color: phase === 'idle' ? (isVerifyWaiting ? '#fcd34d' : '#94a3b8') : phase === 'done' ? '#34d399' : phase === 'failed' ? '#f87171' : '#c4b5fd',
        }}>
          {phase === 'idle'
            ? (isVerifyWaiting ? 'Waiting — verify-close retry' : 'Monitoring — waiting for next task')
            : phase === 'retry'
              ? 'Retry — same step (fix before advancing)'
              : phase.replace('_', ' ')}
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

      {(activeAgent && (isActive || isVerifyWaiting)) || (isFailed && message) || isTesting ? (
        <div style={{
          fontSize: '13px', color: isFailed ? '#fca5a5' : '#c4b5fd', marginBottom: '14px',
          display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap',
        }}>
          {activeAgent && (isActive || isVerifyWaiting) && (
            <span style={{
              background: isVerifyWaiting ? 'rgba(245,158,11,0.25)' : 'rgba(124,58,237,0.3)',
              padding: '4px 12px', borderRadius: '20px',
              fontWeight: 800, fontSize: '11px',
              animation: isVerifyWaiting ? 'none' : 'pulse 1.5s ease-in-out infinite',
            }}>
              {isVerifyWaiting ? '⏳' : '⚡'} {activeAgent.replace(/_/g, ' ').toUpperCase()} {isVerifyWaiting ? 'WAITING' : 'WORKING'}
            </span>
          )}
          {isTesting && testSubphase && (
            <span style={{
              background: 'rgba(59,130,246,0.25)', padding: '4px 12px', borderRadius: '20px',
              fontWeight: 700, fontSize: '11px', color: '#93c5fd',
            }}>
              🧪 {TEST_SUBPHASE_LABELS[testSubphase] || testSubphase}
              {elapsed && ` · ${elapsed}`}
            </span>
          )}
          {isFailed && (
            <span style={{
              background: 'rgba(239,68,68,0.25)', padding: '4px 12px', borderRadius: '20px',
              fontWeight: 800, fontSize: '11px', color: '#fca5a5',
            }}>
              ✕ FAILED — check Task Queue below
            </span>
          )}
          {message && <span style={{ color: '#94a3b8', fontSize: '12px' }}>{message}</span>}
        </div>
      ) : null}

      {isTesting && testSubphase && (
        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '12px' }}>
          {Object.entries(TEST_SUBPHASE_LABELS).filter(([k]) => k !== 'done').map(([key, label]) => {
            const order = ['starting', 'sprint_cases', 'unit', 'browser', 'excel']
            const cur = order.indexOf(testSubphase)
            const idx = order.indexOf(key)
            const done = idx < cur
            const active = key === testSubphase
            return (
              <span
                key={key}
                style={{
                  fontSize: '9px', fontWeight: 700, padding: '3px 8px', borderRadius: '12px',
                  background: active ? 'rgba(124,58,237,0.35)' : done ? 'rgba(16,185,129,0.15)' : 'rgba(255,255,255,0.05)',
                  color: active ? '#e9d5ff' : done ? '#34d399' : '#64748b',
                  border: active ? '1px solid rgba(167,139,250,0.5)' : '1px solid transparent',
                }}
              >
                {done ? '✓ ' : active ? '● ' : ''}{label}
              </span>
            )
          })}
        </div>
      )}

      {(isActive || isVerifyWaiting) && (pipeline?.progress_pct > 0) && (
        <div style={{ marginBottom: '14px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: '#64748b', marginBottom: '4px' }}>
            <span>Progress</span>
            <span>{pipeline.progress_pct}%</span>
          </div>
          <div style={{ height: '8px', background: 'rgba(255,255,255,0.08)', borderRadius: '4px', overflow: 'hidden' }}>
            <div style={{
              width: `${pipeline.progress_pct}%`, height: '100%',
              background: phase === 'failed' ? '#ef4444' : isVerifyWaiting ? '#f59e0b' : 'linear-gradient(90deg, #7c3aed, #34d399)',
              transition: 'width 0.4s ease',
            }} />
          </div>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(100px, 1fr))', gap: '8px' }}>
        {PHASES.map((p) => {
          let bg = 'rgba(255,255,255,0.04)'
          let color = '#64748b'
          let border = '1px solid rgba(255,255,255,0.06)'
          let icon = '○'

          if (isStepComplete(p.key)) {
            bg = 'rgba(16,185,129,0.12)'; color = '#34d399'; border = '1px solid rgba(16,185,129,0.35)'; icon = '✓'
          } else if (p.key === normalizePhase(phase)) {
            const isRetry = phase === 'retry' && p.key === 'building'
            bg = isRetry ? 'rgba(245,158,11,0.18)' : 'rgba(124,58,237,0.22)'
            color = isRetry ? '#fcd34d' : '#e9d5ff'
            border = isRetry ? '2px solid rgba(245,158,11,0.55)' : '2px solid rgba(167,139,250,0.6)'
            icon = isRetry ? '↻' : '●'
          } else if (isVerifyWaiting && p.key === 'testing') {
            bg = 'rgba(245,158,11,0.15)'; color = '#fcd34d'; border = '1px solid rgba(245,158,11,0.45)'; icon = '⏳'
          } else if (isFailed && p.key === 'testing') {
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
              <div style={{ fontSize: '11px', fontWeight: 800, color }}>
                {phase === 'retry' && p.key === 'building' ? 'Build ↻' : p.short}
              </div>
              <div style={{ fontSize: '9px', color: '#64748b', marginTop: '2px' }}>{p.agent}</div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export { PHASES, phaseIndex }
