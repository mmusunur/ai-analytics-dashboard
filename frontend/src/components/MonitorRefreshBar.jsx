/**
 * MonitorRefreshBar — shared status bar for Agent Monitor & Sprint Monitor pages.
 */
import { RefreshCw, Pause, Radio, AlertCircle, Zap } from 'lucide-react'

export default function MonitorRefreshBar({
  title = 'Live Monitor',
  lastUpdated,
  isRefreshing,
  paused,
  softPaused,
  agentWorking,
  secondsUntilRefresh,
  error,
  onRefresh,
  intervalLabel = '5s',
}) {
  const formatTime = (d) => {
    if (!d) return '—'
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  }

  const statusLabel = paused
    ? 'PAUSED'
    : softPaused
      ? `SLOW SYNC ${intervalLabel}`
      : isRefreshing
        ? 'REFRESHING…'
        : `AUTO-REFRESH ${intervalLabel} · next in ${secondsUntilRefresh}s`

  return (
    <div
      id="monitor-refresh-bar"
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '12px',
        padding: '12px 16px',
        marginBottom: '20px',
        background: 'var(--bg-card)',
        border: '1px solid var(--border-color)',
        borderRadius: '10px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {paused ? (
            <Pause size={16} color="#f59e0b" />
          ) : softPaused || agentWorking ? (
            <Zap size={16} color="#a78bfa" />
          ) : isRefreshing ? (
            <RefreshCw size={16} color="#60a5fa" className="spin" />
          ) : (
            <Radio size={16} color="#34d399" />
          )}
          <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)' }}>{title}</span>
        </div>

        <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
          Last updated: <strong style={{ color: 'var(--text-primary)' }}>{formatTime(lastUpdated)}</strong>
        </span>

        <span style={{
          fontSize: '11px', fontWeight: 700, padding: '3px 10px', borderRadius: '20px',
          background: paused ? 'rgba(245,158,11,0.15)' : softPaused ? 'rgba(124,58,237,0.15)' : 'rgba(16,185,129,0.12)',
          color: paused ? '#fbbf24' : softPaused ? '#c4b5fd' : '#34d399',
          border: `1px solid ${paused ? 'rgba(245,158,11,0.35)' : softPaused ? 'rgba(124,58,237,0.35)' : 'rgba(16,185,129,0.3)'}`,
        }}>
          {statusLabel}
        </span>
      </div>

      <button
        type="button"
        onClick={() => onRefresh(false)}
        disabled={isRefreshing}
        style={{
          display: 'flex', alignItems: 'center', gap: '8px',
          background: 'linear-gradient(135deg, #7C3AED, #6d28d9)',
          color: '#fff', border: 'none', padding: '8px 16px', borderRadius: '8px',
          fontSize: '13px', fontWeight: 600, cursor: isRefreshing ? 'wait' : 'pointer',
          opacity: isRefreshing ? 0.7 : 1,
        }}
      >
        <RefreshCw size={14} className={isRefreshing ? 'spin' : ''} />
        Refresh Now
      </button>

      {error && (
        <div style={{
          width: '100%', display: 'flex', alignItems: 'center', gap: '8px',
          fontSize: '12px', color: '#fca5a5', marginTop: '4px',
          background: 'rgba(239,68,68,0.1)', padding: '8px 12px', borderRadius: '6px',
        }}>
          <AlertCircle size={14} />
          {error}
        </div>
      )}
    </div>
  )
}
