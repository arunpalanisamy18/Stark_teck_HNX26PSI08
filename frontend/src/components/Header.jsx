import React from 'react';

export default function Header({ health }) {
  const isOk = health?.status === 'ok';

  return (
    <header style={{
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      paddingBottom: '1.25rem',
      borderBottom: '1px solid var(--border-dim)',
      marginBottom: '1.75rem',
      flexWrap: 'wrap',
      gap: '1rem'
    }}>
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <h1 style={{
            fontSize: '1.65rem',
            letterSpacing: '-0.03em',
            margin: 0,
            color: '#fff',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}>
            VERITAS
          </h1>
          <span style={{
            fontSize: '0.7rem',
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
            padding: '2px 8px',
            backgroundColor: 'var(--bg-subtle)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-sm)',
            color: 'var(--text-secondary)',
            fontWeight: 600
          }}>
            Forensic Engine
          </span>
        </div>
        <p style={{
          color: 'var(--text-muted)',
          fontSize: '0.85rem',
          margin: '3px 0 0 0',
          letterSpacing: '-0.01em'
        }}>
          Proof-Carrying Data Analyst &bull; Deterministic SQL Verification &bull; Zero Hallucination
        </p>
      </div>

      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '0.85rem',
        padding: '0.5rem 0.85rem',
        backgroundColor: 'var(--bg-surface)',
        border: '1px solid var(--border-dim)',
        borderRadius: 'var(--radius-md)'
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.45rem',
          fontSize: '0.8rem',
          fontWeight: 600,
          color: isOk ? 'var(--verified-color)' : 'var(--refusal-color)'
        }}>
          <span className="engine-pulse" style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: isOk ? 'var(--verified-color)' : 'var(--refusal-color)',
            display: 'inline-block'
          }} />
          <span>LOCAL ENGINE</span>
        </div>

        <div style={{ height: '14px', width: '1px', backgroundColor: 'var(--border-subtle)' }} />

        <div style={{ display: 'flex', flexDirection: 'column', fontSize: '0.75rem' }}>
          <span style={{ color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
            {health?.model || 'qwen2.5-coder:1.5b'}
          </span>
          <span style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>
            {isOk ? 'Local / GPU Ready' : 'Connecting to Ollama...'}
          </span>
        </div>

        <div style={{ height: '14px', width: '1px', backgroundColor: 'var(--border-subtle)' }} />

        <span style={{
          fontSize: '0.7rem',
          fontFamily: 'var(--font-mono)',
          color: 'var(--text-muted)',
          padding: '2px 6px',
          backgroundColor: 'var(--bg-canvas)',
          borderRadius: 'var(--radius-sm)'
        }}>
          DuckDB 1.5.6
        </span>
      </div>
    </header>
  );
}

