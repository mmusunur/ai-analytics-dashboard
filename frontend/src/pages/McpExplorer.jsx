import { useCallback } from 'react'
import { motion } from 'framer-motion'
import { Plug, Server, Wrench, ArrowRight, CheckCircle2, AlertTriangle, XCircle } from 'lucide-react'
import axios from 'axios'
import { Link } from 'react-router-dom'
import { useLivePoll } from '../hooks/useLivePoll'
import MonitorRefreshBar from '../components/MonitorRefreshBar'

const API = import.meta.env.VITE_API_URL || ''

const SERVER_COLORS = {
  plane: '#06b6d4',
  github: '#3b82f6',
  memory: '#f59e0b',
  browser: '#10b981',
}

const HEALTH_STYLE = {
  online: { icon: CheckCircle2, color: '#34d399', label: 'Online' },
  degraded: { icon: AlertTriangle, color: '#fbbf24', label: 'Degraded' },
  offline: { icon: XCircle, color: '#f87171', label: 'Offline' },
}

export default function McpExplorer() {
  const fetchMcp = useCallback(async () => {
    const res = await axios.get(`${API}/api/mcp/status`, { timeout: 12000 })
    return res.data
  }, [])

  const { data, lastUpdated, isRefreshing, isInitialLoad, error, refresh, secondsUntilRefresh } =
    useLivePoll(fetchMcp, { intervalMs: 15000, enabled: true })

  const servers = data?.servers || []

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}
    >
      <div style={{ marginBottom: '8px' }}>
        <h1 style={{ fontSize: '26px', fontWeight: 800, margin: 0, display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Plug size={28} color="#7c3aed" /> MCP Explorer
        </h1>
        <p style={{ fontSize: '14px', color: 'var(--text-secondary)', marginTop: '6px' }}>
          Model Context Protocol servers — tools, health, and how agents connect to external services.
        </p>
      </div>

      <MonitorRefreshBar
        title="MCP Fleet Status"
        lastUpdated={lastUpdated}
        isRefreshing={isRefreshing || isInitialLoad}
        paused={false}
        secondsUntilRefresh={secondsUntilRefresh}
        error={error}
        onRefresh={refresh}
        intervalLabel="15s"
      />

      <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginBottom: '20px' }}>
        <StatChip label="Servers" value={data?.serverCount ?? '—'} color="#a78bfa" />
        <StatChip label="Online" value={data?.onlineCount ?? '—'} color="#34d399" />
        <StatChip label="Tools" value={data?.toolCount ?? '—'} color="#60a5fa" />
        <StatChip label="Client" value="mcp_client.py" color="#94a3b8" mono />
      </div>

      {/* Architecture flow */}
      <div style={{
        padding: '16px 20px', borderRadius: '12px', marginBottom: '24px',
        background: 'linear-gradient(135deg, rgba(124,58,237,0.08) 0%, rgba(6,182,212,0.08) 100%)',
        border: '1px solid rgba(124,58,237,0.25)',
      }}>
        <div style={{ fontSize: '12px', fontWeight: 800, color: '#a78bfa', marginBottom: '12px', textTransform: 'uppercase' }}>
          MCP Data Flow
        </div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', flexWrap: 'wrap', gap: '8px', fontSize: '12px' }}>
          {['Agent Fleet', 'mcp_client.py', 'MCP Server', 'External API'].map((step, i, arr) => (
            <span key={step} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{
                padding: '8px 14px', borderRadius: '8px', fontWeight: 700,
                background: i === 1 ? 'rgba(124,58,237,0.25)' : 'var(--bg-card)',
                border: '1px solid var(--border-color)', color: 'var(--text-primary)',
              }}>
                {step}
              </span>
              {i < arr.length - 1 && <ArrowRight size={16} color="#64748b" />}
            </span>
          ))}
        </div>
        <p style={{ fontSize: '11px', color: '#64748b', marginTop: '12px', marginBottom: 0, textAlign: 'center' }}>
          Config: <code style={{ color: '#94a3b8' }}>{data?.configPath || 'mcp_servers/mcp_config.json'}</code>
          {' · '}
          <Link to="/agents" style={{ color: '#60a5fa' }}>Agent Monitor</Link>
          {' · '}
          <Link to="/sprints" style={{ color: '#60a5fa' }}>Sprint Board</Link>
        </p>
      </div>

      <div className="mcp-servers-grid">
        {servers.map((server) => (
          <McpServerCard key={server.id} server={server} />
        ))}
      </div>

      {servers.length === 0 && !isInitialLoad && (
        <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-secondary)' }}>
          No MCP servers loaded — check mcp_servers/mcp_config.json
        </div>
      )}
    </motion.div>
  )
}

