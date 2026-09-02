/**
 * AgentPipelineTracker — visual 6-stage pipeline (embedded in monitor pages).
 */
import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'
import { Activity } from 'lucide-react'
import TaskDeliveryNotice from './TaskDeliveryNotice'

const API = import.meta.env.VITE_API_URL || ''

const PHASES = [
  { key: 'pickup', label: '1. Pickup', short: 'Pickup', agent: 'Sprint Watcher' },
  { key: 'building', label: '2. Building', short: 'Build', agent: 'Builder Agent' },
  { key: 'testing', label: '3. Testing', short: 'Test', agent: 'Tester Agent' },
  { key: 'closing', label: '4. Close', short: 'Close', agent: 'Plane Agent' },
  { key: 'git_push', label: '5. Git Push', short: 'Git', agent: 'Git Agent' },
  { key: 'done', label: '6. Done', short: 'Done', agent: '' },
]

const BUILD_SUBPHASE_LABELS = {
  starting: 'Starting build gate',
  classifying: 'Classifying intent',
  spec_load: 'Loading task spec',
  patching: 'Applying code patches',
  unit_verify: 'Unit verification (pytest)',
  done: 'Build gate finishing',
}

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

function BuildDetailPanel({ open, onClose, pipeline, taskTitle, isBuilding, buildElapsed }) {
  if (!open) return null

  const files = pipeline?.build_files_modified || []
  const functionality = pipeline?.build_functionality || []
  const usageGuide = pipeline?.build_usage_guide || null
  const intents = pipeline?.build_intents || []
  const outcome = pipeline?.build_outcome || ''
  const duration = pipeline?.build_duration_seconds
  const subphase = pipeline?.build_subphase || ''

  return (
    <>
      <div
        role="presentation"
        onClick={onClose}
        style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.55)', zIndex: 9998,
        }}
      />
      <div
        id="build-detail-panel"
        role="dialog"
        aria-label="Build details"
        style={{
          position: 'fixed', top: '50%', left: '50%', transform: 'translate(-50%, -50%)',
          zIndex: 9999, width: 'min(420px, 92vw)', maxHeight: '80vh', overflow: 'auto',
          background: 'linear-gradient(145deg, #1e1b4b 0%, #0f172a 100%)',
          border: '1px solid rgba(124,58,237,0.45)', borderRadius: '12px',
          padding: '18px 20px', boxShadow: '0 20px 50px rgba(0,0,0,0.5)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
          <div>
            <div style={{ fontSize: '15px', fontWeight: 800, color: '#e2e8f0' }}>🔨 Build Details</div>
            {taskTitle && (
              <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '4px' }}>{taskTitle}</div>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            style={{
              background: 'rgba(255,255,255,0.08)', border: 'none', borderRadius: '6px',
              color: '#94a3b8', cursor: 'pointer', padding: '4px 10px', fontSize: '14px',
            }}
          >
            ✕
          </button>
        </div>

        {isBuilding && (
          <div style={{
            fontSize: '12px', color: '#fcd34d', marginBottom: '12px', padding: '8px 10px',
            background: 'rgba(245,158,11,0.12)', borderRadius: '8px',
          }}>
            Build in progress — {BUILD_SUBPHASE_LABELS[subphase] || subphase || 'working'}
            {buildElapsed && ` · ${buildElapsed}`}
          </div>
        )}

        <div style={{ marginBottom: '14px' }}>
          <div style={{ fontSize: '11px', fontWeight: 700, color: '#a78bfa', marginBottom: '6px', textTransform: 'uppercase' }}>
            Outcome
          </div>
          <div style={{ fontSize: '13px', color: '#e2e8f0' }}>
            {outcome === 'verify_only' && 'Verify-only — requirements already in codebase'}
            {outcome === 'code_changed' && `Code changed — ${files.length} file(s)${duration != null ? ` in ${duration}s` : isBuilding ? ' (in progress)' : ''}`}
            {!outcome && isBuilding && 'Build running — files & functionality update live below'}
            {!outcome && !isBuilding && files.length > 0 && `Code changed — ${files.length} file(s)`}
            {!outcome && !isBuilding && !files.length && 'No build recorded for this task yet'}
          </div>
        </div>

        <div style={{ marginBottom: '14px' }}>
          <div style={{ fontSize: '11px', fontWeight: 700, color: '#a78bfa', marginBottom: '6px', textTransform: 'uppercase' }}>
            Functionality added / verified
          </div>
          {functionality.length > 0 ? (
            <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '12px', color: '#cbd5e1', lineHeight: 1.6 }}>
              {functionality.map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
          ) : (
            <div style={{ fontSize: '12px', color: '#64748b', fontStyle: 'italic' }}>
              {isBuilding ? 'Classification in progress…' : 'No functionality summary yet'}
            </div>
          )}
        </div>

        {usageGuide?.headline && (
          <div style={{ marginBottom: '14px' }}>
            <div style={{ fontSize: '11px', fontWeight: 700, color: '#fcd34d', marginBottom: '8px', textTransform: 'uppercase' }}>
              How to use (for you)
            </div>
            <TaskDeliveryNotice guide={usageGuide} taskTitle={taskTitle} compact />
            {usageGuide.route && (
              <Link
                to={usageGuide.route}
                style={{ fontSize: '11px', color: '#60a5fa', marginTop: '6px', display: 'inline-block' }}
              >
                → {usageGuide.route_label || 'Open feature'}
              </Link>
            )}
          </div>
        )}

        {intents.length > 0 && (
          <div style={{ marginBottom: '14px' }}>
            <div style={{ fontSize: '11px', fontWeight: 700, color: '#64748b', marginBottom: '6px' }}>Detected intents</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
              {intents.map((i) => (
                <span key={i} style={{
                  fontSize: '9px', padding: '2px 8px', borderRadius: '10px',
                  background: 'rgba(124,58,237,0.2)', color: '#c4b5fd',
                }}>
                  {i}
                </span>
              ))}
            </div>
          </div>
        )}

        <div>
          <div style={{ fontSize: '11px', fontWeight: 700, color: '#a78bfa', marginBottom: '6px', textTransform: 'uppercase' }}>
            Files changed
          </div>
          {files.length > 0 ? (
            <ul style={{
              margin: 0, padding: '10px 12px', listStyle: 'none',
              background: 'rgba(0,0,0,0.25)', borderRadius: '8px', fontSize: '11px',
              fontFamily: 'ui-monospace, monospace', color: '#86efac', lineHeight: 1.7,
            }}>
              {files.map((f) => (
                <li key={f}>📄 {f}</li>
              ))}
            </ul>
          ) : (
            <div style={{ fontSize: '12px', color: '#64748b', fontStyle: 'italic' }}>
              {outcome === 'verify_only' ? 'No new files — existing code matched task' : 'No files listed yet'}
            </div>
          )}
        </div>
      </div>
    </>
  )
}

