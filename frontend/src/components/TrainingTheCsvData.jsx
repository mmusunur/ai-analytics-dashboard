import React, { useState } from 'react';
import axios from 'axios';
import { Cpu, Play, CheckCircle2, AlertCircle } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function TrainingTheCsvData() {
  const [targetColumn, setTargetColumn] = useState('target');
  const [modelType, setModelType] = useState('both');
  const [isTraining, setIsTraining] = useState(false);
  const [trainResult, setTrainResult] = useState(null);
  const [error, setError] = useState(null);

  const handleTrain = async () => {
    setIsTraining(true);
    setError(null);
    try {
      const response = await axios.post(`${API_URL}/api/analytics/train`, {
        target_column: targetColumn,
        model_type: modelType,
      });
      if (response.data?.status === 'success') {
        setTrainResult(response.data);
      } else {
        setError('Training failed to return expected response format');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to train model. Ensure backend server is running.');
    } finally {
      setIsTraining(false);
    }
  };

  return (
    <div className="trainingthecsvdata-card card" style={{ marginTop: '20px', padding: '20px', borderRadius: '12px', background: 'var(--bg-card)', border: '1px solid var(--border-color)' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ background: 'rgba(124, 58, 237, 0.15)', padding: '8px', borderRadius: '8px', color: '#a78bfa' }}>
            <Cpu size={22} />
          </div>
          <div>
            <h3 style={{ fontSize: '18px', fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>
              CSV Dataset Model Training
            </h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '13px', margin: 0, marginTop: '2px' }}>
              Train machine learning classification models on uploaded warehouse datasets
            </p>
          </div>
        </div>
        <span style={{ fontSize: '11px', padding: '4px 10px', borderRadius: '20px', background: 'rgba(16, 185, 129, 0.15)', color: '#34d399', fontWeight: 600 }}>
          ● Live ML Engine
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginBottom: '20px' }}>
        <div>
          <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px', fontWeight: 500 }}>
            Target Column
          </label>
          <select
            value={targetColumn}
            onChange={(e) => setTargetColumn(e.target.value)}
            style={{
              width: '100%',
              padding: '10px 12px',
              borderRadius: '8px',
              background: 'var(--bg-main, #0f172a)',
              border: '1px solid var(--border-color)',
              color: 'var(--text-primary)',
              fontSize: '14px',
              outline: 'none'
            }}
          >
            <option value="target">target (Binary Label)</option>
            <option value="promoted">promoted (Promotion Status)</option>
            <option value="cases_bld_stg">cases_bld_stg (Cases Staged)</option>
            <option value="orgnl_ordr_qty_stg">orgnl_ordr_qty_stg (Order Qty)</option>
            <option value="whs_scrtch_qty_stg">whs_scrtch_qty_stg (Scratch Qty)</option>
          </select>
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px', fontWeight: 500 }}>
            Algorithm Architecture
          </label>
          <select
            value={modelType}
            onChange={(e) => setModelType(e.target.value)}
            style={{
              width: '100%',
              padding: '10px 12px',
              borderRadius: '8px',
              background: 'var(--bg-main, #0f172a)',
              border: '1px solid var(--border-color)',
              color: 'var(--text-primary)',
              fontSize: '14px',
              outline: 'none'
            }}
          >
            <option value="both">All Algorithms (Random Forest + Logistic Reg)</option>
            <option value="random_forest">Random Forest Classifier</option>
            <option value="logistic_regression">Logistic Regression</option>
          </select>
        </div>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <button
          onClick={handleTrain}
          disabled={isTraining}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            padding: '10px 20px',
            borderRadius: '8px',
            background: isTraining ? 'rgba(124, 58, 237, 0.4)' : '#7c3aed',
            color: '#ffffff',
            fontWeight: 600,
            fontSize: '14px',
            border: 'none',
            cursor: isTraining ? 'not-allowed' : 'pointer',
            transition: 'all 0.2s ease'
          }}
        >
          {isTraining ? (
            <>
              <div style={{ width: '16px', height: '16px', border: '2px solid #ffffff', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
              Training Model...
            </>
          ) : (
            <>
              <Play size={16} /> Execute Model Training
            </>
          )}
        </button>
      </div>

      {error && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '12px', borderRadius: '8px', background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.3)', color: '#fca5a5', fontSize: '13px', marginBottom: '16px' }}>
          <AlertCircle size={16} />
          {error}
        </div>
      )}

      {trainResult && (
        <div style={{ paddingTop: '16px', borderTop: '1px solid var(--border-color)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px', color: '#34d399', fontWeight: 600 }}>
            <CheckCircle2 size={18} /> Training Completed Successfully
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '16px' }}>
            {trainResult.results?.map((m, idx) => (
              <div key={idx} style={{ padding: '14px', borderRadius: '10px', background: 'var(--bg-main, #0f172a)', border: '1px solid var(--border-color)' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '15px' }}>{m.model_name}</div>
                  <span style={{ fontSize: '12px', fontWeight: 700, padding: '2px 8px', borderRadius: '12px', background: 'rgba(124, 58, 237, 0.2)', color: '#a78bfa' }}>
                    {(m.accuracy * 100).toFixed(1)}% Accuracy
                  </span>
                </div>

                <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '8px' }}>Confusion Matrix</div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', textAlign: 'center', fontSize: '12px' }}>
                  {m.confusion_matrix?.map((row, rIdx) =>
                    row.map((val, cIdx) => (
                      <div key={`${rIdx}-${cIdx}`} style={{ padding: '8px', borderRadius: '6px', background: 'rgba(255, 255, 255, 0.05)', border: '1px solid var(--border-color)', fontWeight: 600, color: 'var(--text-primary)' }}>
                        {rIdx === 0 && cIdx === 0 ? `TN: ${val}` : rIdx === 0 && cIdx === 1 ? `FP: ${val}` : rIdx === 1 && cIdx === 0 ? `FN: ${val}` : `TP: ${val}`}
                      </div>
                    ))
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