function McpServerCard({ server }) {
  const color = SERVER_COLORS[server.id] || '#7c3aed'
  const health = HEALTH_STYLE[server.health] || HEALTH_STYLE.offline
  const HealthIcon = health.icon

  return (
    <div style={{
      background: 'var(--bg-card)',
      border: `1px solid ${color}40`,
      borderRadius: '12px',
      padding: '18px',
      boxShadow: '0 4px 16px rgba(0,0,0,0.12)',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <div style={{
            padding: '10px', borderRadius: '10px',
            background: `${color}18`, border: `1px solid ${color}50`,
          }}>
            <Server size={20} color={color} />
          </div>
          <div>
            <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 800 }}>{server.name}</h3>
            <div style={{ fontSize: '10px', color: '#64748b', fontFamily: 'monospace', marginTop: '2px' }}>
              {server.backedBy}
            </div>
          </div>
        </div>
        <span style={{
          display: 'flex', alignItems: 'center', gap: '4px',
          fontSize: '10px', fontWeight: 800, padding: '4px 10px', borderRadius: '12px',
          background: `${health.color}18`, color: health.color, border: `1px solid ${health.color}40`,
        }}>
          <HealthIcon size={12} /> {health.label}
        </span>
      </div>

      <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.5, margin: '0 0 12px' }}>
        {server.description}
      </p>

      <div style={{ fontSize: '11px', color: '#64748b', marginBottom: '10px' }}>
        {server.healthDetail}
      </div>

      <div style={{ marginBottom: '12px' }}>
        <div style={{ fontSize: '10px', fontWeight: 700, color: '#94a3b8', marginBottom: '6px' }}>USED BY</div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
          {(server.usedBy || []).map((agent) => (
            <span key={agent} style={{
              fontSize: '10px', padding: '3px 8px', borderRadius: '6px',
              background: 'rgba(124,58,237,0.12)', color: '#c4b5fd', fontWeight: 600,
            }}>
              {agent}
            </span>
          ))}
        </div>
      </div>

      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '10px', fontWeight: 700, color: '#94a3b8', marginBottom: '8px' }}>
          <Wrench size={12} /> TOOLS ({server.toolCount})
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          {(server.tools || []).map((tool) => {
            const name = typeof tool === 'string' ? tool : tool.name
            const desc = typeof tool === 'object' ? tool.description : ''
            return (
              <div key={name} style={{
                padding: '8px 10px', borderRadius: '6px',
                background: 'var(--bg-secondary)', border: '1px solid var(--border-color)',
              }}>
                <div style={{ fontSize: '12px', fontWeight: 700, fontFamily: 'monospace', color: color }}>{name}</div>
                {desc && <div style={{ fontSize: '10px', color: '#64748b', marginTop: '2px' }}>{desc}</div>}
              </div>
            )
          })}
        </div>
      </div>

      {server.envKeys?.length > 0 && (
        <div style={{ marginTop: '12px', fontSize: '10px', color: server.envConfigured ? '#34d399' : '#fbbf24' }}>
          Env: {server.envKeys.join(', ')} {server.envConfigured ? '✓ configured' : '⚠ missing'}
        </div>
      )}
    </div>
  )
}

function StatChip({ label, value, color, mono }) {
  return (
    <div style={{
      padding: '8px 14px', borderRadius: '8px', background: 'var(--bg-card)',
      border: '1px solid var(--border-color)', fontSize: '12px',
    }}>
      <span style={{ color: 'var(--text-secondary)' }}>{label}: </span>
      <strong style={{ color, fontFamily: mono ? 'monospace' : 'inherit', fontSize: mono ? '11px' : 'inherit' }}>
        {value}
      </strong>
    </div>
  )
}
