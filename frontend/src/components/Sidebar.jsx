import { useState, useEffect } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import axios from 'axios'
import {
  LayoutDashboard, BarChart3, LineChart, Bot,
  Database, ChevronRight, Menu, EyeOff, Kanban, Plug
} from 'lucide-react'

const navItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard, section: 'MAIN' },
  { path: '/analytics', label: 'Analytics', icon: BarChart3, section: 'MAIN' },
  { path: '/charts', label: 'Charts Explorer', icon: LineChart, section: 'MAIN' },
  { path: '/data', label: 'Data Manager', icon: Database, section: 'DATA' },
  { path: '/sprints', label: 'Sprint Board', icon: Kanban, section: 'AGENTS' },
  { path: '/agents', label: 'Agent Monitor', icon: Bot, section: 'AGENTS' },
  { path: '/mcp', label: 'MCP Explorer', icon: Plug, section: 'AGENTS' },
]

const AGENT_LABELS = {
  orchestrator: 'Orchestrator',
  builder: 'Builder',
  tester: 'Tester',
  git: 'Git Agent',
  git_agent: 'Git Agent',
  sprint_watcher: 'Sprint Watcher',
  memory: 'Memory',
}

const DEFAULT_AGENTS = [
  'sprint_watcher', 'builder', 'tester', 'git_agent', 'memory', 'orchestrator',
].map((key) => [key, { status: 'idle', current_task: 'Loading…' }])

const API = import.meta.env.VITE_API_URL || ''

