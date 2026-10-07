import React, { useState } from 'react';

export default function DataProfilePanel({ profile, loading }) {
  const [selectedTableIdx, setSelectedTableIdx] = useState(0);

  if (loading) {
    return (
      <div style={{
        marginBottom: '1.75rem',
        backgroundColor: 'var(--bg-surface)',
        border: '1px solid var(--border-dim)',
        borderRadius: 'var(--radius-md)',
        padding: '1.25rem',
        textAlign: 'center',
        color: 'var(--text-muted)',
        fontSize: '0.85rem'
      }}>
        Profiling dataset schema, statistics, and anomalies...
      </div>
    );
  }

  if (!profile || !profile.tables || profile.tables.length === 0) {
    return null;
  }

  const activeTable = profile.tables[selectedTableIdx] || profile.tables[0];
  const allWarnings = [
    ...(profile.cross_table_warnings || []),
    ...(profile.contradictions || []),
    ...(profile.join_risks || []),
    ...(activeTable?.warnings || [])
  ];

  return (
    <div style={{
      marginBottom: '1.75rem',
      backgroundColor: 'var(--bg-surface)',
      border: '1px solid var(--border-dim)',
      borderRadius: 'var(--radius-md)',
      padding: '1.25rem'
    }}>
      {/* Panel Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '1rem',
        flexWrap: 'wrap',
        gap: '0.5rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{
            fontSize: '0.75rem',
            fontFamily: 'var(--font-mono)',
            fontWeight: 700,
            color: '#38bdf8',
            backgroundColor: 'rgba(56, 189, 248, 0.1)',
            padding: '2px 6px',
            borderRadius: 'var(--radius-sm)'
          }}>
            02
          </span>
          <span style={{
            fontSize: '0.75rem',
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
            fontWeight: 700,
            color: 'var(--text-primary)'
          }}>
            Data Profile &bull; Statistical Diagnostic Panel
          </span>
        </div>

        {/* Global Dataset Metrics */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '1rem',
          fontSize: '0.75rem',
          fontFamily: 'var(--font-mono)'
        }}>
          <div>
            <span style={{ color: 'var(--text-muted)' }}>TOTAL ROWS: </span>
            <strong style={{ color: '#fff' }}>{profile.total_rows.toLocaleString()}</strong>
          </div>
          <div>
            <span style={{ color: 'var(--text-muted)' }}>TABLES: </span>
            <strong style={{ color: '#fff' }}>{profile.tables.length}</strong>
          </div>
          <div>
            <span style={{ color: 'var(--text-muted)' }}>CATALOG ID: </span>
            <span style={{ color: 'var(--text-secondary)' }}>[{profile.dataset_id}]</span>
          </div>
        </div>
      </div>

      {/* Multi-Table Selector Tabs if >1 table */}
      {profile.tables.length > 1 && (
        <div style={{
          display: 'flex',
          gap: '0.4rem',
          marginBottom: '1rem',
          borderBottom: '1px solid var(--border-subtle)',
          paddingBottom: '0.5rem',
          overflowX: 'auto'
        }}>
          {profile.tables.map((t, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => setSelectedTableIdx(idx)}
              style={{
                padding: '0.35rem 0.75rem',
                fontSize: '0.75rem',
                fontFamily: 'var(--font-mono)',
                fontWeight: 600,
                backgroundColor: selectedTableIdx === idx ? 'var(--bg-elevated)' : 'transparent',
                color: selectedTableIdx === idx ? '#fff' : 'var(--text-muted)',
                border: selectedTableIdx === idx ? '1px solid var(--border-accent)' : '1px solid transparent',
                borderRadius: 'var(--radius-sm)',
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.4rem'
              }}
            >
              <span>{t.table}</span>
              <span style={{
                fontSize: '0.65rem',
                color: selectedTableIdx === idx ? 'var(--text-secondary)' : 'var(--text-dim)'
              }}>
                ({t.rows}r)
              </span>
            </button>
          ))}
        </div>
      )}

      {/* Active Table Summary Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
        gap: '0.65rem',
        marginBottom: '1rem'
      }}>
        <div style={{
          backgroundColor: 'var(--bg-canvas)',
          padding: '0.65rem 0.85rem',
          borderRadius: 'var(--radius-sm)',
          border: '1px solid var(--border-dim)'
        }}>
          <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Rows</div>
          <div style={{ fontSize: '1.05rem', fontWeight: 700, color: '#fff', fontFamily: 'var(--font-mono)' }}>
            {activeTable.rows.toLocaleString()}
          </div>
        </div>

        <div style={{
          backgroundColor: 'var(--bg-canvas)',
          padding: '0.65rem 0.85rem',
          borderRadius: 'var(--radius-sm)',
          border: '1px solid var(--border-dim)'
        }}>
          <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Columns</div>
          <div style={{ fontSize: '1.05rem', fontWeight: 700, color: '#fff', fontFamily: 'var(--font-mono)' }}>
            {activeTable.columns.length}
          </div>
        </div>

        <div style={{
          backgroundColor: 'var(--bg-canvas)',
          padding: '0.65rem 0.85rem',
          borderRadius: 'var(--radius-sm)',
          border: '1px solid var(--border-dim)'
        }}>
          <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Duplicate Rows</div>
          <div style={{
            fontSize: '1.05rem',
            fontWeight: 700,
            color: activeTable.duplicate_rows > 0 ? 'var(--clarify-color)' : 'var(--verified-color)',
            fontFamily: 'var(--font-mono)'
          }}>
            {activeTable.duplicate_rows}
          </div>
        </div>

        <div style={{
          backgroundColor: 'var(--bg-canvas)',
          padding: '0.65rem 0.85rem',
          borderRadius: 'var(--radius-sm)',
          border: '1px solid var(--border-dim)'
        }}>
          <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Primary Key(s)</div>
          <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#fff', fontFamily: 'var(--font-mono)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {activeTable.primary_keys?.length > 0 ? activeTable.primary_keys.join(', ') : 'None'}
          </div>
        </div>
      </div>

      {/* Columns Schema & Quality Table */}
      <div style={{
        overflowX: 'auto',
        backgroundColor: 'var(--bg-canvas)',
        border: '1px solid var(--border-dim)',
        borderRadius: 'var(--radius-sm)',
        marginBottom: allWarnings.length > 0 ? '1rem' : 0
      }}>
        <table style={{
          width: '100%',
          borderCollapse: 'collapse',
          fontSize: '0.75rem',
          textAlign: 'left'
        }}>
          <thead>
            <tr style={{
              backgroundColor: 'var(--bg-elevated)',
              borderBottom: '1px solid var(--border-subtle)',
              color: 'var(--text-muted)'
            }}>
              <th style={{ padding: '0.55rem 0.75rem', fontWeight: 600 }}>COLUMN</th>
              <th style={{ padding: '0.55rem 0.75rem', fontWeight: 600 }}>TYPE</th>
              <th style={{ padding: '0.55rem 0.75rem', fontWeight: 600 }}>NULLS</th>
              <th style={{ padding: '0.55rem 0.75rem', fontWeight: 600 }}>DISTINCT</th>
              <th style={{ padding: '0.55rem 0.75rem', fontWeight: 600 }}>ATTRIBUTES</th>
              <th style={{ padding: '0.55rem 0.75rem', fontWeight: 600 }}>SAMPLE VALUES</th>
            </tr>
          </thead>
          <tbody>
            {activeTable.columns.map((col, idx) => (
              <tr
                key={idx}
                style={{
                  borderBottom: '1px solid var(--border-dim)',
                  backgroundColor: idx % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.01)'
                }}
              >
                <td style={{ padding: '0.5rem 0.75rem', fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#fff' }}>
                  {col.name}
                  {col.is_primary_key && (
                    <span style={{
                      marginLeft: '6px',
                      fontSize: '0.65rem',
                      padding: '1px 4px',
                      backgroundColor: 'rgba(56, 189, 248, 0.15)',
                      color: '#38bdf8',
                      borderRadius: '2px'
                    }}>
                      PK
                    </span>
                  )}
                </td>
                <td style={{ padding: '0.5rem 0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
                  {col.type}
                </td>
                <td style={{ padding: '0.5rem 0.75rem' }}>
                  <span style={{
                    color: col.null_count > 0 ? 'var(--clarify-color)' : 'var(--text-muted)',
                    fontFamily: 'var(--font-mono)'
                  }}>
                    {col.null_count} ({col.null_percentage}%)
                  </span>
                </td>
                <td style={{ padding: '0.5rem 0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
                  {col.unique_count}
                </td>
                <td style={{ padding: '0.5rem 0.75rem' }}>
                  <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                    {col.is_numeric && (
                      <span style={{ fontSize: '0.65rem', padding: '1px 4px', backgroundColor: 'var(--bg-subtle)', borderRadius: '2px', color: 'var(--text-muted)' }}>
                        numeric
                      </span>
                    )}
                    {col.is_date && (
                      <span style={{ fontSize: '0.65rem', padding: '1px 4px', backgroundColor: 'var(--bg-subtle)', borderRadius: '2px', color: '#a78bfa' }}>
                        date
                      </span>
                    )}
                    {col.unit_or_currency && (
                      <span style={{ fontSize: '0.65rem', padding: '1px 4px', backgroundColor: 'rgba(16, 185, 129, 0.1)', borderRadius: '2px', color: 'var(--verified-color)' }}>
                        {col.unit_or_currency}
                      </span>
                    )}
                  </div>
                </td>
                <td style={{ padding: '0.5rem 0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-dim)', maxWidth: '240px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {col.sample_values?.slice(0, 3).map(v => String(v)).join(', ') || '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Real Quality & Integrity Notices */}
      {allWarnings.length > 0 && (
        <div style={{
          backgroundColor: 'var(--clarify-bg)',
          border: '1px solid var(--clarify-border)',
          borderRadius: 'var(--radius-sm)',
          padding: '0.75rem 1rem'
        }}>
          <div style={{
            fontSize: '0.7rem',
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
            fontWeight: 700,
            color: 'var(--clarify-color)',
            marginBottom: '0.4rem'
          }}>
            Data Quality & Integrity Diagnostic Notices:
          </div>
          <ul style={{ margin: 0, paddingLeft: '1.25rem', color: '#fcd34d', fontSize: '0.75rem' }}>
            {allWarnings.map((warn, i) => (
              <li key={i} style={{ marginBottom: '2px' }}>{warn}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

