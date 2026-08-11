import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Bot, CheckCircle2, Clock, AlertTriangle, RefreshCw, Activity, Layers, Folder, ListTodo, PlayCircle, FolderCheck, Inbox } from 'lucide-react';

const API = import.meta.env.VITE_API_URL || '';

export default function AgentTaskActivityTracker() {
  const [agents, setAgents] = useState({});
  const [recentActivity, setRecentActivity] = useState([]);
  const [sprintInfo, setSprintInfo] = useState({});
  const [sprintTasks, setSprintTasks] = useState({ backlog: [], todo: [], in_progress: [], completed: [] });
  const [lastActive, setLastActive] = useState('');
  const [loading, setLoading] = useState(true);

  // Workspace & Project state
  const [workspaces, setWorkspaces] = useState([]);
  const [selectedWorkspace, setSelectedWorkspace] = useState('agentbuilder');
  const [selectedProject, setSelectedProject] = useState('all');

  const fetchWorkspaces = async () => {
    try {
      const res = await axios.get(`${API}/api/sprints/workspaces`);
      if (res.data?.workspaces) {
        setWorkspaces(res.data.workspaces);
      }
    } catch (err) {
      console.error('[AgentTaskActivityTracker] Workspace fetch error:', err);
    }
  };

  const fetchTaskStatus = async () => {
    try {
      const params = {};
      if (selectedWorkspace) params.workspace_slug = selectedWorkspace;
      if (selectedProject) params.project_id = selectedProject;

      const [statusRes, tasksRes] = await Promise.all([
        axios.get(`${API}/api/agents/status`),
        axios.get(`${API}/api/sprints/tasks`, { params })
      ]);

      if (statusRes.data) {
        setAgents(statusRes.data.agents || {});
        setLastActive(statusRes.data.last_active || '');
        if (statusRes.data.recent_activity) {
          setRecentActivity(statusRes.data.recent_activity);
        }
      }

      if (tasksRes.data) {
        setSprintInfo(tasksRes.data.sprint || {});
        if (tasksRes.data.tasks) {
          setSprintTasks({
            backlog: tasksRes.data.tasks.backlog || [],
            todo: tasksRes.data.tasks.todo || [],
            in_progress: tasksRes.data.tasks.in_progress || [],
            completed: tasksRes.data.tasks.completed || []
          });
        }
      }
    } catch (err) {
      console.error('[AgentTaskActivityTracker] Failed to fetch agent status:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkspaces();
  }, []);

  useEffect(() => {
    fetchTaskStatus();
    const interval = setInterval(fetchTaskStatus, 4000);
    return () => clearInterval(interval);
  }, [selectedWorkspace, selectedProject]);

  const workingAgent = Object.entries(agents).find(([_, info]) => {
    const task = info.current_task || '';
    return task.includes('🔨') || task.includes('🧪') || task.includes('Picked up') || task.includes('Implementing') || task.includes('Building');
  });

  const activeWsObj = workspaces.find(w => w.slug === selectedWorkspace) || workspaces[0];
  const activeProjects = activeWsObj?.projects || [];

  return (
    <div className="card" id="agent-task-activity-tracker" style={{ marginTop: '24px', padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h2 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Bot size={20} color="#7C3AED" />
            Autonomous Agent Task Pickup &amp; Multi-Project Sprint Board
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginTop: '4px' }}>
            Real-time monitoring across Plane workspace projects: Backlog, Todo, In Progress, and Completed tasks.
          </p>
        </div>

        {/* Dynamic Workspace & Project Selectors */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          <div style={{
            display: 'flex', alignItems: 'center', gap: '8px',
            background: 'rgba(15, 23, 42, 0.95)', padding: '6px 12px', borderRadius: '8px',
            border: '1px solid rgba(124, 58, 237, 0.5)', boxShadow: '0 4px 12px rgba(0,0,0,0.3)'
          }}>
            <Layers size={14} color="#A78BFA" />
            <span style={{ fontSize: '12px', color: '#94A3B8', fontWeight: 600, letterSpacing: '0.5px' }}>WORKSPACE:</span>
            <select
              id="plane-workspace-selector"
              value={selectedWorkspace}
              onChange={(e) => {
                const wsSlug = e.target.value;
                setSelectedWorkspace(wsSlug);
                setSelectedProject('all');
              }}
              style={{
                background: '#1E293B', color: '#F8FAFC', border: '1px solid rgba(255,255,255,0.15)',
                borderRadius: '6px', padding: '4px 8px', fontSize: '12px', fontWeight: 700, cursor: 'pointer', outline: 'none'
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
            background: 'rgba(15, 23, 42, 0.95)', padding: '6px 12px', borderRadius: '8px',
            border: '1px solid rgba(6, 182, 212, 0.5)', boxShadow: '0 4px 12px rgba(0,0,0,0.3)'
          }}>
            <Folder size={14} color="#22D3EE" />
            <span style={{ fontSize: '12px', color: '#94A3B8', fontWeight: 600, letterSpacing: '0.5px' }}>PROJECT SCOPE:</span>
            <select
              id="plane-project-selector"
              value={selectedProject}
              onChange={(e) => setSelectedProject(e.target.value)}
              style={{
                background: '#1E293B', color: '#F8FAFC', border: '1px solid rgba(255,255,255,0.15)',
                borderRadius: '6px', padding: '4px 8px', fontSize: '12px', fontWeight: 700, cursor: 'pointer', outline: 'none'
              }}
            >
              <option value="all" style={{ background: '#0F172A', color: '#F8FAFC' }}>⚡ All Projects (Aggregate Workspace Tasks)</option>
              {activeProjects.map(p => (
                <option key={p.id} value={p.id} style={{ background: '#0F172A', color: '#F8FAFC' }}>{p.name}</option>
              ))}
            </select>
          </div>

          <span style={{
            fontSize: '11px', fontWeight: 700, padding: '4px 10px', borderRadius: '6px',
            background: workingAgent ? 'rgba(124, 58, 237, 0.2)' : 'rgba(52, 211, 153, 0.1)',
            color: workingAgent ? '#c4b5fd' : '#34d399',
            border: workingAgent ? '1px solid rgba(124, 58, 237, 0.5)' : '1px solid rgba(52, 211, 153, 0.2)',
            display: 'flex', alignItems: 'center', gap: '6px'
          }}>
            <Activity size={12} className={workingAgent ? 'animate-spin' : ''} />
            {workingAgent ? `ACTIVE: ${workingAgent[0].toUpperCase()} WORKING` : 'ALL AGENTS IDLE & MONITORING SPRINT'}
          </span>

          <button
            onClick={fetchTaskStatus}
            style={{
              background: 'var(--bg-secondary)', border: '1px solid var(--border-color)',
              color: 'var(--text-secondary)', padding: '4px 10px', borderRadius: '6px',
              fontSize: '12px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px'
            }}
          >
            <RefreshCw size={12} />
            Refresh
          </button>
        </div>
      </div>

      {/* Active Task Execution Banner */}
      {workingAgent && (
        <div style={{
          background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.15) 0%, rgba(6, 182, 212, 0.1) 100%)',
          border: '1px solid rgba(124, 58, 237, 0.4)', borderRadius: '10px',
          padding: '16px 20px', marginBottom: '20px', display: 'flex',
          alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px'
        }}>
          <div>
            <div style={{ fontSize: '11px', textTransform: 'uppercase', tracking: '1px', color: '#a78bfa', fontWeight: 700, marginBottom: '4px' }}>
              ⚡ CURRENTLY EXECUTING WORKSPACE TASK
            </div>
            <div style={{ fontSize: '16px', fontWeight: 700, color: '#ffffff' }}>
              {workingAgent[1].current_task}
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Assigned Agent: <strong style={{ color: '#06b6d4', textTransform: 'capitalize' }}>{workingAgent[0]}</strong> · Workspace: <span style={{ color: '#a78bfa', fontWeight: 600 }}>{selectedWorkspace}</span>
            </div>
          </div>
          <span style={{ fontSize: '11px', background: 'rgba(255,255,255,0.08)', padding: '6px 12px', borderRadius: '6px', color: '#e5e7eb' }}>
            Phase: <strong>Implementation &amp; Testing</strong>
          </span>
        </div>
      )}

      {/* Agent Activity Fleet Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px', marginBottom: '24px' }}>
        {Object.entries(agents).map(([agentName, info]) => {
          const isBusy = (info.current_task || '').includes('🔨') || (info.current_task || '').includes('🧪') || (info.current_task || '').includes('Picked up');
          return (
            <div key={agentName} style={{
              background: 'var(--bg-secondary)',
              border: isBusy ? '1px solid rgba(124, 58, 237, 0.5)' : '1px solid var(--border-color)',
              borderRadius: '8px', padding: '12px 14px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)', textTransform: 'capitalize' }}>
                  {agentName.replace('_', ' ')}
                </span>
                <span style={{
                  fontSize: '10px', fontWeight: 700, padding: '2px 6px', borderRadius: '4px',
                  background: isBusy ? 'rgba(124, 58, 237, 0.25)' : 'rgba(52, 211, 153, 0.1)',
                  color: isBusy ? '#c4b5fd' : '#34d399'
                }}>
                  {isBusy ? 'BUSY ⚡' : info.status.toUpperCase()}
                </span>
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-secondary)', lineHeight: '1.4', wordBreak: 'break-word' }}>
                {info.current_task || 'Idle / Listening for tasks'}
              </div>
            </div>
          );
        })}
      </div>

      {/* ── Multi-Project Sprint Task Board (Backlog, Todo, In Progress, Completed) ── */}
      <div style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
          <h3 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Layers size={16} color="#7C3AED" />
            Workspace Sprint Board Tasks (Aggregated Across Projects)
          </h3>
          <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
            Completion: <strong style={{ color: '#34d399' }}>{sprintInfo.completion_percentage || 100}%</strong> ({sprintInfo.completed_tasks || 0} / {sprintInfo.total_tasks || 0} tasks)
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '14px' }}>
          {/* Column 1: Backlog */}
          <div style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: '8px', padding: '12px' }}>
            <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '10px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><Inbox size={14} color="#94a3b8" /> Backlog</span>
              <span style={{ background: 'rgba(255,255,255,0.1)', padding: '2px 8px', borderRadius: '10px', fontSize: '11px' }}>{sprintTasks.backlog.length}</span>
            </div>
            {sprintTasks.backlog.length === 0 ? (
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)', fontStyle: 'italic', padding: '10px 0' }}>No backlog items</div>
            ) : (
              sprintTasks.backlog.map(t => (
                <div key={t.id} style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '6px', padding: '10px', marginBottom: '8px' }}>
                  <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>{t.name}</div>
                  <div style={{ fontSize: '10px', color: '#93c5fd', fontWeight: 600 }}>🏷️ {t.project_name}</div>
                </div>
              ))
            )}
          </div>

          {/* Column 2: Todo */}
          <div style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: '8px', padding: '12px' }}>
            <div style={{ fontSize: '12px', fontWeight: 700, color: '#60a5fa', marginBottom: '10px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><ListTodo size={14} color="#60a5fa" /> To Do (Ready)</span>
              <span style={{ background: 'rgba(96, 165, 250, 0.2)', padding: '2px 8px', borderRadius: '10px', fontSize: '11px' }}>{sprintTasks.todo.length}</span>
            </div>
            {sprintTasks.todo.length === 0 ? (
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)', fontStyle: 'italic', padding: '10px 0' }}>No tasks in To Do</div>
            ) : (
              sprintTasks.todo.map(t => (
                <div key={t.id} style={{ background: 'var(--bg-card)', border: '1px solid rgba(96, 165, 250, 0.4)', borderRadius: '6px', padding: '10px', marginBottom: '8px' }}>
                  <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>{t.name}</div>
                  <div style={{ fontSize: '10px', color: '#93c5fd', fontWeight: 600 }}>🏷️ {t.project_name}</div>
                </div>
              ))
            )}
          </div>

          {/* Column 3: In Progress */}
          <div style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: '8px', padding: '12px' }}>
            <div style={{ fontSize: '12px', fontWeight: 700, color: '#c4b5fd', marginBottom: '10px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><PlayCircle size={14} color="#c4b5fd" /> In Progress</span>
              <span style={{ background: 'rgba(124, 58, 237, 0.25)', padding: '2px 8px', borderRadius: '10px', fontSize: '11px' }}>{sprintTasks.in_progress.length}</span>
            </div>
            {sprintTasks.in_progress.length === 0 ? (
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)', fontStyle: 'italic', padding: '10px 0' }}>No active in-progress tasks</div>
            ) : (
              sprintTasks.in_progress.map(t => (
                <div key={t.id} style={{ background: 'var(--bg-card)', border: '1px solid rgba(124, 58, 237, 0.5)', borderRadius: '6px', padding: '10px', marginBottom: '8px' }}>
                  <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>⚡ {t.name}</div>
                  <div style={{ fontSize: '10px', color: '#a78bfa', fontWeight: 600 }}>🏷️ {t.project_name}</div>
                </div>
              ))
            )}
          </div>

          {/* Column 4: Completed */}
          <div style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: '8px', padding: '12px' }}>
            <div style={{ fontSize: '12px', fontWeight: 700, color: '#34d399', marginBottom: '10px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><FolderCheck size={14} color="#34d399" /> Completed</span>
              <span style={{ background: 'rgba(52, 211, 153, 0.2)', padding: '2px 8px', borderRadius: '10px', fontSize: '11px' }}>{sprintTasks.completed.length}</span>
            </div>
            {sprintTasks.completed.length === 0 ? (
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)', fontStyle: 'italic', padding: '10px 0' }}>No completed tasks yet</div>
            ) : (
              sprintTasks.completed.slice(0, 5).map(t => (
                <div key={t.id} style={{ background: 'var(--bg-card)', border: '1px solid rgba(52, 211, 153, 0.3)', borderRadius: '6px', padding: '10px', marginBottom: '8px' }}>
                  <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>✅ {t.name}</div>
                  <div style={{ fontSize: '10px', color: '#6ee7b7', fontWeight: 600 }}>🏷️ {t.project_name}</div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Recent Sprint Task Pickup Stream */}
      <div>
        <h3 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Clock size={16} color="#06B6D4" />
          Recent Sprint Task Executions &amp; Log Stream
        </h3>
        {recentActivity.length === 0 ? (
          <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-secondary)', fontSize: '13px', background: 'var(--bg-secondary)', borderRadius: '8px', border: '1px dashed var(--border-color)' }}>
            No recent task execution logs recorded yet. Sprint Watcher polls Plane every 15s for new/updated tasks.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '240px', overflowY: 'auto' }}>
            {recentActivity.map((rec, i) => (
              <div key={i} style={{
                background: 'var(--bg-secondary)', border: '1px solid var(--border-color)',
                borderRadius: '6px', padding: '10px 14px', fontSize: '12px',
                display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  {rec.status === 'completed' ? (
                    <CheckCircle2 size={16} color="#34d399" />
                  ) : (
                    <AlertTriangle size={16} color="#ef4444" />
                  )}
                  <div>
                    <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>
                      #{rec.task_id} — {rec.task_title}
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                      Processed by <span style={{ color: '#a78bfa', textTransform: 'capitalize' }}>{rec.agent}</span> · {new Date(rec.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
                <span style={{
                  fontSize: '10px', fontWeight: 700, padding: '2px 8px', borderRadius: '4px',
                  background: rec.status === 'completed' ? 'rgba(52, 211, 153, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                  color: rec.status === 'completed' ? '#34d399' : '#fca5a5'
                }}>
                  {rec.status.toUpperCase()}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
