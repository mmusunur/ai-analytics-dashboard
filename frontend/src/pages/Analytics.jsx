import { useState } from 'react'
import { motion } from 'framer-motion'
import axios from 'axios'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell
} from 'recharts'
import { Upload, Play, CheckCircle, AlertCircle, Brain } from 'lucide-react'

const API = import.meta.env.VITE_API_URL || ''
const COLORS = ['#7C3AED', '#06B6D4', '#F59E0B', '#10B981', '#EF4444', '#8B5CF6']

export default function Analytics() {
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [uploadDone, setUploadDone] = useState(false)
  const [targetCol, setTargetCol] = useState('target')
  const [modelType, setModelType] = useState('random_forest')
  const [nEstimators, setNEstimators] = useState(100)
  const [training, setTraining] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)
  const [dragging, setDragging] = useState(false)

  const handleUpload = async (csvFile) => {
    if (!csvFile) return
    setUploading(true)
    const formData = new FormData()
    formData.append('file', csvFile)
    try {
      await axios.post(`${API}/api/data/upload`, formData)
      setUploadDone(true)
      setFile(csvFile)
    } catch {
      setError('Upload failed — using sample data instead')
    } finally {
      setUploading(false)
    }
  }

  const handleTrain = async () => {
    setTraining(true)
    setError(null)
    setResults(null)
    try {
      const res = await axios.post(`${API}/api/analytics/train`, {
        target_column: targetCol,
        model_type: modelType,
        n_estimators: nEstimators,
        test_size: 0.2
      })
      setResults(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Training failed')
    } finally {
      setTraining(false)
    }
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.5 }}>
      <div className="page-header">
        <h1 className="page-title">🤖 ML Analytics</h1>
        <p className="page-subtitle">Upload your data, train models, and explore results interactively</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: 24 }}>
        {/* Config Panel */}
        <div>
          {/* Upload */}
          <div className="card" style={{ marginBottom: 20 }}>
            <div className="chart-title">📂 Data Source</div>
            <div
              className={`upload-zone ${dragging ? 'dragging' : ''}`}
              style={{ padding: 24 }}
              onClick={() => document.getElementById('csv-input').click()}
              onDragOver={e => { e.preventDefault(); setDragging(true) }}
              onDragLeave={() => setDragging(false)}
              onDrop={e => { e.preventDefault(); setDragging(false); handleUpload(e.dataTransfer.files[0]) }}
            >
              <input id="csv-input" type="file" accept=".csv,.xlsx,.xls" hidden
                onChange={e => handleUpload(e.target.files[0])} />
              {uploading ? (
                <div className="spinner" style={{ margin: '0 auto' }} />
              ) : uploadDone ? (
                <div>
                  <CheckCircle size={32} color="var(--color-green)" style={{ margin: '0 auto 8px' }} />
                  <p style={{ fontSize: 13, color: 'var(--color-green)' }}>{file?.name}</p>
                </div>
              ) : (
                <div>
                  <Upload size={32} color="var(--color-primary-light)" style={{ margin: '0 auto 8px', display: 'block' }} />
                  <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Drop CSV or click to upload</p>
                  <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>Using sample data if empty</p>
                </div>
              )}
            </div>
          </div>

          {/* Training Config */}
          <div className="card">
            <div className="chart-title">⚙️ Model Config</div>

            <div className="form-group">
              <label className="form-label">Target Column</label>
              <select className="form-select" value={targetCol} onChange={e => setTargetCol(e.target.value)}>
                <option value="target">target</option>
                <option value="attrition">attrition</option>
                <option value="promoted">promoted</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Model Type</label>
              <select className="form-select" value={modelType} onChange={e => setModelType(e.target.value)}>
                <option value="random_forest">Random Forest</option>
                <option value="logistic_regression">Logistic Regression</option>
                <option value="both">Both Models</option>
              </select>
            </div>

            {(modelType === 'random_forest' || modelType === 'both') && (
              <div className="form-group">
                <label className="form-label">Trees: {nEstimators}</label>
                <input type="range" min="10" max="300" value={nEstimators}
                  onChange={e => setNEstimators(+e.target.value)}
                  style={{ width: '100%', accentColor: 'var(--color-primary)' }} />
              </div>
            )}

            <button className="btn btn-primary" style={{ width: '100%' }}
              onClick={handleTrain} disabled={training}>
              {training ? (
                <><div className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} /> Training...</>
              ) : (
                <><Play size={16} /> Train Model</>
              )}
            </button>
          </div>
        </div>

        {/* Results Panel */}
        <div>
          {error && (
            <div style={{ 
              background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)',
              borderRadius: 12, padding: '16px 20px', marginBottom: 20,
              display: 'flex', gap: 12, alignItems: 'center', color: 'var(--color-red)'
            }}>
              <AlertCircle size={18} /> {error}
            </div>
          )}

          {!results && !training && (
            <div className="card" style={{ textAlign: 'center', padding: '60px 32px' }}>
              <Brain size={48} color="var(--text-muted)" style={{ margin: '0 auto 16px', display: 'block' }} />
              <p style={{ color: 'var(--text-secondary)', fontSize: 15 }}>Configure and train a model to see results</p>
              <p style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 8 }}>
                Results include accuracy, confusion matrix, and feature importance
              </p>
            </div>
          )}

          {training && (
            <div className="card" style={{ textAlign: 'center', padding: '60px 32px' }}>
              <div className="spinner" style={{ margin: '0 auto 16px' }} />
              <p style={{ color: 'var(--text-secondary)' }}>Training model, please wait...</p>
            </div>
          )}

          {results && results.results?.map((model, idx) => (
            <motion.div key={idx} className="card" style={{ marginBottom: 20 }}
              initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: idx * 0.1 }}>
              
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
                <div className="chart-title" style={{ marginBottom: 0 }}>
                  🔹 {model.model_name}
                </div>
                <span className="badge badge-green">Accuracy: {(model.accuracy * 100).toFixed(1)}%</span>
              </div>

              {/* Metrics Row */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 24 }}>
                {[
                  { label: 'Accuracy', value: (model.accuracy * 100).toFixed(1) + '%', color: 'var(--color-green)' },
                  { label: 'Precision', value: (model.precision * 100).toFixed(1) + '%', color: 'var(--color-cyan)' },
                  { label: 'Recall', value: (model.recall * 100).toFixed(1) + '%', color: 'var(--color-amber)' },
                  { label: 'F1 Score', value: (model.f1_score * 100).toFixed(1) + '%', color: 'var(--color-purple)' },
                ].map(m => (
                  <div key={m.label} style={{ textAlign: 'center', padding: '12px', background: 'var(--bg-primary)', borderRadius: 8 }}>
                    <div style={{ fontSize: 22, fontWeight: 700, color: m.color }}>{m.value}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>{m.label}</div>
                  </div>
                ))}
              </div>

              {/* Feature Importance */}
              {model.feature_importance && (
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 12 }}>
                    Feature Importance (Top 10)
                  </div>
                  <ResponsiveContainer width="100%" height={220}>
                    <BarChart
                      data={Object.entries(model.feature_importance).slice(0, 10).map(([k, v]) => ({ name: k, value: +(v * 100).toFixed(2) }))}
                      layout="vertical"
                      margin={{ top: 0, right: 20, bottom: 0, left: 100 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" horizontal={false} />
                      <XAxis type="number" tick={{ fill: '#8B949E', fontSize: 11 }} axisLine={false} tickLine={false} />
                      <YAxis type="category" dataKey="name" tick={{ fill: '#8B949E', fontSize: 11 }} axisLine={false} tickLine={false} width={95} />
                      <Tooltip formatter={(v) => [`${v}%`, 'Importance']} />
                      <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                        {Object.keys(model.feature_importance).slice(0, 10).map((_, i) => (
                          <Cell key={i} fill={COLORS[i % COLORS.length]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </motion.div>
          ))}
        </div>
      </div>
    </motion.div>
  )
}
