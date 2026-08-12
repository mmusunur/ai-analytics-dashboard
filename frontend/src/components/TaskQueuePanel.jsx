/**
 * TaskQueuePanel — multi-task sprint queue with progress (pending / active / completed).
 */
import { ListTodo, PlayCircle, CheckCircle2, XCircle } from 'lucide-react'

function ProgressBar({ pct, color = '#7c3aed' }) {
  const value = Math.min(100, Math.max(0, pct || 0))
  return (
    <div style={{ height: '6px', background: 'rgba(255,255,255,0.08)', borderRadius: '4px', overflow: 'hidden', marginTop: '8px' }}>
      <div style={{
        width: `${value}%`, height: '100%', background: color,
        borderRadius: '4px', transition: 'width 0.4s ease',
      }} />
    </div>
  )
}

function QueueSection({ title, icon: Icon, color, items, renderItem, emptyText }) {
  if (!items?.length) {
    return (
      <div style={{ padding: '10px 12px', background: 'rgba(0,0,0,0.15)', borderRadius: '8px', minHeight: '48px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', fontWeight: 700, color, marginBottom: '6px' }}>
          <Icon size={14} /> {title}
        </div>
        <div style={{ fontSize: '11px', color: '#64748b', fontStyle: 'italic' }}>{emptyText}</div>
      </div>
    )
  }
  return (
    <div style={{ padding: '10px 12px', background: 'rgba(0,0,0,0.15)', borderRadius: '8px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', fontWeight: 700, color, marginBottom: '8px' }}>
        <Icon size={14} /> {title} ({items.length})
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {items.map(renderItem)}
      </div>
    </div>
  )
}

export default function TaskQueuePanel({ taskQueue, pipeline }) {
  const queue = taskQueue || {}
  const pending = queue.pending || []
  const active = queue.active
  const completed = (queue.completed || []).slice(0, 5)
  const failed = (queue.failed || []).slice(0, 3)

  const activeItems = active ? [active] : []

  return (
    <div id="task-queue-panel" style={{
      background: 'var(--bg-card)',
      border: '1px solid var(--border-color)',
      borderRadius: '12px',
      padding: '16px',
      marginBottom: '20px',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
        <span style={{ fontSize: '14px', fontWeight: 800, color: 'var(--text-primary)' }}>Task Queue</span>
        <span style={{ fontSize: '11px', color: '#64748b' }}>
          {pending.length} queued · {active ? '1 active' : '0 active'} · {completed.length} recent done
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '12px' }}>
        <QueueSection
          title="Queued (To Do)"
          icon={ListTodo}
          color="#60a5fa"
          items={pending}
          emptyText="No tasks waiting — add To Do tasks in Plane"
          renderItem={(t) => (
            <div key={t.id} style={{ fontSize: '12px', color: '#cbd5e1' }}>
              <div style={{ fontWeight: 600 }}>{t.title}</div>
              <div style={{ fontSize: '10px', color: '#64748b', marginTop: '2px' }}>
                {(t.priority || 'medium').toUpperCase()} · {t.project_name || 'Project'}
              </div>
            </div>
          )}
        />

        <QueueSection
          title="Active Now"
          icon={PlayCircle}
          color="#a78bfa"
          items={activeItems}
          emptyText="No task in progress"
          renderItem={(t) => (
            <div key={t.id}>
              <div style={{ fontSize: '13px', fontWeight: 700, color: '#e2e8f0' }}>{t.title}</div>
              <div style={{ fontSize: '10px', color: '#c4b5fd', marginTop: '4px', fontWeight: 700 }}>
                {(t.phase || pipeline?.phase || 'working').replace(/_/g, ' ').toUpperCase()}
                {t.active_agent && ` · ${t.active_agent.replace(/_/g, ' ')}`}
              </div>
              {t.message && (
                <div style={{ fontSize: '10px', color: '#94a3b8', marginTop: '4px' }}>{t.message}</div>
              )}
              <ProgressBar pct={t.progress_pct ?? pipeline?.progress_pct} color="#a78bfa" />
              <div style={{ fontSize: '10px', color: '#64748b', marginTop: '4px', textAlign: 'right' }}>
                {t.progress_pct ?? pipeline?.progress_pct ?? 0}% complete
              </div>
            </div>
          )}
        />

        <QueueSection
          title="Recently Completed"
          icon={CheckCircle2}
          color="#34d399"
          items={completed}
          emptyText="No completed tasks yet this session"
          renderItem={(t) => (
            <div key={t.id} style={{ fontSize: '12px' }}>
              <div style={{ fontWeight: 600, color: '#a7f3d0' }}>✓ {t.title}</div>
              <div style={{ fontSize: '10px', color: '#64748b', marginTop: '2px' }}>
                {t.duration_seconds ? `${t.duration_seconds}s` : 'closed on Plane'}
              </div>
              <ProgressBar pct={100} color="#34d399" />
            </div>
          )}
        />
      </div>

      {failed.length > 0 && (
        <div style={{ marginTop: '12px', padding: '10px 12px', background: 'rgba(239,68,68,0.08)', borderRadius: '8px', border: '1px solid rgba(239,68,68,0.25)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', fontWeight: 700, color: '#f87171', marginBottom: '6px' }}>
            <XCircle size={14} /> Returned to To Do ({failed.length})
          </div>
          {failed.map((t) => (
            <div key={t.id} style={{ fontSize: '11px', color: '#fca5a5', marginBottom: '4px' }}>
              {t.title} — {t.reason?.slice(0, 80) || 'tests failed'}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