export default function Sidebar({ collapsed, onToggle, onHide }) {
  const location = useLocation()
  const [agentsData, setAgentsData] = useState({})
  const [pipeline, setPipeline] = useState({ phase: 'idle' })
  const [agentsError, setAgentsError] = useState(false)

  useEffect(() => {
    let cancelled = false

    const fetchStatus = () => {
      axios.get(`${API}/api/agents/status`, { timeout: 8000 })
        .then(res => {
          if (cancelled) return
          if (res.data?.agents) {
            setAgentsData(res.data.agents)
            setAgentsError(false)
          }
          if (res.data?.pipeline) setPipeline(res.data.pipeline)
        })
        .catch(() => {
          if (!cancelled) setAgentsError(true)
        })
    }
    fetchStatus()
    const timer = setInterval(fetchStatus, 10000)
    return () => {
      cancelled = true
      clearInterval(timer)
    }
  }, [])

  const sections = [...new Set(navItems.map(n => n.section))]

  const isAgentRunning = (name, info) => {
    const task = (info?.current_task || '').toLowerCase()
    const status = (info?.status || '').toLowerCase()
    return status === 'running' || task.includes('building') || task.includes('test') ||
      task.includes('active task') || task.includes('picked') || task.includes('implementing')
  }

  const pipelineActive = pipeline.phase && !['idle', 'done'].includes(pipeline.phase)

  const agentEntries = Object.keys(agentsData).length > 0
    ? Object.entries(agentsData)
    : DEFAULT_AGENTS

  return (
    <aside
      className={`sidebar ${collapsed ? 'collapsed' : ''}`}
      style={{
        width: collapsed ? '72px' : '272px',
        minWidth: collapsed ? '72px' : '272px',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        overflowX: 'hidden'
      }}
    >
      <div
        className="sidebar-logo"
        style={{
          display: 'flex',
          flexDirection: 'row',
          alignItems: 'center',
          justifyContent: collapsed ? 'center' : 'space-between',
          padding: collapsed ? '14px 2px' : '16px 12px',
          gap: collapsed ? '5px' : '0px',
          width: '100%'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div
            className="logo-icon"
            title="AgenticOps AI"
            style={{
              width: collapsed ? '30px' : '40px',
              height: collapsed ? '30px' : '40px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              borderRadius: collapsed ? '6px' : '12px'
            }}
            onClick={collapsed ? onToggle : undefined}
          >
            <BarChart3 size={collapsed ? 16 : 20} color="#7C3AED" />
          </div>
          {!collapsed && (
            <div>
              <div className="logo-text">AgenticOps AI</div>
              <div className="logo-subtitle">Autonomous Dashboard</div>
            </div>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <button
            id="sidebar-toggle-btn"
            onClick={onToggle}
            title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            style={{
              background: 'transparent', border: 'none', color: '#FFFFFF',
              padding: '6px', borderRadius: '6px', cursor: 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              width: collapsed ? '30px' : '36px', height: collapsed ? '30px' : '36px',
            }}
          >
            <Menu size={22} color="#FFFFFF" strokeWidth={2.5} />
          </button>
          {onHide && !collapsed && (
            <button
              id="sidebar-hide-btn"
              onClick={onHide}
              title="Hide sidebar"
              style={{
                background: 'rgba(148, 163, 184, 0.12)',
                border: '1px solid var(--border-color)',
                color: 'var(--text-secondary)', padding: '6px', borderRadius: '6px', cursor: 'pointer',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                height: '40px', width: '32px'
              }}
            >
              <EyeOff size={16} />
            </button>
          )}
        </div>
      </div>

      <nav className="sidebar-nav">
        {sections.map(section => (
          <div key={section}>
            {!collapsed && <div className="nav-section-label">{section}</div>}
            {navItems
              .filter(item => item.section === section)
              .map(item => {
                const Icon = item.icon
                const isActive = location.pathname === item.path
                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    className={`nav-item ${isActive ? 'active' : ''}`}
                    title={collapsed ? item.label : undefined}
                    style={{
                      justifyContent: collapsed ? 'center' : 'flex-start',
                      padding: collapsed ? '10px 0' : '10px 14px'
                    }}
                  >
                    <Icon size={18} className="nav-icon" />
                    {!collapsed && <span>{item.label}</span>}
                    {!collapsed && isActive && <ChevronRight size={14} style={{ marginLeft: 'auto', opacity: 0.5 }} />}
                  </NavLink>
                )
              })}
          </div>
        ))}
      </nav>

      {!collapsed && (
        <div className="sidebar-agent-panel" style={{
          padding: '14px 8px',
          borderTop: '1px solid var(--border-subtle)',
        }}>
          <div className="nav-section-label" style={{ paddingTop: 0, marginBottom: '6px' }}>AGENT STATUS</div>

          {agentsError && (
            <div style={{ fontSize: '10px', color: '#fbbf24', marginBottom: '6px' }}>
              Backend unreachable — showing last known / default agents
            </div>
          )}

          {pipelineActive && pipeline.task_title && (
            <div style={{
              padding: '8px', borderRadius: '8px', marginBottom: '8px',
              background: 'rgba(124, 58, 237, 0.15)',
              border: '1px solid rgba(124, 58, 237, 0.35)',
              fontSize: '11px',
            }}>
              <div style={{ fontWeight: 800, color: '#a78bfa', marginBottom: '4px' }}>ACTIVE SPRINT TASK</div>
              <div style={{ color: '#e2e8f0', fontWeight: 600, lineHeight: 1.3 }}>{pipeline.task_title}</div>
              <div style={{ color: '#94a3b8', marginTop: '4px' }}>
                Phase: <strong style={{ color: '#c4b5fd' }}>{pipeline.phase}</strong>
                {pipeline.active_agent && <> · {pipeline.active_agent}</>}
              </div>
            </div>
          )}

          {agentEntries.map(([name, info]) => {
            const working = isAgentRunning(name, info) || (pipeline.active_agent === name && pipelineActive)
            const label = AGENT_LABELS[name] || name.replace('_', ' ')
            const taskDesc = info?.current_task || 'Idle'

            return (
              <div key={name} title={taskDesc} style={{
                padding: '5px 8px', borderRadius: '6px', marginBottom: '4px',
                background: working ? 'rgba(124, 58, 237, 0.12)' : 'transparent',
                border: working ? '1px solid rgba(124, 58, 237, 0.3)' : '1px solid transparent',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px' }}>
                  <span className={`status-dot ${working ? 'running' : (info?.status || 'idle')}`} />
                  <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{label}</span>
                  <span style={{
                    marginLeft: 'auto', fontSize: '10px',
                    color: working ? '#a78bfa' : 'var(--text-muted)',
                    fontWeight: working ? 700 : 400
                  }}>
                    {working ? 'WORKING' : (info?.status || 'idle')}
                  </span>
                </div>
                <div style={{
                  fontSize: '10px', color: working ? '#c4b5fd' : 'var(--text-muted)',
                  marginTop: '2px', whiteSpace: 'nowrap', overflow: 'hidden',
                  textOverflow: 'ellipsis', paddingLeft: '14px'
                }}>
                  {taskDesc}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </aside>
  )
}
