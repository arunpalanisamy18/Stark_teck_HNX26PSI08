import React, { useRef, useState } from 'react';
import { uploadDatasetFile } from '../services/api';

export default function DataUpload({ activeDatasetId, onDatasetLoaded, currentProfile }) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const fileInputRef = useRef(null);

  const formatFileSize = (bytes) => {
    if (!bytes && bytes !== 0) return '';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const handleFiles = async (files) => {
    if (!files || files.length === 0) return;
    const fileList = Array.from(files).filter(f => {
      const name = f.name.toLowerCase();
      return name.endsWith('.csv') || name.endsWith('.xlsx') || name.endsWith('.xls');
    });

    if (fileList.length === 0) {
      setUploadError('Please select CSV or Excel (.xlsx) files.');
      return;
    }

    setUploading(true);
    setUploadError(null);

    try {
      let currentId = null;
      let lastProfile = null;
      const loadedInfoList = [];

      // Upload sequentially to attach to same dataset if multiple
      for (const file of fileList) {
        const profile = await uploadDatasetFile(file, currentId);
        currentId = profile.dataset_id;
        lastProfile = profile;

        // Find the table profile matching this file
        const baseName = file.name.replace(/\.[^/.]+$/, '').toLowerCase().replace(/[^a-z0-9_]/g, '_');
        const matchedTable = profile.tables.find(t => t.table.toLowerCase().includes(baseName)) || profile.tables[profile.tables.length - 1];

        loadedInfoList.push({
          name: file.name,
          size: file.size,
          tableName: matchedTable ? matchedTable.table : baseName,
          rows: matchedTable ? matchedTable.rows : 0,
          columns: matchedTable ? matchedTable.columns.length : 0,
          timestamp: new Date().toLocaleTimeString()
        });
      }

      setUploadedFiles(prev => [...loadedInfoList, ...prev]);
      if (lastProfile) {
        onDatasetLoaded(lastProfile);
      }
    } catch (err) {
      setUploadError(err.message || 'File upload failed');
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const onDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const onDragLeave = () => {
    setIsDragging(false);
  };

  const onDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files) {
      handleFiles(e.dataTransfer.files);
    }
  };

  return (
    <div style={{
      marginBottom: '1.75rem',
      backgroundColor: 'var(--bg-surface)',
      border: '1px solid var(--border-dim)',
      borderRadius: 'var(--radius-md)',
      padding: '1.25rem'
    }}>
      {/* Section Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '0.85rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{
            fontSize: '0.75rem',
            fontFamily: 'var(--font-mono)',
            fontWeight: 700,
            color: 'var(--verified-color)',
            backgroundColor: 'var(--verified-bg)',
            padding: '2px 6px',
            borderRadius: 'var(--radius-sm)'
          }}>
            01
          </span>
          <span style={{
            fontSize: '0.75rem',
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
            fontWeight: 700,
            color: 'var(--text-primary)'
          }}>
            Data Source &bull; Ingestion Chamber
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
            Active Dataset ID: <strong style={{ color: '#fff' }}>[{activeDatasetId || 'none'}]</strong>
          </span>
          {activeDatasetId === 'demo' && (
            <span style={{
              fontSize: '0.7rem',
              padding: '1px 6px',
              backgroundColor: 'var(--bg-subtle)',
              border: '1px solid var(--border-dim)',
              borderRadius: 'var(--radius-sm)',
              color: 'var(--text-muted)'
            }}>
              Fallback Demo Ready
            </span>
          )}
        </div>
      </div>

      {/* Drag & Drop Upload Zone */}
      <div
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        onClick={() => fileInputRef.current && fileInputRef.current.click()}
        style={{
          border: isDragging ? '2px dashed var(--verified-color)' : '1px dashed var(--border-accent)',
          borderRadius: 'var(--radius-sm)',
          backgroundColor: isDragging ? 'var(--verified-bg)' : 'var(--bg-canvas)',
          padding: '1.5rem 1rem',
          textAlign: 'center',
          cursor: uploading ? 'wait' : 'pointer',
          transition: 'all 0.15s ease-in-out'
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".csv,.xlsx,.xls"
          style={{ display: 'none' }}
          onChange={(e) => handleFiles(e.target.files)}
          disabled={uploading}
        />

        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.35rem' }}>
          <div style={{
            fontSize: '1.25rem',
            lineHeight: 1,
            color: isDragging ? 'var(--verified-color)' : 'var(--text-secondary)'
          }}>
            {uploading ? '⚙' : '⇪'}
          </div>
          <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>
            {uploading ? 'Ingesting & Profiling Data...' : 'Drop CSV or Excel files here, or click to browse'}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Supports multi-CSV upload for multi-table relational schemas (.csv, .xlsx)
          </div>
        </div>
      </div>

      {/* Upload Error Banner */}
      {uploadError && (
        <div style={{
          marginTop: '0.75rem',
          padding: '0.65rem 0.85rem',
          backgroundColor: 'var(--refusal-bg)',
          border: '1px solid var(--refusal-border)',
          borderRadius: 'var(--radius-sm)',
          color: 'var(--refusal-color)',
          fontSize: '0.75rem'
        }}>
          <strong>Upload Error:</strong> {uploadError}
        </div>
      )}

      {/* Ingested Tables List */}
      {(uploadedFiles.length > 0 || (currentProfile && currentProfile.tables)) && (
        <div style={{ marginTop: '0.85rem' }}>
          <div style={{
            fontSize: '0.7rem',
            textTransform: 'uppercase',
            letterSpacing: '0.06em',
            color: 'var(--text-muted)',
            marginBottom: '0.4rem',
            fontWeight: 600
          }}>
            Loaded Tables in Active Catalog:
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            {currentProfile?.tables?.map((tbl, i) => (
              <div
                key={i}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.35rem 0.65rem',
                  backgroundColor: 'var(--bg-canvas)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.75rem'
                }}
              >
                <span style={{ color: 'var(--verified-color)', fontSize: '0.75rem' }}>✓</span>
                <strong style={{ color: '#fff', fontFamily: 'var(--font-mono)' }}>{tbl.table}</strong>
                <span style={{ color: 'var(--text-muted)' }}>
                  {tbl.rows.toLocaleString()} rows &bull; {tbl.columns.length} cols
                </span>
                {tbl.duplicate_rows > 0 && (
                  <span style={{
                    fontSize: '0.65rem',
                    color: 'var(--clarify-color)',
                    backgroundColor: 'var(--clarify-bg)',
                    padding: '1px 4px',
                    borderRadius: '2px'
                  }}>
                    {tbl.duplicate_rows} dups
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

