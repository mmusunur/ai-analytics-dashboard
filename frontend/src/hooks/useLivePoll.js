/**
 * useLivePoll — auto-refresh with optional soft-pause (slow poll) during agent work.
 */
import { useState, useEffect, useRef, useCallback } from 'react'

async function fetchWithRetry(fn, retries = 2) {
  let lastErr
  for (let i = 0; i <= retries; i++) {
    try {
      return await fn()
    } catch (err) {
      lastErr = err
      if (i < retries) await new Promise((r) => setTimeout(r, 800 * (i + 1)))
    }
  }
  throw lastErr
}

export function useLivePoll(fetchFn, options = {}) {
  const {
    intervalMs = 5000,
    pause = false,
    /** When pause=true, still poll at this slower interval (keeps UI alive). null = stop polling. */
    pauseIntervalMs = null,
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

  const effectiveInterval = pause && pauseIntervalMs ? pauseIntervalMs : intervalMs
  const isSoftPaused = pause && pauseIntervalMs != null
  const isHardPaused = pause && pauseIntervalMs == null

  const refresh = useCallback(async (silent = true) => {
    if (!enabled) return null
    try {
      setIsRefreshing(true)
      const result = await fetchWithRetry(() => fetchRef.current())
      setData(result)
      setLastUpdated(new Date())
      setError(null)
      setSecondsUntilRefresh(Math.ceil(effectiveInterval / 1000))
      return result
    } catch (err) {
      const msg = err?.response?.data?.message || err?.message || 'Failed to refresh data'
      setError(msg)
      return null
    } finally {
      setIsRefreshing(false)
      setIsInitialLoad(false)
    }
  }, [enabled, effectiveInterval])

  useEffect(() => {
    if (!enabled) return
    refresh(false)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, refresh, ...deps])

  useEffect(() => {
    if (!enabled || isHardPaused) return undefined

    const pollTimer = setInterval(() => {
      refresh(true)
    }, effectiveInterval)

    const countdownTimer = setInterval(() => {
      setSecondsUntilRefresh((s) => (s <= 1 ? Math.ceil(effectiveInterval / 1000) : s - 1))
    }, 1000)

    return () => {
      clearInterval(pollTimer)
      clearInterval(countdownTimer)
    }
  }, [enabled, effectiveInterval, isHardPaused, refresh])

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
    paused: isHardPaused,
    softPaused: isSoftPaused,
  }
}
