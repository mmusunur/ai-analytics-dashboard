import React, { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  CheckCircle2, Clock, PlayCircle, RefreshCw,
  Search, Layers, Folder, Inbox, ListTodo, FolderCheck, Activity,
  AlertTriangle, CalendarClock, RotateCcw
} from 'lucide-react'
import axios from 'axios'
import { useAgentWorking } from '../context/AgentWorkingContext'
import { useLivePoll } from '../hooks/useLivePoll'
import MonitorRefreshBar from '../components/MonitorRefreshBar'
import SprintMonitorPanel from '../components/SprintMonitorPanel'

const API = import.meta.env.VITE_API_URL || ''

export default function SprintBoard() {
  const { agentWorking, agentWorkingTask } = useAgentWorking()
  const [searchTerm, setSearchTerm] = useState('')

  // Workspace & Project state
  const [workspaces, setWorkspaces] = useState([])
  const [selectedWorkspace, setSelectedWorkspace] = useState('agentbuilder')
  const [selectedProject, setSelectedProject] = useState('all')

  // Sprint expiry state
  const [sprintExpiry, setSprintExpiry] = useState(null)   // null | 'expiring_today' | 'expired'
  const [extendingSprint, setExtendingSprint] = useState(false)
  const [restoringTasks, setRestoringTasks] = useState(false)
  const [actionMsg, setActionMsg] = useState(null)

  // Column Collapse States
  const [collapsedColumns, setCollapsedColumns] = useState({
    backlog: false,
    todo: false,
    in_progress: false,
    completed: false
  })

  const toggleColumnCollapse = (colKey) => {
    setCollapsedColumns(prev => ({
      ...prev,
      [colKey]: !prev[colKey]
    }))
  }

  // Priority Filter State
  const [enabledPriorities, setEnabledPriorities] = useState({
    URGENT: true,
    HIGH: true,
    MEDIUM: true,
    LOW: true
  })

  const togglePriority = (p) => {
    setEnabledPriorities(prev => ({
      ...prev,
      [p]: !prev[p]
    }))
  }

  const fetchWorkspaces = async () => {
    try {
      const res = await axios.get(`${API}/api/sprints/workspaces`)
      if (res.data?.workspaces) {
        setWorkspaces(res.data.workspaces)
      }
    } catch (err) {
      console.error('[SprintBoard] Workspace fetch error:', err)
    }
  }

  const fetchSprintTasksApi = useCallback(async () => {
    const params = {}
    if (selectedWorkspace) params.workspace_slug = selectedWorkspace
    if (selectedProject) params.project_id = selectedProject
    const res = await axios.get(`${API}/api/sprints/tasks`, { params, timeout: 15000 })
    return res.data
  }, [selectedWorkspace, selectedProject])

  const fetchFleetApi = useCallback(async () => {
    const res = await axios.get(`${API}/api/agents/status`, { timeout: 8000 })
    return res.data
  }, [])

  const {
    data: sprintData,
    lastUpdated: tasksLastUpdated,
    isRefreshing: tasksRefreshing,
    isInitialLoad: tasksInitialLoad,
    error: tasksError,
    refresh: refreshTasks,
    secondsUntilRefresh: tasksCountdown,
    paused: tasksPaused,
  } = useLivePoll(fetchSprintTasksApi, {
    intervalMs: 12000,
    pause: agentWorking,
    enabled: true,
    deps: [selectedWorkspace, selectedProject],
  })

  const { data: fleetData } = useLivePoll(fetchFleetApi, {
    intervalMs: 4000,
    pause: agentWorking,
    enabled: true,
  })

  const pipeline = fleetData?.pipeline || {}
  const watcherActive = (fleetData?.agents?.sprint_watcher?.status || 'running') === 'running'
  const loading = tasksInitialLoad && !sprintData
  const error = tasksError

  // Detect sprint expiry whenever sprint data changes
  useEffect(() => {
    const sprint = sprintData?.sprint
    if (!sprint?.end_date) { setSprintExpiry(null); return }
    try {
      const end = new Date(sprint.end_date)
      const today = new Date()
      today.setHours(0, 0, 0, 0)
      end.setHours(0, 0, 0, 0)
      const diffDays = Math.floor((end - today) / 86400000)
      if (diffDays < 0) setSprintExpiry('expired')
      else if (diffDays === 0) setSprintExpiry('expiring_today')
      else setSprintExpiry(null)
    } catch { setSprintExpiry(null) }
  }, [sprintData])

  const handleExtendSprint = async () => {
    const sprint = sprintData?.sprint
    if (!sprint?.id || sprint.id === 'sprint-1') {
      setActionMsg({ type: 'error', text: 'No active sprint found to extend. Check your Plane project.' })
      return
    }
    // Resolve the project ID: use the first scanned project
    const pid = selectedProject !== 'all' ? selectedProject : sprintData?.project_id
    if (!pid || pid === 'all') {
      setActionMsg({ type: 'error', text: 'Please select a specific project (not "All Projects") to extend the sprint.' })
      return
    }
    setExtendingSprint(true)
    setActionMsg(null)
    try {
      const res = await axios.post(`${API}/api/sprints/extend-sprint`, {
        project_id: pid,
        cycle_id: sprint.id,
        days: 14,
        workspace_slug: selectedWorkspace
      })
      if (res.data?.status === 'success') {
        setActionMsg({ type: 'success', text: `✅ ${res.data.message}` })
        setTimeout(() => refreshTasks(true), 1500)
      } else {
        setActionMsg({ type: 'error', text: res.data?.message || 'Sprint extension failed.' })
      }
    } catch (err) {
      setActionMsg({ type: 'error', text: `Extension failed: ${err.response?.data?.message || err.message}` })
    } finally {
      setExtendingSprint(false)
    }
  }

  const handleRestoreAllCancelled = async () => {
    const cancelledTasks = sprintData?.tasks?.cancelled || []
    if (!cancelledTasks.length) {
      setActionMsg({ type: 'info', text: 'No cancelled tasks found to restore.' })
      return
    }
    setRestoringTasks(true)
    setActionMsg(null)
    let restored = 0, failed = 0
    for (const task of cancelledTasks) {
      try {
        const pid = task.project_id || selectedProject
        if (!pid || pid === 'all') { failed++; continue }
        const res = await axios.post(`${API}/api/sprints/restore-task`, {
          project_id: pid,
          task_id: task.id,
          workspace_slug: selectedWorkspace
        })
        if (res.data?.status === 'success') restored++
        else failed++
      } catch { failed++ }
    }
    setActionMsg({
      type: restored > 0 ? 'success' : 'error',
      text: `↩️ Restored ${restored}/${cancelledTasks.length} tasks to To Do${failed > 0 ? ` (${failed} failed)` : ''}.`
    })
    setTimeout(() => refreshTasks(true), 1500)
    setRestoringTasks(false)
  }

  useEffect(() => {
    fetchWorkspaces()
  }, [])

  const priorityColors = {
    urgent: { bg: 'rgba(239, 68, 68, 0.15)', text: '#ef4444', border: 'rgba(239, 68, 68, 0.4)' },
    high: { bg: 'rgba(245, 158, 11, 0.15)', text: '#f59e0b', border: 'rgba(245, 158, 11, 0.4)' },
    medium: { bg: 'rgba(59, 130, 246, 0.15)', text: '#3b82f6', border: 'rgba(59, 130, 246, 0.4)' },
    low: { bg: 'rgba(107, 114, 128, 0.15)', text: '#9ca3af', border: 'rgba(107, 114, 128, 0.4)' }
  }

  const allTasks = sprintData?.tasks?.all || []
  // Explicitly filter backlog to never contain cancelled tasks (defensive guard)
  const backlogTasks = (sprintData?.tasks?.backlog || []).filter(
    t => !['cancelled', 'wont_fix', 'rejected'].includes((t.state_group || '').toLowerCase())
  )
  const todoTasks = sprintData?.tasks?.todo || []
  const inProgressTasks = sprintData?.tasks?.in_progress || []
  const completedTasks = sprintData?.tasks?.completed || []
  const cancelledTasks = sprintData?.tasks?.cancelled || []

  const filterFn = (task) => {
    const matchesSearch = task.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          (task.description && task.description.toLowerCase().includes(searchTerm.toLowerCase()))
    const pKey = (task.priority || 'MEDIUM').toUpperCase()
    const isPriorityEnabled = enabledPriorities[pKey] !== false
    return matchesSearch && isPriorityEnabled
  }

  const filteredBacklog = backlogTasks.filter(filterFn)
  const filteredTodo = todoTasks.filter(filterFn)
  const filteredInProgress = inProgressTasks.filter(filterFn)
  const filteredCompleted = completedTasks.filter(filterFn)

  const sprintInfo = sprintData?.sprint || {
    name: 'Sprint AAD-5 · Multi-Project Sprint Board',
    total_tasks: allTasks.length,
    open_tasks: allTasks.length - cancelledTasks.length,
    completed_tasks: completedTasks.length,
    in_progress_tasks: inProgressTasks.length,
    todo_tasks: todoTasks.length,
    backlog_tasks: backlogTasks.length,
    cancelled_tasks: cancelledTasks.length,
    completion_percentage: allTasks.length > 0
      ? ((completedTasks.length / Math.max(allTasks.length - cancelledTasks.length, 1)) * 100).toFixed(1)
      : 100
  }

  const activeWsObj = workspaces.find(w => w.slug === selectedWorkspace) || workspaces[0]
  const activeProjects = activeWsObj?.projects || []
  const selectedProjObj = activeProjects.find(p => p.id === selectedProject)
  const displayProjName = selectedProject === 'all' ? 'All Projects' : (selectedProjObj?.name || selectedProject)
  const formattedTitle = `${selectedWorkspace} / ${displayProjName} — ${sprintInfo.name}`

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      style={{ padding: '24px', maxWidth: '1440px', margin: '0 auto' }}
    >
      <div style={{ marginBottom: '8px' }}>
        <h1 style={{ fontSize: '26px', fontWeight: 800, color: 'var(--text-primary)', margin: 0 }}>
          Sprint Monitor & Board
        </h1>
        <p style={{ fontSize: '14px', color: 'var(--text-secondary)', marginTop: '6px' }}>
          Live Plane tasks with auto-refresh — watcher picks up To Do / Unstarted tasks automatically.
        </p>
      </div>

      <MonitorRefreshBar
        title="Sprint Board Sync"
        lastUpdated={tasksLastUpdated}
        isRefreshing={tasksRefreshing || loading}
        paused={tasksPaused}
        secondsUntilRefresh={tasksCountdown}
        error={error}
        onRefresh={refreshTasks}
        intervalLabel="12s"
      />

      <SprintMonitorPanel
        pipeline={pipeline}
        agentWorking={agentWorking}
        agentWorkingTask={agentWorkingTask}
        inProgressCount={inProgressTasks.length}
        todoCount={todoTasks.length}
        watcherActive={watcherActive}
      />

      <div style={{
        background: 'linear-gradient(135deg, rgba(124,58,237,0.12) 0%, rgba(6,182,212,0.12) 100%)',
        border: '1px solid rgba(124,58,237,0.3)', borderRadius: '16px',
        padding: '24px', marginBottom: '24px', boxShadow: '0 8px 32px rgba(0,0,0,0.2)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{
                background: 'linear-gradient(135deg, #7C3AED, #06B6D4)',
                color: '#fff', fontSize: '11px', fontWeight: 800,
                padding: '4px 10px', borderRadius: '20px', textTransform: 'uppercase', letterSpacing: '0.5px'
              }}>
                Plane Multi-Project Sprint Board
              </span>
              <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                🤖 Synchronized via Sprint Watcher Agent
              </span>
            </div>
            <h2 style={{ fontSize: '20px', fontWeight: 800, color: 'var(--text-primary)', marginTop: '8px', marginBottom: '4px' }}>
              {formattedTitle}
            </h2>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
              Real-time task monitoring &amp; execution across Plane workspace projects (Backlog, Todo, In Progress, Completed).
            </p>
          </div>

          {/* Dynamic Workspace & Project Dropdown Controls */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
            <div style={{
              display: 'flex', alignItems: 'center', gap: '8px',
              background: 'rgba(15, 23, 42, 0.95)', padding: '8px 14px', borderRadius: '10px',
              border: '1px solid rgba(124, 58, 237, 0.5)', boxShadow: '0 4px 12px rgba(0,0,0,0.3)'
            }}>
              <Layers size={15} color="#A78BFA" />
              <span style={{ fontSize: '12px', color: '#94A3B8', fontWeight: 600, letterSpacing: '0.5px' }}>WORKSPACE:</span>
              <select
                id="sprint-board-workspace-select"
                value={selectedWorkspace}
                onChange={(e) => {
                  const wsSlug = e.target.value
                  setSelectedWorkspace(wsSlug)
                  setSelectedProject('all')
                }}
                style={{
                  background: '#1E293B', color: '#F8FAFC', border: '1px solid rgba(255,255,255,0.15)',
                  borderRadius: '6px', padding: '4px 10px', fontSize: '13px', fontWeight: 700, cursor: 'pointer', outline: 'none'
                }}
              >
                {workspaces.length === 0 ? (
                  <option value="agentbuilder" style={{ background: '#0F172A', color: '#F8FAFC' }}>agentbuilder</option>
                ) : (
                  workspaces.map(ws => (
                    <option key={ws.slug} value={ws.slug} style={{ background: '#0F172A', color: '#F8FAFC' }}>{ws.name} ({ws.slug})</option>
                  ))
                )}
              </select>
            </div>

            <div style={{
              display: 'flex', alignItems: 'center', gap: '8px',
              background: 'rgba(15, 23, 42, 0.95)', padding: '8px 14px', borderRadius: '10px',
              border: '1px solid rgba(6, 182, 212, 0.5)', boxShadow: '0 4px 12px rgba(0,0,0,0.3)'
            }}>
              <Folder size={15} color="#22D3EE" />
              <span style={{ fontSize: '12px', color: '#94A3B8', fontWeight: 600, letterSpacing: '0.5px' }}>PROJECT:</span>
              <select
                id="sprint-board-project-select"
                value={selectedProject}
                onChange={(e) => setSelectedProject(e.target.value)}
                style={{
                  background: '#1E293B', color: '#F8FAFC', border: '1px solid rgba(255,255,255,0.15)',
                  borderRadius: '6px', padding: '4px 10px', fontSize: '13px', fontWeight: 700, cursor: 'pointer', outline: 'none'
                }}
              >
                <option value="all" style={{ background: '#0F172A', color: '#F8FAFC' }}>⚡ All Projects (Aggregate Workspace Tasks)</option>
                {activeProjects.map(p => (
                  <option key={p.id} value={p.id} style={{ background: '#0F172A', color: '#F8FAFC' }}>{p.name}</option>
                ))}
              </select>
            </div>

            <button
              type="button"
              onClick={() => refreshTasks(false)}
              disabled={tasksRefreshing}
              style={{
                background: 'var(--bg-secondary)', border: '1px solid var(--border-color)',
                color: 'var(--text-primary)', padding: '8px 16px', borderRadius: '8px',
                fontSize: '13px', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px'
              }}
            >
              <RefreshCw size={14} className={tasksRefreshing ? 'spin' : ''} />
              Refresh Board
            </button>
          </div>
        </div>

        {/* Sprint Progress Bar */}
        <div style={{ marginTop: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', fontWeight: 700, marginBottom: '6px', flexWrap: 'wrap', gap: '8px' }}>
            <span style={{ color: 'var(--text-secondary)' }}>Sprint Completion Progress</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span style={{ color: '#34d399' }}>
                {sprintInfo.completion_percentage}% ({completedTasks.length}/{(sprintInfo.open_tasks ?? allTasks.length - cancelledTasks.length)} Open Tasks Completed)
              </span>
              {cancelledTasks.length > 0 && (
                <span style={{
                  fontSize: '11px', fontWeight: 700,
                  background: 'rgba(239,68,68,0.15)', color: '#f87171',
                  border: '1px solid rgba(239,68,68,0.3)',
                  padding: '2px 8px', borderRadius: '10px'
                }}>
                  {cancelledTasks.length} Cancelled
                </span>
              )}
            </div>
          </div>

          <div style={{ height: '8px', background: 'rgba(255,255,255,0.08)', borderRadius: '4px', overflow: 'hidden' }}>
            <div style={{
              width: `${sprintInfo.completion_percentage}%`,
              height: '100%',
              background: 'linear-gradient(90deg, #7C3AED 0%, #34D399 100%)',
              borderRadius: '4px',
              transition: 'width 0.6s ease'
            }} />
          </div>
        </div>
      </div>

      {/* ── Sprint Expiry Warning Banner ── */}
      <AnimatePresence>
        {sprintExpiry && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            style={{
              background: sprintExpiry === 'expired'
                ? 'linear-gradient(135deg, rgba(239,68,68,0.18) 0%, rgba(185,28,28,0.18) 100%)'
                : 'linear-gradient(135deg, rgba(245,158,11,0.18) 0%, rgba(180,83,9,0.18) 100%)',
              border: sprintExpiry === 'expired'
                ? '1px solid rgba(239,68,68,0.5)'
                : '1px solid rgba(245,158,11,0.5)',
              borderRadius: '12px', padding: '14px 18px', marginBottom: '16px',
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              flexWrap: 'wrap', gap: '12px',
              boxShadow: sprintExpiry === 'expired'
                ? '0 4px 20px rgba(239,68,68,0.2)'
                : '0 4px 20px rgba(245,158,11,0.15)'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <AlertTriangle size={18} color={sprintExpiry === 'expired' ? '#f87171' : '#fbbf24'} />
              <div>
                <div style={{ fontSize: '13px', fontWeight: 800, color: sprintExpiry === 'expired' ? '#f87171' : '#fbbf24' }}>
                  {sprintExpiry === 'expired'
                    ? '⚠️ SPRINT EXPIRED — Plane is auto-cancelling tasks in this cycle!'
                    : '⏰ SPRINT ENDS TODAY — Tasks may be auto-cancelled at midnight!'}
                </div>
                <div style={{ fontSize: '11px', color: '#94A3B8', marginTop: '3px' }}>
                  {sprintExpiry === 'expired'
                    ? 'Extend the sprint end date to stop Plane from cancelling tasks. Then restore any auto-cancelled tasks back to To Do.'
                    : 'Extend the sprint now to prevent Plane from cancelling unfinished tasks when the cycle completes tonight.'}
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
              {actionMsg && (
                <span style={{
                  fontSize: '12px', fontWeight: 600, padding: '4px 10px', borderRadius: '6px',
                  background: actionMsg.type === 'success' ? 'rgba(52,211,153,0.15)' : actionMsg.type === 'error' ? 'rgba(239,68,68,0.15)' : 'rgba(96,165,250,0.15)',
                  color: actionMsg.type === 'success' ? '#34d399' : actionMsg.type === 'error' ? '#f87171' : '#60a5fa',
                  border: `1px solid ${actionMsg.type === 'success' ? 'rgba(52,211,153,0.4)' : actionMsg.type === 'error' ? 'rgba(239,68,68,0.4)' : 'rgba(96,165,250,0.4)'}`
                }}>
                  {actionMsg.text}
                </span>
              )}

              {/* Restore All Cancelled Tasks */}
              {(sprintData?.tasks?.cancelled || []).length > 0 && (
                <button
                  id="restore-cancelled-tasks-btn"
                  onClick={handleRestoreAllCancelled}
                  disabled={restoringTasks}
                  style={{
                    background: 'rgba(96,165,250,0.15)', border: '1px solid rgba(96,165,250,0.5)',
                    color: '#60a5fa', padding: '7px 14px', borderRadius: '8px',
                    fontSize: '12px', fontWeight: 700, cursor: restoringTasks ? 'wait' : 'pointer',
                    display: 'flex', alignItems: 'center', gap: '6px', opacity: restoringTasks ? 0.7 : 1
                  }}
                >
                  <RotateCcw size={13} />
                  {restoringTasks ? 'Restoring...' : `Restore ${(sprintData?.tasks?.cancelled || []).length} Cancelled Tasks`}
                </button>
              )}

              {/* Extend Sprint */}
              <button
                id="extend-sprint-btn"
                onClick={handleExtendSprint}
                disabled={extendingSprint}
                style={{
                  background: sprintExpiry === 'expired'
                    ? 'linear-gradient(135deg, #dc2626, #b91c1c)'
                    : 'linear-gradient(135deg, #d97706, #b45309)',
                  border: 'none', color: '#fff',
                  padding: '7px 16px', borderRadius: '8px',
                  fontSize: '12px', fontWeight: 800, cursor: extendingSprint ? 'wait' : 'pointer',
                  display: 'flex', alignItems: 'center', gap: '6px',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
                  opacity: extendingSprint ? 0.7 : 1
                }}
              >
                <CalendarClock size={13} />
                {extendingSprint ? 'Extending...' : 'Extend Sprint +14 Days'}
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Search & Priority Filter Controls */}

      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        flexWrap: 'wrap', gap: '16px', marginBottom: '24px',
        background: 'var(--bg-card)', border: '1px solid var(--border-color)',
        borderRadius: '12px', padding: '12px 18px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flex: '1', minWidth: '240px' }}>
          <Search size={16} style={{ color: 'var(--text-secondary)' }} />
          <input
            type="text"
            placeholder="Search sprint tasks by name or description..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{
              background: 'transparent', border: 'none', color: 'var(--text-primary)',
              fontSize: '13px', width: '100%', outline: 'none'
            }}
          />
        </div>

        {/* Priority Filter Toggles */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          {['URGENT', 'HIGH', 'MEDIUM', 'LOW'].map(p => {
            const isEnabled = enabledPriorities[p]
            const colors = priorityColors[p.toLowerCase()] || priorityColors.medium
            return (
              <button
                key={p}
                onClick={() => togglePriority(p)}
                style={{
                  background: isEnabled ? colors.bg : 'var(--bg-secondary)',
                  color: isEnabled ? colors.text : 'var(--text-secondary)',
                  border: isEnabled ? `1px solid ${colors.border}` : '1px solid var(--border-color)',
                  padding: '4px 10px', borderRadius: '6px', fontSize: '11px', fontWeight: 700, cursor: 'pointer'
                }}
              >
                {p}
              </button>
            )
          })}
        </div>
      </div>

      {/* ── 4-Column Multi-Project Sprint Kanban Board ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
        {/* Column 1: Backlog */}
        <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '12px', padding: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <span style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Inbox size={16} color="#94a3b8" /> Backlog
            </span>
            <span style={{ background: 'rgba(255,255,255,0.1)', padding: '2px 10px', borderRadius: '12px', fontSize: '12px', fontWeight: 700 }}>
              {filteredBacklog.length}
            </span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {filteredBacklog.length === 0 ? (
              <div style={{ padding: '16px', textAlign: 'center', color: 'var(--text-secondary)', fontSize: '12px', fontStyle: 'italic' }}>
                No backlog tasks
              </div>
            ) : (
              filteredBacklog.map(task => <TaskCard key={task.id} task={task} colors={priorityColors} />)
            )}
          </div>
        </div>

        {/* Column 2: To Do */}
        <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '12px', padding: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <span style={{ fontSize: '14px', fontWeight: 700, color: '#60a5fa', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <ListTodo size={16} color="#60a5fa" /> To Do (Ready)
            </span>
            <span style={{ background: 'rgba(96,165,250,0.2)', color: '#60a5fa', padding: '2px 10px', borderRadius: '12px', fontSize: '12px', fontWeight: 700 }}>
              {filteredTodo.length}
            </span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {filteredTodo.length === 0 ? (
              <div style={{ padding: '16px', textAlign: 'center', color: 'var(--text-secondary)', fontSize: '12px', fontStyle: 'italic' }}>
                No tasks in To Do
              </div>
            ) : (
              filteredTodo.map(task => <TaskCard key={task.id} task={task} colors={priorityColors} />)
            )}
          </div>
        </div>

        {/* Column 3: In Progress */}
        <div style={{ background: 'var(--bg-card)', border: '1px solid rgba(124,58,237,0.3)', borderRadius: '12px', padding: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <span style={{ fontSize: '14px', fontWeight: 700, color: '#c4b5fd', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <PlayCircle size={16} color="#c4b5fd" /> In Progress (Agent Active)
            </span>
            <span style={{ background: 'rgba(124,58,237,0.25)', color: '#c4b5fd', padding: '2px 10px', borderRadius: '12px', fontSize: '12px', fontWeight: 700 }}>
              {filteredInProgress.length}
            </span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {filteredInProgress.length === 0 ? (
              <div style={{ padding: '16px', textAlign: 'center', color: 'var(--text-secondary)', fontSize: '12px', fontStyle: 'italic' }}>
                No active in-progress tasks
              </div>
            ) : (
              filteredInProgress.map(task => <TaskCard key={task.id} task={task} colors={priorityColors} isProgress />)
            )}
          </div>
        </div>

        {/* Column 4: Completed */}
        <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '12px', padding: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <span style={{ fontSize: '14px', fontWeight: 700, color: '#34d399', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <FolderCheck size={16} color="#34d399" /> Completed
            </span>
            <span style={{ background: 'rgba(52,211,153,0.2)', color: '#34d399', padding: '2px 10px', borderRadius: '12px', fontSize: '12px', fontWeight: 700 }}>
              {filteredCompleted.length}
            </span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {filteredCompleted.length === 0 ? (
              <div style={{ padding: '16px', textAlign: 'center', color: 'var(--text-secondary)', fontSize: '12px', fontStyle: 'italic' }}>
                No completed tasks yet
              </div>
            ) : (
              filteredCompleted.map(task => <TaskCard key={task.id} task={task} colors={priorityColors} isDone />)
            )}
          </div>
        </div>
      </div>
    </motion.div>
  )
}

function TaskCard({ task, colors, isProgress, isDone }) {
  const pStyle = colors[(task.priority || 'medium').toLowerCase()] || colors.medium
  return (
    <div style={{
      background: 'var(--bg-secondary)',
      border: isProgress ? '1px solid rgba(124,58,237,0.5)' : '1px solid var(--border-color)',
      borderRadius: '8px', padding: '12px 14px', transition: 'all 0.2s ease'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px', marginBottom: '6px' }}>
        <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)', lineHeight: '1.4' }}>
          {isDone ? '✅ ' : isProgress ? '⚡ ' : ''}{task.name}
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '8px', flexWrap: 'wrap', gap: '6px' }}>
        <span style={{ fontSize: '10px', color: '#93c5fd', fontWeight: 700, background: 'rgba(147,197,253,0.1)', padding: '2px 6px', borderRadius: '4px' }}>
          🏷️ {task.project_name || 'Project'}
        </span>
        <span style={{
          fontSize: '10px', fontWeight: 700, padding: '2px 6px', borderRadius: '4px',
          background: pStyle.bg, color: pStyle.text, border: `1px solid ${pStyle.border}`
        }}>
          {(task.priority || 'MEDIUM').toUpperCase()}
        </span>
      </div>
    </div>
  )
}
