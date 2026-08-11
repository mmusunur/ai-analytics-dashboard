/**
 * QuickNavBar — sticky top tabs for fast screen switching.
 */
import { NavLink, useLocation } from 'react-router-dom'
import {
  LayoutDashboard, BarChart3, Kanban, Bot, Plug, Database, LineChart
} from 'lucide-react'

const QUICK_ROUTES = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard, color: '#818cf8' },
  { path: '/analytics', label: 'Analytics', icon: BarChart3, color: '#38bdf8' },
  { path: '/sprints', label: 'Sprint Board', icon: Kanban, color: '#a78bfa' },
  { path: '/agents', label: 'Agents', icon: Bot, color: '#34d399' },
  { path: '/mcp', label: 'MCP', icon: Plug, color: '#f472b6' },
  { path: '/data', label: 'Data', icon: Database, color: '#fbbf24' },
  { path: '/charts', label: 'Charts', icon: LineChart, color: '#22d3ee' },
]

export default function QuickNavBar() {
  const location = useLocation()
  const current = QUICK_ROUTES.find((r) => r.path === location.pathname)

  return (
    <nav className="quick-nav-bar" aria-label="Quick navigation">
      <div className="quick-nav-current">
        {current ? (
          <>
            <current.icon size={18} color={current.color} />
            <span>{current.label}</span>
          </>
        ) : (
          <span>Navigate</span>
        )}
      </div>
      <div className="quick-nav-tabs">
        {QUICK_ROUTES.map(({ path, label, icon: Icon, color }) => (
          <NavLink
            key={path}
            to={path}
            className={({ isActive }) => `quick-nav-tab ${isActive ? 'active' : ''}`}
            title={label}
          >
            <Icon size={15} style={{ color: location.pathname === path ? color : undefined }} />
            <span>{label}</span>
          </NavLink>
        ))}
      </div>
    </nav>
  )
}
