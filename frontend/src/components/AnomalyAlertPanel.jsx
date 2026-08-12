import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { AlertTriangle, AlertCircle, Info, CheckCircle2, Filter, RefreshCw } from 'lucide-react';

const API = import.meta.env.VITE_API_URL || '';

export default function AnomalyAlertPanel({ globalDate, globalTargetDb = 'pg_dev', selectedWhse = '', onApplyFilter }) {
  const [anomalies, setAnomalies] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchAnomalies = async () => {
    setLoading(true);
    try {
      const oerdte = globalDate ? globalDate.replace(/-/g, '') : '';
      const res = await axios.get(`${API}/api/analytics/anomalies?target_db=${globalTargetDb}&oerdte=${oerdte}&oewhse=${selectedWhse || ''}`, { timeout: 12000 });
      setAnomalies(res.data.anomalies || []);
    } catch (err) {
      console.error('[AnomalyAlertPanel] Error fetching anomalies:', err);
      setAnomalies([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnomalies();
  }, [globalDate, globalTargetDb, selectedWhse]);

  const getSeverityStyle = (severity) => {
    switch (severity) {
      case 'critical':
        return {
          bg: 'rgba(239, 68, 68, 0.08)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          color: '#ef4444',
          icon: AlertTriangle
        };
      case 'warning':
        return {
          bg: 'rgba(245, 158, 11, 0.08)',
          border: '1px solid rgba(245, 158, 11, 0.3)',
          color: '#f59e0b',
          icon: AlertCircle
        };
      case 'info':
        return {
          bg: 'rgba(6, 182, 212, 0.08)',
          border: '1px solid rgba(6, 182, 212, 0.3)',
          color: '#06b6d4',
          icon: Info
        };
      default:
        return {
          bg: 'rgba(52, 211, 153, 0.08)',
          border: '1px solid rgba(52, 211, 153, 0.3)',
          color: '#34d399',
          icon: CheckCircle2
        };
    }
  };

  return (
    <div className="card" style={{ marginTop: '20px', padding: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '10px' }}>
        <div>
          <h3 style={{ fontSize: '17px', fontWeight: 700, color: 'var(--text-primary)', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertTriangle size={18} color="#ef4444" /> Real-Time Anomaly &amp; Risk Alerts
          </h3>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)', margin: 0, marginTop: '2px' }}>
            Automated anomaly detection scanning line-item scratches, transfer delays, and order spikes
          </p>
        </div>

        <button
          type="button"
          onClick={fetchAnomalies}
          style={{
            background: 'var(--bg-secondary)',
            color: 'var(--text-secondary)',
            border: '1px solid var(--border-color)',
            padding: '5px 12px',
            borderRadius: '6px',
            fontSize: '12px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontWeight: 600
          }}
        >
          <RefreshCw size={12} className={loading ? 'spin' : ''} /> Refresh Alerts
        </button>
      </div>

      {loading ? (
        <div style={{ padding: '16px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '13px' }}>
          Scanning database for fulfillment anomalies...
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '14px' }}>
          {anomalies.map((item) => {
            const style = getSeverityStyle(item.severity);
            const Icon = style.icon;

            return (
              <div
                key={item.id}
                style={{
                  background: style.bg,
                  border: style.border,
                  borderRadius: '10px',
                  padding: '14px 16px',
                  display: 'flex',
                  flexDirection: 'column',
                  justify: 'space-between'
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <span style={{ fontSize: '13px', fontWeight: 700, color: style.color, display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <Icon size={16} /> {item.title}
                    </span>
                    <span style={{ fontSize: '10px', textTransform: 'uppercase', fontWeight: 700, color: style.color, background: 'rgba(0,0,0,0.2)', padding: '2px 6px', borderRadius: '4px' }}>
                      {item.severity}
                    </span>
                  </div>
                  <p style={{ fontSize: '12px', color: 'var(--text-secondary)', margin: 0, marginBottom: '10px', lineHeight: 1.4 }}>
                    {item.message}
                  </p>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: '8px', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                    Whse: <strong style={{ color: 'var(--text-primary)' }}>{item.warehouse}</strong>
                  </span>

                  {item.filter_whse && onApplyFilter && (
                    <button
                      type="button"
                      onClick={() => onApplyFilter({ whse: item.filter_whse, effectiveDate: item.effective_date || '', onlyScratches: item.filter_scratch || false })}
                      style={{
                        background: 'rgba(255,255,255,0.1)',
                        color: 'var(--text-primary)',
                        border: 'none',
                        padding: '4px 10px',
                        borderRadius: '6px',
                        fontSize: '11px',
                        fontWeight: 600,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px'
                      }}
                    >
                      <Filter size={10} /> Filter Table
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
