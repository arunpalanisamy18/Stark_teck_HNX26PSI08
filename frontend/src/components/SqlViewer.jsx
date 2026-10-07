import React, { useState } from 'react';

export default function SqlViewer({ sql, execution }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (!sql) return;
    navigator.clipboard.writeText(sql);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!sql) {
    return (
      <div style={{
        marginBottom: '1.5rem',
        padding: '1.25rem',
        backgroundColor: 'var(--bg-surface)',
        border: '1px solid var(--border-dim)',
        borderRadius: 'var(--radius-md)',
        fontSize: '0.85rem',
        color: 'var(--text-muted)'
      }}>
        <div style={{
          fontSize: '0.75rem',
          textTransform: 'uppercase',
          letterSpacing: '0.08em',
          fontWeight: 700,
          color: 'var(--text-secondary)',
          marginBottom: '0.5rem'
        }}>
          SQL Execution Record
        </div>
        <div>No SQL was generated or executed. The verification engine refused execution at the boundary check to prevent incorrect or unprovable answers.</div>
      </div>
    );
  }

  const lines = sql.trim().split('\n');

  return (
    <div style={{
      marginBottom: '1.5rem',
      backgroundColor: 'var(--bg-code)',
      border: '1px solid var(--border-dim)',
      borderRadius: 'var(--radius-md)',
      overflow: 'hidden'
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '0.65rem 1rem',
        backgroundColor: 'var(--bg-surface)',
        borderBottom: '1px solid var(--border-dim)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <span style={{
            fontSize: '0.75rem',
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
            fontWeight: 700,
            color: 'var(--text-primary)'
          }}>
            Executed SQL
          </span>
          <span style={{
            fontSize: '0.65rem',
            fontFamily: 'var(--font-mono)',
            padding: '2px 6px',
            backgroundColor: 'var(--bg-canvas)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-sm)',
            color: 'var(--text-secondary)'
          }}>
            DuckDB In-Process
          </span>
        </div>

        <button
          type="button"
          onClick={handleCopy}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.35rem',
            fontSize: '0.75rem',
            color: copied ? 'var(--verified-color)' : 'var(--text-secondary)',
            backgroundColor: 'var(--bg-subtle)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-sm)',
            padding: '0.3rem 0.65rem',
            cursor: 'pointer'
          }}
        >
          {copied ? '✓ Copied' : 'Copy Query'}
        </button>
      </div>

      <div style={{
        padding: '1rem',
        fontFamily: 'var(--font-mono)',
        fontSize: '0.85rem',
        lineHeight: 1.6,
        color: '#e2e8f0',
        overflowX: 'auto',
        display: 'flex'
      }}>
        {/* Line numbers */}
        <div style={{
          color: 'var(--text-dim)',
          paddingRight: '1rem',
          userSelect: 'none',
          textAlign: 'right',
          borderRight: '1px solid var(--border-dim)',
          marginRight: '1rem'
        }}>
          {lines.map((_, i) => (
            <div key={i}>{i + 1}</div>
          ))}
        </div>

        {/* Code body */}
        <div style={{ flex: 1, whiteSpace: 'pre' }}>
          {sql}
        </div>
      </div>
    </div>
  );
}

