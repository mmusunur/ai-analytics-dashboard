import { useState } from 'react'
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import Analytics from './pages/Analytics'
import SprintBoard from './pages/SprintBoard'
import AgentMonitor from './pages/AgentMonitor'
import McpExplorer from './pages/McpExplorer'
import Footer from './components/Footer'
import AgentWorkingBanner from './components/AgentWorkingBanner'
import AgentPipelineStatus from './components/AgentPipelineStatus'
import QuickNavBar from './components/QuickNavBar'
import { AgentWorkingProvider, useAgentWorking } from './context/AgentWorkingContext'
import { Menu } from 'lucide-react'
import './index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 5 * 60 * 1000, retry: 2 }
  }
})

// Placeholder pages for sections not yet built
const Placeholder = ({ title, emoji }) => (
  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '60vh', gap: 16 }}>
    <span style={{ fontSize: 64 }}>{emoji}</span>
    <h2 style={{ color: 'var(--text-primary)', fontSize: 24, fontWeight: 700 }}>{title}</h2>
    <p style={{ color: 'var(--text-secondary)' }}>This page is being built by the AI agents...</p>
    <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
      {[...Array(3)].map((_, i) => (
        <div key={i} style={{
          width: 8, height: 8, borderRadius: '50%',
          background: 'var(--color-primary)',
          animation: `pulse ${0.8 + i * 0.2}s ease-in-out infinite alternate`
        }} />
      ))}
    </div>
  </div>
)

function AppShell() {
  const location = useLocation()
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [sidebarHidden, setSidebarHidden] = useState(false)
  const { agentWorking, agentWorkingTask, agentWorkingSince } = useAgentWorking()

  const hideFloatingPipeline = ['/agents', '/sprints', '/mcp'].includes(location.pathname)

  return (
    <div className="app-layout">
      <AgentWorkingBanner
        agentWorking={agentWorking}
        taskName={agentWorkingTask}
        since={agentWorkingSince}
      />

      {sidebarHidden && (
        <button
          id="sidebar-unhide-btn"
          onClick={() => setSidebarHidden(false)}
          title="Show sidebar"
          style={{
            position: 'fixed', top: agentWorking ? '56px' : '16px', left: '16px', zIndex: 999,
            background: 'linear-gradient(135deg, var(--color-primary), #6d28d9)',
            color: '#fff', border: '1px solid rgba(255, 255, 255, 0.2)',
            padding: '10px 16px', borderRadius: '8px', cursor: 'pointer',
            boxShadow: '0 4px 20px rgba(124, 58, 237, 0.5)',
            display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 600, fontSize: '13px'
          }}
        >
          <Menu size={18} /> Show Nav Bar
        </button>
      )}

      {!sidebarHidden && (
        <Sidebar
          collapsed={sidebarCollapsed}
          onToggle={() => setSidebarCollapsed(prev => !prev)}
          onHide={() => setSidebarHidden(true)}
        />
      )}

      <main
        className="main-content"
        style={{
          marginLeft: sidebarHidden ? '0' : (sidebarCollapsed ? '72px' : '272px'),
          maxWidth: sidebarHidden ? '100vw' : (sidebarCollapsed ? 'calc(100vw - 72px)' : 'calc(100vw - 272px)'),
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          display: 'flex', flexDirection: 'column', minHeight: '100vh',
          padding: sidebarHidden ? '32px 32px 32px 64px' : '32px',
          paddingTop: agentWorking ? '56px' : '32px',
        }}
      >
        <QuickNavBar />
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/charts" element={<Placeholder title="Charts Explorer" emoji="📈" />} />
          <Route path="/data" element={<Placeholder title="Data Manager" emoji="🗄️" />} />
          <Route path="/agents" element={<AgentMonitor />} />
          <Route path="/mcp" element={<McpExplorer />} />
          <Route path="/sprints" element={<SprintBoard />} />
        </Routes>
        <Footer />
      </main>

      {!hideFloatingPipeline && <AgentPipelineStatus compact />}
    </div>
  )
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <AgentWorkingProvider>
          <AppShell />
        </AgentWorkingProvider>
      </Router>
    </QueryClientProvider>
  )
}

export default App
