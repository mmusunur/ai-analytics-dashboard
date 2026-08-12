import React from 'react';

export default function AddAditionalFeatures() {
  return (
    <div className="addaditionalfeatures-card card" style={{ marginTop: '20px' }}>
      <h3 style={{ fontSize: '18px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '12px' }}>
        ⚡ Add Aditional Features
      </h3>
      <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginBottom: '16px' }}>
        Add Aditional Features Task spec reference --- section_1_mandatory_tasks.md ---   Section 1 Manda...
      </p>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
        <div style={{ background: 'var(--bg-card)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
          <div style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>Metric / Status</div>
          <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--color-primary)' }}>Active</div>
        </div>
      </div>
    </div>
  );
}
