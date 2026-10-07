import React, { useState } from 'react';

export default function ProofCertificate({ certificate, verification, warnings }) {
  const [expanded, setExpanded] = useState(true);

  if (!certificate && !verification) return null;

  const checks = certificate?.checks || verification?.checks || [];
  const isOverallPass = certificate?.overall_verified || verification?.verified;

  const booleanFlags = [
    { key: 'sql_safe', label: 'SQL Safety', val: certificate?.sql_safe },
    { key: 'tables_exist', label: 'Tables Exist', val: certificate?.tables_exist },
    { key: 'columns_exist', label: 'Columns Exist', val: certificate?.columns_exist },
    { key: 'data_quality_checked', label: 'Data Quality Audited', val: certificate?.data_quality_checked },
    { key: 'ambiguity_checked', label: 'Ambiguity Cleared', val: certificate?.ambiguity_checked },
    { key: 'join_checked', label: 'Join Integrity', val: certificate?.join_checked },
    { key: 'result_reproduced', label: 'Re-Execution Match', val: certificate?.result_reproduced },
    { key: 'answer_from_execution', label: 'Execution Provenance', val: certificate?.answer_from_execution },
  ];

  return (
    <div style={{
      marginBottom: '1.5rem',
      backgroundColor: 'var(--bg-surface)',
      border: '1px solid var(--border-dim)',
      borderRadius: 'var(--radius-md)',
      overflow: 'hidden'
    }}>
      <div
        onClick={() => setExpanded(!expanded)}
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '0.85rem 1.25rem',
          backgroundColor: 'var(--bg-subtle)',
          cursor: 'pointer',
          userSelect: 'none',
          borderBottom: expanded ? '1px solid var(--border-dim)' : 'none'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span style={{
            fontSize: '0.75rem',
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
            fontWeight: 700,
            color: 'var(--text-primary)'
          }}>
            Proof Certificate & Audit Record
          </span>

          <span style={{
            fontSize: '0.7rem',
            fontWeight: 700,
            padding: '2px 8px',
            borderRadius: 'var(--radius-sm)',
            backgroundColor: isOverallPass ? 'var(--verified-bg)' : 'var(--refusal-bg)',
            color: isOverallPass ? 'var(--verified-color)' : 'var(--refusal-color)',
            border: isOverallPass ? '1px solid var(--verified-border)' : '1px solid var(--refusal-border)'
          }}>
            {isOverallPass ? 'VERIFIED AUDIT' : 'REFUSAL AUDIT'}
          </span>
        </div>

        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          {expanded ? '▲ Collapse' : '▼ Expand'}
        </span>
      </div>

      {expanded && (
        <div style={{ padding: '1.25rem' }}>
          {/* Boolean verification checks grid */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))',
            gap: '0.5rem',
            marginBottom: '1.25rem'
          }}>
            {booleanFlags.map((flag, idx) => {
              const pass = flag.val === true;
              return (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '0.45rem 0.65rem',
                    backgroundColor: 'var(--bg-canvas)',
                    border: '1px solid var(--border-dim)',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: '0.75rem'
                  }}
                >
                  <span style={{ color: 'var(--text-secondary)' }}>{flag.label}</span>
                  <span style={{
                    fontFamily: 'var(--font-mono)',
                    fontWeight: 700,
                    color: pass ? 'var(--verified-color)' : 'var(--refusal-color)'
                  }}>
                    {pass ? '✓ PASS' : '✕ NO'}
                  </span>
                </div>
              );
            })}
          </div>

          {/* Detailed Verification Checks List */}
          {checks.length > 0 && (
            <div>
              <div style={{
                fontSize: '0.7rem',
                textTransform: 'uppercase',
                letterSpacing: '0.06em',
                color: 'var(--text-muted)',
                fontWeight: 600,
                marginBottom: '0.5rem'
              }}>
                10-Point Independent Verification Log
              </div>

              <div style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '0.4rem',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.78rem'
              }}>
                {checks.map((chk, idx) => (
                  <div
                    key={idx}
                    style={{
                      display: 'flex',
                      alignItems: 'baseline',
                      padding: '0.4rem 0.65rem',
                      backgroundColor: 'var(--bg-subtle)',
                      border: '1px solid var(--border-dim)',
                      borderRadius: 'var(--radius-sm)',
                      gap: '0.65rem'
                    }}
                  >
                    <span style={{
                      color: chk.status === 'PASS' ? 'var(--verified-color)' : chk.status === 'WARN' ? 'var(--clarify-color)' : 'var(--refusal-color)',
                      fontWeight: 700,
                      flexShrink: 0
                    }}>
                      [{chk.status}]
                    </span>
                    <strong style={{ color: '#fff', flexShrink: 0 }}>{chk.name}:</strong>
                    <span style={{ color: 'var(--text-secondary)' }}>{chk.details}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Data Quality Notices */}
          {warnings && warnings.length > 0 && (
            <div style={{ marginTop: '1rem', paddingTop: '0.85rem', borderTop: '1px solid var(--border-dim)' }}>
              <div style={{
                fontSize: '0.7rem',
                textTransform: 'uppercase',
                letterSpacing: '0.06em',
                color: 'var(--clarify-color)',
                fontWeight: 700,
                marginBottom: '0.35rem'
              }}>
                Data Quality Notices
              </div>
              <ul style={{ listStyle: 'none', paddingLeft: 0, fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                {warnings.map((w, idx) => (
                  <li key={idx} style={{ marginBottom: '2px' }}>
                    &bull; {w}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

