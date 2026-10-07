import React from 'react';

export default function ProofPipeline({ result, loading, activeStage, onSelectStage }) {
  // Determine states of each stage
  const getStageState = (stageKey) => {
    if (loading) {
      return { status: 'RUNNING', badge: '...', color: 'var(--text-muted)' };
    }
    if (!result) {
      return { status: 'IDLE', badge: 'READY', color: 'var(--text-dim)' };
    }

    const isVerified = result.status === 'VERIFIED';
    const isRefusal = result.status === 'CANNOT_DETERMINE';
    const isClarify = result.status === 'NEEDS_CLARIFICATION';

    switch (stageKey) {
      case 'question':
        return { status: 'PASS', badge: '✓ PARSED', color: 'var(--verified-color)' };

      case 'plan':
        if (isVerified) return { status: 'PASS', badge: '✓ BOUNDED', color: 'var(--verified-color)' };
        if (isRefusal) return { status: 'REFUSED', badge: '✕ UNANSWERABLE', color: 'var(--refusal-color)' };
        if (isClarify) return { status: 'AMBIGUOUS', badge: '⚠ AMBIGUOUS', color: 'var(--clarify-color)' };
        return { status: 'FAIL', badge: '✕ FAIL', color: 'var(--refusal-color)' };

      case 'sql':
        if (isVerified) return { status: 'PASS', badge: '✓ SAFE SQL', color: 'var(--verified-color)' };
        return { status: 'HALTED', badge: '— HALTED', color: 'var(--text-dim)' };

      case 'execute':
        if (isVerified) return {
          status: 'PASS',
          badge: `✓ ${result.execution?.execution_time_ms ? result.execution.execution_time_ms.toFixed(1) + 'ms' : 'EXECUTED'}`,
          color: 'var(--verified-color)'
        };
        return { status: 'HALTED', badge: '— HALTED', color: 'var(--text-dim)' };

      case 'rerun':
        if (isVerified) return { status: 'PASS', badge: '✓ MATCH 100%', color: 'var(--verified-color)' };
        return { status: 'HALTED', badge: '— HALTED', color: 'var(--text-dim)' };

      case 'verify':
        if (isVerified) return { status: 'PASS', badge: '✓ PROVEN', color: 'var(--verified-color)' };
        if (isRefusal) return { status: 'AUDIT', badge: 'REFUSAL CERT', color: 'var(--refusal-color)' };
        if (isClarify) return { status: 'AUDIT', badge: 'PROVENANCE', color: 'var(--clarify-color)' };
        return { status: 'FAIL', badge: '✕ UNVERIFIED', color: 'var(--refusal-color)' };

      default:
        return { status: 'IDLE', badge: '—', color: 'var(--text-dim)' };
    }
  };

  const STAGES = [
    { id: 'question', num: '01', title: 'QUESTION', desc: 'Intent Extraction' },
    { id: 'plan', num: '02', title: 'PLAN', desc: 'Schema Bound Check' },
    { id: 'sql', num: '03', title: 'SQL SYNTHESIS', desc: 'Read-Only DuckDB' },
    { id: 'execute', num: '04', title: 'EXECUTION', desc: 'Physical Buffer' },
    { id: 'rerun', num: '05', title: 'REPRODUCTION', desc: 'Independent Re-Run' },
    { id: 'verify', num: '06', title: 'VERIFIER', desc: '10-Point Proof' }
  ];

  return (
    <div style={{
      marginBottom: '1.75rem',
      padding: '1.15rem 1.25rem',
      backgroundColor: 'var(--bg-surface)',
      border: '1px solid var(--border-dim)',
      borderRadius: 'var(--radius-md)'
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '0.85rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{
            fontSize: '0.75rem',
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
            fontWeight: 700,
            color: 'var(--text-secondary)'
          }}>
            Proof-Carrying Pipeline
          </span>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
            &bull; Traceable execution & independent verification stages
          </span>
        </div>

        <span style={{
          fontSize: '0.7rem',
          fontFamily: 'var(--font-mono)',
          color: 'var(--text-muted)'
        }}>
          AI proposes &rarr; Code calculates &rarr; Verifier proves
        </span>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
        gap: '0.65rem'
      }}>
        {STAGES.map((stg) => {
          const state = getStageState(stg.id);
          const isSelected = activeStage === stg.id;

          return (
            <button
              key={stg.id}
              type="button"
              onClick={() => onSelectStage(stg.id)}
              style={{
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                padding: '0.65rem 0.75rem',
                backgroundColor: isSelected ? 'var(--bg-elevated)' : 'var(--bg-subtle)',
                border: isSelected
                  ? `1px solid ${state.color}`
                  : '1px solid var(--border-dim)',
                borderRadius: 'var(--radius-sm)',
                cursor: 'pointer',
                textAlign: 'left',
                minHeight: '74px'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
                <span style={{
                  fontSize: '0.65rem',
                  fontFamily: 'var(--font-mono)',
                  color: 'var(--text-dim)',
                  fontWeight: 600
                }}>
                  {stg.num}
                </span>
                <span style={{
                  fontSize: '0.65rem',
                  fontFamily: 'var(--font-mono)',
                  fontWeight: 700,
                  color: state.color,
                  letterSpacing: '0.03em'
                }}>
                  {state.badge}
                </span>
              </div>

              <div>
                <div style={{
                  fontSize: '0.8rem',
                  fontWeight: 700,
                  letterSpacing: '-0.01em',
                  color: 'var(--text-primary)',
                  marginTop: '0.35rem'
                }}>
                  {stg.title}
                </div>
                <div style={{
                  fontSize: '0.65rem',
                  color: 'var(--text-muted)',
                  marginTop: '1px'
                }}>
                  {stg.desc}
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

