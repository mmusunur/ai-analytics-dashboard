import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import axios from 'axios'
import KPICard from '../components/KPICard'
import WarehouseSalesAnalytics from '../components/WarehouseSalesAnalytics'
import AiDataCopilot from '../components/AiDataCopilot'
import AnomalyAlertPanel from '../components/AnomalyAlertPanel'
import DataAnalytics from '../components/DataAnalytics'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  ScatterChart, Scatter, Cell
} from 'recharts'

const API = import.meta.env.VITE_API_URL || ''

const COLORS = ['#7C3AED', '#06B6D4', '#F59E0B', '#10B981', '#EF4444', '#8B5CF6']

// Format today's date as YYYY-MM-DD for <input type="date">
const todayISO = () => {
  const d = new Date()
  return d.toISOString().slice(0, 10)
}

// Convert YYYY-MM-DD → YYYYMMDD for API
const toOerdte = (iso) => iso.replace(/-/g, '')

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload?.length) {
    return (
      <div style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border-subtle)',
        borderRadius: '8px',
        padding: '10px 14px',
        fontSize: '13px'
      }}>
        {label && <p style={{ color: 'var(--text-secondary)', marginBottom: 4 }}>{label}</p>}
        {payload.map((p, i) => (
          <p key={i} style={{ color: p.color || 'var(--text-primary)', fontWeight: 600 }}>
            {p.name}: {typeof p.value === 'number' ? p.value.toLocaleString() : p.value}
          </p>
        ))}
      </div>
    )
  }
  return null
}

const DEFAULT_KPIS = [
  { title: "TOTAL WAREHOUSES", value: "...", unit: "Facilities", trend: 0.0, trend_direction: "up", color: "#7C3AED" },
  { title: "CASES BUILT (cases_bld)", value: "...", unit: "Cases", trend: 8.4, trend_direction: "up", color: "#06B6D4" },
  { title: "ORIGINAL ORDER QTY", value: "...", unit: "Cases", trend: 6.2, trend_direction: "up", color: "#F59E0B" },
  { title: "INVOICES PROCESSED", value: "...", unit: "Invoices", trend: 4.1, trend_direction: "up", color: "#10B981" },
  { title: "FULFILLMENT RATE", value: "...", unit: "Target 95%", trend: 2.1, trend_direction: "up", color: "#34D399" },
  { title: "SCRATCH RATE", value: "...", unit: "...", trend: -1.5, trend_direction: "down", color: "#EF4444" }
]

