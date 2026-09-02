import { useState, useEffect, useRef } from 'react'
import axios from 'axios'

const API = import.meta.env.VITE_API_URL || ''
const CACHE_KEY = 'agent_status_cache'
const CACHE_TTL = 30000

const DEFAULT_AGENTS = {
  sprint_watcher: { status: 'idle', current_task: 'Idle' },
  builder: { status: 'idle', current_task: 'Idle' },
  tester: { status: 'idle', current_task: 'Idle' },
  git_agent: { status: 'idle', current_task: 'Idle' },
  memory: { status: 'idle', current_task: 'Idle' },
  orchestrator: { status: 'idle', current_task: 'Idle' },
}

function readCachedStatus() {
  try {
    const cached = JSON.parse(localStorage.getItem(CACHE_KEY) || 'null')
    return cached?.agents ? cached : null
  } catch {
    return null
  }
}

export const useAgentStatus = () => {
  const cachedStatus = readCachedStatus()
  const [agentsData, setAgentsData] = useState(cachedStatus?.agents || DEFAULT_AGENTS)
  const [pipeline, setPipeline] = useState(cachedStatus?.pipeline || { phase: 'idle' })
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const cacheRef = useRef(null)
  const fetchTimeRef = useRef(0)
  const requestInProgress = useRef(false)

  useEffect(() => {
    let cancelled = false
    const abortController = new AbortController()

    const fetchStatus = async () => {
      const now = Date.now()
      const cached = cacheRef.current
      if (requestInProgress.current) return

      // Use cache if still valid
      if (cached && now - fetchTimeRef.current < CACHE_TTL) {
        setAgentsData(cached.agents)
        setPipeline(cached.pipeline)
        return
      }

      try {
        requestInProgress.current = true
        setIsLoading(true)
        const res = await axios.get(`${API}/api/agents/status`, {
          timeout: 8000,
          signal: abortController.signal
        })

        if (cancelled) return

        if (res.data?.agents) {
          setAgentsData(res.data.agents)
          cacheRef.current = {
            agents: res.data.agents,
            pipeline: res.data.pipeline || pipeline
          }
          localStorage.setItem(CACHE_KEY, JSON.stringify(cacheRef.current))
          fetchTimeRef.current = now
          setError(null)
        }

        if (res.data?.pipeline) {
          setPipeline(res.data.pipeline)
        }
      } catch (err) {
        if (!cancelled && err.name !== 'CanceledError') {
          setError(err)
          // Use cached data if available even if fetch failed
          if (cached) {
            setAgentsData(cached.agents)
            setPipeline(cached.pipeline)
          }
        }
      } finally {
        requestInProgress.current = false
        if (!cancelled) {
          setIsLoading(false)
        }
      }
    }

    // Immediate fetch on mount
    fetchStatus()

    // Poll every 3 seconds
    const timer = setInterval(fetchStatus, 3000)

    return () => {
      cancelled = true
      clearInterval(timer)
      abortController.abort()
    }
  }, [])

  return { agentsData, pipeline, isLoading, error }
}
