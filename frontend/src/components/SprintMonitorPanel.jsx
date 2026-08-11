/**
 * SprintMonitorPanel — live sprint watcher status + pipeline on Sprint Board page.
 */
import { Link } from 'react-router-dom'
import { Bot, ExternalLink } from 'lucide-react'
import AgentPipelineTracker from './AgentPipelineTracker'

export default function SprintMonitorPanel({
  pipeline,
  agentWorking,
  agentWorkingTask,
  inProgressCount,
  todoCount,
  watcherActive,
}) {
  return (
    <div id="sprint-monitor-panel" style={{ marginBottom: '20px' }}>
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        marginBottom: '12px', flexWrap: 'wrap', gap: '10px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Bot size={20} color="#7C3AED" />
          <span style={{ fontSize: '15px', fontWeight: 800, color: 'var(--text-primary)' }}>
            Sprint Monitor
          </span>
          <span style={{
            fontSize: '11px', fontWeight: 700, padding: '3px 10px', borderRadius: '20px',
            background: watcherActive ? 'rgba(16,185,129,0.15)' : 'rgba(245,158,11,0.15)',
            color: watcherActive ? '#34d399' : '#fbbf24',
          }}>
            {watcherActive ? '● Watcher active' : '○ Watcher idle'}
          </span>
        </div>
        <Link to="/agents" style={{
          fontSize: '12px', fontWeight: 600, color: '#60a5fa', textDecoration: 'none',
          display: 'flex', alignItems: 'center', gap: '4px',
        }}>
          Agent Monitor <ExternalLink size={12} />
        </Link>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '10px', marginBottom: '14px' }}>
        <MiniStat label="In Progress" value={inProgressCount} color="#c4b5fd" highlight={inProgressCount > 0} />
        <MiniStat label="To Do (ready)" value={todoCount} color="#60a5fa" />
        <MiniStat label="Pipeline" value={pipeline?.phase || 'idle'} color="#a78bfa" />
        <MiniStat
          label="Active agent"
          value={pipeline?.active_agent?.replace(/_/g, ' ') || (agentWorking ? 'working' : '—')}
          color="#34d399"
          highlight={Boolean(pipeline?.active_agent || agentWorking)}
        />
      </div>

      <AgentPipelineTracker
        pipeline={pipeline}
        agentWorking={agentWorking}
        agentWorkingTask={agentWorkingTask}
      />
    </div>
  )
}

function MiniStat({ label, value, color, highlight }) {
  return (
    <div style={{
      padding: '12px 14px', borderRadius: '10px',
      background: highlight ? `${color}12` : 'var(--bg-card)',
      border: `1px solid ${highlight ? color + '55' : 'var(--border-color)'}`,
    }}>
      <div style={{ fontSize: '10px', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase' }}>{label}</div>
      <div style={{ fontSize: '18px', fontWeight: 800, color, marginTop: '4px', textTransform: 'capitalize' }}>{value}</div>
    </div>
  )
}
