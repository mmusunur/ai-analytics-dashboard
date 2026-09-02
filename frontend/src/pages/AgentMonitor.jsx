import { useCallback } from 'react'
import { motion } from 'framer-motion'
import {
  Cpu, Activity, Terminal, ShieldCheck, RefreshCw, Database, GitBranch, Zap, ExternalLink
} from 'lucide-react'
import { Link } from 'react-router-dom'
import axios from 'axios'
import { useLivePoll } from '../hooks/useLivePoll'
import { useAgentWorking } from '../context/AgentWorkingContext'
import MonitorRefreshBar from '../components/MonitorRefreshBar'
import AgentPipelineTracker from '../components/AgentPipelineTracker'
import TaskQueuePanel from '../components/TaskQueuePanel'

const API = import.meta.env.VITE_API_URL || ''

const AGENT_DEFS = [
  { name: 'Sprint Watcher', key: 'sprint_watcher', role: 'Plane task pickup & pipeline orchestration', icon: Activity, color: '#06b6d4' },
  { name: 'Builder Agent', key: 'builder', role: 'Autonomous code implementation', icon: Cpu, color: '#7c3aed' },
  { name: 'Tester Agent', key: 'tester', role: 'Unit + browser + sprint dynamic tests', icon: ShieldCheck, color: '#10b981' },
  { name: 'Git Agent', key: 'git_agent', role: 'Commit & push after task completion', icon: GitBranch, color: '#3b82f6' },
  { name: 'Memory Manager', key: 'memory', role: 'Persistent state & conversation logs', icon: Database, color: '#f59e0b' },
  { name: 'Orchestrator', key: 'orchestrator', role: 'Fleet health & watchdog coordination', icon: Terminal, color: '#f43f5e' },
]

function formatUpdated(iso) {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  } catch {
    return '—'
  }
}

function agentStatusLabel(key, info, pipeline) {
  const task = (info?.current_task || '').toLowerCase()
  const isPipelineActive = pipeline?.active_agent === key
  if (isPipelineActive) return { label: 'ACTIVE NOW', tone: 'active' }
  if (info?.status === 'running' || task.includes('active') || task.includes('building') || task.includes('test')) {
    return { label: 'RUNNING', tone: 'running' }
  }
  if (info?.status === 'idle') return { label: 'IDLE', tone: 'idle' }
  return { label: (info?.status || 'unknown').toUpperCase(), tone: 'idle' }
}

const toneStyles = {
  active: { bg: 'rgba(124,58,237,0.25)', color: '#c4b5fd', border: 'rgba(124,58,237,0.55)' },
  running: { bg: 'rgba(16,185,129,0.15)', color: '#34d399', border: 'rgba(16,185,129,0.4)' },
  idle: { bg: 'rgba(245,158,11,0.12)', color: '#fbbf24', border: 'rgba(245,158,11,0.35)' },
}

