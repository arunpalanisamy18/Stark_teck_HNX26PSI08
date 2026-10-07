import React, { useState, useEffect } from 'react';

export default function DatasetInfo({ datasetId = 'demo' }) {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    fetch(`/api/dataset/${datasetId}`)
      .then(res => res.json())
      .then(data => setProfile(data))
      .catch(() => setProfile(null))
      .finally(() => setLoading(false));
  }, [datasetId]);

  if (loading || !profile || !profile.tables) return null;

  return (
    <div style={{
      marginBottom: '1.5rem',
      padding: '0.85rem 1rem',
      backgroundColor: 'var(--bg-surface)',
      border: '1px solid var(--border-dim)',
      borderRadius: 'var(--radius-md)',
      fontSize: '0.8rem'
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '0.5rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{
            fontSize: '0.7rem',
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
            fontWeight: 700,
            color: 'var(--text-muted)'
          }}>
            Active Dataset Catalog
          </span>
          <span style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '0.75rem',
            color: '#fff',
            fontWeight: 600
          }}>
            [{datasetId}]
          </span>
        </div>

        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
          {profile.total_rows} total rows &bull; {profile.tables.length} tables
        </span>
      </div>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.65rem' }}>
        {profile.tables.map((t, idx) => (
          <div
            key={idx}
            style={{
              padding: '0.4rem 0.65rem',
              backgroundColor: 'var(--bg-canvas)',
              border: '1px solid var(--border-dim)',
              borderRadius: 'var(--radius-sm)',
              fontSize: '0.75rem'
            }}
          >
            <strong style={{ color: '#fff', fontFamily: 'var(--font-mono)' }}>{t.table}</strong>
            <span style={{ color: 'var(--text-muted)', marginLeft: '6px' }}>
              ({t.rows} rows, {t.columns?.length || 0} cols)
            </span>
            {t.duplicate_rows > 0 && (
              <span style={{ color: 'var(--clarify-color)', marginLeft: '6px' }}>
                [{t.duplicate_rows} dups]
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

