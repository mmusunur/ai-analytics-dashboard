/**
 * TaskDeliveryNotice — tells the user what the agent built and how to use it.
 */
import { Link } from 'react-router-dom'
import { Sparkles, MapPin, ListOrdered, ExternalLink } from 'lucide-react'

export default function TaskDeliveryNotice({ guide, taskTitle, compact = false, onDismiss }) {
  if (!guide?.headline) return null

  const route = guide.route || '/'
  const steps = guide.steps || []

  if (compact) {
    return (
      <div style={{
        marginTop: '8px', padding: '8px 10px', borderRadius: '8px',
        background: 'rgba(124,58,237,0.12)', border: '1px solid rgba(167,139,250,0.35)',
        fontSize: '11px',
      }}>
        <div style={{ fontWeight: 700, color: '#c4b5fd', marginBottom: '4px' }}>📦 {guide.headline}</div>
        <Link to={route} style={{ color: '#60a5fa', fontWeight: 600, textDecoration: 'none' }}>
          {guide.route_label || 'Open'} →
        </Link>
      </div>
    )
  }

  return (
    <div
      id="task-delivery-notice"
      style={{
        background: 'linear-gradient(135deg, rgba(30,27,75,0.85) 0%, rgba(15,23,42,0.95) 100%)',
        border: '1px solid rgba(124,58,237,0.45)',
        borderRadius: '12px',
        padding: '16px 18px',
        marginBottom: '16px',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Sparkles size={18} color="#a78bfa" />
          <span style={{ fontSize: '14px', fontWeight: 800, color: '#e2e8f0' }}>
            Agent delivered — how to use it
          </span>
        </div>
        {onDismiss && (
          <button
            type="button"
            onClick={onDismiss}
            style={{
              background: 'rgba(255,255,255,0.08)', border: 'none', borderRadius: '6px',
              color: '#94a3b8', cursor: 'pointer', padding: '4px 10px', fontSize: '12px',
            }}
          >
            Dismiss
          </button>
        )}
      </div>

      {taskTitle && (
        <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '6px' }}>Task: {taskTitle}</div>
      )}

      <div style={{
        fontSize: '15px', fontWeight: 700, color: '#fcd34d', marginTop: '10px', lineHeight: 1.4,
      }}>
        {guide.headline}
      </div>

      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', marginTop: '12px' }}>
        <MapPin size={14} color="#34d399" style={{ marginTop: '2px', flexShrink: 0 }} />
        <div>
          <div style={{ fontSize: '10px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase' }}>Where</div>
          <div style={{ fontSize: '13px', color: '#cbd5e1' }}>{guide.where}</div>
        </div>
      </div>

      {steps.length > 0 && (
        <div style={{ marginTop: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
            <ListOrdered size={14} color="#a78bfa" />
            <span style={{ fontSize: '10px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase' }}>
              How to use
            </span>
          </div>
          <ol style={{ margin: 0, paddingLeft: '20px', fontSize: '12px', color: '#cbd5e1', lineHeight: 1.7 }}>
            {steps.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ol>
        </div>
      )}

      <Link
        to={route}
        style={{
          display: 'inline-flex', alignItems: 'center', gap: '6px', marginTop: '14px',
          padding: '8px 16px', borderRadius: '8px', fontWeight: 700, fontSize: '13px',
          background: 'linear-gradient(135deg, #7c3aed, #6d28d9)', color: '#fff',
          textDecoration: 'none', boxShadow: '0 4px 14px rgba(124,58,237,0.35)',
        }}
      >
        <ExternalLink size={14} />
        {guide.route_label || 'Open feature'}
      </Link>
    </div>
  )
}

export { TaskDeliveryNotice }