export default function AgentMonitor() {
  const { agentWorking, agentWorkingTask, agentWorkingSince } = useAgentWorking()

  const fetchFleet = useCallback(async () => {
    const res = await axios.get(`${API}/api/agents/status`, { timeout: 8000 })
    return res.data
  }, [])

  const {
    data: fleet,
    lastUpdated,
    isRefreshing,
    isInitialLoad,
    error,
    refresh,
    secondsUntilRefresh,
  } = useLivePoll(fetchFleet, {
    intervalMs: 4000,
    pause: false,
    enabled: true,
  })

  const agents = fleet?.agents || {}
  const pipeline = fleet?.pipeline || {}
  const taskQueue = fleet?.task_queue || {}
  const runningCount = Object.values(agents).filter((a) => (a.status || '').toLowerCase() === 'running').length

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}
    >
      <div style={{ marginBottom: '8px' }}>
        <h1 style={{ fontSize: '26px', fontWeight: 800, color: 'var(--text-primary)', margin: 0 }}>
          Agent Monitor
        </h1>
        <p style={{ fontSize: '14px', color: 'var(--text-secondary)', marginTop: '6px' }}>
          Live fleet telemetry — which agent is working, current sprint task, and pipeline phase.
        </p>
      </div>

      <MonitorRefreshBar
        title="Agent Fleet Telemetry"
        lastUpdated={lastUpdated}
        isRefreshing={isRefreshing || isInitialLoad}
        paused={false}
        agentWorking={agentWorking}
        secondsUntilRefresh={secondsUntilRefresh}
        error={error}
        onRefresh={refresh}
        intervalLabel="4s"
      />

      {agentWorking && (
        <div style={{
          marginBottom: '16px', padding: '10px 14px', borderRadius: '10px',
          background: 'rgba(124,58,237,0.12)', border: '1px solid rgba(124,58,237,0.35)',
          fontSize: '12px', color: '#c4b5fd',
        }}>
          ⚡ <strong>Agent working</strong> — fleet telemetry stays live so you can track pipeline progress.
          {agentWorkingTask && <> Task: <em>{agentWorkingTask}</em></>}
        </div>
      )}

      <AgentPipelineTracker
        pipeline={pipeline}
        agentWorking={agentWorking}
        agentWorkingTask={agentWorkingTask}
      />

      <TaskQueuePanel taskQueue={taskQueue} pipeline={pipeline} />

      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        marginBottom: '16px', flexWrap: 'wrap', gap: '12px',
      }}>
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          <StatPill label="Agents running" value={`${runningCount}/6`} color="#34d399" />
          <StatPill label="Pipeline phase" value={pipeline.phase || 'idle'} color="#a78bfa" />
          <StatPill label="Queued tasks" value={taskQueue?.pending?.length ?? 0} color="#38bdf8" />
          <StatPill label="Progress" value={pipeline?.progress_pct ? `${pipeline.progress_pct}%` : '—'} color="#34d399" />
          <StatPill label="Backend sync" value={fleet?.status === 'success' ? 'Connected' : 'Live'} color="#60a5fa" />
        </div>
        <Link to="/sprints" style={{
          display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px',
          color: '#60a5fa', fontWeight: 600, textDecoration: 'none',
        }}>
          Open Sprint Monitor <ExternalLink size={14} />
        </Link>
        <Link to="/mcp" style={{
          display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px',
          color: '#a78bfa', fontWeight: 600, textDecoration: 'none',
        }}>
          MCP Explorer <ExternalLink size={14} />
        </Link>
      </div>

      <div
        id="agents-grid-container"
        className="agents-grid"
        style={{ gap: '16px' }}
      >
        {AGENT_DEFS.map((ag) => {
          const info = agents[ag.key] || {}
          const Icon = ag.icon
          const { label, tone } = agentStatusLabel(ag.key, info, pipeline)
          const style = toneStyles[tone]

          return (
            <div
              key={ag.key}
              style={{
                background: 'var(--bg-card)',
                border: `1px solid ${ag.color}35`,
                borderRadius: '12px',
                padding: '18px',
                boxShadow: tone === 'active' ? `0 0 24px ${ag.color}25` : '0 4px 12px rgba(0,0,0,0.12)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                  <div style={{
                    padding: '10px', borderRadius: '10px',
                    background: `${ag.color}18`, border: `1px solid ${ag.color}40`,
                  }}>
                    <Icon size={20} color={ag.color} />
                  </div>
                  <div>
                    <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 700 }}>{ag.name}</h3>
                    <p style={{ margin: '2px 0 0', fontSize: '11px', color: 'var(--text-secondary)' }}>{ag.role}</p>
                  </div>
                </div>
                <span style={{
                  fontSize: '10px', fontWeight: 800, padding: '4px 10px', borderRadius: '12px',
                  background: style.bg, color: style.color, border: `1px solid ${style.border}`,
                }}>
                  {label}
                </span>
              </div>

              <div style={{
                background: 'var(--bg-secondary)', borderRadius: '8px', padding: '12px',
                border: '1px solid var(--border-color)', minHeight: '52px',
              }}>
                <div style={{ fontSize: '10px', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '4px', textTransform: 'uppercase' }}>
                  Current activity
                </div>
                <div style={{ fontSize: '13px', fontWeight: 600, lineHeight: 1.4, wordBreak: 'break-word' }}>
                  {info.current_task || 'Idle — awaiting next sprint task'}
                </div>
              </div>

              <div style={{
                display: 'flex', justifyContent: 'space-between', marginTop: '12px',
                fontSize: '11px', color: 'var(--text-secondary)',
              }}>
                <span>Updated {formatUpdated(info.last_updated)}</span>
                {info.pid && <span style={{ fontFamily: 'monospace' }}>PID {info.pid}</span>}
                <span style={{ color: ag.color, display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <Zap size={11} /> Live
                </span>
              </div>
            </div>
          )
        })}
      </div>
    </motion.div>
  )
}

function StatPill({ label, value, color }) {
  return (
    <div style={{
      padding: '8px 14px', borderRadius: '8px', background: 'var(--bg-card)',
      border: '1px solid var(--border-color)', fontSize: '12px',
    }}>
      <span style={{ color: 'var(--text-secondary)' }}>{label}: </span>
      <strong style={{ color }}>{value}</strong>
    </div>
  )
}