export default function Dashboard() {
  // ── Form Input State ──────────
  const [selectedDate, setSelectedDate] = useState(todayISO())
  const [selectedDb, setSelectedDb] = useState('pg_dev')

  // ── Applied State (submitted) ──
  const [appliedDate, setAppliedDate] = useState(todayISO())
  const [appliedTargetDb, setAppliedTargetDb] = useState('pg_dev')

  // ── Table Filter Synchronization State ──
  const [tableFilters, setTableFilters] = useState(null)
  // Tracks whether the Copilot has pushed an ACTIVE filter to the page
  const [copilotFilterActive, setCopilotFilterActive] = useState(false)

  const tableFiltersRef = React.useRef(tableFilters)
  const copilotActiveRef = React.useRef(copilotFilterActive)

  React.useEffect(() => {
    tableFiltersRef.current = tableFilters
  }, [tableFilters])

  React.useEffect(() => {
    copilotActiveRef.current = copilotFilterActive
  }, [copilotFilterActive])

  // ── Global warehouse (header selector — NOT copilot) ──
  const [globalWhse, setGlobalWhse] = useState('')

  const handleApplyTableFilter = (filters) => {
    const nextFilters = { ...filters, effectiveDate: '', _ts: Date.now() };
    tableFiltersRef.current = nextFilters;
    copilotActiveRef.current = true;
    setTableFilters(nextFilters);
    setCopilotFilterActive(true);
    fetchAll(appliedDate, appliedTargetDb, nextFilters, true);
  }

  const [kpis, setKpis] = useState(DEFAULT_KPIS)
  const [barData, setBarData] = useState([])
  const [scatterData, setScatterData] = useState([])

  const fetchAll = (dateVal, dbVal, filterParams = null, copilotMode = null) => {
    const isCopilot = copilotMode !== null ? copilotMode : copilotActiveRef.current;
    const currentFilters = filterParams !== null ? filterParams : (tableFiltersRef.current || {});

    let whseVal = '';
    let batchVal = '';
    let invVal = '';
    let scratchesVal = false;
    let oerdte = '';

    if (isCopilot) {
      // Copilot search: no date — query whatever the user asked across all dates
      whseVal = currentFilters.whse || currentFilters.oewhse || currentFilters.whs_num || currentFilters.filtered_whse || '';
      batchVal = currentFilters.batch || currentFilters.batch_id || currentFilters.filtered_batch || '';
      invVal = currentFilters.invoice || currentFilters.oeinv || currentFilters.filtered_invoice || '';
      scratchesVal = Boolean(currentFilters.onlyScratches || currentFilters.filter_scratch);
      oerdte = '';
    } else {
      // Global header: date + DB + optional warehouse
      whseVal = (filterParams && filterParams.whse !== undefined)
        ? filterParams.whse
        : globalWhse;
      oerdte = dateVal ? toOerdte(dateVal) : '';
    }

    let queryParams = `oerdte=${oerdte}&target_db=${dbVal}`;
    if (whseVal) queryParams += `&oewhse=${encodeURIComponent(whseVal)}`;
    if (batchVal) queryParams += `&batch_id=${encodeURIComponent(batchVal)}`;
    if (invVal) queryParams += `&oeinv=${encodeURIComponent(invVal)}`;
    if (scratchesVal) queryParams += `&only_scratches=true`;

    axios.get(`${API}/api/charts/kpi?${queryParams}`, { timeout: 12000 })
      .then(res => {
        if (res.data?.kpis) setKpis(res.data.kpis)
      })
      .catch(err => console.error('Failed to fetch KPI cards:', err))

    axios.get(`${API}/api/charts/bar?${queryParams}`, { timeout: 12000 })
      .then(res => {
        if (res.data?.data) setBarData(res.data.data)
      })
      .catch(err => console.error('Failed to fetch Bar chart data:', err))

    axios.get(`${API}/api/charts/scatter?${queryParams}`, { timeout: 12000 })
      .then(res => {
        if (res.data?.data) setScatterData(res.data.data)
      })
      .catch(err => console.error('Failed to fetch Scatter plot data:', err))
  }

  // Initial fetch and on submission or filter change
  useEffect(() => {
    if (copilotFilterActive) {
      fetchAll(appliedDate, appliedTargetDb, tableFiltersRef.current, true)
    } else {
      fetchAll(appliedDate, appliedTargetDb, { whse: globalWhse }, false)
    }
    const timer = setInterval(() => {
      if (copilotActiveRef.current) {
        fetchAll(appliedDate, appliedTargetDb, tableFiltersRef.current, true)
      } else {
        fetchAll(appliedDate, appliedTargetDb, { whse: globalWhse }, false)
      }
    }, 15000)
    return () => clearInterval(timer)
  }, [appliedDate, appliedTargetDb, globalWhse, tableFilters, copilotFilterActive])


  const handleSubmit = (e) => {
    if (e) e.preventDefault()
    // Global Submit — deactivate copilot and apply date + DB + warehouse
    setCopilotFilterActive(false)
    setTableFilters(null)
    tableFiltersRef.current = null
    copilotActiveRef.current = false
    setAppliedDate(selectedDate)
    setAppliedTargetDb(selectedDb)
    fetchAll(selectedDate, selectedDb, { whse: globalWhse }, false)
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      {/* ── Global Date & DB Selector Header ── */}
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 className="page-title">AgenticOps AI — Enterprise Control Plane</h1>
          <p className="page-subtitle">MCP-Driven Multi-Agent Fleet Telemetry &amp; Autonomous Telemetry Dashboard</p>
        </div>

        {/* Global Date + DB Controls + Submit Button */}
        <form onSubmit={handleSubmit} style={{
          display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap',
          background: 'var(--bg-card)', border: '1px solid var(--border-color)',
          borderRadius: '10px', padding: '10px 16px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-secondary)', fontWeight: 600 }}>Order Date (Global):</span>
            <input
              id="global-date-picker"
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              style={{
                background: 'var(--bg-secondary)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border-color)',
                padding: '6px 10px',
                borderRadius: '6px',
                fontSize: '13px',
                fontWeight: 600,
                colorScheme: 'dark'
              }}
            />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-secondary)', fontWeight: 600 }}>Selected Whse:</span>
            <select
              id="global-whse-selector"
              value={copilotFilterActive
                ? (tableFilters?.whse || tableFilters?.oewhse || tableFilters?.whs_num || '').toString()
                : globalWhse}
              onChange={(e) => {
                const val = e.target.value;
                if (copilotFilterActive) return;
                setGlobalWhse(val);
                fetchAll(appliedDate, appliedTargetDb, { whse: val }, false);
              }}
              style={{
                background: 'var(--bg-secondary)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border-color)',
                padding: '6px 10px',
                borderRadius: '6px',
                fontSize: '13px',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              <option value="">All Warehouses</option>
              {(() => {
                const whsSet = new Set();
                (barData || []).forEach(b => {
                  const w = (b.whs_num || b.label || '').toString().replace(/^WHS\s*/i, '').trim();
                  if (w) whsSet.add(w);
                });
                if (globalWhse) whsSet.add(globalWhse);
                if (copilotFilterActive) {
                  const cw = (tableFilters?.whse || tableFilters?.oewhse || tableFilters?.whs_num || '').toString().trim();
                  if (cw) whsSet.add(cw);
                }
                const sorted = Array.from(whsSet).sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));
                return sorted.map(w => (
                  <option key={w} value={w}>Whse {w}</option>
                ));
              })()}
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-secondary)', fontWeight: 600 }}>Target DB:</span>
            <select
              id="global-db-selector"
              value={selectedDb}
              onChange={(e) => setSelectedDb(e.target.value)}
              style={{
                background: 'var(--bg-secondary)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border-color)',
                padding: '6px 10px',
                borderRadius: '6px',
                fontSize: '13px',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              <option value="pg_dev">PostgreSQL DEV</option>
              <option value="oracle_dev">Oracle DEV</option>
              <option value="oracle_f1">Oracle F1</option>
            </select>
          </div>

          <button
            type="submit"
            id="submit-db-btn"
            onClick={handleSubmit}
            style={{
              background: 'linear-gradient(135deg, #7C3AED 0%, #6D28D9 100%)',
              color: '#FFFFFF',
              border: 'none',
              padding: '7px 18px',
              borderRadius: '6px',
              fontSize: '13px',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              transition: 'all 0.2s ease',
              boxShadow: '0 2px 6px rgba(124, 58, 237, 0.4)'
            }}
          >
            Submit
          </button>

          {Boolean(tableFilters?.whse || tableFilters?.oewhse || tableFilters?.whs_num || tableFilters?.batch || tableFilters?.invoice || tableFilters?.onlyScratches || copilotFilterActive || (!copilotFilterActive && globalWhse)) && (
            <button
              type="button"
              id="header-clear-filter-btn"
              onClick={() => {
                setGlobalWhse('');
                setCopilotFilterActive(false);
                setTableFilters(null);
                tableFiltersRef.current = null;
                copilotActiveRef.current = false;
                fetchAll(appliedDate, appliedTargetDb, { whse: '' }, false);
              }}
              style={{
                background: 'rgba(239, 68, 68, 0.15)',
                color: '#fca5a5',
                border: '1px solid rgba(239, 68, 68, 0.4)',
                padding: '7px 14px',
                borderRadius: '6px',
                fontSize: '12px',
                fontWeight: 700,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                transition: 'all 0.2s ease'
              }}
            >
              ✕ Clear Filters
            </button>
          )}

          <span style={{
            fontSize: '11px', color: '#34d399', fontWeight: 700,
            background: 'rgba(52,211,153,0.1)', padding: '3px 8px', borderRadius: '4px'
          }}>
            Active: {appliedTargetDb.toUpperCase()}
          </span>
        </form>
      </div>

      {/* ── Active Warehouse & Filter Synchronizer Banner ── */}
      {Boolean(tableFilters?.whse || tableFilters?.oewhse || tableFilters?.batch || tableFilters?.invoice || tableFilters?.onlyScratches || (!copilotFilterActive && globalWhse)) && (
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px',
          background: 'linear-gradient(135deg, rgba(52,211,153,0.12) 0%, rgba(16,185,129,0.06) 100%)',
          border: '1px solid rgba(52,211,153,0.4)', borderRadius: '8px', padding: '10px 16px', marginTop: '16px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '12px', fontWeight: 700, color: '#34d399', display: 'flex', alignItems: 'center', gap: '6px' }}>
              ⚡ Active Page Filters:
            </span>
            {(!copilotFilterActive && globalWhse) && (
              <span style={{ fontSize: '12px', fontWeight: 700, background: 'rgba(52,211,153,0.2)', color: '#6ee7b7', padding: '3px 10px', borderRadius: '6px', border: '1px solid rgba(52,211,153,0.5)' }}>
                🏢 Global Warehouse: Whse {globalWhse}
              </span>
            )}
            {(tableFilters?.whse || tableFilters?.oewhse || tableFilters?.whs_num) && (
              <span style={{ fontSize: '12px', fontWeight: 700, background: 'rgba(52,211,153,0.2)', color: '#6ee7b7', padding: '3px 10px', borderRadius: '6px', border: '1px solid rgba(52,211,153,0.5)' }}>
                🏢 Warehouse: Whse {(tableFilters?.whse || tableFilters?.oewhse || tableFilters?.whs_num)}
              </span>
            )}
            {tableFilters?.batch && (
              <span style={{ fontSize: '12px', fontWeight: 700, background: 'rgba(245,158,11,0.2)', color: '#fcd34d', padding: '3px 10px', borderRadius: '6px', border: '1px solid rgba(245,158,11,0.5)' }}>
                📦 Batch: #{tableFilters.batch}
              </span>
            )}
            {tableFilters?.invoice && (
              <span style={{ fontSize: '12px', fontWeight: 700, background: 'rgba(192,132,252,0.2)', color: '#e9d5ff', padding: '3px 10px', borderRadius: '6px', border: '1px solid rgba(192,132,252,0.5)' }}>
                🧾 Invoice: #{tableFilters.invoice}
              </span>
            )}
            {tableFilters?.onlyScratches && (
              <span style={{ fontSize: '12px', fontWeight: 700, background: 'rgba(239,68,68,0.2)', color: '#fca5a5', padding: '3px 10px', borderRadius: '6px', border: '1px solid rgba(239,68,68,0.5)' }}>
                🔴 Scratch Items Only
              </span>
            )}
          </div>
          <button
            type="button"
            onClick={() => {
              setGlobalWhse('');
              setCopilotFilterActive(false);
              setTableFilters(null);
              tableFiltersRef.current = null;
              copilotActiveRef.current = false;
              fetchAll(appliedDate, appliedTargetDb, { whse: '' }, false);
            }}
            style={{
              background: 'rgba(255,255,255,0.08)', color: 'var(--text-secondary)',
              border: '1px solid var(--border-color)', padding: '4px 12px',
              borderRadius: '6px', fontSize: '11px', fontWeight: 700,
              cursor: 'pointer', transition: 'all 0.2s ease'
            }}
          >
            Clear All Filters
          </button>
        </div>
      )}

      {/* ── AI Data Copilot Feature ── */}
      <AiDataCopilot
        globalDate={appliedDate}
        globalTargetDb={appliedTargetDb}
        onApplyFilter={handleApplyTableFilter}
        onClearFilter={() => {
          setCopilotFilterActive(false)
          setTableFilters(null)
          tableFiltersRef.current = null
          copilotActiveRef.current = false
          fetchAll(appliedDate, appliedTargetDb, { whse: globalWhse }, false)
        }}
        copilotFilterActive={copilotFilterActive}
      />

      {/* ── Real-Time Anomaly & Risk Alerts Feature ── */}
      <AnomalyAlertPanel
        globalDate={appliedDate}
        globalTargetDb={appliedTargetDb}
        selectedWhse={tableFilters?.whse || tableFilters?.whs_num || ''}
        onApplyFilter={handleApplyTableFilter}
      />

      {/* ── Data Analytics — CSV/Excel upload + ML training on dashboard ── */}
      <DataAnalytics />

      {/* ── Warehouse Level KPI Grid ── */}
      <div className="kpi-grid" style={{ marginTop: '24px' }}>
        {kpis.map((kpi, i) => (
          <KPICard key={kpi.title} {...kpi} index={i} />
        ))}
      </div>

      {/* ── Charts Grid ── */}
      <div className="chart-grid" style={{ marginTop: '24px' }}>
        {/* Bar Chart */}
        <motion.div
          className="chart-card"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
        >
          <div className="chart-title">Cases Built by Warehouse</div>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={barData} margin={{ top: 5, right: 10, bottom: 5, left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="label" interval={0} tick={{ fill: '#8B949E', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#8B949E', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(124,58,237,0.08)' }} />
              <Bar dataKey="value" name="Cases Built Qty" radius={[6, 6, 0, 0]}>
                {barData.map((entry, i) => {
                  const targetW = (tableFilters?.whse || tableFilters?.oewhse || tableFilters?.whs_num || tableFilters?.filtered_whse || '').toString().replace(/^0+/, '');
                  const currentW = (entry.whs_num || '').toString().replace(/^0+/, '');
                  const isHighlighted = targetW && currentW === targetW;
                  return (
                    <Cell key={i} fill={isHighlighted ? '#34D399' : COLORS[i % COLORS.length]} opacity={targetW && !isHighlighted ? 0.35 : 1.0} />
                  );
                })}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Scatter Chart */}
        <motion.div
          className="chart-card"
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.4 }}
        >
          <div className="chart-title">Original Order Qty vs Cases Built</div>
          <ResponsiveContainer width="100%" height={280}>
            <ScatterChart margin={{ top: 5, right: 10, bottom: 5, left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis type="number" dataKey="x" name="Order Qty" tick={{ fill: '#8B949E', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis type="number" dataKey="y" name="Cases Built" tick={{ fill: '#8B949E', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip cursor={{ strokeDasharray: '3 3' }} content={<CustomTooltip />} />
              <Scatter name="Order vs Built" data={scatterData} fill="#06B6D4">
                {scatterData.map((entry, i) => {
                  const targetW = (tableFilters?.whse || tableFilters?.oewhse || tableFilters?.whs_num || tableFilters?.filtered_whse || '').toString().replace(/^0+/, '');
                  const currentW = (entry.whs_num || entry.whse || entry.color || '').toString().replace(/[^0-9]/g, '').replace(/^0+/, '');
                  const isHighlighted = targetW && currentW === targetW;
                  return (
                    <Cell key={i} fill={isHighlighted ? '#34D399' : '#06B6D4'} opacity={targetW && !isHighlighted ? 0.25 : 0.85} />
                  );
                })}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
        </motion.div>
      </div>

      {/* ── Autonomous Agent Task Pickup & Execution Stream ── */}

      {/* ── Warehouse Sales & Invoice Analytics — receives global date, db & external filters ── */}
      <WarehouseSalesAnalytics
        globalDate={copilotFilterActive ? '' : appliedDate}
        globalTargetDb={appliedTargetDb}
        externalFilters={copilotFilterActive ? tableFilters : (globalWhse ? { whse: globalWhse } : null)}
        copilotFilterActive={copilotFilterActive}
      />

      {/* ── Warehouse Inventory Level Statistics ── */}
    </motion.div>
  )
}


