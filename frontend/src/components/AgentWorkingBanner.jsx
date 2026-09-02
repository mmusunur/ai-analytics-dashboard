/**
 * AgentWorkingBanner — Global sticky banner shown across ALL pages when the
 * sprint watcher / builder agent is actively modifying code.
 *
 * While the banner is shown:
 *  - All API polling is paused to prevent uvicorn hot-reload from breaking
 *    in-flight requests and corrupting UI state.
 *  - User can still interact with the UI (filters, navigation etc.) but data
 *    will not refresh until the agent finishes.
 *  - Once the flag clears, polling automatically resumes and data re-fetches.
 */

import React, { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

export default function AgentWorkingBanner({ agentWorking, taskName, since }) {
  const [elapsed, setElapsed] = useState(0)

  useEffect(() => {
    if (!agentWorking || !since) {
      setElapsed(0)
      return
    }
    const sinceMs = new Date(since).getTime()
    const tick = () => setElapsed(Math.floor((Date.now() - sinceMs) / 1000))
    tick()
    const interval = setInterval(tick, 1000)
    return () => clearInterval(interval)
  }, [agentWorking, since])

  const formatElapsed = (secs) => {
    if (secs < 60) return `${secs}s`
    const m = Math.floor(secs / 60)
    const s = secs % 60
    return `${m}m ${s}s`
  }

  return (
    <AnimatePresence>
      {agentWorking && (
        <motion.div
          key="agent-working-banner"
          initial={{ opacity: 0, y: -48 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -48 }}
          transition={{ duration: 0.3, ease: 'easeOut' }}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            zIndex: 9999,
            background: 'linear-gradient(90deg, rgba(124,58,237,0.97) 0%, rgba(6,182,212,0.97) 100%)',
            boxShadow: '0 4px 24px rgba(124,58,237,0.5)',
            padding: '10px 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '16px',
            flexWrap: 'wrap',
          }}
          role="status"
          aria-live="polite"
          id="agent-working-banner"
        >
          {/* Left: animated pulse + message */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            {/* Animated dual-ring pulse */}
            <div style={{ position: 'relative', width: 18, height: 18, flexShrink: 0 }}>
              <div style={{
                position: 'absolute', inset: 0, borderRadius: '50%',
                background: '#fff',
                animation: 'agentPulseOuter 1.2s ease-in-out infinite',
                opacity: 0.3,
              }} />
              <div style={{
                position: 'absolute', inset: '4px', borderRadius: '50%',
                background: '#fff',
              }} />
            </div>

            <div>
              <span style={{
                fontSize: '13px', fontWeight: 800, color: '#fff',
                letterSpacing: '0.3px'
              }}>
                🔒 Agent is working on a sprint task
              </span>
              {taskName && (
                <span style={{
                  marginLeft: '10px', fontSize: '12px', color: 'rgba(255,255,255,0.8)',
                  fontWeight: 600
                }}>
                  Task: <em>{taskName.slice(0, 60)}{taskName.length > 60 ? '…' : ''}</em>
                </span>
              )}
            </div>
          </div>

          {/* Right: elapsed time + explanation */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <span style={{
              fontSize: '12px', color: 'rgba(255,255,255,0.7)', fontWeight: 600,
              background: 'rgba(0,0,0,0.2)', padding: '3px 10px', borderRadius: '20px',
              fontFamily: 'monospace'
            }}>
              ⏱ {formatElapsed(elapsed)}
            </span>
            <span style={{
              fontSize: '11px', color: 'rgba(255,255,255,0.6)',
              maxWidth: '320px', lineHeight: '1.4'
            }}>
              Agent Monitor &amp; pipeline stay live · Sprint board syncs on slow interval
            </span>
          </div>

          <style>{`
            @keyframes agentPulseOuter {
              0%, 100% { transform: scale(1); opacity: 0.3; }
              50%       { transform: scale(1.8); opacity: 0; }
            }
          `}</style>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
