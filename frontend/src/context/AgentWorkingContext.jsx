/**
 * AgentWorkingContext — Global React context that polls /api/sprints/agent-working
 * every 5 seconds and broadcasts the agent_working flag to ALL pages.
 *
 * Usage:
 *   const { agentWorking, agentWorkingTask, agentWorkingSince } = useAgentWorking()
 *
 * When agentWorking is true:
 *   - All data-fetching intervals should be paused
 *   - The AgentWorkingBanner is shown at the top of every page
 *   - On transition back to false, components should immediately re-fetch to restore state
 */

import React, { createContext, useContext, useState, useEffect, useRef } from 'react'
import axios from 'axios'

const API = import.meta.env.VITE_API_URL || ''

const AgentWorkingContext = createContext({
  agentWorking: false,
  agentWorkingTask: '',
  agentWorkingSince: null,
})

export function AgentWorkingProvider({ children }) {
  const [agentWorking, setAgentWorking] = useState(false)
  const [agentWorkingTask, setAgentWorkingTask] = useState('')
  const [agentWorkingSince, setAgentWorkingSince] = useState(null)
  const prevWorking = useRef(false)

  useEffect(() => {
    let cancelled = false

    const poll = async () => {
      try {
        const res = await axios.get(`${API}/api/sprints/agent-working`, { timeout: 4000 })
        if (cancelled) return
        const working = res.data?.agent_working === true
        setAgentWorking(working)
        setAgentWorkingTask(res.data?.task || '')
        setAgentWorkingSince(res.data?.since || null)
        prevWorking.current = working
      } catch {
        // Non-critical: if the endpoint fails, don't change existing state
        // (avoid flipping to "not working" on a transient network error)
      }
    }

    poll() // immediate first poll
    const interval = setInterval(poll, agentWorking ? 2000 : 5000)
    return () => {
      cancelled = true
      clearInterval(interval)
    }
  }, [agentWorking])

  return (
    <AgentWorkingContext.Provider value={{ agentWorking, agentWorkingTask, agentWorkingSince }}>
      {children}
    </AgentWorkingContext.Provider>
  )
}

export function useAgentWorking() {
  return useContext(AgentWorkingContext)
}
