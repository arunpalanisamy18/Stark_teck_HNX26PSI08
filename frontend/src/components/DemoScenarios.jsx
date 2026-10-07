import React from 'react';

const SCENARIOS = [
  {
    label: 'Clean Query (2025 Revenue)',
    question: 'What was the total revenue in 2025?',
    badge: 'VERIFIED Expected',
    badgeColor: 'var(--verified-color)',
    datasetId: 'demo'
  },
  {
    label: 'Multi-Table Join (Segment)',
    question: 'What is the total revenue by customer segment?',
    badge: 'JOIN Proof',
    badgeColor: '#38bdf8',
    datasetId: 'demo'
  },
  {
    label: 'Missing Metric (Profit)',
    question: 'What was the profit in 2025?',
    badge: 'Refusal Test',
    badgeColor: 'var(--refusal-color)',
    datasetId: 'demo'
  },
  {
    label: 'Ambiguous Date (February)',
    question: 'What was the total revenue in February?',
    badge: 'Ambiguity Test',
    badgeColor: 'var(--clarify-color)',
    datasetId: 'demo'
  },
  {
    label: 'Nonexistent Entity (C999)',
    question: 'What was the revenue for customer C999?',
    badge: 'Boundary Test',
    badgeColor: 'var(--refusal-color)',
    datasetId: 'demo'
  }
];

export default function DemoScenarios({ onSelectScenario, activeQuestion }) {
  return (
    <div style={{
      marginBottom: '1.5rem',
      padding: '0.85rem 1rem',
      backgroundColor: 'var(--bg-surface)',
      border: '1px solid var(--border-dim)',
      borderRadius: 'var(--radius-md)'
    }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '0.65rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{
            fontSize: '0.7rem',
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
            color: 'var(--text-muted)',
            fontWeight: 700
          }}>
            Evaluator Scenarios
          </span>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
            &bull; Instant 1-click test triggers for judges
          </span>
        </div>
      </div>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
        {SCENARIOS.map((sc, idx) => {
          const isSelected = activeQuestion === sc.question;
          return (
            <button
              key={idx}
              type="button"
              onClick={() => onSelectScenario(sc.question, sc.datasetId)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.45rem',
                padding: '0.35rem 0.65rem',
                fontSize: '0.75rem',
                color: isSelected ? '#fff' : 'var(--text-secondary)',
                backgroundColor: isSelected ? 'var(--bg-elevated)' : 'var(--bg-subtle)',
                border: isSelected ? '1px solid var(--border-accent)' : '1px solid var(--border-dim)',
                borderRadius: 'var(--radius-sm)',
                cursor: 'pointer',
                textAlign: 'left'
              }}
            >
              <span style={{
                width: '6px',
                height: '6px',
                borderRadius: '50%',
                backgroundColor: sc.badgeColor
              }} />
              <span style={{ fontWeight: 500 }}>{sc.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

