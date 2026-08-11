/**
 * useLivePoll — reliable auto-refresh with pause support, last-updated tracking, countdown.
 */
import { useState, useEffect, useRef, useCallback } from 'react'

export function useLivePoll(fetchFn, options = {}) {
  const {
    intervalMs = 5000,
    pause = false,
    enabled = true,
    deps = [],
  } = options

  const [data, setData] = useState(null)
  const [lastUpdated, setLastUpdated] = useState(null)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [isInitialLoad, setIsInitialLoad] = useState(true)
  const [error, setError] = useState(null)
  const [secondsUntilRefresh, setSecondsUntilRefresh] = useState(Math.ceil(intervalMs / 1000))

  const fetchRef = useRef(fetchFn)
  fetchRef.current = fetchFn
  const pauseRef = useRef(pause)
  pauseRef.current = pause

  const refresh = useCallback(async (silent = true) => {
    if (!enabled) return null
    try {
      setIsRefreshing(true)
      const result = await fetchRef.current()
      setData(result)
      setLastUpdated(new Date())
      setError(null)
      setSecondsUntilRefresh(Math.ceil(intervalMs / 1000))
      return result
    } catch (err) {
      const msg = err?.message || 'Failed to refresh data'
      setError(msg)
      return null
    } finally {
      setIsRefreshing(false)
      setIsInitialLoad(false)
    }
  }, [enabled, intervalMs])

  // Initial + dependency-triggered refresh
  useEffect(() => {
    if (!enabled) return
    refresh(false)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, refresh, ...deps])

  // Auto-refresh interval (paused when agent is working)
  useEffect(() => {
    if (!enabled) return undefined

    const pollTimer = setInterval(() => {
      if (!pauseRef.current) refresh(true)
    }, intervalMs)

    const countdownTimer = setInterval(() => {
      if (pauseRef.current) return
      setSecondsUntilRefresh((s) => (s <= 1 ? Math.ceil(intervalMs / 1000) : s - 1))
    }, 1000)

    return () => {
      clearInterval(pollTimer)
      clearInterval(countdownTimer)
    }
  }, [enabled, intervalMs, refresh])

  // Immediate refresh when pause lifts (agent finished working)
  const prevPause = useRef(pause)
  useEffect(() => {
    if (prevPause.current && !pause && enabled) {
      refresh(true)
    }
    prevPause.current = pause
  }, [pause, enabled, refresh])

  return {
    data,
    lastUpdated,
    isRefreshing,
    isInitialLoad,
    error,
    refresh,
    secondsUntilRefresh,
    paused: pause,
  }
}
