import React from 'react';

export default function ResultDisplay({ result }) {
  if (!result) return null;

  const status = result.status;
  const isVerified = status === 'VERIFIED';
  const isRefusal = status === 'CANNOT_DETERMINE';
  const isClarify = status === 'NEEDS_CLARIFICATION';

  const formatValue = (val) => {
    if (val === null || val === undefined) return 'null';
    if (typeof val === 'number') {
      return val.toLocaleString('en-IN', {
        maximumFractionDigits: 2,
        minimumFractionDigits: Number.isInteger(val) ? 0 : 2
      });
    }
    if (typeof val === 'object') {
      return JSON.stringify(val, null, 2);
    }
    return String(val);
  };

  return (
    <div style={{
      marginBottom: '1.75rem',
      backgroundColor: 'var(--bg-surface)',
      border: isVerified
        ? '1px solid var(--verified-border)'
        : isRefusal
        ? '1px solid var(--refusal-border)'
        : '1px solid var(--clarify-border)',
      borderRadius: 'var(--radius-lg)',
      padding: '1.5rem',
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* Top accent bar */}
      <div style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        height: '3px',
        backgroundColor: isVerified
          ? 'var(--verified-color)'
          : isRefusal
          ? 'var(--refusal-color)'
          : 'var(--clarify-color)'
      }} />

      {/* Header Badge & Identifier */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '1.25rem',
        flexWrap: 'wrap',
        gap: '0.75rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.45rem',
            padding: '0.35rem 0.85rem',
            borderRadius: 'var(--radius-sm)',
            fontSize: '0.85rem',
            fontWeight: 800,
            letterSpacing: '0.05em',
            backgroundColor: isVerified
              ? 'var(--verified-bg)'
              : isRefusal
              ? 'var(--refusal-bg)'
              : 'var(--clarify-bg)',
            color: isVerified
              ? 'var(--verified-color)'
              : isRefusal
              ? 'var(--refusal-color)'
              : 'var(--clarify-color)',
            border: isVerified
              ? '1px solid var(--verified-border)'
              : isRefusal
              ? '1px solid var(--refusal-border)'
              : '1px solid var(--clarify-border)'
          }}>
            {isVerified && '✓ VERIFIED RESULT'}
            {isRefusal && '✕ CANNOT_DETERMINE'}
            {isClarify && '⚠ NEEDS_CLARIFICATION'}
            {!isVerified && !isRefusal && !isClarify && status}
          </span>

          <span style={{
            fontSize: '0.75rem',
            fontFamily: 'var(--font-mono)',
            color: 'var(--text-muted)'
          }}>
            ID: {result.result_id}
          </span>
        </div>

        <div style={{
          display: 'flex',
          gap: '0.5rem',
          fontSize: '0.75rem',
          fontFamily: 'var(--font-mono)',
          color: 'var(--text-secondary)'
        }}>
          {isVerified && (
            <>
              <span style={{
                padding: '2px 8px',
                backgroundColor: 'var(--bg-subtle)',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-dim)'
              }}>
                {result.execution?.execution_time_ms ? `${result.execution.execution_time_ms.toFixed(2)} ms` : '< 1 ms'}
              </span>
              <span style={{
                padding: '2px 8px',
                backgroundColor: 'var(--bg-subtle)',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-dim)'
              }}>
                {result.execution?.row_count ?? 1} row
              </span>
              <span style={{
                padding: '2px 8px',
                backgroundColor: 'var(--verified-bg)',
                color: 'var(--verified-color)',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--verified-border)',
                fontWeight: 600
              }}>
                Reproduction: MATCH ✓
              </span>
            </>
          )}
        </div>
      </div>

      {/* Main Body: Verified vs Refusal */}
      {isVerified ? (
        <div>
          <div style={{
            padding: '1.25rem',
            backgroundColor: 'var(--bg-canvas)',
            border: '1px solid var(--border-dim)',
            borderRadius: 'var(--radius-md)',
            marginBottom: '1rem'
          }}>
            <div style={{
              fontSize: '0.75rem',
              textTransform: 'uppercase',
              letterSpacing: '0.06em',
              color: 'var(--text-muted)',
              marginBottom: '0.35rem',
              fontWeight: 600
            }}>
              Proven Numerical Value
            </div>

            <div style={{
              fontSize: '2.5rem',
              fontWeight: 800,
              fontFamily: 'var(--font-mono)',
              letterSpacing: '-0.03em',
              color: '#fff',
              lineHeight: 1.1
            }}>
              {typeof result.answer === 'number' && (
                <span style={{ color: 'var(--verified-color)', marginRight: '6px' }}>
                  {result.question.toLowerCase().includes('revenue') || result.question.toLowerCase().includes('amount') ? '₹' : ''}
                </span>
              )}
              {formatValue(result.answer)}
            </div>

            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              marginTop: '0.85rem',
              fontSize: '0.8rem',
              color: 'var(--text-secondary)'
            }}>
              <span style={{ color: 'var(--verified-color)', fontWeight: 700 }}>&bull;</span>
              <span>Computed strictly from executed DuckDB bytecode and independently reproduced.</span>
            </div>
          </div>
        </div>
      ) : isRefusal ? (
        <div style={{
          padding: '1.25rem',
          backgroundColor: 'var(--refusal-bg)',
          border: '1px solid var(--refusal-border)',
          borderRadius: 'var(--radius-md)'
        }}>
          <div style={{
            fontSize: '0.8rem',
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
            color: 'var(--refusal-color)',
            fontWeight: 800,
            marginBottom: '0.35rem'
          }}>
            Boundary Refusal Triggered
          </div>

          <div style={{
            fontSize: '1.15rem',
            fontWeight: 700,
            color: '#fff',
            marginBottom: '0.85rem'
          }}>
            {result.reason || 'The dataset lacks necessary attributes to calculate an authoritative answer.'}
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '0.75rem',
            paddingTop: '0.85rem',
            borderTop: '1px solid rgba(244, 63, 94, 0.2)',
            fontSize: '0.8rem'
          }}>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Missing Requirement: </span>
              <strong style={{ color: '#fff', fontFamily: 'var(--font-mono)' }}>
                {result.missing_information?.length ? result.missing_information.join(', ') : 'Required column not found'}
              </strong>
            </div>

            <div>
              <span style={{ color: 'var(--text-muted)' }}>Execution Gate: </span>
              <strong style={{ color: 'var(--refusal-color)' }}>No SQL Executed (Zero Guessing)</strong>
            </div>

            <div>
              <span style={{ color: 'var(--text-muted)' }}>Integrity Rule: </span>
              <strong style={{ color: '#fff' }}>No Hallucinated Numbers</strong>
            </div>
          </div>
        </div>
      ) : (
        <div style={{
          padding: '1.25rem',
          backgroundColor: 'var(--clarify-bg)',
          border: '1px solid var(--clarify-border)',
          borderRadius: 'var(--radius-md)'
        }}>
          <div style={{
            fontSize: '0.8rem',
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
            color: 'var(--clarify-color)',
            fontWeight: 800,
            marginBottom: '0.35rem'
          }}>
            Ambiguity Discovered &bull; Clarification Needed
          </div>

          <div style={{
            fontSize: '1.15rem',
            fontWeight: 700,
            color: '#fff',
            marginBottom: '0.85rem'
          }}>
            {result.reason || 'Multiple valid interpretations exist in the data.'}
          </div>

          <div style={{
            fontSize: '0.85rem',
            color: 'var(--text-secondary)',
            lineHeight: 1.5,
            paddingTop: '0.75rem',
            borderTop: '1px solid rgba(245, 158, 11, 0.2)'
          }}>
            <p><strong>Suggested Resolution:</strong> Explicitly state required dimension or date convention (e.g. "DD/MM/YYYY" vs "MM/DD/YYYY", or specify currency exchange table) to enable proof execution.</p>
          </div>
        </div>
      )}
    </div>
  );
}

