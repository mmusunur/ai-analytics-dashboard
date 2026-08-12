import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'
import { Upload, Play, Brain, ExternalLink } from 'lucide-react'

const API = import.meta.env.VITE_API_URL || ''

export default function DataAnalytics() {
  const [uploading, setUploading] = useState(false)
  const [uploadMsg, setUploadMsg] = useState('')
  const [training, setTraining] = useState(false)
  const [trainResult, setTrainResult] = useState(null)

  const handleUpload = async (file) => {
    if (!file) return
    setUploading(true)
    setUploadMsg('')
    const formData = new FormData()
    formData.append('file', file)
    try {
      const res = await axios.post(`${API}/api/data/upload`, formData)
      setUploadMsg(`Uploaded ${res.data.rows} rows (${res.data.columns} columns)`)
    } catch {
      setUploadMsg('Upload failed — open ML Analytics for sample data')
    } finally {
      setUploading(false)
    }
  }

  const handleTrain = async () => {
    setTraining(true)
    setTrainResult(null)
    try {
      const res = await axios.post(`${API}/api/analytics/train`, {
        target_column: 'target',
        model_type: 'random_forest',
        n_estimators: 50,
        test_size: 0.2,
      })
      setTrainResult(res.data)
    } catch {
      setTrainResult(null)
    } finally {
      setTraining(false)
    }
  }

  const accuracy = trainResult?.results?.[0]?.accuracy

  return (
    <div id="data-analytics-panel" className="card" style={{ marginTop: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px', marginBottom: '16px' }}>
        <div>
          <h3 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
            Data Analytics
          </h3>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '6px' }}>
            Upload CSV or Excel, train ML models, and explore results on the dashboard.
          </p>
        </div>
        <Link to="/analytics" style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '12px', fontWeight: 600, color: '#a78bfa', textDecoration: 'none' }}>
          Full ML Analytics <ExternalLink size={14} />
        </Link>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
        <div className="upload-zone" style={{ padding: '20px', cursor: 'pointer', textAlign: 'center' }}
          onClick={() => document.getElementById('dashboard-csv-input')?.click()}
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => { e.preventDefault(); handleUpload(e.dataTransfer.files[0]) }}>
          <input id="dashboard-csv-input" type="file" accept=".csv,.xlsx,.xls" hidden
            onChange={(e) => handleUpload(e.target.files?.[0])} />
          {uploading ? <div className="spinner" style={{ margin: '0 auto' }} /> : (
            <>
              <Upload size={28} color="var(--color-primary-light)" style={{ margin: '0 auto 8px', display: 'block' }} />
              <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Drop CSV / Excel or click to upload</p>
              {uploadMsg && <p style={{ fontSize: '12px', color: 'var(--color-green)', marginTop: '8px' }}>{uploadMsg}</p>}
            </>
          )}
        </div>
        <div style={{ padding: '16px', background: 'var(--bg-primary)', borderRadius: '10px', border: '1px solid var(--border-subtle)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <Brain size={20} color="#a78bfa" />
            <span style={{ fontWeight: 600, fontSize: '14px', color: 'var(--text-primary)' }}>Quick Train</span>
          </div>
          <button type="button" className="btn btn-primary" style={{ width: '100%' }} onClick={handleTrain} disabled={training}>
            {training ? 'Training…' : (<><Play size={14} /> Train Random Forest</>)}
          </button>
          {accuracy != null && (
            <p style={{ fontSize: '12px', color: 'var(--color-green)', marginTop: '10px' }}>
              Accuracy: {(accuracy * 100).toFixed(1)}%
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
