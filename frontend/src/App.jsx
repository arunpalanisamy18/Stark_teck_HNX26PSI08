import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import DataUpload from './components/DataUpload';
import DataProfilePanel from './components/DataProfilePanel';

import ProofPipeline from './components/ProofPipeline';
import ResultDisplay from './components/ResultDisplay';
import SqlViewer from './components/SqlViewer';
import EvidencePanel from './components/EvidencePanel';
import ProofCertificate from './components/ProofCertificate';
import { fetchHealth, askQuestion, fetchDatasetProfile } from './services/api';

export default function App() {
  const [health, setHealth] = useState(null);
  const [datasetId, setDatasetId] = useState('demo');
  const [datasetProfile, setDatasetProfile] = useState(null);
  const [profileLoading, setProfileLoading] = useState(false);

  const [question, setQuestion] = useState('What was the total revenue in 2025?');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeStage, setActiveStage] = useState('verify');

  // Load health check and initial demo profile on mount
  useEffect(() => {
    fetchHealth()
      .then(data => setHealth(data))
      .catch(err => setHealth({ status: 'offline', error: String(err) }));

    loadProfile('demo');
  }, []);

  const loadProfile = async (id) => {
    setProfileLoading(true);
    try {
      const data = await fetchDatasetProfile(id);
      setDatasetProfile(data);
    } catch {
      // If profile fetch fails, keep null
    } finally {
      setProfileLoading(false);
    }
  };

  // Called when user uploads files in 01 DATA SOURCE
  const handleDatasetLoaded = (newProfile) => {
    setDatasetId(newProfile.dataset_id);
    setDatasetProfile(newProfile);
    setResult(null);
    setError(null);
  };

  // Submit query to backend
  const handleAsk = async (e) => {
    if (e) e.preventDefault();
    if (!question.trim() || loading) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await askQuestion(question.trim(), datasetId);
      setResult(data);
      setActiveStage(data.status === 'VERIFIED' ? 'verify' : 'plan');
    } catch (err) {
      setError(String(err.message || err));
    } finally {
      setLoading(false);
    }
  };


  return (
    <div className="app-shell">
      {/* Header with live local engine indicator */}
      <Header health={health} />

      {/* 01 DATA SOURCE: Primary CSV & Multi-Table Ingestion Chamber */}
      <DataUpload
        activeDatasetId={datasetId}
        onDatasetLoaded={handleDatasetLoaded}
        currentProfile={datasetProfile}
      />

      {/* 02 DATA PROFILE: Schema, Statistics & Integrity Diagnostic Panel */}
      <DataProfilePanel
        profile={datasetProfile}
        loading={profileLoading}
      />

      {/* 03 ASK YOUR DATA: Analytical Query Console + Compact Demo Scenarios */}
      <div style={{
        marginBottom: '1.75rem',
        padding: '1.25rem',
        backgroundColor: 'var(--bg-surface)',
        border: '1px solid var(--border-dim)',
        borderRadius: 'var(--radius-md)'
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '0.65rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{
              fontSize: '0.75rem',
              fontFamily: 'var(--font-mono)',
              fontWeight: 700,
              color: '#a78bfa',
              backgroundColor: 'rgba(167, 139, 250, 0.12)',
              padding: '2px 6px',
              borderRadius: 'var(--radius-sm)'
            }}>
              03
            </span>
            <span style={{
              fontSize: '0.75rem',
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              fontWeight: 700,
              color: 'var(--text-primary)'
            }}>
              Ask Your Data &bull; Analytical Query Console
            </span>
          </div>

          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
            Target: <strong style={{ color: '#fff' }}>[{datasetId}]</strong> Active Catalog
          </span>
        </div>


        {/* Input Form */}
        <form onSubmit={handleAsk} style={{ display: 'flex', gap: '0.65rem', flexWrap: 'wrap' }}>
          <div style={{ position: 'relative', flex: 1, minWidth: '280px' }}>
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask a factual question (e.g., 'What was the total revenue in 2025?')..."
              style={{
                width: '100%',
                padding: '0.85rem 1rem',
                fontSize: '0.95rem',
                fontFamily: 'var(--font-display)',
                backgroundColor: 'var(--bg-canvas)',
                color: '#fff',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                outline: 'none',
                transition: 'border-color 0.15s ease'
              }}
              onFocus={(e) => e.target.style.borderColor = 'var(--verified-color)'}
              onBlur={(e) => e.target.style.borderColor = 'var(--border-subtle)'}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              padding: '0.85rem 1.65rem',
              fontSize: '0.9rem',
              fontWeight: 700,
              backgroundColor: loading ? 'var(--bg-elevated)' : 'var(--verified-color)',
              color: loading ? 'var(--text-muted)' : '#041d13',
              border: 'none',
              borderRadius: 'var(--radius-sm)',
              cursor: loading ? 'not-allowed' : 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.5rem',
              letterSpacing: '0.02em'
            }}
          >
            {loading ? (
              <>
                <span className="engine-pulse" style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: 'var(--text-muted)' }} />
                <span>Verifying Proof...</span>
              </>
            ) : (
              <span>Run Proof Pipeline &rarr;</span>
            )}
          </button>
        </form>
      </div>

      {/* Network / Client Error Notice */}
      {error && (
        <div style={{
          marginBottom: '1.5rem',
          padding: '1rem',
          backgroundColor: 'var(--refusal-bg)',
          border: '1px solid var(--refusal-border)',
          borderRadius: 'var(--radius-md)',
          color: 'var(--refusal-color)',
          fontSize: '0.85rem'
        }}>
          <strong>Execution Notice:</strong> {error}
        </div>
      )}

      {/* 04 PROOF PIPELINE: Interactive Multi-Stage Stepper */}
      <ProofPipeline
        result={result}
        loading={loading}
        activeStage={activeStage}
        onSelectStage={setActiveStage}
      />

      {/* 05 RESULT: Primary Verified Answer vs Refusal Notice */}
      <ResultDisplay result={result} />

      {/* 06 AUDIT & EVIDENCE: Executed SQL, Tuple Evidence & Proof Certificate */}
      {result && (
        <SqlViewer
          sql={result.sql}
          execution={result.execution}
        />
      )}

      {result && result.execution && (
        <EvidencePanel
          execution={result.execution}
          evidence={result.evidence}
          result={result}
        />
      )}

      {result && (
        <ProofCertificate
          certificate={result.proof_certificate}
          verification={result.verification}
          warnings={result.warnings}
        />
      )}
    </div>
  );
}