export default function AgentPipelineTracker({ pipeline, agentWorking, agentWorkingTask }) {
  const [, tick] = useState(0)
  const [buildDetailOpen, setBuildDetailOpen] = useState(false)
  const [detailPipeline, setDetailPipeline] = useState(pipeline)

  useEffect(() => {
    setDetailPipeline(pipeline)
  }, [pipeline])

  useEffect(() => {
    if (!buildDetailOpen) return undefined
    const fetchDetail = async () => {
      try {
        const res = await axios.get(`${API}/api/agents/status`, { timeout: 4000 })
        if (res.data?.pipeline) setDetailPipeline(res.data.pipeline)
      } catch {
        /* keep last snapshot */
      }
    }
    fetchDetail()
    const id = setInterval(fetchDetail, 2000)
    return () => clearInterval(id)
  }, [buildDetailOpen, pipeline?.task_id])

  const activePipeline = buildDetailOpen ? detailPipeline : pipeline
  const phase = activePipeline?.phase || pipeline?.phase || 'idle'
  const taskTitle = activePipeline?.task_title || pipeline?.task_title || agentWorkingTask || ''
  const activeAgent = activePipeline?.active_agent || pipeline?.active_agent || ''
  const message = activePipeline?.message || pipeline?.message || ''
  const testSubphase = activePipeline?.test_subphase || pipeline?.test_subphase || ''
  const testStartedAt = activePipeline?.test_started_at || pipeline?.test_started_at || ''
  const buildSubphase = activePipeline?.build_subphase || pipeline?.build_subphase || ''
  const buildStartedAt = activePipeline?.build_started_at || pipeline?.build_started_at || ''
  const buildOutcome = activePipeline?.build_outcome || pipeline?.build_outcome || ''
  const buildFiles = activePipeline?.build_files_modified || pipeline?.build_files_modified || []
  const buildDuration = activePipeline?.build_duration_seconds ?? pipeline?.build_duration_seconds
  const currentIdx = phaseIndex(phase)
  const completedSteps = new Set(activePipeline?.completed_steps || pipeline?.completed_steps || [])
  const isActive = !['idle', 'done', 'failed'].includes(phase)
  const isFailed = phase === 'failed'
  const isTesting = phase === 'testing'
  const isBuilding = phase === 'building' || phase === 'retry'
  const isVerifyWaiting = phase === 'idle' && taskTitle && message.includes('Verify-close failed')

  useEffect(() => {
    if ((!isTesting && !testStartedAt) && (!isBuilding && !buildStartedAt)) return undefined
    const id = setInterval(() => tick((n) => n + 1), 1000)
    return () => clearInterval(id)
  }, [isTesting, testStartedAt, isBuilding, buildStartedAt])

  const testElapsed = formatElapsed(testStartedAt)
  const buildElapsed = formatElapsed(buildStartedAt)

  const isMonitoringIdle = phase === 'idle' && !taskTitle && !pipeline?.task_id

  const phaseStepIndex = {
    idle: -1, pickup: 0, building: 1, retry: 1, testing: 2, closing: 3, git_push: 4, done: 5, failed: -1,
  }
  const stepIndex = { pickup: 0, building: 1, testing: 2, closing: 3, git_push: 4, done: 5 }
  const currentStepIdx = phaseStepIndex[normalizePhase(phase)] ?? -1

  const isStepComplete = (key) => {
    if (isMonitoringIdle) return false
    if (phase === 'done') return true
    if (completedSteps.has(key)) return true
    const idx = stepIndex[key] ?? -1
    return currentStepIdx >= 0 && idx >= 0 && currentStepIdx > idx
  }

  const hasBuildDetail = Boolean(
    activePipeline?.build_files_modified?.length
    || pipeline?.build_files_modified?.length
    || activePipeline?.build_functionality?.length
    || pipeline?.build_functionality?.length
    || activePipeline?.build_outcome
    || pipeline?.build_outcome
    || activePipeline?.build_usage_guide?.headline
    || isBuilding
    || completedSteps.has('building')
  )
  const buildStepClickable = isStepComplete('building') || isBuilding || hasBuildDetail

  return (
    <>
    <BuildDetailPanel
      open={buildDetailOpen}
      onClose={() => setBuildDetailOpen(false)}
      pipeline={detailPipeline}
      taskTitle={taskTitle}
      isBuilding={isBuilding}
      buildElapsed={buildElapsed}
    />
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

      {(activeAgent && (isActive || isVerifyWaiting)) || (isFailed && message) || isTesting || isBuilding ? (
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
              {testElapsed && ` · ${testElapsed}`}
            </span>
          )}
          {isBuilding && buildSubphase && (
            <span style={{
              background: 'rgba(245,158,11,0.22)', padding: '4px 12px', borderRadius: '20px',
              fontWeight: 700, fontSize: '11px', color: '#fcd34d',
            }}>
              🔨 {BUILD_SUBPHASE_LABELS[buildSubphase] || buildSubphase}
              {buildElapsed && ` · ${buildElapsed}`}
            </span>
          )}
          {buildOutcome === 'verify_only' && completedSteps.has('building') && !isBuilding && (
            <span style={{
              background: 'rgba(245,158,11,0.2)', padding: '4px 12px', borderRadius: '20px',
              fontSize: '11px', color: '#fcd34d', fontWeight: 700,
            }}>
              Verify-only build ({buildDuration != null ? `${buildDuration}s` : 'no new files'})
            </span>
          )}
          {buildOutcome === 'code_changed' && buildFiles.length > 0 && completedSteps.has('building') && !isBuilding && (
            <span style={{
              background: 'rgba(16,185,129,0.2)', padding: '4px 12px', borderRadius: '20px',
              fontSize: '11px', color: '#6ee7b7', fontWeight: 700,
            }}>
              {buildFiles.length} file(s) changed ({buildDuration != null ? `${buildDuration}s` : ''})
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

      {isBuilding && buildSubphase && (
        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '12px' }}>
          {Object.entries(BUILD_SUBPHASE_LABELS).filter(([k]) => k !== 'done').map(([key, label]) => {
            const order = ['starting', 'classifying', 'spec_load', 'patching', 'unit_verify']
            const cur = order.indexOf(buildSubphase)
            const idx = order.indexOf(key)
            const done = idx < cur
            const active = key === buildSubphase
            return (
              <span
                key={key}
                style={{
                  fontSize: '9px', fontWeight: 700, padding: '3px 8px', borderRadius: '12px',
                  background: active ? 'rgba(245,158,11,0.35)' : done ? 'rgba(16,185,129,0.15)' : 'rgba(255,255,255,0.05)',
                  color: active ? '#fcd34d' : done ? '#34d399' : '#64748b',
                  border: active ? '1px solid rgba(251,191,36,0.5)' : '1px solid transparent',
                }}
              >
                {done ? '✓ ' : active ? '● ' : ''}{label}
              </span>
            )
          })}
        </div>
      )}

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
            const verifyBuild = p.key === 'building' && buildOutcome === 'verify_only'
            bg = verifyBuild ? 'rgba(245,158,11,0.12)' : 'rgba(16,185,129,0.12)'
            color = verifyBuild ? '#fcd34d' : '#34d399'
            border = verifyBuild ? '1px solid rgba(245,158,11,0.35)' : '1px solid rgba(16,185,129,0.35)'
            icon = verifyBuild ? '✓v' : '✓'
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
              data-testid={`pipeline-step-${p.key}`}
              data-step-complete={isStepComplete(p.key) ? 'true' : 'false'}
              role={buildStepClickable && p.key === 'building' ? 'button' : undefined}
              tabIndex={buildStepClickable && p.key === 'building' ? 0 : undefined}
              onClick={p.key === 'building' && buildStepClickable ? () => setBuildDetailOpen(true) : undefined}
              onKeyDown={p.key === 'building' && buildStepClickable ? (e) => {
                if (e.key === 'Enter' || e.key === ' ') setBuildDetailOpen(true)
              } : undefined}
              title={p.key === 'building' && buildStepClickable ? 'Click to see files changed & functionality' : undefined}
              style={{
                textAlign: 'center', padding: '10px 8px', borderRadius: '8px',
                background: bg, border, transition: 'all 0.2s ease',
                cursor: p.key === 'building' && buildStepClickable ? 'pointer' : 'default',
                outline: 'none',
              }}
            >
              <div style={{ fontSize: '16px', marginBottom: '4px' }}>{icon}</div>
              <div style={{ fontSize: '11px', fontWeight: 800, color }}>
                {phase === 'retry' && p.key === 'building' ? 'Build ↻' : p.short}
              </div>
              <div style={{ fontSize: '9px', color: '#64748b', marginTop: '2px' }}>{p.agent}</div>
              {p.key === 'building' && buildStepClickable && (
                <div style={{ fontSize: '8px', color: '#a78bfa', marginTop: '4px' }}>Click for details</div>
              )}
            </div>
          )
        })}
      </div>
    </div>
    </>
  )
}

export { PHASES, phaseIndex }
